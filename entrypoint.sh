#!/bin/sh

echo "Waiting for PostgreSQL to start..."

while ! nc -z db 5432; do
  sleep 1
done

echo "PostgreSQL is up!"

# Start Django development server in background
python manage.py runserver 0.0.0.0:8000 &

# Start Celery worker in background
celery -A delivery_service worker --loglevel=debug &

wait