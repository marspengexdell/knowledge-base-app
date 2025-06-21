FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

LABEL maintainer="Your Name <youremail@example.com>"
LABEL description="Dockerfile for the AI Inference Service of Knowledge Base App"

ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/protos

RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

# 先复制 requirements.txt 并装依赖
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制源码（务必保证 app/server.py 存在）
COPY ./app /app

# 可选：自动生成 gRPC Python 文件（如果开发期有变）
RUN if [ -f /app/protos/inference.proto ]; then \
    python3 -m grpc_tools.protoc -I/app/protos --python_out=/app/protos --grpc_python_out=/app/protos /app/protos/inference.proto; \
    fi

EXPOSE 50051

CMD ["python3", "server.py"]
