#!/bin/bash
echo "启动 supervisord 同时运行后端和 Chroma..."
exec supervisord -c /app/supervisord.conf
