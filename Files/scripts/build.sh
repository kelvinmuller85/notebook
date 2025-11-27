#!/bin/bash
set -euo pipefail

# build.sh - Creates rootfs and wheelhouse for Note Book installer
# Uses proot to build without requiring root privileges

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARCH=$(uname -m)
DEBIAN_RELEASE="bookworm"
ROOTFS_DIR="$SCRIPT_DIR/usb-installer/root"
WHEELHOUSE_DIR="$SCRIPT_DIR/usb-installer/wheelhouse"
ROOTFS_NAME="rootfs-debian-book-${ARCH}.tar.xz"

echo "=== Building Note Book installer package ==="

# Download and extract minimal rootfs
echo "Downloading minimal Debian rootfs..."
mkdir -p "$ROOTFS_DIR"

# Use wget to download a minimal Debian rootfs from Docker
ROOTFS_URL="https://github.com/debuerreotype/docker-debian-artifacts/raw/dist-${DEBIAN_RELEASE}/${ARCH}/rootfs.tar.xz"
wget -O - "$ROOTFS_URL" | tar -xJ -C "$ROOTFS_DIR"

# Set up package management in rootfs
mkdir -p "$ROOTFS_DIR/etc/apt/apt.conf.d"
cat > "$ROOTFS_DIR/etc/apt/sources.list" << EOF
deb http://deb.debian.org/debian ${DEBIAN_RELEASE} main
deb http://deb.debian.org/debian ${DEBIAN_RELEASE}-updates main
deb http://security.debian.org/debian-security ${DEBIAN_RELEASE}-security main
EOF

# Configure proot to handle package installation
"$SCRIPT_DIR/usb-installer/proot" -r "$ROOTFS_DIR" -b /dev -b /proc -b /sys /bin/bash -c "
set -ex
# Update package lists
apt-get update

# Install required packages
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 gir1.2-gtksource-3.0 aspell locales fonts-dejavu x11-utils

# Configure locale
echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen
locale-gen
"

# Create wheelhouse for offline installation
echo "Creating wheelhouse..."
mkdir -p "$WHEELHOUSE_DIR"

# Create Python virtual environment inside rootfs
"$SCRIPT_DIR/usb-installer/proot" -r "$ROOTFS_DIR" /bin/bash -c "
set -ex
python3 -m venv /build-venv
source /build-venv/bin/activate

# Generate wheels for offline installation
pip wheel -w /wheelhouse \
    setuptools wheel pip pygobject pyxdg pytest
"

# Copy wheels from rootfs to USB installer
cp -r "$ROOTFS_DIR/wheelhouse/"* "$WHEELHOUSE_DIR/"

# Generate requirements ordering file for deterministic installation
"$SCRIPT_DIR/usb-installer/proot" -r "$ROOTFS_DIR" /bin/bash -c "
cd /wheelhouse
ls *.whl > /requirements-order.txt"
cp "$ROOTFS_DIR/requirements-order.txt" "$SCRIPT_DIR/usb-installer/"

# Create final rootfs tarball
echo "Creating rootfs tarball..."
cd "$ROOTFS_DIR"
tar cJf "$SCRIPT_DIR/usb-installer/$ROOTFS_NAME" .
cd "$SCRIPT_DIR"

# Generate checksums
echo "Generating checksums..."
cd usb-installer
sha256sum "$ROOTFS_NAME" > SHA256SUMS
cd "$WHEELHOUSE_DIR"
sha256sum *.whl > ../WHEEL_SHA256SUMS
cd ..

# Copy application files to USB installer root
echo "Copying application files..."
mkdir -p "$SCRIPT_DIR/usb-installer/root/opt/notebook"
cp -r "$SCRIPT_DIR/Files" "$SCRIPT_DIR/tests" "$SCRIPT_DIR/requirements.txt" \
    "$SCRIPT_DIR/usb-installer/root/opt/notebook/"

# Clean up temporary files in rootfs
rm -rf "$ROOTFS_DIR/wheelhouse" "$ROOTFS_DIR/build-venv" "$ROOTFS_DIR/tmp"/*

echo "=== Build complete ==="
echo "Created: usb-installer/$ROOTFS_NAME"
echo "Created: $WHEELHOUSE_DIR with Python wheels"
echo "Checksums generated in usb-installer/SHA256SUMS"
echo
echo "You can now distribute the 'usb-installer' directory or create a self-extracting package."