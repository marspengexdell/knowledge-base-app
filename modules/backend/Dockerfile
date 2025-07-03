FROM python:3.10-slim

WORKDIR /app

COPY ./modules/backend/requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 1. 复制 proto 到统一的 /protos 目录
COPY ./modules/backend/app/protos/opentelemetry /protos/opentelemetry
COPY ./modules/inference/app/protos/inference.proto /protos/inference.proto

# 2. 编译 proto 文件到 /app/protos
RUN mkdir -p /app/protos && \
    python3 -m grpc_tools.protoc -I/protos --python_out=/app/protos --grpc_python_out=/app/protos \
        /protos/inference.proto \
        /protos/opentelemetry/proto/collector/logs/v1/logs_service.proto \
        /protos/opentelemetry/proto/collector/metrics/v1/metrics_service.proto \
        /protos/opentelemetry/proto/collector/profiles/v1development/profiles_service.proto \
        /protos/opentelemetry/proto/collector/trace/v1/trace_service.proto \
        /protos/opentelemetry/proto/common/v1/common.proto \
        /protos/opentelemetry/proto/logs/v1/logs.proto \
        /protos/opentelemetry/proto/metrics/v1/metrics.proto \
        /protos/opentelemetry/proto/profiles/v1development/profiles.proto \
        /protos/opentelemetry/proto/resource/v1/resource.proto \
        /protos/opentelemetry/proto/trace/v1/trace.proto

# 3. 确保包结构
RUN touch /app/protos/__init__.py

# 4. 复制实际业务代码（main.py等）
COPY ./modules/backend/app /app

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
