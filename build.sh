#!/bin/bash
# Vercel Build Script

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Running migrations..."
python manage.py migrate

echo "Build completed successfully!"
