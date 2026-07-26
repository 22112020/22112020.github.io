#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  TGQ — Termux Native VPS Deploy (root only)
#  Install semua deps + setup VPS pribadi di HP rooted
#  Bisa jalan standalone via curl ke GitHub:
#
#    curl -sL https://raw.githubusercontent.com/22112020/22112020.github.io/master/termux_deploy.sh | su -c bash
#
#  Atau:
#    su -c bash termux_deploy.sh
# ============================================================
#  Cocok untuk: rooted Android + mini cooling fan + 24/7 VPS
# ============================================================

set -euo pipefail

# Konfigurasi
TGQ_REPO="https://github.com/22112020/22112020.github.io.git"
TGQ_BRANCH="master"
TGQ_DIR="${TGQ_DIR:-$HOME/tgq}"
SSH_PORT=8022

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1"; }
title() { echo -e "${CYAN}━━━ $1 ━━━${NC}"; }
section() { echo; echo -e "${CYAN}════════════════════════════════════════════════${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}════════════════════════════════════════════════${NC}"; }

echo -e "${CYAN}"
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║     TGQ — Termux Native VPS Deploy              ║"
echo "  ║     Rooted Android | No Battery | Mini Fan       ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================
# 0. ROOT CHECK
# ============================================================
section "0/8: ROOT CHECK"

if [ "$(id -u)" -ne 0 ]; then
    err "Harus jalan sebagai root! Gunakan: su -c bash termux_deploy.sh"
    echo ""
    echo "  Alternatif dari GitHub (tanpa download manual):"
    echo "    curl -sL https://raw.githubusercontent.com/22112020/22112020.github.io/master/termux_deploy.sh | su -c bash"
    echo ""
    exit 1
fi
info "Root user confirmed"

if [ ! -d /data/data/com.termux ]; then
    err "Bukan lingkungan Termux!"
    exit 1
fi
info "Termux environment detected"

PREFIX="/data/data/com.termux/files/usr"

# ============================================================
# 0b. SETUP TGQ DIRECTORY
# ============================================================
section "0b/8: TGQ DIRECTORY"

SCRIPT_SOURCE="$(cd "$(dirname "$0")" 2>/dev/null && pwd || echo "")"

# Deteksi apakah sudah di dalam TGQ repo atau perlu clone
if [ -f "$SCRIPT_SOURCE/run_server.sh" ] && [ -f "$SCRIPT_SOURCE/api/main.py" ]; then
    TGQ_DIR="$SCRIPT_SOURCE"
    info "Script berjalan dari dalam TGQ repo: $TGQ_DIR"
elif [ -d "$TGQ_DIR/.git" ]; then
    info "TGQ sudah ada di $TGQ_DIR, update repo..."
    cd "$TGQ_DIR"
    git pull origin "$TGQ_BRANCH" 2>/dev/null || true
elif [ -d "$TGQ_DIR" ] && [ -f "$TGQ_DIR/run_server.sh" ]; then
    info "TGQ sudah ada di $TGQ_DIR (tanpa .git)"
elif [ -f "$TGQ_DIR" ]; then
    err "$TGQ_DIR bukan direktori"
    exit 1
else
    warn "TGQ belum ada di $TGQ_DIR — cloning dari GitHub..."
    mkdir -p "$TGQ_DIR"
    git clone --depth 1 -b "$TGQ_BRANCH" "$TGQ_REPO" "$TGQ_DIR" 2>&1
    info "TGQ cloned ke $TGQ_DIR"
fi

cd "$TGQ_DIR"
APP_DIR="$TGQ_DIR"
info "Working directory: $APP_DIR"

# ============================================================
# 1. SYSTEM UPDATE
# ============================================================
section "1/8: SYSTEM UPDATE"

info "Updating packages..."
apt update -qq && apt upgrade -y -qq
info "System updated"

# ============================================================
# 2. INSTALL NATIVE TERMUX PACKAGES
# ============================================================
section "2/8: INSTALL PACKAGES"

PKGS=(
    python3
    clang
    git
    openssh
    screen
    nodejs
    nginx
    termux-services
    termux-exec
    openssl-tool
    curl
    wget
    htop
    nmon
    tsu
)

for pkg in "${PKGS[@]}"; do
    if ! which "$pkg" &>/dev/null && ! dpkg -s "$pkg" &>/dev/null 2>&1; then
        warn "Installing $pkg..."
        apt install -y "$pkg" -qq 2>/dev/null || true
    else
        info "$pkg already installed"
    fi
done

PYTHON_VERSION=$(python3 --version 2>&1)
NODE_VERSION=$(node --version 2>&1)
NGINX_VERSION=$(nginx -v 2>&1 | grep -oP 'nginx/\K[0-9.]+' || echo "unknown")
info "Python: $PYTHON_VERSION"
info "Node:   $NODE_VERSION"
info "Nginx:  $NGINX_VERSION"

# ============================================================
# 3. INSTALL PYTHON PACKAGES
# ============================================================
section "3/8: PYTHON PACKAGES"

info "Upgrading pip..."
python3 -m pip install --upgrade pip setuptools wheel -q

if [ -f "$APP_DIR/requirements.txt" ]; then
    info "Installing from requirements.txt..."
    python3 -m pip install -r "$APP_DIR/requirements.txt" -q
else
    warn "requirements.txt not found, installing core packages..."
    python3 -m pip install fastapi uvicorn pydantic python-dotenv pyyaml markdown rich orjson -q
fi

python3 -c "import fastapi, uvicorn, pydantic, yaml, markdown, rich, orjson; print('[OK] All Python packages verified')" 2>&1
info "Python packages OK"

# ============================================================
# 4. SETUP SSH
# ============================================================
section "4/8: SSH SERVER"

SSHD_CONFIG="$PREFIX/etc/ssh/sshd_config"

if [ ! -f "$SSHD_CONFIG" ]; then
    warn "sshd_config not found, installing openssh..."
    apt install -y openssh -qq
fi

cp "$SSHD_CONFIG" "${SSHD_CONFIG}.bak" 2>/dev/null || true

sed -i "s/^Port .*/Port $SSH_PORT/" "$SSHD_CONFIG" 2>/dev/null || \
    echo "Port $SSH_PORT" >> "$SSHD_CONFIG"
sed -i "s/^#Port .*/Port $SSH_PORT/" "$SSHD_CONFIG" 2>/dev/null

sed -i "s/^PermitRootLogin .*/PermitRootLogin yes/" "$SSHD_CONFIG" 2>/dev/null || \
    echo "PermitRootLogin yes" >> "$SSHD_CONFIG"

sed -i "s/^PasswordAuthentication .*/PasswordAuthentication no/" "$SSHD_CONFIG" 2>/dev/null || \
    echo "PasswordAuthentication no" >> "$SSHD_CONFIG"

sed -i "s/^PubkeyAuthentication .*/PubkeyAuthentication yes/" "$SSHD_CONFIG" 2>/dev/null || \
    echo "PubkeyAuthentication yes" >> "$SSHD_CONFIG"

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ ! -f "$HOME/.ssh/authorized_keys" ]; then
    touch "$HOME/.ssh/authorized_keys"
    chmod 600 "$HOME/.ssh/authorized_keys"
    warn "~/.ssh/authorized_keys kosong!"
    echo ""
    echo "  Tambahkan public key SSH-mu:"
    echo "    echo 'ssh-ed25519 AAAA...' >> ~/.ssh/authorized_keys"
    echo "    chmod 600 ~/.ssh/authorized_keys"
    echo ""
fi

if pgrep sshd >/dev/null 2>&1; then
    info "SSH already running"
else
    sshd -p "$SSH_PORT" 2>/dev/null || true
    sleep 1
    if pgrep sshd >/dev/null 2>&1; then
        info "SSH started on port $SSH_PORT"
    fi
fi

# ============================================================
# 5. SETUP NGINX (reverse proxy TGQ)
# ============================================================
section "5/8: NGINX REVERSE PROXY"

NGINX_CONF="$PREFIX/etc/nginx/conf.d/tgq.conf"
mkdir -p "$PREFIX/etc/nginx/conf.d"

cat > "$NGINX_CONF" << NGINXEOF
server {
    listen 80 default_server;
    server_name localhost;

    access_log $APP_DIR/logs/nginx_access.log;
    error_log  $APP_DIR/logs/nginx_error.log;

    location / {
        proxy_pass http://127.0.0.1:8443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias $APP_DIR/UI/webapp/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
NGINXEOF
info "Nginx config created: $NGINX_CONF"

nginx -t 2>&1 | head -1 && info "Nginx config OK" || warn "Nginx config error"

# ============================================================
# 6. SETUP CLOUDFLARED TUNNEL (opsional)
# ============================================================
section "6/8: CLOUDFLARED TUNNEL (optional)"

ARCH=$(uname -m)
case "$ARCH" in
    aarch64|arm64) CF_ARCH="arm64" ;;
    armv7l|armhf)  CF_ARCH="arm" ;;
    x86_64|amd64)  CF_ARCH="amd64" ;;
    i686|i386)     CF_ARCH="386" ;;
    *)             CF_ARCH="arm64" ;;
esac

if which cloudflared &>/dev/null; then
    info "cloudflared already installed: $(cloudflared version 2>/dev/null | head -1)"
else
    warn "Installing cloudflared ($CF_ARCH)..."
    curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$CF_ARCH" -o "$PREFIX/bin/cloudflared"
    chmod +x "$PREFIX/bin/cloudflared"
    if cloudflared version &>/dev/null; then
        info "cloudflared installed"
    else
        warn "cloudflared install failed — install manual nanti"
    fi
fi

echo ""
echo "  Untuk tunnel publik (opsional):"
echo "    cloudflared tunnel --url http://localhost:8443"
echo ""

# ============================================================
# 7. TEST SUITE TGQ
# ============================================================
section "7/8: TEST SUITE"

cd "$APP_DIR"
if [ -d tests ]; then
    info "Running TGQ test suite..."
    python3 -m unittest discover tests -v 2>&1 | tail -5 || true
    info "Tests selesai"
else
    warn "Folder tests/ tidak ditemukan — skip testing"
fi

# ============================================================
# 8. SETUP AUTO-BOOT & START SERVICES
# ============================================================
section "8/8: AUTO-BOOT & START SERVICES"

# --- Termux:Boot ---
BOOT_DIR="$HOME/.termux/boot"
mkdir -p "$BOOT_DIR"

cat > "$BOOT_DIR/tgq.sh" << 'BOOTSCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
# TGQ — Auto-start VPS services (diinstall oleh termux_deploy.sh)
termux-wake-lock
sleep 5

# SSH
sshd -p 8022 2>/dev/null || true

# Nginx
nginx 2>/dev/null || true

# TGQ server
APP_DIR="$HOME/tgq"
if [ -f "$APP_DIR/run_server.sh" ]; then
    cd "$APP_DIR" || exit 1
    nohup bash run_server.sh > "$APP_DIR/logs/boot.log" 2>&1 &
fi
BOOTSCRIPT

chmod +x "$BOOT_DIR/tgq.sh"
info "Boot script installed: $BOOT_DIR/tgq.sh"
echo "  Pastikan Termux:Boot terinstall dari F-Droid"

# --- Start services ---
title "START SERVICES"

# Start SSH
if ! pgrep sshd >/dev/null 2>&1; then
    sshd -p "$SSH_PORT" 2>/dev/null && info "SSH started on port $SSH_PORT" || warn "SSH start failed"
else
    info "SSH already running on port $SSH_PORT"
fi

# Start Nginx
if pgrep nginx >/dev/null 2>&1; then
    info "Nginx already running"
else
    nginx 2>/dev/null && info "Nginx started" || warn "Nginx start failed (check config)"
fi

# Start TGQ server
cd "$APP_DIR"
if pgrep -f "uvicorn api.main" >/dev/null 2>&1; then
    info "TGQ server already running"
else
    if [ -f run_server.sh ]; then
        nohup bash run_server.sh > /dev/null 2>&1 &
        info "TGQ server started (run_server.sh)"
    else
        nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8443 > "$APP_DIR/logs/server.log" 2>&1 &
        info "TGQ server started (direct uvicorn)"
    fi
fi

# ============================================================
# SUMMARY
# ============================================================
section "DEPLOY COMPLETE"

echo ""
echo -e "${GREEN}"
echo "  ┌─────────────────────────────────────────────────────┐"
echo "  │  TGQ — Termux VPS Siap!                            │"
echo "  ├─────────────────────────────────────────────────────┤"
echo "  │  TGQ API    : http://localhost:8443                 │"
echo "  │              : http://localhost/ (via nginx)        │"
echo "  │  UI Web     : http://localhost/static/              │"
echo "  │  SSH        : ssh -p $SSH_PORT root@<IP_HP>        │"
echo "  │  Nginx      : $PREFIX/etc/nginx/conf.d/tgq.conf  │"
echo "  │  Boot       : $BOOT_DIR/tgq.sh                    │"
echo "  │  Logs       : $APP_DIR/logs/                       │"
echo "  ├─────────────────────────────────────────────────────┤"
echo "  │  PENTING:                                          │"
echo "  │  1. Tambahkan SSH public key di ~/.ssh/authorized_keys │"
echo "  │  2. Untuk akses publik: cloudflared tunnel          │"
echo "  │  3. Cek IP HP: ifconfig atau ip addr                │"
echo "  │  4. Pastikan mini fan menyala                      │"
echo "  └─────────────────────────────────────────────────────┘"
echo -e "${NC}"

echo ""
title "PORT CHECK"
for port in 80 8443 8022; do
    if grep -q ":$port " /proc/net/tcp 2>/dev/null || grep -q ":$port " /proc/net/tcp6 2>/dev/null; then
        info "Port $port OPEN"
    else
        warn "Port $port CLOSED"
    fi
done

echo ""
echo -e "${YELLOW} Jangan lupa tambahkan SSH public key!${NC}"
echo "    echo 'ssh-ed25519 AAAA...' >> ~/.ssh/authorized_keys"
echo ""

# ============================================================
# EOF
