# Stage 1: 基础镜像 + CUDA + 工具
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 AS base

RUN apt-get update && apt-get install -y \
    build-essential python3.10 python3-pip git cmake dos2unix \
    && rm -rf /var/lib/apt/lists/* \
 && echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && ldconfig

# Stage 2: 安装 Python 依赖
FROM base AS deps
WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN python3 -m pip install --no-cache-dir --upgrade pip
RUN export CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 \
 && pip install --no-cache-dir -r requirements.txt

# Stage 3: 构建最终镜像 & protobuf
FROM base AS final
WORKDIR /app

COPY --from=deps /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY app /app/app

WORKDIR /app/app
RUN touch __init__.py protos/__init__.py \
 && python3 -m grpc_tools.protoc -I=protos --python_out=. --grpc_python_out=. protos/inference.proto \
 && dos2unix inference_pb2.py inference_pb2_grpc.py \
 && sed -i 's/^import inference_pb2 as inference__pb2$/from . import inference_pb2 as inference__pb2/' inference_pb2_grpc.py

WORKDIR /app
ENV PYTHONPATH="${PYTHONPATH}:/app/app"

EXPOSE 8000 50051

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
