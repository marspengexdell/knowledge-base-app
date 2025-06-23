FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

LABEL maintainer="Your Name <youremail@example.com>"
LABEL description="Dockerfile for the AI Inference Service of Knowledge Base App"

# 设置环境变量
ENV TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/protos

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# 创建python符号链接
RUN ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

# 升级pip
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip

# 关键步骤：使用新的环境变量强制重新编译和安装 llama-cpp-python
# 确保您已经从 requirements.txt 中移除了 llama-cpp-python
# 将 LLAMA_CUBLAS=on 更改为 GGML_CUDA=on
ENV CMAKE_ARGS="-DGGML_CUDA=on"
ENV FORCE_CMAKE=1
# 注意：这里我们明确指定一个已知可以工作的版本，增加稳定性
RUN pip3 install --no-cache-dir --force-reinstall --upgrade "llama-cpp-python[cuda]==0.2.78"

# 安装 requirements.txt 中的其余依赖项
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制源码
COPY ./app /app

# 可选：生成 gRPC Python 文件
RUN if [ -f /app/protos/inference.proto ]; then \
    python3 -m grpc_tools.protoc -I/app/protos --python_out=/app/protos --grpc_python_out=/app/protos /app/protos/inference.proto; \
    fi

EXPOSE 50051

CMD ["python3", "server.py"]