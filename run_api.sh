#!/bin/bash
# NyayaSetu AI - API Server Launcher

echo "Starting NyayaSetu AI API Server..."
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""

uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
