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

RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./app /app

# 保证 protos/inference.proto 存在
RUN python3 -m grpc_tools.protoc -I/app/protos --python_out=/app/protos --grpc_python_out=/app/protos /app/protos/inference.proto

EXPOSE 50051

CMD ["python3", "server.py"]
