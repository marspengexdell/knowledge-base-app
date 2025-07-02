# 使用官方的Python基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 1. 首先只复制依赖文件
# 这样做可以利用Docker的缓存机制。只要 requirements.txt 不变，就不会重新安装依赖。
COPY ./modules/backend/requirements.txt .

# 2. 安装项目依赖 (包括 grpcio-tools)
# 请确保 'grpcio-tools' 已经添加到了你的 requirements.txt 文件中！
RUN pip install --no-cache-dir --upgrade -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 复制 .proto 文件
# 因为构建上下文是项目根目录，所以可以轻松访问 protos 目录
COPY ./protos ./protos

# 4. 编译 .proto 文件为 Python 代码
# 这会在 /app 目录下生成一个 protos 包，其中包含 inference_pb2.py 和 inference_pb2_grpc.py
RUN python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/*.proto

# 5. 复制后端应用的所有代码
COPY ./modules/backend/app ./app

# 设置环境变量，解决 protobuf 的一个潜在问题
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# 暴露端口
EXPOSE 8000

# 启动应用的命令
# 注意：生产环境中建议去掉 --reload 标志
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
