# Knowledge Base Application

This repository contains a simple knowledge-base system built from several services. The project provides two Vue frontends, a FastAPI backend, an inference service running Llama models, and a Chroma vector database. All components can be orchestrated using Docker Compose.

## Components

- **backend** – FastAPI API server that exposes REST and WebSocket endpoints. It communicates with the inference service via gRPC and manages uploaded models.
- **inference** – Python gRPC server that loads language models via `llama_cpp` and performs generation and retrieval.
- **frontend-admin** – Vue 3 interface for administrators to upload models and manage the knowledge base.
- **frontend-user** – Vue 3 chat interface for end users.
- **vector-db** – Chroma database container used to store vector embeddings for retrieval.

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- At least one `.gguf` or `.safetensors` model file under `models/` before starting (embedding model optional)
- Python package `protobuf` version 6.x

### Build and Run

From the repository root, execute:

```bash
docker compose up --build
```

If the build fails with an error such as `Option python_package unknown`, your
Docker cache may still contain an old copy of `inference.proto`. Rebuilding
without the cache ensures the latest proto file bundled with `grpcio-tools` is
used:

```bash
docker compose build --no-cache backend
```

The application depends on `protobuf` 6.x. If your images were built
with an older major version, rebuild all services without the Docker
cache to avoid import errors.

The services will be available on the following ports:

- **Backend API** – [http://localhost:8000](http://localhost:8000)
- **Vector DB** – [http://localhost:8001](http://localhost:8001)
- **Admin Frontend** – [http://localhost:8081](http://localhost:8081)
- **User Frontend** – [http://localhost:8080](http://localhost:8080)

The backend connects to the inference service internally at `inference:50051` and uses the Chroma database container for vector storage.

Stop the stack with `Ctrl+C` or `docker compose down`.


### Adding Models

Before starting the containers you must have at least one generation model
available. Place a `.gguf` or `.safetensors` file directly in the `models/`
folder **before** running `docker compose up`. For example:

```bash
cp ~/Downloads/my-llama-model.gguf models/
```

The inference service looks for generation and embedding models inside the `models/` directory, which is mounted into the containers. At least one generation model (`.gguf` or `.safetensors` file) must exist for the chat interface to produce responses. Place your Llama model file directly under `models/` and restart the stack.

Embedding models can be placed under `models/embedding-model/`. A list of URLs for an example embedding model is provided in `models/urls.txt`. Download the files to that folder if you want to enable embedding retrieval. When the inference service starts it will automatically load the first generation and embedding models it discovers.

Once the files are in place you can visit `http://localhost:8081/model-management` to switch or upload models.

### Switching Models via API

The backend exposes a `POST /api/admin/models/switch` endpoint. The request body
must be JSON in the following form:

```json
{
  "model_name": "your-model-file.gguf"
}
```

The backend will update `models/active_models.json` with the selected
generation model.


The `backend` and `inference` services use pinned Python package versions
defined in their respective `requirements.txt` files. If you modify these
dependencies or encounter build/runtime errors, rebuild the Docker images to
ensure the changes are applied:

```bash
docker compose build
docker compose up
```

Rebuilding guarantees the containers use the updated packages.
=======
### Regenerating gRPC Stubs

If you modify `inference.proto`, regenerate the Python stubs so that both the
`backend` and `inference` copies stay in sync. From the repository root run:

```bash
python -m grpc_tools.protoc -I backend/app/protos \
    --python_out=backend/app/protos \
    --grpc_python_out=backend/app/protos \
    backend/app/protos/inference.proto
python -m grpc_tools.protoc -I inference/app/protos \
    --python_out=inference/app/protos \
    --grpc_python_out=inference/app/protos \
    inference/app/protos/inference.proto
```

Docker automatically performs this step during image builds, but keeping the
generated files committed avoids mismatches between local sources and what the
containers see at build time.
