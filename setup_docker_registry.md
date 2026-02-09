# Docker 镜像源配置指南

## 问题说明

构建失败的原因是 Docker 尝试从腾讯云镜像源拉取基础镜像时超时：
```
failed to do request: Head "https://mirror.ccs.tencentyun.com/v2/library/python/manifests/3.11-slim"
net/http: TLS handshake timeout
```

## 解决方案：配置国内镜像源

### 方法一：通过 Docker Desktop 配置（推荐）

1. **打开 Docker Desktop**

2. **进入设置**
   - 点击右上角的齿轮图标 ⚙️
   - 选择 "Docker Engine"

3. **修改配置**
   在配置文件中添加或修改 `registry-mirrors`：

```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev",
    "https://docker.anyhub.us.kg",
    "https://dockerhub.icu"
  ]
}
```

4. **应用并重启**
   - 点击 "Apply & Restart"
   - 等待 Docker 重启完成

### 方法二：使用阿里云镜像加速器（备选）

1. **访问阿里云容器镜像服务**
   https://cr.console.aliyun.com/cn-hangzhou/instances/mirrors

2. **获取专属加速地址**
   登录后会看到类似：`https://xxxxxx.mirror.aliyuncs.com`

3. **配置到 Docker Desktop**
```json
{
  "registry-mirrors": [
    "https://xxxxxx.mirror.aliyuncs.com"
  ]
}
```

### 方法三：使用官方源（如果网络好）

如果你的网络可以直接访问 Docker Hub：

```json
{
  "registry-mirrors": []
}
```

## 验证配置

配置完成后，运行以下命令验证：

```bash
# 查看 Docker 信息
docker info

# 应该看到 Registry Mirrors 部分
# Registry Mirrors:
#  https://docker.m.daocloud.io/
```

## 测试拉取镜像

```bash
# 测试拉取 Python 基础镜像
docker pull python:3.11-slim

# 如果成功，应该看到下载进度
```

## 推荐的镜像源（2024年可用）

按优先级排序：

1. **DaoCloud** - `https://docker.m.daocloud.io`
2. **1Panel** - `https://docker.1panel.live`
3. **Rat.dev** - `https://hub.rat.dev`
4. **AnyHub** - `https://docker.anyhub.us.kg`
5. **DockerHub.icu** - `https://dockerhub.icu`

## 配置后重新测试

```bash
# 重新运行构建测试
python test_build_local.py
```

## 如果还是失败

### 选项 1：手动拉取基础镜像

```bash
# 先手动拉取基础镜像
docker pull python:3.11-slim

# 然后再构建
docker build -t weld-backend-test:latest -f backend/Dockerfile backend
```

### 选项 2：使用代理

如果有 VPN 或代理：

```json
{
  "proxies": {
    "http-proxy": "http://proxy.example.com:8080",
    "https-proxy": "http://proxy.example.com:8080",
    "no-proxy": "localhost,127.0.0.1"
  }
}
```

### 选项 3：直接在服务器上构建

如果本地网络不好，可以直接在服务器上构建：

```bash
# 上传代码到服务器
python deploy_from_local.py

# 服务器的网络通常更好
```

