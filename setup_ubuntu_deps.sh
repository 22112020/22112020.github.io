#!/bin/bash
# Setup Ubuntu proot — dependencies untuk TGQ server
# Jalanin satu per satu (jangan langsung copas semua)

echo "=== 1. System update ==="
sudo apt update && sudo apt upgrade -y

echo "=== 2. Python + pip ==="
sudo apt install -y python3 python3-pip python3-venv

echo "=== 3. Tools umum ==="
sudo apt install -y git curl wget nano htop net-tools

echo "=== 4. SSH server ==="
sudo apt install -y openssh-server
# Jalanin manual:
# sudo /usr/sbin/sshd -p 8023

echo "=== 5. Nginx (reverse proxy) ==="
sudo apt install -y nginx

echo "=== 6. Process manager ==="
# Di proot systemd gak jalan, pake supervisord
sudo apt install -y supervisor

echo "=== 7. Monitoring ==="
sudo apt install -y neofetch tmux

echo "=== 8. Python packages (via pip) ==="
python3 -m pip install --upgrade pip
python3 -m pip install fastapi uvicorn pydantic python-dotenv orjson

echo "=== 9. Cloudflare Tunnel (opsional, untuk public akses) ==="
# Download cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o /tmp/cloudflared
chmod +x /tmp/cloudflared
sudo mv /tmp/cloudflared /usr/local/bin/

echo "=== DONE ==="
echo ""
echo "Sisa manual:"
echo "  1. Clone repo TGQ"
echo "  2. Setup SSH config (/etc/ssh/sshd_config port 8023)"
echo "  3. Jalankan server: uvicorn api.main:app --host 0.0.0.0 --port 8443"
echo "  4. cloudflared tunnel --url http://localhost:8443  (untuk akses publik)"
