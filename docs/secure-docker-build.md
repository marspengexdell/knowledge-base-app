# Building a Private Docker Image

This guide explains one approach to package the knowledge-base application into a Docker image without exposing the Python source code.

## Overview

The default Dockerfile copies all source files into the final image. To avoid distributing raw `.py` files, compile them into bytecode during the build and remove the original files.

## Example Dockerfile Snippet

Use a multi-stage build. After installing dependencies and copying the backend code, compile all modules:

```Dockerfile
FROM python:3.10-slim AS backend-build
WORKDIR /backend
COPY modules/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY modules/backend /backend

# Compile Python files and remove the sources
RUN python -m compileall -b /backend \
    && find /backend -name '*.py' -delete
```

In the final stage, copy only the compiled code:

```Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY --from=backend-build /backend /app
# copy frontend build artifacts as usual
```

This keeps only the `.pyc` bytecode inside the image. Although bytecode can still be decompiled, it hides the plain source code.

## Building the Image

```bash
docker build -t kb-app-private .
```

## Running the Container

```bash
docker run -d --name kb-app \
  -p 8000:8000 \
  -v $(pwd)/models:/models \
  -v $(pwd)/knowledge_base_docs:/knowledge_base_docs \
  kb-app-private
```

The application will be available on port `8000`. Mount the `models` and `knowledge_base_docs` directories so the container can access your models and documents.

