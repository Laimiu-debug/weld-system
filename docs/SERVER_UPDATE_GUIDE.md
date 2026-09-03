# 生产服务器更新手册

本文用于更新当前焊序生产环境。命令已经在现有服务器上验证。

## 环境信息

- SSH：`ubuntu@43.142.188.252`
- 项目目录：`/home/ubuntu/weld-system`
- 分支：`main`
- Compose 项目：`weld-system`
- 用户门户：<https://laimiu.sdhaohan.cn>
- API 健康检查：<https://api.sdhaohan.cn/api/v1/health>

密钥、`.env`、`backend/.env.production` 和数据库备份不得提交到 Git。

## 禁止使用的旧流程

不要运行 `deploy_from_local.py` 或任何包含以下命令的更新脚本：

```bash
docker compose down -v
docker system prune -af --volumes
rm -rf /home/ubuntu/weld-system
```

这些命令可能删除 PostgreSQL、Redis、上传文件或证书相关数据。日常更新只使用下面的增量流程。

## 一、在本地检查并推送

在仓库根目录执行：

```bash
git status -sb
git diff --check
git log -1 --oneline
git push origin main
```

确认需要发布的提交已经出现在远端 `main`。`.playwright-cli/`、`tmp_*`、日志、备份和本机调试文件不要提交。

## 二、连接服务器并预检

Windows PowerShell：

```powershell
ssh -i "$HOME\.ssh\id_ed25519" ubuntu@43.142.188.252
```

登录后执行：

```bash
set -e
cd /home/ubuntu/weld-system

git fetch origin main
git status -sb
git log -1 --oneline
docker compose ps
df -h /
```

`git status` 应当没有未提交文件。如果服务器工作区有修改，先检查来源，不要直接 `reset --hard`。确认只是历史部署产物后，可以保存为可恢复的 stash：

```bash
git stash push -u -m "pre-deploy-$(date +%Y%m%d-%H%M%S)"
git status -sb
```

如果 stash 清理失败，停止部署并处理文件权限；不要覆盖未知的服务器修改。

## 三、部署前备份

```bash
set -e
cd /home/ubuntu/weld-system

stamp=$(date +%Y%m%d-%H%M%S)
backup_dir=/home/ubuntu/weld-backups
backup_file="$backup_dir/weld_db_pre_deploy_$stamp.sql.gz"
mkdir -p "$backup_dir"

docker compose exec -T postgres sh -c \
  'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  | gzip -9 > "$backup_file"

test -s "$backup_file"
ls -lh "$backup_file"
```

只有备份文件存在且大小非零时才继续。

## 四、拉取、构建和迁移

```bash
set -e
cd /home/ubuntu/weld-system

git pull --ff-only origin main
git status -sb
git log -1 --oneline

docker compose build backend frontend admin-portal

# 使用新后端镜像执行迁移，但暂不切换在线容器。
docker compose run --rm --no-deps backend alembic upgrade head
docker compose run --rm --no-deps backend alembic current
```

生产后端镜像从 `backend/requirements.prod.txt` 安装依赖。新增运行时 Python 库时，必须同时更新该文件和 `backend/pyproject.toml`。

如果构建或迁移失败，不要重启在线容器。修复问题后重新构建；数据库恢复操作必须先评估迁移是否已经部分执行。

## 五、切换服务

```bash
set -e
cd /home/ubuntu/weld-system

docker compose up -d --no-deps \
  backend celery-worker celery-beat frontend admin-portal

# 等后端健康后再刷新 Nginx，避免容器 IP 更新后仍使用旧上游地址。
for i in $(seq 1 20); do
  state=$(docker inspect -f '{{.State.Health.Status}}' weld_backend)
  echo "backend=$state"
  [ "$state" = healthy ] && break
  sleep 3
done
test "$(docker inspect -f '{{.State.Health.Status}}' weld_backend)" = healthy

docker compose up -d --no-deps --force-recreate nginx
```

这套流程不会停止 PostgreSQL、Redis、备份服务或 Certbot，也不会删除数据卷。

## 六、部署后验证

```bash
set -e
cd /home/ubuntu/weld-system

docker compose ps
docker compose exec -T backend alembic current
curl -fsS --max-time 15 https://api.sdhaohan.cn/api/v1/health
curl -fsS -o /dev/null -w 'portal_status=%{http_code}\n' \
  --max-time 15 https://laimiu.sdhaohan.cn/

docker compose logs --since=10m backend celery-worker celery-beat nginx \
  | grep -Ei 'traceback|exception|critical|panic' || true
```

验收标准：

- 后端、Celery Worker、Celery Beat、Nginx、PostgreSQL 和 Redis 为 `healthy`；
- API 返回 `status: ready`，PostgreSQL 与 Redis 检查均为 `ok: true`；
- `alembic current` 与仓库 head 一致；
- 用户门户返回 HTTP 200；
- 最近日志没有新的异常堆栈。

## 七、故障处理与回滚

### 新容器无法健康启动

```bash
cd /home/ubuntu/weld-system
docker compose logs --tail=200 backend
docker compose logs --tail=200 nginx
docker inspect weld_backend --format '{{json .State.Health}}'
```

不要使用 `down -v`。优先修复配置或代码后重新构建单个服务。

### 代码回滚

推荐在本地对问题提交执行 `git revert`，推送新的回滚提交，再按本手册重新部署。这样服务器和 GitHub 历史始终一致：

```bash
git revert <bad-commit>
git push origin main
```

### 数据库回滚

不要默认执行 `alembic downgrade -1`。先检查迁移文件、线上写入和兼容性；只有确认新版本已停止写入并制定恢复方案后，才能降级或使用部署前备份恢复。

## 常见问题

| 现象 | 检查与处理 |
| --- | --- |
| `git pull` 提示本地修改 | `git diff --stat` 检查来源；保存 stash，禁止强制重置未知修改 |
| 后端构建很慢 | 首次下载系统/Python 依赖可能较慢；在线旧容器在构建期间仍可服务 |
| 更新后出现 502 | 等后端健康，然后强制重建 Nginx 以刷新上游地址 |
| 数据库字段不存在 | 检查 `alembic current`，确认迁移已由新后端镜像执行 |
| PDF 下载 500 | 检查 WeasyPrint、pydyf、ReportLab 版本和后端日志；生产依赖必须写入 `requirements.prod.txt` |
| 本机 HTTPS 无法推 GitHub | 可测试 `ssh -T git@github.com`，然后使用 Git SSH 地址推送 |
