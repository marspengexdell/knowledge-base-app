# E:\knowledge-base-app\inference\Dockerfile (最终完美版)

FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 AS base

RUN apt-get update && apt-get install -y \
    build-essential python3.10 python3-pip \
    git cmake dos2unix \
    && rm -rf /var/lib/apt/lists/* \
    && echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf \
    && ldconfig

FROM base AS deps
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --upgrade pip \
 && export CMAKE_ARGS="-DLLAMA_CUBLAS=on" \
 && export FORCE_CMAKE=1 \
 && pip install --no-cache-dir -r /app/requirements.txt

FROM base AS final
WORKDIR /app
COPY --from=deps /usr/local/lib/python3.10/dist-packages/ /usr/local/lib/python3.10/dist-packages/
COPY --from=deps /usr/local/bin/ /usr/local/bin/
COPY app /app/app

WORKDIR /app/app
RUN touch protos/__init__.py \
 && python3 -m grpc_tools.protoc -I=protos \
      --python_out=protos --grpc_python_out=protos \
      protos/inference.proto

WORKDIR /app
ENV PYTHONPATH="${PYTHONPATH}:/app"

EXPOSE 50051
CMD ["python3", "-m", "app.main"]
