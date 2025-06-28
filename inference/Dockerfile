# E:\knowledge-base-app\inference\Dockerfile (最终完美版)

# 使用官方 CUDA 镜像作为基础
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 as base

# 安装编译依赖和 Python，新增 git 和 cmake
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    git \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# 设置 CUDA 路径
RUN echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && ldconfig

# 创建依赖安装阶段
FROM base as deps
RUN python3 -m pip install --upgrade pip
WORKDIR /app
COPY requirements.txt /app/requirements.txt
# 设置编译时环境变量，确保使用CUDA
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"
ENV FORCE_CMAKE=1
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# 创建最终阶段
FROM base as final
WORKDIR /app
COPY --from=deps /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY app /app/app

# gRPC 文件生成
WORKDIR /app/app
RUN python3 -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

# 设置Python路径
WORKDIR /app
ENV PYTHONPATH "${PYTHONPATH}:/app/app"

# 暴露端口
EXPOSE 50051

# 【关键修复】使用正确的 python3 命令启动 gRPC 服务
CMD ["python3", "app/main.py"]