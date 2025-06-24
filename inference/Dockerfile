# Base image with CUDA 12.1.1 and cuDNN 8 development tools
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# Set environment variables to non-interactive to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# --- 1. Install System Dependencies and Build Tools ---
# Update package lists and install a complete build toolchain
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    python3-pip \
    git \
    cmake \
    pkg-config \
    ninja-build \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# --- 2. Configure Environment for CUDA ---
# **THE FIX IS HERE**: Make the CUDA libraries permanently available to the system linker.
# This ensures that all subprocesses, including those for linking C++ code, can find libcuda.so.
RUN echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && ldconfig
ENV PATH="/usr/local/cuda/bin:${PATH}"

# --- 3. Install PyTorch with CUDA Support ---
# Pre-download the required wheels and copy them into the image. This avoids
# reaching out to the remote index during the build which is useful for
# offline or reproducible setups.
COPY pytorch-wheels /tmp/pytorch-wheels
RUN pip3 install --no-cache-dir /tmp/pytorch-wheels/*.whl

# --- 4. Install Remaining Python Dependencies (Including llama-cpp-python) ---
# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/requirements.txt

# Set the correct environment variable to force CUDA compilation for llama-cpp-python.
ENV CMAKE_ARGS="-DGGML_CUDA=ON"

# Install all other dependencies from requirements.txt.
# Pip will automatically build llama-cpp-python from source using the environment variables above.
RUN pip3 install --no-cache-dir -r requirements.txt

# --- 5. Copy Application Code and Generate gRPC files ---
# Copy the entire app directory into the container's /app
# (This path is relative to the Dockerfile's location)
COPY app /app

# Generate gRPC code from .proto file
# Ensure the 'protos' directory is correctly placed in your build context.
RUN python3 -m grpc_tools.protoc \
    -I=. \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

# --- 6. Set Container Entrypoint ---
# The command to run when the container starts.
CMD ["python", "app/main.py"]
