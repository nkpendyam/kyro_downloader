#!/usr/bin/env bash
# Build macOS DMG installer for Kyro Downloader
set -euo pipefail

APP_NAME="Kyro Downloader"
APP_VERSION="1.0.0"
DIST_DIR="dist/macos"
APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"
DMG_FILE="${DIST_DIR}/KyroDownloader-${APP_VERSION}.dmg"

echo "=== Building macOS DMG for ${APP_NAME} v${APP_VERSION} ==="

# Create dist directory
mkdir -p "${DIST_DIR}"

# Build with PyInstaller
echo "Building app bundle with PyInstaller..."
pyinstaller --name "Kyro Downloader" \
    --windowed \
    --onefile \
    --icon=resources/icon.icns \
    --add-data "src:src" \
    --add-data "requirements.txt:." \
    --hidden-import textual \
    --hidden-import fastapi \
    --hidden-import uvicorn \
    src/gui/gui_main.py

# Move the .app to dist
if [ -d "build/Kyro Downloader" ]; then
    cp -R "build/Kyro Downloader/${APP_NAME}.app" "${APP_BUNDLE}"
elif [ -d "dist/Kyro Downloader.app" ]; then
    cp -R "dist/Kyro Downloader.app" "${APP_BUNDLE}"
fi

if [ ! -d "${APP_BUNDLE}" ]; then
    echo "ERROR: App bundle not found at ${APP_BUNDLE}"
    exit 1
fi

# Create DMG
echo "Creating DMG file..."
if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "${APP_NAME}" \
        --volicon "resources/icon.icns" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "${APP_NAME}.app" 200 190 \
        --hide-extension "${APP_NAME}.app" \
        --app-drop-link 600 185 \
        "${DMG_FILE}" \
        "${APP_BUNDLE}"
else
    echo "create-dmg not found, using hdiutil fallback..."
    TEMP_DIR=$(mktemp -d)
    cp -R "${APP_BUNDLE}" "${TEMP_DIR}/${APP_NAME}.app"
    ln -s /Applications "${TEMP_DIR}/Applications"
    hdiutil create -volname "${APP_NAME}" -srcfolder "${TEMP_DIR}" -ov -format UDZO "${DMG_FILE}"
    rm -rf "${TEMP_DIR}"
fi

echo "=== DMG created: ${DMG_FILE} ==="
echo "Done!"
