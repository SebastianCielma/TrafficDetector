#!/bin/bash


if [ -z "$CELERY_BROKER_URL" ]; then
    echo "WARNING: CELERY_BROKER_URL is missing! Background tasks will fail."
fi


uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &


echo "Start Celery Worker..."
celery -A backend.app.core.celery_app worker --loglevel=info --concurrency=1 &

echo "Waiting..."
sleep 10


echo "Start Frontend..."
export API_URL="http://localhost:8000"
python frontend/app.py
