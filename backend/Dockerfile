# backend/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# 安装常用工具和 dos2unix（处理 CRLF 换行问题）
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 并安装依赖
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# 复制 app 源码（包含 protos）
COPY app /app/app

# 确保 Python 包识别
RUN touch /app/app/__init__.py && touch /app/app/protos/__init__.py

WORKDIR /app/app

# 生成 proto 文件
RUN python -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

# 统一 proto 生成的 py 文件为 UNIX 格式，避免 sed 替换失败
RUN dos2unix protos/*.py

# 强力修正 import，兼容各种 import 风格
RUN sed -i 's/^import[[:space:]]\+inference_pb2[[:space:]]\+as[[:space:]]\+inference__pb2/from . import inference_pb2 as inference__pb2/' protos/inference_pb2_grpc.py

WORKDIR /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
