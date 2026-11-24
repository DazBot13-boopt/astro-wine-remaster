#!/usr/bin/env bash
# Dès que Wine écrit un temp.rtf / temp.htm vide, on régénère le HTML.
set -euo pipefail
ROOT="${1:-$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope}"
FIX="$(dirname "$0")/rtf_to_htm.py"
echo "[watch-horoscope] $ROOT"
python3 "$FIX" || true
while true; do
  # polling: robuste sans inotify
  python3 "$FIX" >/tmp/horo-rtf-fix.log 2>&1 || true
  sleep 1
done
