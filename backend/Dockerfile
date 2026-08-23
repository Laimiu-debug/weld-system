# 使用官方 Python 3.11 slim 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 配置国内镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖（包含运行时需要的库）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    libmagic1 \
    libjpeg62-turbo \
    libpng16-16 \
    libgomp1 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    antiword \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 只安装生产运行依赖
COPY requirements.prod.txt .

# 配置 pip 使用阿里云镜像源并安装 Python 依赖
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.prod.txt

# 使用非 root 用户运行应用
RUN addgroup --system app && adduser --system --ingroup app app

# 复制应用代码
COPY --chown=app:app . .

# 创建上传目录和字体缓存目录，确保非 root 运行时可写
ENV XDG_CACHE_HOME=/home/app/.cache
RUN mkdir -p /app/storage/uploads /home/app/.cache/fontconfig && \
    chown -R app:app /app/storage /home/app

USER app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

