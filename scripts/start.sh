#!/bin/bash

echo "🔍 Generowanie konfiguracji (Environment -> .env)..."


touch .env
echo "DATABASE_URL=$DATABASE_URL" >> .env
echo "CELERY_BROKER_URL=$CELERY_BROKER_URL" >> .env
echo "S3_BUCKET_NAME=$S3_BUCKET_NAME" >> .env
echo "S3_ENDPOINT=$S3_ENDPOINT" >> .env
echo "S3_ACCESS_KEY=$S3_ACCESS_KEY" >> .env
echo "S3_SECRET_KEY=$S3_SECRET_KEY" >> .env


echo "Start Backend FastAPI..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &

echo "Start Celery Worker..."
celery -A backend.app.core.celery_app worker --loglevel=info --concurrency=1 &

echo "Waiting..."
sleep 10

echo "Frontend Gradio..."
export API_URL="http://localhost:8000"
python frontend/app.py
