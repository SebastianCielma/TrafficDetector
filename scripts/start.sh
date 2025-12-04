#!/bin/bash

echo "🔍 --- DIAGNOSTYKA ZMIENNYCH ŚRODOWISKOWYCH ---"
echo "Wypisuję nazwy dostępnych zmiennych (bez wartości):"

printenv | cut -d= -f1 | sort

echo "------------------------------------------------"
echo "Sprawdzam specyficzne klucze S3:"

if [ -z "${S3_BUCKET_NAME}" ]; then echo "❌ S3_BUCKET_NAME jest PUSTA lub NIEISTNIEJE"; else echo "✅ S3_BUCKET_NAME obecna"; fi
if [ -z "${S3_ENDPOINT}" ]; then echo "❌ S3_ENDPOINT jest PUSTA lub NIEISTNIEJE"; else echo "✅ S3_ENDPOINT obecna"; fi
if [ -z "${S3_ACCESS_KEY}" ]; then echo "❌ S3_ACCESS_KEY jest PUSTA lub NIEISTNIEJE"; else echo "✅ S3_ACCESS_KEY obecna"; fi
if [ -z "${S3_SECRET_KEY}" ]; then echo "❌ S3_SECRET_KEY jest PUSTA lub NIEISTNIEJE"; else echo "✅ S3_SECRET_KEY obecna"; fi

echo "🔍 --- KONIEC DIAGNOSTYKI ---"

# 1. Start Backendu
echo "🚀 Uruchamiam Backend FastAPI..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &

# 2. Czekanie
echo "⏳ Czekam 5 sekund..."
sleep 5

# 3. Start Frontendu
echo "🚀 Uruchamiam Frontend Gradio..."
export API_URL="http://localhost:8000"
python frontend/app.py
