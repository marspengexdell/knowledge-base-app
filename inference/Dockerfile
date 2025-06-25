FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 1. 系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    python3-venv \
    git \
    cmake \
    pkg-config \
    ninja-build \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# 2. CUDA 环境变量和动态库
RUN echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && ldconfig
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV GGML_CUDA=1

# 3. pip/torch
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# ★★★★★ 关键点：先单独安装 CUDA wheel 版 llama-cpp-python ★★★★★
RUN pip3 install --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python-cu121/ llama-cpp-python

# 4. 复制 requirements.txt，安装剩余依赖（llama-cpp-python 不要写在 requirements.txt）
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# 5. 复制应用代码
COPY app /app/app

# 6. proto 自动生成
WORKDIR /app/app
RUN python3 -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

WORKDIR /app

# 7. 启动命令
CMD ["python3", "app/main.py"]
