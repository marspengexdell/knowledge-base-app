# 使用官方 Python 3.10 slim 镜像作为基础
FROM python:3.10-slim

# 设置工作目录为 /app
WORKDIR /app

# 设置环境变量，避免时区和缓冲问题
ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 更新系统包并安装编译依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- 关键修正：确保 gRPC 文件正确生成和导入 ---

# 1. 首先，将 requirements.txt 复制进来并安装依赖
#    这样可以利用 Docker 的层缓存，在代码变动但依赖不变时加快构建速度
COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# 2. 将后端整个 app 目录复制到容器中
COPY ./backend/app /app/app

# 3. 将 protos 定义文件也复制到顶级目录，为生成代码做准备
COPY ./backend/app/protos/inference.proto /app/inference.proto

# 4. 运行 protoc 命令生成 gRPC Python 文件
#    -I/app 指定 .proto 文件的搜索根目录
#    --python_out=/app/app 和 --grpc_python_out=/app/app 指定生成文件的输出目录
#    这样生成的代码会放在 app 包内，可以使用 app.protos.xxx 的方式导入
RUN python -m grpc_tools.protoc \
    -I/app \
    --python_out=/app/app \
    --grpc_python_out=/app/app \
    /app/inference.proto

# 暴露端口
EXPOSE 8000

# 容器启动时运行的命令
# 使用 --reload 以便在开发过程中，代码更改时 uvicorn 自动重启
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]