# ===============================
# Stage 1: 基础依赖环境（CUDA/Python）
# ===============================
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

# ===============================
# Stage 2: 安装Python依赖
# ===============================
FROM base AS deps

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# llama-cpp-python 必须单独提前安装，不要写在 requirements.txt
RUN pip3 install \
    --no-cache-dir \
    --prefer-binary \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 \
    llama-cpp-python

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

# ===============================
# Stage 3: 最终运行镜像
# ===============================
FROM deps AS final

WORKDIR /app

# ★★★★ 关键点！拷贝 dist-packages 而不是 site-packages ★★★★
COPY --from=deps /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# 复制应用代码（你的 app 下已经包含 protos 目录，无需单独 COPY protos）
COPY app /app/app

WORKDIR /app/app

# 生成 gRPC 代码（proto 文件在 app/protos 目录下）
RUN python3 -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

WORKDIR /app

CMD ["python3", "-u", "app/main.py"]
