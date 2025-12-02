#!/bin/bash

echo "🔍 Weryfikacja..."
which python
python -c "import gradio; print('✅ Gradio OK')"

# 1. Start Backendu
echo "🚀 Backend..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &

# 2. Czekanie
echo "⏳ Czekam 5s..."
sleep 5

# 3. Start Frontendu
echo "🚀 Frontend..."
export API_URL="http://localhost:8000"
python frontend/app.py
