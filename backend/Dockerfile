# backend/Dockerfile

FROM python:3.10-slim

LABEL maintainer="Your Name <youremail@example.com>"
LABEL description="Dockerfile for the Backend API Service of Knowledge Base App"

ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
RUN mkdir -p /app/app/protos && touch /app/app/protos/__init__.py

# 注意：前提是 backend/app/protos/inference.proto 已经存在
RUN python -m grpc_tools.protoc -I/app/app/protos --python_out=/app/app/protos --grpc_python_out=/app/app/protos /app/app/protos/inference.proto

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
