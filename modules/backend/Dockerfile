# 使用官方的Python基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 将 app 目录下的所有内容复制到容器的 /app 目录
COPY ./app /app

# 安装项目依赖
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Work around protobuf runtime incompatibility with some packages by forcing
# the slower pure-Python implementation
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# 暴露端口
EXPOSE 8000

# 启动应用的命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
