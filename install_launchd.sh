#!/bin/bash
set -e

USERNAME=$(whoami)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing mc-gws launchd plists for user: $USERNAME"

for plist in com.mcgws.briefing.plist com.mcgws.midday.plist com.mcgws.wrap.plist com.mcgws.weekly.plist; do
    src="$SCRIPT_DIR/$plist"
    dest="$HOME/Library/LaunchAgents/$plist"

    if [ ! -f "$src" ]; then
        echo "Skipping $plist (not found)"
        continue
    fi

    # Replace placeholder with actual username
    sed "s/YOUR_USERNAME/$USERNAME/g" "$src" > "$dest"
    echo "Installed: $dest"

    # Unload if already loaded, then load
    launchctl unload "$dest" 2>/dev/null || true
    launchctl load "$dest"
    echo "Loaded: $plist"
done

echo "Done. Logs at ~/.config/mc-gws/logs/"
