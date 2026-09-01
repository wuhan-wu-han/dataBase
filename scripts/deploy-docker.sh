#!/bin/bash
# ============================================================
# 部署脚本：将项目同步到虚拟机并启动 Docker 基础设施
# 用法：在 Windows Git Bash 中执行 bash scripts/deploy-docker.sh
# ============================================================

set -e

VM_USER="Ubuntu22"
VM_HOST="192.168.152.128"
REMOTE_DIR="~/dataBase"

echo "========================================="
echo "  Step 1: 同步项目文件到虚拟机"
echo "========================================="

# 用 rsync 同步（排除不需要的目录）
rsync -avz --progress \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'data/' \
  --exclude 'models/' \
  --exclude 'output/__pycache__' \
  -e ssh \
  "$(cd "$(dirname "$0")/.." && pwd)/" \
  "${VM_USER}@${VM_HOST}:${REMOTE_DIR}/"

echo ""
echo "========================================="
echo "  Step 2: SSH 到虚拟机启动 Docker"
echo "========================================="

ssh "${VM_USER}@${VM_HOST}" bash -s <<'REMOTE_SCRIPT'
  set -e
  cd ~/dataBase/docker

  echo ">>> 停止旧容器（如有）..."
  docker compose down 2>/dev/null || true

  echo ""
  echo ">>> 启动所有基础设施服务..."
  docker compose up -d

  echo ""
  echo ">>> 等待服务健康检查..."
  sleep 15

  echo ""
  echo ">>> 服务状态："
  docker compose ps

  echo ""
  echo ">>> 端口监听检查："
  ss -tlnp | grep -E ':(2181|9092|3306|6379|9200|5601|8080|9870|10000) ' || echo "部分端口尚未就绪，请稍后检查"

  echo ""
  echo "========================================="
  echo "  部署完成！"
  echo "========================================="
  echo ""
  echo "服务端口映射："
  echo "  Zookeeper:      2181"
  echo "  Kafka:          9092"
  echo "  MySQL:          3306  (root/123456, db=alert_db)"
  echo "  Redis:          6379"
  echo "  Hadoop NN:      9870  (Web UI)"
  echo "  HiveServer2:    10000"
  echo "  Elasticsearch:  9200"
  echo "  Kibana:         5601"
  echo "  Spark Master:   8080  (Web UI)"
  echo "  Logstash:       5044"
  echo ""
  echo "验证命令："
  echo "  docker compose ps"
  echo "  docker compose logs -f mysql"
  echo "  docker compose logs -f redis"
REMOTE_SCRIPT

echo ""
echo "部署脚本执行完毕。"
