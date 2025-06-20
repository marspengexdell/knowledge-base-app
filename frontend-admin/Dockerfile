# --- Stage 1: Build Stage ---
FROM node:20.11.1-alpine AS builder
WORKDIR /app

# The build context is './frontend-admin', so paths are simple.
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# --- Stage 2: Production Stage ---
FROM nginx:1.25.4-alpine
LABEL maintainer="Your Name <youremail@example.com>"
COPY --from=builder /app/dist /usr/share/nginx/html

# The path is relative to the build context ('./frontend-admin').
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
