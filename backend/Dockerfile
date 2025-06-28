FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential curl dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY app /app/app

WORKDIR /app/app
RUN touch protos/__init__.py \
 && python -m grpc_tools.protoc -I=protos \
      --python_out=protos --grpc_python_out=protos \
      protos/inference.proto

WORKDIR /app
ENV PYTHONPATH="${PYTHONPATH}:/app"

RUN mkdir -p /app/knowledge_base_storage \
 && chmod -R 777 /app/knowledge_base_storage

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
