#!/usr/bin/env bash
# Build DEB package for Kyro Downloader
set -euo pipefail

APP_NAME="kyro-downloader"
VERSION="1.0.0"
ARCH="amd64"
DEB_FILE="${APP_NAME}_${VERSION}_${ARCH}.deb"

echo "=== Building DEB package: ${DEB_FILE} ==="

# Clean previous builds
rm -f "${DEB_FILE}"

# Build the package
dpkg-deb --build installer/debian/kyro "${DEB_FILE}"

echo "=== DEB package created: ${DEB_FILE} ==="
echo "Install with: sudo dpkg -i ${DEB_FILE}"
echo "Done!"
