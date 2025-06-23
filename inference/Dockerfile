# inference/Dockerfile (最终修正版)

FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# 设置工作目录
WORKDIR /app

# --- 关键修正：在这里添加 git ---
# 更新系统包并安装编译依赖，包括 python, pip, 和 git
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# 复制并安装 Python 依赖
# (路径相对于 inference 目录)
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# 复制整个 app 目录到容器的 /app
# (路径相对于 inference 目录)
COPY app /app

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