#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Installing gettext for translations..."
apt-get update && apt-get install -y gettext

echo "Compiling translations..."
python manage.py compilemessages

echo "Running database migrations..."
python manage.py migrate

echo "Build completed successfully!"
