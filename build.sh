#!/bin/bash

# Build script for Vercel
echo "Building Django static files..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

echo "Build complete!"
