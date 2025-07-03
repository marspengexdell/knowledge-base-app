FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

RUN sed -i 's@http://archive.ubuntu.com/ubuntu@https://mirrors.aliyun.com/ubuntu@g' /etc/apt/sources.list \
 && sed -i 's@http://security.ubuntu.com/ubuntu@https://mirrors.aliyun.com/ubuntu@g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    cmake \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/local/cuda/lib64/stubs/libcuda.so /usr/lib/x86_64-linux-gnu/libcuda.so.1 || true

WORKDIR /app

COPY ./modules/inference/requirements.txt .

ENV CMAKE_ARGS="-DGGML_CUDA=on"
ENV FORCE_CMAKE=1

RUN python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install torch --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝 inference proto 文件
COPY ./modules/inference/app/protos/inference.proto ./protos/inference.proto

# 创建 proto 输出目录并加 __init__.py
RUN mkdir -p ./app/protos && touch ./app/protos/__init__.py

# 编译 proto
RUN python3 -m grpc_tools.protoc -I./protos --python_out=./app/protos --grpc_python_out=./app/protos ./protos/inference.proto

# 拷贝主 app 代码
COPY ./modules/inference/app ./app

ENV PYTHONPATH="${PYTHONPATH}:/app/app"

EXPOSE 50051

CMD ["python3", "-m", "app.main"]
