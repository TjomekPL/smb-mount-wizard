#!/bin/bash
set -e

INSTALL_DIR="/opt/smb-mount-wizard"

echo "Removing $INSTALL_DIR (needs sudo)..."
sudo rm -rf "$INSTALL_DIR"

echo "Removing the application menu entry..."
rm -f ~/.local/share/applications/smb-mount-wizard.desktop
update-desktop-database ~/.local/share/applications 2>/dev/null || true

echo
echo "Done. Your settings (~/.config/smb-mount-wizard) and any currently"
echo "mounted shares were left untouched - remove those yourself if you"
echo "no longer want them."
