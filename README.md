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
- Optional: place your Llama or embedding models in the `models/` directory before starting

### Build and Run

From the repository root, execute:

```bash
docker compose up --build
```

The services will be available on the following ports:

- **Backend API** – [http://localhost:8000](http://localhost:8000)
- **Vector DB** – [http://localhost:8001](http://localhost:8001)
- **Admin Frontend** – [http://localhost:8081](http://localhost:8081)
- **User Frontend** – [http://localhost:8080](http://localhost:8080)

The backend connects to the inference service internally at `inference:50051` and uses the Chroma database container for vector storage.

Stop the stack with `Ctrl+C` or `docker compose down`.

