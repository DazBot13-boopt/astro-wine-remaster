#!/usr/bin/env bash
set -euo pipefail
export WINEPREFIX="${WINEPREFIX:-$HOME/.wine-astro}"
export DISPLAY="${DISPLAY:-:0}"
APP="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope"
TOOLS="$(cd "$(dirname "$0")/../tools" && pwd)"

ln -sfn "$APP/Astrofic32" "$APP/astrofic32"
python3 "$TOOLS/patch_horoscope_paths.py" >/dev/null 2>&1 || true

# Watchers: portrait + horoscope HTML (+ ouverture navigateur si Wine IE noir)
pkill -f 'watch_horoscope_htm.sh' 2>/dev/null || true
pkill -f 'watch_temp_htm.sh' 2>/dev/null || true
# Un seul Horoscope à la fois (2 instances → OOM adresse 32-bit / cadre noir)
pkill -f 'Horoscope_.*\.exe' 2>/dev/null || true
rm -f /tmp/astro-horoscope-opened.stamp
nohup bash "$TOOLS/watch_horoscope_htm.sh" >/tmp/watch-horoscope.log 2>&1 &
nohup bash "$TOOLS/watch_temp_htm.sh" >/tmp/watch-portrait.log 2>&1 &

echo "Astuce: si la fenêtre Horoscope est noire, le texte s'ouvre dans le navigateur."
echo "Manuel: $(dirname "$0")/voir-horoscope.sh"

cd "$APP"
exec wine "./Astrologie & Horoscope.exe" "$@"
