#!/bin/bash

# ================================
# 🚀 Auto Deployment Script
# ================================

APP_NAME="face-stream"
VENV_DIR="venv"
PYTHON_VERSION="python3.12"
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"

echo "📦 Setting up project: $APP_NAME"

# ------------------------
# 1. Update & install dependencies
# ------------------------
echo "🔧 Installing system packages..."
sudo apt-get update -y
sudo apt-get install -y $PYTHON_VERSION $PYTHON_VERSION-venv libgl1 libglib2.0-0 ffmpeg curl

# ------------------------
# 2. Create virtual environment
# ------------------------
if [ ! -d "$VENV_DIR" ]; then
  echo "🐍 Creating virtual environment..."
  $PYTHON_VERSION -m venv $VENV_DIR
fi

echo "📥 Installing Python dependencies..."
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ------------------------
# 3. Create systemd service
# ------------------------
echo "🛠️ Setting up systemd service..."

cat <<EOF | sudo tee $SERVICE_FILE > /dev/null
[Unit]
Description=RTSP Multi-Camera Face Stream Processor
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/$VENV_DIR/bin/python main.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# ------------------------
# 4. Enable + Start service
# ------------------------
echo "🚀 Starting service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl restart $APP_NAME
sudo systemctl status $APP_NAME --no-pager

echo "✅ Deployment complete. Logs: journalctl -u $APP_NAME -f"
