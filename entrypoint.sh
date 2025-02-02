#!/bin/sh
echo "Waiting for PostgreSQL to start..."

while ! nc -z db 5432; do
  sleep 1
done

echo "PostgreSQL is up!"

# DB migrations and starting Django
python manage.py runserver 0.0.0.0:8000

exec "$@"
