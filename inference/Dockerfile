# inference/Dockerfile (最终的、包含完整编译工具链的修正版)

FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# 设置环境变量，避免在安装过程中出现交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# --- 关键修正：安装所有可能的编译依赖 ---
# 更新系统包并安装一个完整的编译工具链
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    git \
    cmake \
    pkg-config \
    autoconf \
    automake \
    libtool \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# --- 关键修正：强制编译 CUDA ---
# 设置环境变量，强制 llama-cpp-python 在安装时编译 CUDA 支持
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"
ENV FORCE_CUDA="1"

# 复制并安装 Python 依赖
# (路径相对于 inference 目录)
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip && \
    # --force-reinstall 确保即使有缓存也重新安装
    # --no-binary :all: 强制从源码编译以应用我们的环境变量
    pip3 install --no-cache-dir --force-reinstall --no-binary :all: -r requirements.txt

# 复制整个 app 目录到容器的 /app
# (路径相对于 inference 目录)
COPY app /app

# 生成 gRPC 代码
RUN python3 -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

# 容器启动时运行的命令
CMD ["python", "main.py"]