#!/bin/bash
# rotate-update-key.sh - Rotates the Chronos update API key
# Called by systemd timer every 72 hours

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEY_FILE="$SCRIPT_DIR/update.key"
LOG_FILE="/var/log/chronos-key-rotation.log"

# Generate new key
python3 -c "import secrets; print(secrets.token_hex(32))" > "$KEY_FILE"
chmod 600 "$KEY_FILE"

# Log rotation
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Key rotated successfully" >> "$LOG_FILE"
