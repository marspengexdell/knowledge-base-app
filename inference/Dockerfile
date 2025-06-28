# E:\knowledge-base-app\inference\Dockerfile (最终修正版)

# 使用官方 CUDA 镜像
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 as base

# 安装编译依赖和 Python
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 设置 CUDA 路径
RUN echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && ldconfig

# 创建依赖安装阶段
FROM base as deps
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip3 install \
    --no-cache-dir \
    --prefer-binary \
    --extra-index-url https://pip.pypa.io/simple/ \
    "llama-cpp-python[server,cuda]"
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

# 创建最终阶段
FROM base as final
WORKDIR /app
COPY --from=deps /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY app /app/app

# --- gRPC 文件生成 ---
WORKDIR /app/app
RUN python3 -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

# 【关键修复】将工作目录切换回 /app
WORKDIR /app

# 【关键修复】将 app 目录添加到 PYTHONPATH
# 这会告诉 Python 在导入模块时也要搜索 /app/app 目录
ENV PYTHONPATH "${PYTHONPATH}:/app/app"

# 暴露端口
EXPOSE 50051

# 容器启动时运行的命令
CMD ["python3", "/app/app/main.py"]