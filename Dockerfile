# 构建 admin 前端
FROM node:18-alpine AS frontend-admin-build
WORKDIR /frontend-admin
COPY frontend-admin/package*.json ./
RUN npm install
COPY frontend-admin/ ./
RUN npm run build

# 构建 user 前端
FROM node:18-alpine AS frontend-user-build
WORKDIR /frontend-user
COPY frontend-user/package*.json ./
RUN npm install
COPY frontend-user/ ./
RUN npm run build

# 构建后端
FROM python:3.10-slim AS backend-build
WORKDIR /backend
COPY modules/backend/requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY modules/backend /backend

# 最终镜像
FROM python:3.10-slim

# 安装 supervisor
RUN apt-get update && apt-get install -y supervisor

WORKDIR /app

# 拷贝后端
COPY --from=backend-build /backend /app

# 拷贝前端构建产物
COPY --from=frontend-admin-build /frontend-admin/dist /app/frontend-admin
COPY --from=frontend-user-build /frontend-user/dist /app/frontend-user

# 拷贝模型
COPY models /models

# supervisord 配置
COPY supervisord.conf /etc/supervisord.conf

# 环境变量
ENV CHROMA_PERSIST_DIR=/app/chroma_store
ENV PYTHONUNBUFFERED=1
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

EXPOSE 8000

ENTRYPOINT ["supervisord", "-c", "/etc/supervisord.conf"]
