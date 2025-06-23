# inference/Dockerfile (最终的 GPU 强制编译版)

FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# 设置工作目录
WORKDIR /app

# 安装编译所需的系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    git \
    cmake \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# --- 关键修正：强制编译 CUDA ---
# 设置环境变量，强制 llama-cpp-python 在安装时编译 CUDA 支持
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"
ENV FORCE_CUDA="1"

# 复制并安装 Python 依赖
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip && \
    # --no-binary :all: 强制从源码编译
    pip3 install --no-cache-dir --no-binary :all: -r requirements.txt

# 复制应用代码
COPY app /app

# 生成 gRPC 代码
RUN python3 -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

# 容器启动时运行的命令
CMD ["python", "main.py"]