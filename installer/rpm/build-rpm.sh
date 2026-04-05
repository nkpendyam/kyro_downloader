#!/usr/bin/env bash
# Build RPM package for Kyro Downloader
set -euo pipefail

APP_NAME="kyro-downloader"
VERSION="1.0.0"

echo "=== Building RPM package: ${APP_NAME}-${VERSION} ==="

# Create RPM build directory structure
RPMBUILD_DIR="${HOME}/rpmbuild"
mkdir -p "${RPMBUILD_DIR}"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create source tarball
TARBALL="${RPMBUILD_DIR}/SOURCES/${APP_NAME}-${VERSION}.tar.gz"
tar -czf "${TARBALL}" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='venv' \
    --exclude='dist' \
    --exclude='build' \
    .

# Copy spec file
cp installer/rpm/kyro-downloader.spec "${RPMBUILD_DIR}/SPECS/"

# Build the RPM
rpmbuild -ba "${RPMBUILD_DIR}/SPECS/kyro-downloader.spec"

echo "=== RPM package created ==="
echo "Find it in: ${RPMBUILD_DIR}/RPMS/x86_64/"
echo "Install with: sudo rpm -i ${RPMBUILD_DIR}/RPMS/x86_64/${APP_NAME}-${VERSION}-1.*.rpm"
echo "Done!"
