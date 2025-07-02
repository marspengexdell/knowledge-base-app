# 使用官方的 NVIDIA CUDA 基础镜像
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# 1. 安装系统依赖
# 更新包列表并安装 Python、pip 和编译工具
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. 设置工作目录
WORKDIR /app

# 3. 复制并安装 Python 依赖
# 首先只复制依赖文件以利用 Docker 缓存
COPY ./modules/inference/requirements.txt .

# 设置环境变量，强制 llama-cpp-python 在编译时启用 CUDA
ENV CMAKE_ARGS="-DGGML_CUDA=on"
ENV FORCE_CMAKE=1

# 安装所有 Python 依赖
# pip 会首先读取 requirements.txt 中的 --index-url 来安装 torch
RUN python3 -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. 复制 .proto 文件
# 确保 docker-compose.yml 中的构建上下文是项目根目录 (context: .)
COPY ./protos ./protos

# 5. 编译 .proto 文件为 Python 代码
RUN python3 -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/*.proto

# 6. 复制应用代码
COPY ./modules/inference/app ./app

# 7. 设置 Python 路径，以便能正确找到模块
ENV PYTHONPATH="${PYTHONPATH}:/app"

# 暴露 gRPC 服务的端口
EXPOSE 50051

# 启动应用的命令
CMD ["python3", "-m", "app.main"]
