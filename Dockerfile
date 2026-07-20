# =============================================
# Mini Mall API Server — Docker 镜像
# =============================================
FROM python:3.11-slim

LABEL maintainer="linchuanbin"
LABEL description="Mini Mall 电商接口自动化测试 — Mock 后端服务"

# ---- 系统依赖 ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        default-libmysqlclient-dev \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---- 工作目录 ----
WORKDIR /app

# ---- 依赖安装（利用 Docker 层缓存） ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn==22.0.0

# ---- 复制项目代码 ----
COPY . .

# ---- 环境变量（可在 docker-compose 或 k8s 中覆盖） ----
ENV FLASK_HOST=0.0.0.0 \
    DB_HOST=127.0.0.1 \
    DB_PORT=3306 \
    DB_USER=root \
    DB_PASS=root \
    DB_NAME=pycharm_test \
    REDIS_HOST=127.0.0.1 \
    REDIS_PORT=6379 \
    ES_HOST=127.0.0.1 \
    ES_PORT=9200 \
    MQ_HOST=127.0.0.1 \
    MQ_PORT=5672 \
    JWT_SECRET=mini_mall_jwt_secret_2026 \
    PYTHONUNBUFFERED=1

# ---- 健康检查 ----
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# ---- 暴露端口 ----
EXPOSE 5000

# ---- 启动（gunicorn 生产级服务器） ----
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "server.my_server:app"]
