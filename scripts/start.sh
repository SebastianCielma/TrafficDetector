#!/bin/bash


touch .env

echo "DATABASE_URL=$DATABASE_URL" >> .env
echo "CELERY_BROKER_URL=$CELERY_BROKER_URL" >> .env
echo "S3_BUCKET_NAME=$S3_BUCKET_NAME" >> .env
echo "S3_ENDPOINT=$S3_ENDPOINT" >> .env
echo "S3_ACCESS_KEY=$S3_ACCESS_KEY" >> .env
echo "S3_SECRET_KEY=$S3_SECRET_KEY" >> .env
echo "LOKI_URL=$LOKI_URL" >> .env
echo "LOKI_USERNAME=$LOKI_USERNAME" >> .env
echo "LOKI_PASSWORD=$LOKI_PASSWORD" >> .env

echo "API_KEY=$API_KEY" >> .env
echo "UI_USERNAME=$UI_USERNAME" >> .env
echo "UI_PASSWORD=$UI_PASSWORD" >> .env


echo " Backend FastAPI..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &

echo "Celery Worker..."
celery -A backend.app.core.celery_app worker --loglevel=info --concurrency=1 &

echo "Waiting..."
sleep 10

echo "Frontend Gradio..."
export API_URL="http://localhost:8000"
python frontend/app.py
