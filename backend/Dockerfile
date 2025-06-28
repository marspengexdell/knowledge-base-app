# E:\knowledge-base-app\backend\Dockerfile (最终、最终修正版)

FROM python:3.10-slim

WORKDIR /app

# 安装编译依赖和常用工具
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制app源码
COPY app /app/app

# --- gRPC 文件生成与修复 ---
WORKDIR /app/app
RUN touch __init__.py protos/__init__.py
RUN python -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto
RUN dos2unix inference_pb2.py inference_pb2_grpc.py
RUN sed -i \
    's/^import inference_pb2 as inference__pb2$/from . import inference_pb2 as inference__pb2/' \
    inference_pb2_grpc.py

# --- 关键修复：切换回主工作目录并设置PYTHONPATH ---
WORKDIR /app

# 告诉Python在导入模块时也要搜索 /app/app 目录
ENV PYTHONPATH "${PYTHONPATH}:/app/app"

# 预创建知识库目录并赋予权限
RUN mkdir -p /app/knowledge_base_storage && \
    chmod -R 777 /app/knowledge_base_storage

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]