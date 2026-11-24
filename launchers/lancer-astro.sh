#!/usr/bin/env bash
set -euo pipefail
export WINEPREFIX="${WINEPREFIX:-$HOME/.wine-astro}"
export DISPLAY="${DISPLAY:-:0}"
APP_ROOT="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope"
TOOLS="$HOME/Documents/Astrologie/windows-apps/tools"

ln -sfn "$APP_ROOT/Astrofic32" "$APP_ROOT/astrofic32"
ln -sfn ../astrofic32 "$APP_ROOT/Astrologie/astrofic32"
ln -sfn ../Astrofic32 "$APP_ROOT/Astrologie/Astrofic32"

# Watcher HTML (sommaire + scroll) en arrière-plan
pkill -f 'watch_temp_htm.sh' 2>/dev/null || true
nohup bash "$TOOLS/watch_temp_htm.sh" >/tmp/astro-watch-htm.log 2>&1 &
python3 "$TOOLS/fix_temp_htm.py" "$APP_ROOT/Astrologie/res/temp.htm" 2>/dev/null || true

cd "$APP_ROOT/Astrologie"
exec wine "./astrologie.exe" "$@"
