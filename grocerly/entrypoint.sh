#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn server..."
exec gunicorn grocerly.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120
