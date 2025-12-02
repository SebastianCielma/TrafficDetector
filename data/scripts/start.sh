#!/bin/bash

echo "Backend FastAPI loading.."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &

echo "Waiting.."
sleep 5


echo "Gradio loading..."
export API_URL="http://localhost:8000"
python frontend/app.py
