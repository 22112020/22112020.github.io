#!/bin/bash
# TGQ — Ubuntu proot dependency installer
# Run: bash setup_ubuntu_deps.sh
# Tested on: ARM64 (Snapdragon 835 / Note 8)
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }

echo "========================================"
echo "  TGQ — Ubuntu proot Setup"
echo "  Note 8 ARM64 | $(uname -m)"
echo "========================================"

# --- 1. System update ---
echo; info "System update..."
sudo apt update && sudo apt upgrade -y

# --- 2. Python ---
echo; info "Python + pip..."
sudo apt install -y python3 python3-pip python3-venv
python3 --version

# --- 3. Tools ---
echo; info "Basic tools..."
sudo apt install -y git curl wget nano htop net-tools

# --- 4. SSH server ---
echo; info "OpenSSH server (port 8023)..."
sudo apt install -y openssh-server
# Proot: systemctl gak jalan, start manual
sudo mkdir -p /var/run/sshd
sudo /usr/sbin/sshd -p 8023 2>/dev/null || true
sleep 1
ss -tlnp | grep 8023 && info "SSH running on port 8023" || warn "SSH not running, start manual: sudo /usr/sbin/sshd -p 8023"

# --- 5. Python packages ---
echo; info "Python packages..."
python3 -m pip install --upgrade pip -q
python3 -m pip install fastapi uvicorn pydantic python-dotenv orjson -q

# --- 6. Clone / update TGQ ---
echo; info "Clone TGQ from GitHub..."
if [ -d "/mnt/d/Alfian/Togelku" ]; then
  warn "Local TGQ found — skip clone"
elif [ -d "$HOME/Togelku" ]; then
  warn "TGQ already cloned — skip"
else
  git clone https://github.com/viantmocy/tgq.git "$HOME/Togelku" 2>/dev/null || \
  git clone https://github.com/viantmocy/tgq.git /tmp/tgq
fi

# --- 7. Test TGQ ---
echo; info "Testing TGQ..."
TGQ_DIR=""
[ -d "$HOME/Togelku" ] && TGQ_DIR="$HOME/Togelku"
[ -d "/mnt/d/Alfian/Togelku" ] && TGQ_DIR="/mnt/d/Alfian/Togelku"
[ -d "/tmp/tgq" ] && TGQ_DIR="/tmp/tgq"

if [ -n "$TGQ_DIR" ]; then
  cd "$TGQ_DIR"
  python3 -m unittest discover tests -v 2>&1 | tail -3 || warn "Some tests may have failed"
else
  warn "TGQ repo not found — clone manual: git clone https://github.com/viantmocy/tgq.git"
fi

# --- 8. Cloudflare Tunnel (optional) ---
echo; info "Cloudflared (optional)..."
curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o /tmp/cloudflared
chmod +x /tmp/cloudflared
sudo mv /tmp/cloudflared /usr/local/bin/cloudflared 2>/dev/null || true
cloudflared version 2>/dev/null && info "cloudflared installed" || warn "cloudflared not installed (ARM binary?)"

# --- Summary ---
echo; echo "========================================"
info "Setup complete!"
echo ""
echo "  Start server:"
echo "    cd ~/Togelku"
echo "    python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8443 --reload"
echo ""
echo "  Public tunnel:"
echo "    cloudflared tunnel --url http://localhost:8443"
echo ""
echo "  Remote SSH:"
echo "    ssh milklho@<IP_NOTE8> -p 8023"
echo "========================================"
