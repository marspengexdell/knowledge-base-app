# Knowledge Base Application

This repository contains a simple knowledge-base system built from several services. The project provides two Vue frontends, a FastAPI backend, an inference service running Llama models, and a Chroma vector database. All components can be orchestrated using Docker Compose.

## Components

- **backend** – FastAPI API server that exposes REST and WebSocket endpoints. It communicates with the inference service via gRPC and manages uploaded models.
- **inference** – Python gRPC server that loads language models via `llama_cpp` and performs generation and retrieval. The container runs `python app/main.py` at startup.
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

### Generation Limits

The inference service streams at most `150` new tokens by default. Set the
`MAX_NEW_TOKENS` environment variable to change this limit. If `STOP_TOKEN` is
defined, generation stops early whenever the substring appears in the output.

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

### Managing Knowledge Documents

Documents uploaded through the admin interface are saved under
`knowledge_base_docs/`, which is mounted into the backend container for
persistence. The following admin API endpoints are available:

- `POST /api/admin/knowledge/upload` – upload a `.txt` file
- `GET  /api/admin/knowledge/list` – list stored documents
- `GET  /api/admin/knowledge/download?file=<name>` – download a document
- `DELETE /api/admin/knowledge/delete?file=<name>` – remove a document

The admin UI at `http://localhost:8081/knowledge-base` provides a simple file
uploader for these operations.

### Embedding API

If an embedding model is loaded, the endpoint
`GET /api/embedding/embed_doc?file_name=<name>` returns the vector embedding for
a stored document.


The `backend` and `inference` services use pinned Python package versions
defined in their respective `requirements.txt` files. If you modify these
dependencies or encounter build/runtime errors, rebuild the Docker images to
ensure the changes are applied:

```bash
docker compose build
docker compose up
```

Rebuilding guarantees the containers use the updated packages.

### Stop Token

During chat generation the backend instructs the model to append `<END>` once it
finishes reasoning. The inference service watches the output stream and stops
producing further tokens as soon as this marker appears. The WebSocket client
still receives `[DONE]` when the stream ends.

### Updating PyTorch Wheels

The inference image installs PyTorch from local wheel files found in
`inference/pytorch-wheels/`. These wheels are not committed to the repository.
When upgrading PyTorch, manually download the CUDA 12.1 builds of
`torch`, `torchvision` and `torchaudio` from the official
[PyTorch wheel index](https://download.pytorch.org/whl/cu121) and place them in
that directory before rebuilding the containers.

### Caching with `llama_cpp`

The inference service now enables key/value caching when generating text. This
improves throughput but increases memory usage. Set the environment variable
`USE_KV_CACHE=0` when starting the container to disable caching if your
system has limited RAM.
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

After editing `inference.proto` or code under `inference/app`, rebuild the `inference` service and restart the containers:

```bash
docker compose build inference    # add --no-cache if necessary
docker compose up -d
```

## Tuning Generation

The inference container exposes a few environment variables that control how text
is generated. Adjust these values in `docker-compose.yml` under the
`inference` service.

### Maximum generation length

Set `MAX_TOKENS` to limit the number of tokens returned for a single request.
The default is `4096`.

```yaml
  inference:
    environment:
      - MAX_TOKENS=2048
```

### Early stopping tokens

Provide a comma‑separated list via `EARLY_STOP_TOKENS` to stop generation when
any of the tokens appear in the output.

```yaml
  inference:
    environment:
      - EARLY_STOP_TOKENS=<|eot|>,<|endoftext|>
```

### Key‑value cache

The `USE_KV_CACHE` variable toggles the model’s KV cache. Set it to `0` to
disable caching or `1` to enable it (the default).

```yaml
  inference:
    environment:
      - USE_KV_CACHE=0
```

## Deploying with Nginx

The project ships with an optional Nginx reverse proxy configuration located
under `nginx/`. It routes incoming HTTPS traffic to the backend API and the two
Vue frontends while Certbot manages the TLS certificates.

### Obtaining certificates

Edit `nginx/nginx.conf` and replace the example domain names with your own.
Create the certificate volumes and run Certbot once to generate the initial
certificates:

```bash
docker volume create certbot-etc
docker volume create certbot-web
docker compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  -d example.com -d api.example.com -d admin.example.com \
  --email you@example.com --agree-tos --no-eff-email
```

The certificates reside in the `certbot-etc` volume. The `certbot` service runs
`certbot renew` every 12&nbsp;hours to keep them up to date.

### Starting the stack

Start all containers, including Nginx, with:

```bash
docker compose up --build
```

Nginx exposes ports `80` and `443` while the individual services communicate
through the internal Docker network.
