# 基础镜像：CUDA + Python + 工具
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 AS base

# 安装基础环境和构建工具
RUN apt-get update && apt-get install -y \
    build-essential python3.10 python3-pip \
    git cmake dos2unix \
    && rm -rf /var/lib/apt/lists/*

# 第二阶段：构建最终镜像
FROM base AS final

# ★ 核心修复：为链接器设置正确的库搜索路径 ★
# 确保在构建过程和运行时都能找到CUDA库
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}
RUN echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && ldconfig

WORKDIR /app

# 拷贝依赖文件和你的应用代码
COPY requirements.txt .
COPY app /app/app

# 使用新的编译标志 GGML_CUDA 重新安装所有依赖
RUN python3 -m pip install --upgrade pip \
    && export CMAKE_ARGS="-DGGML_CUDA=on" \
    && export FORCE_CMAKE=1 \
    && pip install --no-cache-dir -r requirements.txt

# 进入 app 目录编译 gRPC protos 文件
WORKDIR /app/app
RUN touch protos/__init__.py \
 && python3 -m grpc_tools.protoc -I=protos \
    --python_out=protos --grpc_python_out=protos \
    protos/inference.proto

# 设置工作目录和 Python 路径
WORKDIR /app
ENV PYTHONPATH="/app:${PYTHONPATH}"

EXPOSE 50051

CMD ["python3", "-m", "app.main"]