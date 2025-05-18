#!/bin/bash

# ================================
# 🚀 Auto Deployment Script
# ================================

set -e  # Exit on error

APP_NAME="face-stream"
APP_DIR="$(pwd)"
VENV_DIR="$APP_DIR/venv"
PYTHON_VERSION="python3.12"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
MAIN_FILE="main.py"

echo "📦 Setting up project: $APP_NAME in $APP_DIR"

# ------------------------
# 1. Update & install dependencies
# ------------------------
echo "🔧 Installing system packages..."
sudo apt-get update -y
sudo apt-get install -y $PYTHON_VERSION $PYTHON_VERSION-venv libgl1 libglib2.0-0 ffmpeg curl

# Check Python version exists
if ! command -v $PYTHON_VERSION >/dev/null 2>&1; then
  echo "❌ Python version $PYTHON_VERSION not found!"
  exit 1
fi

# ------------------------
# 2. Create virtual environment
# ------------------------
if [ ! -d "$VENV_DIR" ]; then
  echo "🐍 Creating virtual environment..."
  $PYTHON_VERSION -m venv "$VENV_DIR"
fi

# Activate environment
source "$VENV_DIR/bin/activate"

# ------------------------
# 3. Install Python packages
# ------------------------
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
if [ ! -f "requirements.txt" ]; then
  echo "❌ requirements.txt not found!"
  exit 1
fi
pip install -r requirements.txt

# ------------------------
# 4. Create systemd service
# ------------------------
echo "🛠️ Creating systemd service at $SERVICE_FILE"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=RTSP Multi-Camera Face Stream Processor
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/python $APP_DIR/$MAIN_FILE
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# ------------------------
# 5. Start and enable service
# ------------------------
echo "🚀 Starting systemd service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$APP_NAME"
sudo systemctl restart "$APP_NAME"

# Show status
echo "📋 Service status:"
sudo systemctl status "$APP_NAME" --no-pager

echo "✅ Deployment complete."
echo "📜 View logs: journalctl -u $APP_NAME -f"
