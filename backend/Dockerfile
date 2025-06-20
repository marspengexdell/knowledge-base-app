# --- Stage 1: Base Image ---
FROM python:3.10-slim

# --- Metadata ---
LABEL maintainer="Your Name <youremail@example.com>"
LABEL description="Dockerfile for the Backend API Service of Knowledge Base App"

# --- Environment Variables ---
ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# --- System Dependencies ---
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- Working Directory ---
WORKDIR /app

# --- Python Dependencies ---
COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy Application Code ---
COPY ./backend/app /app/app

# --- gRPC Proto Files ---
COPY ./inference/app/protos/inference.proto /app/app/protos/inference.proto

# --- CRITICAL FIX: Turn 'protos' into a Python package ---
# Create the directory and an __init__.py file inside it.
RUN mkdir -p /app/app/protos && touch /app/app/protos/__init__.py

# Now, compile the .proto file, which will generate code inside the 'protos' package.
RUN python -m grpc_tools.protoc -I/app/app/protos --python_out=/app/app/protos --grpc_python_out=/app/app/protos /app/app/protos/inference.proto

# --- Expose Port ---
EXPOSE 8000

# --- Entry Point ---
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
