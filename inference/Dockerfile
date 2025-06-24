FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 1. 安装系统依赖（包含常用调试工具）
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

# 2. CUDA 环境变量和动态库配置（llama-cpp-python CUDA 编译需要）
RUN echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && ldconfig
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV GGML_CUDA=1

# 3. 升级 pip 并单独安装 PyTorch 相关依赖（更高效、可避免 hash 校验问题）
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. 复制 Python 依赖描述文件并安装剩余依赖（不要再在 requirements.txt 里写 torch/torchvision/torchaudio）
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# 5. 复制全部应用代码
COPY app /app/app

# 6. 自动生成 proto 代码（确保 app/app/protos/inference.proto 存在！）
WORKDIR /app/app
RUN python3 -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

WORKDIR /app

# 7. 启动命令
CMD ["python3", "app/main.py"]
