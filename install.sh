#!/bin/bash
# Kyro Downloader - Universal Install Script for Mac/Linux
# Usage: curl -sSL https://raw.githubusercontent.com/nkpendyam/kyro_downloader/main/install.sh | bash
set -e

GREEN="[0;32m"; YELLOW="[1;33m"; BLUE="[0;34m"; NC="[0m"

echo -e "${BLUE}  __  __ _     _     _ _             "
echo -e " |  \/  (_)___(_)___| (_) __ _ _ __  "
echo -e " | |/\| | / __| / __| | |/ _` | '_ \ "
echo -e " | |  | | \__ \ \__ \ | | (_| | | | |"
echo -e " |_|  |_|_|___/_|___/_|_|\__,_|_| |_|"
echo -e "                                     "
echo -e "  Production-grade media downloader v1.0.0${NC}"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then OS="linux"; echo -e "${GREEN}Detected: Linux${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then OS="macos"; echo -e "${GREEN}Detected: macOS${NC}"
else echo "Unsupported OS"; exit 1; fi

# Detect package manager
if command -v apt-get &> /dev/null; then PKG_INSTALL="sudo apt-get install -y"; PKG_UPDATE="sudo apt-get update"
elif command -v dnf &> /dev/null; then PKG_INSTALL="sudo dnf install -y"; PKG_UPDATE="sudo dnf update -y"
elif command -v pacman &> /dev/null; then PKG_INSTALL="sudo pacman -S --noconfirm"; PKG_UPDATE="sudo pacman -Sy"
elif command -v brew &> /dev/null; then PKG_INSTALL="brew install"; PKG_UPDATE="brew update"
else echo "No supported package manager found"; exit 1; fi

# Install deps
if ! command -v python3 &> /dev/null; then echo -e "${YELLOW}Installing Python3...${NC}"; $PKG_INSTALL python3 python3-pip python3-venv; fi
if ! command -v ffmpeg &> /dev/null; then echo -e "${YELLOW}Installing FFmpeg...${NC}"; $PKG_INSTALL ffmpeg; fi
if ! command -v aria2c &> /dev/null; then echo -e "${YELLOW}Installing aria2c...${NC}"; $PKG_INSTALL aria2; fi

# Setup
INSTALL_DIR="${KYRO_INSTALL_DIR:-$HOME/.kyro}"
mkdir -p "$INSTALL_DIR"
python3 -m venv "$INSTALL_DIR/venv" 2>/dev/null || true
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip -q

# Clone or update
if [ -d "$INSTALL_DIR/kyro_downloader" ]; then
    cd "$INSTALL_DIR/kyro_downloader" && git pull -q
else
    git clone -q https://github.com/nkpendyam/kyro_downloader.git "$INSTALL_DIR/kyro_downloader"
    cd "$INSTALL_DIR/kyro_downloader"
fi

pip install -r requirements.txt -q
pip install -r requirements-web.txt -q
if [ "$KYRO_INSTALL_GUI" != "no" ]; then pip install flet -q; fi

# Create commands
BIN_DIR="${KYRO_BIN_DIR:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"
for cmd in kyro kyro-tui kyro-web kyro-gui; do
    echo "#!/bin/bash" > "$BIN_DIR/$cmd"
    echo "source \"${KYRO_INSTALL_DIR:-$HOME/.kyro}/venv/bin/activate\"" >> "$BIN_DIR/$cmd"
    echo "cd \"${KYRO_INSTALL_DIR:-$HOME/.kyro}/kyro_downloader\"" >> "$BIN_DIR/$cmd"
    if [ "$cmd" = "kyro" ]; then echo "python -m src.cli \"\$@\"" >> "$BIN_DIR/$cmd"
    elif [ "$cmd" = "kyro-tui" ]; then echo "python -m src.ui.tui \"\$@\"" >> "$BIN_DIR/$cmd"
    elif [ "$cmd" = "kyro-web" ]; then echo "python -m src.ui.web.server \"\$@\"" >> "$BIN_DIR/$cmd"
    else echo "python -m src.gui.gui_main \"\$@\"" >> "$BIN_DIR/$cmd"; fi
    chmod +x "$BIN_DIR/$cmd"
done

# Linux desktop entry
if [ "$OS" = "linux" ]; then
    mkdir -p "$HOME/.local/share/applications"
    cat > "$HOME/.local/share/applications/kyro-downloader.desktop" << DESKTOP
[Desktop Entry]
Name=Kyro Downloader
Comment=Production-grade media downloader by nkpendyam
Exec=$BIN_DIR/kyro-gui
Icon=video-display
Terminal=false
Type=Application
Categories=AudioVideo;Video;Audio;Network;
DESKTOP
fi

# macOS app
if [ "$OS" = "macos" ]; then
    APP_DIR="/Applications/Kyro Downloader.app/Contents/MacOS"
    mkdir -p "$APP_DIR"
    cat > "$APP_DIR/kyro-gui" << MACOS
#!/bin/bash
source "${KYRO_INSTALL_DIR:-$HOME/.kyro}/venv/bin/activate"
cd "${KYRO_INSTALL_DIR:-$HOME/.kyro}/kyro_downloader"
python -m src.gui.gui_main
MACOS
    chmod +x "$APP_DIR/kyro-gui"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Kyro Downloader v1.0.0 installed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Commands:"
echo -e "  ${BLUE}kyro${NC}          - CLI"
echo -e "  ${BLUE}kyro-tui${NC}      - Terminal UI"
echo -e "  ${BLUE}kyro-web${NC}      - Web UI"
echo -e "  ${BLUE}kyro-gui${NC}      - Desktop GUI"
echo ""
echo -e "Config: ${BLUE}~/.config/kyro/config.yaml${NC}"
echo -e "Update: ${BLUE}kyro --update${NC}"
echo ""
