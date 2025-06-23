# backend/Dockerfile

# 使用官方 Python 3.10 slim 镜像作为基础
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
# 注意：路径是相对于构建上下文（./backend）的
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# 复制整个 app 目录到容器的 /app/app
# 注意：路径是相对于构建上下文（./backend）的
COPY app /app/app

# --- 关键修正：确保 gRPC 文件在正确的位置生成 ---
# 切换到包含 protos 的目录
WORKDIR /app/app

# 从当前目录运行 protoc，生成的文件将具有正确的相对导入
RUN python -m grpc_tools.protoc \
    -I=protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

# 将工作目录切换回 /app
WORKDIR /app

# 暴露端口
EXPOSE 8000

# 容器启动时运行的命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]