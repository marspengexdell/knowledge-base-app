# inference/Dockerfile

FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# 设置工作目录
WORKDIR /app

# 安装 Python 和编译依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    && ln -sf /usr/bin/python3 /usr/bin/python

# 复制并安装 Python 依赖
# 注意：路径是相对于构建上下文（./inference）的
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# 复制整个 app 目录到容器的 /app
# 注意：路径是相对于构建上下文（./inference）的
COPY app /app

# --- 关键修正：确保 gRPC 文件在正确的位置生成 ---
# 切换到 /app 目录
WORKDIR /app

# 生成 gRPC 代码
RUN python3 -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

# 容器启动时运行的命令
CMD ["python", "main.py"]