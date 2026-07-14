#!/bin/bash
set -e

INSTALL_DIR="/opt/smb-mount-wizard"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing required system packages (needs sudo)..."
sudo apt-get update -qq
sudo apt-get install -y python3-venv nmap smbclient cifs-utils libsecret-tools samba-common-bin

# policykit-1 was split into polkitd + pkexec on Debian 13 (trixie) and
# newer - try the old single-package name first, fall back to the new
# split names if that fails, so this works across Debian versions.
sudo apt-get install -y policykit-1 || sudo apt-get install -y polkitd pkexec

echo
echo "Installing SMB Mount Wizard to $INSTALL_DIR ..."
echo "(this needs sudo, since /opt is a system-wide directory)"
echo

sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "$SOURCE_DIR/main.py" \
           "$SOURCE_DIR/core" \
           "$SOURCE_DIR/gui" \
           "$SOURCE_DIR/kde" \
           "$SOURCE_DIR/resources" \
           "$SOURCE_DIR/requirements.txt" \
           "$INSTALL_DIR/"

echo
echo "Creating a self-contained virtual environment..."
sudo python3 -m venv "$INSTALL_DIR/venv"
sudo "$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

echo
echo "Installing the application menu entry (for your account only)..."
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/smb-mount-wizard.desktop << DESKTOPEOF
[Desktop Entry]
Name=SMB Mount Wizard
Comment=Discover and mount SMB network shares
Exec=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/main.py
Path=$INSTALL_DIR
Icon=$INSTALL_DIR/resources/icon.svg
Terminal=false
Type=Application
Categories=System;Utility;Network;
DESKTOPEOF

update-desktop-database ~/.local/share/applications 2>/dev/null || true

echo
echo "Done. Look for 'SMB Mount Wizard' in your application menu."
