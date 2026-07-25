#!/bin/bash
# TGQ — Ubuntu proot dependency installer
# Run inside proot-distri: bash setup_ubuntu_deps.sh
# Note: proot = root, no sudo needed
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

echo "========================================"
echo "  TGQ — Ubuntu proot Setup"
echo "  $(uname -m) | $(cat /etc/os-release 2>/dev/null | head -1)"
echo "========================================"

# --- 1. System update ---
echo; info "System update..."
apt update && apt upgrade -y

# --- 2. Python ---
echo; info "Python + pip..."
apt install -y python3 python3-pip python3-venv
python3 --version

# --- 3. Tools ---
echo; info "Basic tools..."
apt install -y git curl wget nano htop net-tools

# --- 4. SSH server ---
echo; info "OpenSSH server (port 8023)..."
apt install -y openssh-server
mkdir -p /var/run/sshd
/usr/sbin/sshd -p 8023 2>/dev/null || true
sleep 1
ss -tlnp | grep 8023 && info "SSH running on port 8023" || warn "SSH not running, start manual: /usr/sbin/sshd -p 8023"

# --- 5. Python packages ---
echo; info "Python packages..."
python3 -m pip install --upgrade pip -q
python3 -m pip install fastapi uvicorn pydantic python-dotenv orjson -q

# --- 6. Clone TGQ ---
echo; info "Clone TGQ from GitHub..."
if [ -d "$HOME/Togelku" ]; then
  warn "TGQ already exists at \$HOME/Togelku — skip clone"
else
  git clone https://github.com/viantmocy/tgq.git "$HOME/Togelku"
fi

# --- 7. Test TGQ ---
echo; info "Testing TGQ..."
cd "$HOME/Togelku"
python3 -m unittest discover tests -v 2>&1 | tail -3

# --- 8. Cloudflare Tunnel (optional) ---
echo; info "Cloudflared (optional)..."
curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o /tmp/cloudflared
chmod +x /tmp/cloudflared
mv /tmp/cloudflared /usr/local/bin/cloudflared 2>/dev/null || true
cloudflared version 2>/dev/null && info "cloudflared installed" || warn "cloudflared not installed"

# --- Summary ---
echo; echo "========================================"
info "Setup done!"
echo ""
echo "  Start TGQ server:"
echo "    cd ~/Togelku"
echo "    python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8443 --reload"
echo ""
echo "  Public tunnel (optional):"
echo "    cloudflared tunnel --url http://localhost:8443"
echo ""
echo "  SSH remote (from WSL):"
echo "    ssh <IP_NOTE8> -p 8023"
echo "========================================"
