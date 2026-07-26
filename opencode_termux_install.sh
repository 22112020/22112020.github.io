#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  OpenCode — Termux Native Installer (root-friendly)
#  Referensi: https://github.com/guysoft/opencode-termux
#  Binary: cross-compiled Bun + WebKit/JSC untuk Android aarch64
# ============================================================
# Cara pakai:
#   su -c bash opencode_termux_install.sh
# ============================================================

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$APP_DIR/logs/opencode_install.log"
mkdir -p "$APP_DIR/logs"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1"; }
title() { echo -e "${CYAN}━━━ $1 ━━━${NC}"; }
section() { echo; echo -e "${CYAN}════════════════════════════════════════════════${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}════════════════════════════════════════════════${NC}"; }

echo -e "${CYAN}"
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║     OpenCode — Termux Native Installer          ║"
echo "  ║     https://github.com/guysoft/opencode-termux   ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

exec 2>>"$LOG"

# ============================================================
# 1. ENVIRONMENT CHECK
# ============================================================
section "1/5: ENVIRONMENT CHECK"

if [ ! -d /data/data/com.termux ]; then
    err "Bukan lingkungan Termux!"
    exit 1
fi
info "Termux environment detected"

ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ] && [ "$ARCH" != "arm64" ]; then
    err "Architecture $ARCH tidak didukung — butuh aarch64/arm64"
    exit 1
fi
info "Architecture: $ARCH"

PREFIX="/data/data/com.termux/files/usr"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Cek apakah sudah terinstall
if [ -f "$PREFIX/bin/opencode" ]; then
    INSTALLED_VER=$("$PREFIX/bin/opencode" --version 2>/dev/null || echo "unknown")
    warn "OpenCode sudah terinstall: $INSTALLED_VER"
    echo ""
    echo "  Pilihan:"
    echo "    1) Skip — biarkan yang sudah ada"
    echo "    2) Reinstall — download & install ulang"
    echo "    3) Hentikan"
    echo ""
    read -rp "  Pilih [1/2/3]: " choice </dev/tty || choice="1"
    case "$choice" in
        2) warn "Reinstall...";;
        3) info "Dibatalkan"; exit 0;;
        *) info "Skip instalasi"; exit 0;;
    esac
fi

# ============================================================
# 2. DOWNLOAD RELEASE
# ============================================================
section "2/5: DOWNLOAD RELEASE"

REPO="guysoft/opencode-termux"
LATEST=$(curl -sL -H "User-Agent: opencode-termux" \
    "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null || echo "")

TAG=$(echo "$LATEST" | python3 -c "import sys,json;print(json.load(sys.stdin).get('tag_name',''))" 2>/dev/null || echo "v0.2.1")

info "Release: $TAG"

DEB_NAME="opencode_${TAG#v}_aarch64.deb"
# Coba cari nama deb dari API response
DEB_URL=$(echo "$LATEST" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for a in d.get('assets', []):
    if a['name'].endswith('.deb'):
        print(a['browser_download_url'])
        break
" 2>/dev/null || echo "")

if [ -z "$DEB_URL" ]; then
    DEB_URL="https://github.com/$REPO/releases/download/$TAG/$DEB_NAME"
fi

ZIP_URL=$(echo "$LATEST" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for a in d.get('assets', []):
    if a['name'].endswith('.zip'):
        print(a['browser_download_url'])
        break
" 2>/dev/null || echo "")

if [ -z "$ZIP_URL" ]; then
    ZIP_URL="https://github.com/$REPO/releases/download/$TAG/opencode-${TAG#v}-android-aarch64.zip"
fi

info "Downloading OpenCode for Termux..."
echo "  URL deb: $DEB_URL"

# Coba download deb dulu
DEB_PATH="$TMP_DIR/opencode.deb"
if curl -sL -o "$DEB_PATH" "$DEB_URL" 2>/dev/null; then
    INSTALL_METHOD="deb"
    info "Download OK (deb)"
else
    warn "Deb tidak tersedia, coba zip..."
    ZIP_PATH="$TMP_DIR/opencode.zip"
    if curl -sL -o "$ZIP_PATH" "$ZIP_URL" 2>/dev/null; then
        INSTALL_METHOD="zip"
        info "Download OK (zip)"
    else
        err "Gagal download dari $REPO"
        warn "Beralih ke metode cadangan (npm)..."
        INSTALL_METHOD="npm"
    fi
fi

# ============================================================
# 3. INSTALL
# ============================================================
section "3/5: INSTALL"

case "$INSTALL_METHOD" in
    deb)
        info "Installing via dpkg..."
        DEPS_NEEDED=()

        if ! dpkg -s ripgrep &>/dev/null 2>&1; then
            DEPS_NEEDED+=("ripgrep")
        fi

        if [ ${#DEPS_NEEDED[@]} -gt 0 ]; then
            warn "Installing dependencies: ${DEPS_NEEDED[*]}..."
            if apt install -y "${DEPS_NEEDED[@]}" -qq 2>/dev/null; then
                info "Dependencies installed"
            else
                warn "Gunakan dpkg langsung tanpa dependensi..."
            fi
        fi

        # Coba install dengan force-architecture (atasi aarch64 vs arm64)
        if ! dpkg -i "$DEB_PATH" 2>/dev/null; then
            warn "dpkg gagal — coba dengan --force-architecture..."
            dpkg --force-architecture -i "$DEB_PATH" 2>/dev/null || true
        fi

        if [ -f "$PREFIX/bin/opencode" ]; then
            info "OpenCode installed via deb"
        else
            warn "dpkg gagal — coba method zip..."
            INSTALL_METHOD="zip"
        fi
        ;;

    zip)
        info "Installing via zip..."
        mkdir -p "$PREFIX/libexec/opencode" "$PREFIX/lib"

        cd "$TMP_DIR"
        if ! unzip -q "$ZIP_PATH" 2>/dev/null; then
            err "Zip corrupt atau gagal extract"
            INSTALL_METHOD="npm"
        else
            # Cari file hasil extract — bisa flat atau dalam subfolder
            EXTRACT_DIR="$TMP_DIR"
            for f in "$TMP_DIR"/*/; do
                if [ -f "${f}opencode" ] || [ -f "${f}opencode.bin" ]; then
                    EXTRACT_DIR="$f"
                    break
                fi
            done
            cd "$EXTRACT_DIR"

            if [ -f opencode ]; then
                mv opencode "$PREFIX/bin/opencode"
                chmod +x "$PREFIX/bin/opencode"
                info "opencode wrapper installed"
            fi

            if [ -f opencode.bin ]; then
                mv opencode.bin "$PREFIX/libexec/opencode/opencode.bin"
                chmod +x "$PREFIX/libexec/opencode/opencode.bin"
                info "opencode.bin installed"
            fi

            for lib in libtagfix.so libc++_shared.so libopentui.so; do
                [ -f "$lib" ] && mv "$lib" "$PREFIX/lib/" 2>/dev/null && info "$lib installed" || true
            done

            if ! dpkg -s ripgrep &>/dev/null 2>&1; then
                warn "Installing ripgrep dependency..."
                apt install -y ripgrep -qq 2>/dev/null || true
            fi

            if [ -f "$PREFIX/bin/opencode" ]; then
                info "OpenCode installed via zip"
            else
                err "Instalasi zip gagal — file opencode tidak ditemukan"
                INSTALL_METHOD="npm"
            fi
        fi
        ;;

    npm)
        warn "Menggunakan metode cadangan: npm install -g opencode"
        if ! which node &>/dev/null; then
            warn "Node.js tidak ditemukan, install dulu..."
            apt install -y nodejs -qq 2>/dev/null || true
        fi
        if which npm &>/dev/null; then
            npm install -g opencode@latest 2>&1
            info "OpenCode installed via npm"
        else
            err "npm tidak tersedia — instalasi gagal total"
            exit 1
        fi
        ;;
esac

# ============================================================
# 4. VERIFY
# ============================================================
section "4/5: VERIFY"

if which opencode &>/dev/null; then
    OPENCODE_VER=$(opencode --version 2>/dev/null || echo "unknown")
    info "OpenCode: $OPENCODE_VER"
    info "Path: $(which opencode)"
else
    err "OpenCode tidak ditemukan di PATH"
    warn "Coba: export PATH=\$PREFIX/bin:\$PATH"
    exit 1
fi

# Cek apakah binary native atau npm
if [ -f "$PREFIX/bin/opencode" ] && file "$PREFIX/bin/opencode" | grep -qi "ELF"; then
    info "Type: Native binary (Bun + WebKit)"
elif which opencode &>/dev/null && file "$(which opencode)" | grep -qi "script"; then
    info "Type: npm/Node.js script"
else
    info "Type: unknown"
fi

# ============================================================
# 5. CONFIGURE API PROVIDER
# ============================================================
section "5/5: API PROVIDER"

echo ""
echo "  OpenCode butuh AI provider untuk bekerja."
echo ""
echo "  Provider tersedia:"
echo "    1) Anthropic Claude  (recommended)"
echo "    2) OpenAI / GPT"
echo "    3) GitHub Copilot"
echo "    4) Lewati — setup manual nanti"
echo ""
read -rp "  Pilih provider [1-4]: " prov_choice </dev/tty || prov_choice="4"

case "$prov_choice" in
    1)
        PROVIDER="anthropic"
        ENV_KEY="ANTHROPIC_API_KEY"
        echo ""
        echo "  Dapatkan API key: https://console.anthropic.com/"
        ;;
    2)
        PROVIDER="openai"
        ENV_KEY="OPENAI_API_KEY"
        echo ""
        echo "  Dapatkan API key: https://platform.openai.com/api-keys"
        ;;
    3)
        PROVIDER="copilot"
        ENV_KEY="GITHUB_TOKEN"
        echo ""
        echo "  GitHub token harus punya akses ke GitHub Copilot"
        ;;
    4|*)
        PROVIDER=""
        ENV_KEY=""
        warn "Setup manual nanti. Lihat: https://opencode.ai/docs"
        ;;
esac

if [ -n "$PROVIDER" ] && [ -n "$ENV_KEY" ]; then
    echo ""
    read -rp "  Masukkan $ENV_KEY: " api_key </dev/tty || api_key=""
    if [ -n "$api_key" ]; then
        # Simpan ke profile Termux
        PROFILE="$HOME/.bashrc"
        if ! grep -q "$ENV_KEY" "$PROFILE" 2>/dev/null; then
            echo "export $ENV_KEY=\"$api_key\"" >> "$PROFILE"
        fi
        export "$ENV_KEY=$api_key"
        info "$ENV_KEY tersimpan di $PROFILE"
    else
        warn "Key kosong — setup nanti via export $ENV_KEY=..."
    fi
fi

# ============================================================
# SUMMARY
# ============================================================
section "INSTALL COMPLETE"

echo ""
echo -e "${GREEN}"
echo "  ┌─────────────────────────────────────────────────────┐"
echo "  │  OpenCode — Termux Siap Digunakan!                 │"
echo "  ├─────────────────────────────────────────────────────┤"
echo "  │  Version  : $(opencode --version 2>/dev/null || echo 'OK')"
echo "  │  Path     : $(which opencode)"
echo "  │  Method   : $INSTALL_METHOD"
echo "  ├─────────────────────────────────────────────────────┤"
echo "  │  Jalankan:  opencode                                │"
echo "  │  Docs    :  https://opencode.ai                     │"
echo "  └─────────────────────────────────────────────────────┘"
echo -e "${NC}"

echo ""
echo "  Tips:"
echo "    opencode                          # Start interactive session"
echo "    opencode --help                   # Lihat semua opsi"
echo "    opencode --version                # Cek versi"
echo ""
echo "  Log install: $LOG"
echo ""

# ============================================================
# EOF
