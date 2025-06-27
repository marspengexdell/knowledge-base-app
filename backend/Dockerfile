FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

RUN touch /app/app/__init__.py && touch /app/app/protos/__init__.py

WORKDIR /app/app

RUN python -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto
RUN dos2unix protos/*.py
RUN sed -i 's/^import[[:space:]]\+inference_pb2[[:space:]]\+as[[:space:]]\+inference__pb2/from . import inference_pb2 as inference__pb2/' protos/inference_pb2_grpc.py

# 必须和 Python 一致
RUN mkdir -p /app/app/knowledge_base_docs && chmod -R 777 /app/app/knowledge_base_docs

WORKDIR /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
