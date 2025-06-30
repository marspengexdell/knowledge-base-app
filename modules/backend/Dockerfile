# 使用官方的Python基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# (关键修正) 将 app 目录下的所有内容复制到容器的 /app 目录
# 而不是创建 /app/app 结构
COPY ./app /app

# 安装项目依赖
# 确保 requirements.txt 在 modules/backend/ 目录下
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 暴露端口
EXPOSE 8000

# 启动应用的命令 (保持不变)
# Uvicorn 现在会直接在 /app 下找到 main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
