#!/usr/bin/env bash
# Réécrit temp.htm dès que l'appli le régénère (après Calcul).
set -euo pipefail
RES="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Astrologie/res"
FIX="$(cd "$(dirname "$0")" && pwd)/fix_temp_htm.py"
mkdir -p "$RES"
# initial
python3 "$FIX" "$RES/temp.htm" 2>/dev/null || true
if command -v inotifywait >/dev/null; then
  echo "[watch] inotify sur $RES/temp.htm"
  while inotifywait -e close_write,moved_to,create "$RES" --include 'temp\.htm$' 2>/dev/null; do
    sleep 0.3
    python3 "$FIX" "$RES/temp.htm" || true
  done
else
  echo "[watch] polling (pas d'inotifywait)"
  last=0
  while true; do
    if [ -f "$RES/temp.htm" ]; then
      now=$(stat -c %Y "$RES/temp.htm")
      if [ "$now" != "$last" ]; then
        last=$now
        sleep 0.2
        python3 "$FIX" "$RES/temp.htm" || true
      fi
    fi
    sleep 1
  done
fi
