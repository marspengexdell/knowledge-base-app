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
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# --- 2. Install PyTorch with CUDA Support ---
# This is the most reliable way to install PyTorch with GPU support.
# It fetches pre-compiled wheels for CUDA 12.1, avoiding a lengthy and error-prone source build.
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# --- 3. Install llama-cpp-python with Forced CUDA Compilation ---
# Set environment variables to force llama-cpp-python to compile with CUDA support.
# We install it separately and use --no-binary to ensure it's built from source using these flags.
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"
ENV FORCE_CUDA="1"
# Note: We only force compilation for this specific package
RUN pip3 install --no-cache-dir --force-reinstall --no-binary llama-cpp-python "llama-cpp-python[cuda]"

# --- 4. Install Remaining Python Dependencies ---
# Set the working directory
WORKDIR /app
# Copy the requirements file
COPY requirements.txt /app/requirements.txt
# Install the rest of the dependencies from requirements.txt.
# This will use pre-compiled wheels where available, which is much faster.
RUN pip3 install --no-cache-dir -r requirements.txt

# --- 5. Copy Application Code and Generate gRPC files ---
# Copy the entire app directory into the container's /app
# (This path is relative to the Dockerfile's location, i.e., inside the 'inference' directory)
COPY app /app

# Generate gRPC code from .proto file
# Ensure the 'protos' directory exists in the build context.
RUN python3 -m grpc_tools.protoc \
    -I=. \
    --python_out=. \
    --grpc_python_out=. \
    protos/inference.proto

# --- 6. Set Container Entrypoint ---
# The command to run when the container starts.
CMD ["python", "app/main.py"]
