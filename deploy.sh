#!/bin/bash
# =============================================
# Mini Mall — CD 部署脚本
# 用法: ./deploy.sh <env> <image_tag>
# 示例: ./deploy.sh test v1.2.3
# =============================================
set -euo pipefail

ENV="${1:-test}"
IMAGE_TAG="${2:-latest}"
REGISTRY="${DOCKER_REGISTRY:-docker.io/linchuanbin}"
IMAGE="${REGISTRY}/mini-mall-api:${IMAGE_TAG}"

echo "=========================================="
echo "  部署 Mini Mall - 环境: ${ENV}"
echo "  镜像: ${IMAGE}"
echo "=========================================="

# ---- 1. 拉取镜像 ----
echo "[1/4] 拉取镜像..."
docker pull "${IMAGE}" || {
    echo "[ERROR] 镜像拉取失败: ${IMAGE}"
    exit 1
}

# ---- 2. 备份当前运行的容器 ----
echo "[2/4] 备份当前容器..."
CURRENT_ID=$(docker ps -q -f name=mini-mall-api 2>/dev/null || echo "")
if [ -n "${CURRENT_ID}" ]; then
    docker tag mini-mall-api:latest "mini-mall-api:backup-$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
fi

# ---- 3. 滚动更新 ----
echo "[3/4] 滚动更新服务..."
export BUILD_TAG="${IMAGE_TAG}"
export DOCKER_REGISTRY="${REGISTRY}/"

# 打本地标签（docker-compose 需要）
docker tag "${IMAGE}" "mini-mall-api:${IMAGE_TAG}" 2>/dev/null || true

# 拉取最新镜像后重新创建容器（--no-build 禁止重新构建，只拉取）
docker-compose -f docker-compose.yml up -d --no-deps --no-build app

# ---- 4. 健康检查 ----
echo "[4/4] 健康检查..."
MAX_RETRIES=12
RETRY_COUNT=0

while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
    if curl -sf http://localhost:5000/api/health > /dev/null 2>&1; then
        echo "[OK] 服务健康检查通过！"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ ${RETRY_COUNT} -ge ${MAX_RETRIES} ]; then
        echo "[ERROR] 健康检查失败！回滚中..."
        # 回滚到上一个版本
        docker-compose -f docker-compose.yml up -d --no-deps app
        exit 1
    fi
    echo "  等待服务就绪... (${RETRY_COUNT}/${MAX_RETRIES})"
    sleep 5
done

echo ""
echo "=========================================="
echo "  部署完成！环境: ${ENV}  版本: ${IMAGE_TAG}"
echo "  健康检查: http://localhost:5000/api/health"
echo "=========================================="
