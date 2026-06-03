#!/bin/bash
set -e

# VPS deployment helper for Al Barakah Mart
# Usage:
#   1) Upload this repository to the VPS, or clone it there.
#   2) SSH into the VPS and run: bash deploy_vps.sh
# Notes:
#   - This script assumes Ubuntu/Debian.
#   - It uses SQLite by default and stores media in frontend/public/media.
#   - Edit the generated .env file before restarting if you need email or social auth.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="albarakahmart"
SOCK_FILE="$PROJECT_DIR/$SERVICE_NAME.sock"
NGINX_CONF="/etc/nginx/sites-available/$SERVICE_NAME"
NGINX_LINK="/etc/nginx/sites-enabled/$SERVICE_NAME"

if [ ! -f "$PROJECT_DIR/manage.py" ]; then
  echo "Error: This script must be placed at the root of the Django project."
  exit 1
fi

echo "Updating package list..."
sudo apt update

echo "Installing required packages..."
sudo apt install -y python3 python3-venv python3-pip nginx git

echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f "$PROJECT_DIR/.env" ]; then
  echo "Creating .env file with production defaults..."
  cat > "$PROJECT_DIR/.env" <<'EOF'
SECRET_KEY=replace-this-with-a-strong-secret
DEBUG=False
ALLOWED_HOSTS=67.205.133.96
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
GOOGLE_CLIENT_ID=
GOOGLE_SECRET=
EOF
  echo "Created .env. Please edit it before starting the service."
fi

echo "Running Django migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

sudo tee "/etc/systemd/system/$SERVICE_NAME.service" > /dev/null <<EOF
[Unit]
Description=Gunicorn service for Al Barakah Mart
After=network.target

[Service]
User=$(whoami)
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn config.wsgi:application --workers 3 --bind unix:$SOCK_FILE

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name 67.205.133.96;

    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
    }

    location /media/ {
        alias $PROJECT_DIR/frontend/public/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$SOCK_FILE;
    }
}
EOF

sudo ln -sf "$NGINX_CONF" "$NGINX_LINK"
sudo nginx -t
sudo systemctl restart nginx

echo "Deployment complete."
echo "If you need an admin user, run: source $VENV_DIR/bin/activate && python manage.py createsuperuser"
