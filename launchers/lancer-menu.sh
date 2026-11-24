#!/usr/bin/env bash
set -euo pipefail
export WINEPREFIX="${WINEPREFIX:-$HOME/.wine-astro}"
export DISPLAY="${DISPLAY:-:0}"
APP="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope"
TOOLS="$(cd "$(dirname "$0")/../tools" && pwd)"

ln -sfn "$APP/Astrofic32" "$APP/astrofic32"
python3 "$TOOLS/patch_horoscope_paths.py" >/dev/null 2>&1 || true

# Watchers: portrait + horoscope HTML
pkill -f 'watch_horoscope_htm.sh' 2>/dev/null || true
pkill -f 'watch_temp_htm.sh' 2>/dev/null || true
nohup bash "$TOOLS/watch_horoscope_htm.sh" >/tmp/watch-horoscope.log 2>&1 &
nohup bash "$TOOLS/watch_temp_htm.sh" >/tmp/watch-portrait.log 2>&1 &

cd "$APP"
exec wine "./Astrologie & Horoscope.exe" "$@"
