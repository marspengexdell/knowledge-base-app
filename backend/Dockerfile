FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app /app/app

WORKDIR /app/app
RUN touch __init__.py protos/__init__.py

# 生成 gRPC protobuf 绑定
RUN python -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

# 统一行结束符
RUN dos2unix inference_pb2.py inference_pb2_grpc.py

# 修复 import 路径，确保引用相对
RUN sed -i \
    's/^import inference_pb2 as inference__pb2$/from . import inference_pb2 as inference__pb2/' \
    inference_pb2_grpc.py

WORKDIR /app
RUN mkdir -p knowledge_base_storage && chmod -R 777 knowledge_base_storage

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
