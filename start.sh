#!/bin/bash

# 設定工作目錄
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $APP_DIR

# 確保日誌目錄存在
mkdir -p logs

# 確保虛擬環境已啟用
source .venv/bin/activate

# 確保 Redis 容器正在運行
if ! docker ps | grep -q catfeed_redis; then
    echo "啟動 Redis 容器..."
    docker run -d --name catfeed_redis \
        -p 6379:6379 \
        -v $APP_DIR/redis-data:/data \
        redis:7.2-alpine redis-server --appendonly yes
fi

# 啟動 Gunicorn
echo "啟動 Catfeed 應用程式..."
exec gunicorn -c gunicorn.conf.py app:app 