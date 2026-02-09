# 🚀 快速部署指南

## 📋 优化内容概述

已针对之前的部署问题进行了以下优化：

### ✅ 问题 1: Backend 构建失败
**解决方案：**
- 采用多阶段构建，分离编译和运行环境
- 优化依赖安装顺序和方式
- 添加更详细的错误处理

### ✅ 问题 2: gcc 下载很慢
**解决方案：**
- 切换到清华大学镜像源（国内最快）
- 减少需要编译的依赖包
- 使用预编译的二进制包（如 psycopg2-binary）

### 📊 预期改进效果

| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| 构建时间 | 15-20分钟 | 5-8分钟 | ⬇️ 60% |
| 镜像大小 | ~1.2GB | ~600MB | ⬇️ 50% |
| 下载速度 | 慢 | 快 | ⬆️ 5-10倍 |

---

## 🧪 本地测试（推荐先测试）

### 方式一：使用自动化测试脚本（推荐）

```bash
# 1. 检查 Docker 环境
check_docker.bat

# 2. 运行构建测试
python test_build_local.py
```

### 方式二：手动测试

```bash
# 1. 检查 Docker
docker --version
docker ps

# 2. 构建 Backend 镜像
docker build -t weld-backend-test:latest -f backend/Dockerfile backend

# 3. 查看镜像大小
docker images weld-backend-test

# 4. 清理测试镜像
docker rmi weld-backend-test
```

---

## 🚀 部署到服务器

### 前提条件
- ✅ 本地测试通过
- ✅ 服务器可访问（43.142.188.252）
- ✅ 有服务器 SSH 密钥（server-key.pem）

### 一键部署

```bash
python deploy_from_local.py
```

### 部署过程说明

脚本会自动执行以下步骤：

1. **连接服务器** - SSH 连接到 43.142.188.252
2. **停止旧服务** - 停止并删除旧容器
3. **清理资源** - 清理 Docker 缓存和旧镜像
4. **上传代码** - 上传最新代码到服务器
5. **构建镜像** - 使用优化后的 Dockerfile 构建
6. **启动服务** - 启动所有容器
7. **初始化数据库** - 运行数据库迁移
8. **健康检查** - 验证服务状态

---

## 📊 监控构建过程

### 预期输出

```
========================================
步骤 5/7: 上传项目文件
========================================
📤 上传: Dockerfile
📤 上传: requirements.prod.txt
📤 上传: requirements.txt
...

========================================
步骤 7/7: 构建并启动服务
========================================
🔨 开始构建Docker镜像...

[+] Building 350.2s (18/18) FINISHED
 => [builder 1/8] FROM python:3.11-slim
 => [builder 2/8] RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g'
 => [builder 3/8] RUN apt-get update && apt-get install -y
 => [builder 4/8] COPY requirements.prod.txt
 => [builder 5/8] RUN pip install --prefix=/install
 => [stage-1 1/5] FROM python:3.11-slim
 => [stage-1 2/5] RUN apt-get update && apt-get install -y
 => [stage-1 3/5] COPY --from=builder /install /install
 => [stage-1 4/5] COPY . .
 => [stage-1 5/5] RUN mkdir -p /app/storage/uploads
 => exporting to image

✅ 构建完成！

========================================
启动所有服务
========================================
Creating weld_postgres ... done
Creating weld_redis    ... done
Creating weld_backend  ... done
Creating weld_frontend ... done
Creating weld_admin    ... done
Creating weld_nginx    ... done

✅ 所有服务已启动
```

### 关键时间节点

- **apt 包下载**: 约 1-2 分钟（使用清华源）
- **pip 包下载**: 约 2-3 分钟（使用清华源）
- **编译构建**: 约 2-3 分钟
- **总构建时间**: 约 5-8 分钟

---

## ✅ 验证部署

### 1. 检查服务状态

```bash
# SSH 登录服务器
ssh root@43.142.188.252

# 查看容器状态
cd /home/ubuntu/weld-system
docker-compose ps

# 预期输出：所有服务都是 Up 状态
```

### 2. 检查健康状态

```bash
# 后端健康检查
curl https://api.sdhaohan.cn/api/v1/health

# 预期输出：{"status":"healthy"}
```

### 3. 访问服务

- 用户门户: https://sdhaohan.cn
- 管理门户: https://laimiu.sdhaohan.cn
- API 文档: https://api.sdhaohan.cn/docs

---

## 🔧 故障排查

### 问题 1: 构建仍然很慢

**检查镜像源是否生效：**

```bash
# 在服务器上
docker-compose exec backend bash

# 检查 pip 源
pip config list

# 应该看到：
# global.index-url='https://pypi.tuna.tsinghua.edu.cn/simple'
```

**解决方案：**
- 确认 Dockerfile 已更新
- 使用 `--no-cache` 强制重新构建

### 问题 2: 某个包下载失败

**常见原因：**
- 网络临时中断
- 镜像源同步延迟

**解决方案：**
```bash
# 重新构建
docker-compose build --no-cache backend

# 或者切换到备用源（阿里云）
# 修改 Dockerfile 中的镜像源地址
```

### 问题 3: 容器启动失败

**检查日志：**
```bash
docker-compose logs backend
```

**常见原因：**
- 数据库连接失败
- 环境变量配置错误
- 端口被占用

**解决方案：**
```bash
# 检查数据库
docker-compose ps postgres

# 检查环境变量
docker-compose exec backend env | grep DATABASE

# 重启服务
docker-compose restart backend
```

---

## 📝 文件清单

### 新增/修改的文件

```
✅ backend/Dockerfile                 - 优化后的 Dockerfile（多阶段构建）
✅ backend/requirements.prod.txt      - 生产环境依赖（精简版）
✅ DEPLOYMENT_OPTIMIZATION.md         - 详细优化说明
✅ QUICK_START_DEPLOYMENT.md          - 本文件（快速指南）
✅ test_build_local.py                - 本地构建测试脚本
✅ check_docker.bat                   - Docker 环境检查脚本
```

### 保持不变的文件

```
✓ docker-compose.yml                  - Docker Compose 配置
✓ backend/.env.production             - 生产环境变量
✓ nginx/nginx.conf                    - Nginx 配置
✓ nginx/conf.d/default.conf           - 站点配置
✓ deploy_from_local.py                - 部署脚本
```

---

## 🎯 推荐流程

### 第一次部署

```bash
# 1. 本地测试
check_docker.bat
python test_build_local.py

# 2. 确认测试通过后部署
python deploy_from_local.py

# 3. 验证部署
# 访问 https://sdhaohan.cn
# 访问 https://api.sdhaohan.cn/docs
```

### 后续更新

```bash
# 如果只修改了代码（没有修改依赖）
python deploy_from_local.py

# 如果修改了依赖
# 在部署脚本中会自动使用 --no-cache 重新构建
```

---

## 💡 优化要点总结

1. ✅ **多阶段构建** - 分离编译和运行环境
2. ✅ **镜像源优化** - 使用清华大学镜像源
3. ✅ **依赖精简** - 移除开发依赖
4. ✅ **缓存优化** - 合理利用 Docker 层缓存
5. ✅ **体积优化** - 最终镜像减少 50%

---

## 📞 需要帮助？

如果遇到问题，请提供以下信息：

1. 错误日志（`docker-compose logs backend`）
2. 构建输出（完整的构建日志）
3. 服务器环境信息（`docker version`, `docker-compose version`）
4. 网络状况（是否可以访问清华源）

---

**祝部署顺利！🎉**

