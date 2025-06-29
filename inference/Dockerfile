# 基础镜像：CUDA + Python + 工具
# 使用了多阶段构建，以保持最终镜像的整洁
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 AS base

# 安装基础环境和构建工具
RUN apt-get update && apt-get install -y \
    build-essential python3.10 python3-pip \
    git cmake dos2unix \
    && rm -rf /var/lib/apt/lists/* \
    # 配置 CUDA 库路径
    && echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && ldconfig

# 第二阶段：安装 Python 依赖
FROM base AS deps

WORKDIR /app
COPY requirements.txt .

# 升级 pip 并安装所有依赖
# - CMAKE_ARGS 和 FORCE_CMAKE 用于确保 llama-cpp-python 编译时启用 GPU 支持
# - --no-cache-dir 避免缓存，确保每次都全新安装
RUN ln -s /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/libcuda.so \
    && ln -s /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/libcuda.so.1 \
    && export LD_LIBRARY_PATH="/usr/local/cuda/lib64/stubs:/usr/local/cuda/lib64:${LD_LIBRARY_PATH}" \
    && python3 -m pip install --upgrade pip \
    && export CMAKE_ARGS="-DLLAMA_CUBLAS=on" \
    && export FORCE_CMAKE=1 \
    && pip install --no-cache-dir -r requirements.txt

# ★ 新增的调试步骤 ★
# 打印所有已安装的 Python 包及其版本到构建日志中
# 这可以帮助我们确认 llama-cpp-python 的确切版本
RUN pip freeze

# 第三阶段：构建最终镜像
FROM base AS final

WORKDIR /app

# 从依赖阶段拷贝已安装的库文件
COPY --from=deps /usr/local/lib/python3.10/dist-packages/ /usr/local/lib/python3.10/dist-packages/
COPY --from=deps /usr/local/bin/ /usr/local/bin/

# 拷贝你的应用代码
COPY app /app/app

# 进入 app 目录编译 gRPC protos 文件
WORKDIR /app/app
RUN touch protos/__init__.py \
 && python3 -m grpc_tools.protoc -I=protos \
    --python_out=protos --grpc_python_out=protos \
    protos/inference.proto

# 设置工作目录和 Python 路径
WORKDIR /app
ENV PYTHONPATH="${PYTHONPATH}:/app"

EXPOSE 50051

# 启动 gRPC 服务 (这里假设你的主入口是 main.py 里的 app 对象)
# 注意：你的原始 CMD 是 `python3 -m app.main`。如果你的服务是用 uvicorn 启动的，
# 请使用 `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "50051"]`
# 否则，保持原样即可。
CMD ["python3", "-m", "app.main"]