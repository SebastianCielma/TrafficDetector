#!/bin/bash

echo "Verify..."
which python
python -c "import gradio; print('✅ Gradio OK')"

echo "Backend..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &

echo "Waiting..."
sleep 5

echo "Frontend..."
export API_URL="http://localhost:8000"
python frontend/app.py
