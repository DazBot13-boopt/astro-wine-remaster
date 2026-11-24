#!/usr/bin/env bash
# Lanceur Linux/Wine — Horoscope affiché dans le viewer intégré (GTK), pas Firefox.
set -euo pipefail
export WINEPREFIX="${WINEPREFIX:-$HOME/.wine-astro}"
export DISPLAY="${DISPLAY:-:0}"
export ASTRO_OPEN_BROWSER=0
APP="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope"
TOOLS="$(cd "$(dirname "$0")/../tools" && pwd)"

ln -sfn "$APP/Astrofic32" "$APP/astrofic32"
python3 "$TOOLS/patch_horoscope_paths.py" >/dev/null 2>&1 || true

pkill -f 'watch_horoscope_htm.sh' 2>/dev/null || true
pkill -f 'watch_temp_htm.sh' 2>/dev/null || true
pkill -f 'horoscope_inapp_viewer.py' 2>/dev/null || true

if pgrep -af 'AstroHoroscope|Horoscope_[0-9]' >/dev/null 2>&1; then
  echo "Nettoyage session Wine précédente…"
  wineserver -k 2>/dev/null || true
  sleep 1
fi

nohup bash "$TOOLS/watch_horoscope_htm.sh" >/tmp/watch-horoscope.log 2>&1 &
nohup bash "$TOOLS/watch_temp_htm.sh" >/tmp/watch-portrait.log 2>&1 &

echo "Horoscope: fenêtre intégrée OREAC (WebKit) — le TWebBrowser Wine reste noir/1x1."
cd "$APP"
exec wine "./Astrologie & Horoscope.exe" "$@"
