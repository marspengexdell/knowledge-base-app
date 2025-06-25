# Stage 1: 使用官方的 NVIDIA CUDA 基础镜像
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    git \
    cmake \
    pkg-config \
    ninja-build \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

RUN echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && ldconfig
ENV PATH="/usr/local/cuda/bin:${PATH}"

# Stage 2: 依赖安装
FROM base AS deps

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 关键点：llama-cpp-python 不要写在 requirements.txt
RUN pip3 install \
    --no-cache-dir \
    --prefer-binary \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 \
    llama-cpp-python

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

# Stage 3: 构建最终应用镜像
FROM deps AS final

WORKDIR /app

# 复制 Python 依赖和可执行文件
COPY --from=deps /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# 复制应用代码（包含 protos 文件夹，因为都在 app 目录下）
COPY app /app/app

# 可选：如果你需要把项目根目录的 protos 也拷贝进来（你的情况应该不用！）
# COPY app/protos /app/app/protos

WORKDIR /app/app

# 生成 gRPC 代码（proto 在 app/protos 目录下）
RUN python3 -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

WORKDIR /app

# 启动命令
CMD ["python3", "-u", "app/main.py"]
