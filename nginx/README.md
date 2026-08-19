# Nginx 与 TLS

仓库只保存 Nginx 配置，**不保存证书、Certbot 账户信息或私钥**。运行时数据位于
`nginx/certbot/conf/`，该目录已被 Git 忽略并由 Docker 挂载。

## 自动引导

Nginx 启动脚本会检查
`/etc/letsencrypt/live/sdhaohan.cn/{fullchain,privkey}.pem`：

- 未找到证书时加载 `conf.d/default.conf.http`，开放 ACME 验证并以 HTTP 提供服务。
- 找到证书时加载 `conf.d/default.conf`，HTTP 自动跳转 HTTPS。

因此首次部署不会因为证书尚不存在而导致 Nginx 启动失败。

## 首次签发证书

先确保四个域名均已解析到服务器并启动服务：

```bash
docker compose up -d
docker compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email YOUR_EMAIL@example.com \
  --agree-tos --no-eff-email \
  --cert-name sdhaohan.cn \
  -d sdhaohan.cn \
  -d laimiu.sdhaohan.cn \
  -d api.sdhaohan.cn \
  -d lifecard.sdhaohan.cn
docker compose restart nginx
```

Certbot 服务每 12 小时检查续期。证书续期后执行
`docker compose exec nginx nginx -s reload` 使 Nginx 读取新证书；也可以重启 Nginx。

## 检查与维护

```bash
docker compose exec nginx nginx -t
docker compose logs nginx certbot
docker compose run --rm certbot renew --dry-run
```

若仓库曾经提交过真实私钥，应立即在证书颁发机构吊销/轮换对应证书；仅从当前提交删除文件不能消除 Git 历史中的泄露。
