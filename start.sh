#!/bin/bash

# 启动 Chroma 向量数据库（子进程）
echo "Starting Chroma..."
python3 /chroma/server.py &

# 启动后端
echo "Starting backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
