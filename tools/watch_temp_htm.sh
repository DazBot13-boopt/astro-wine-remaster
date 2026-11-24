#!/usr/bin/env bash
# Réécrit temp.htm dès que l'appli le régénère + curseur de défilement overlay.
set -euo pipefail
export DISPLAY="${DISPLAY:-:0}"
RES="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Astrologie/res"
TOOLS="$(cd "$(dirname "$0")" && pwd)"
FIX="$TOOLS/fix_temp_htm.py"
OVERLAY="$TOOLS/portrait_scroll_overlay.py"
mkdir -p "$RES"

python3 "$FIX" "$RES/temp.htm" 2>/dev/null || true

overlay_pid=0
ensure_overlay() {
  if [[ "$overlay_pid" -gt 0 ]] && kill -0 "$overlay_pid" 2>/dev/null; then
    return 0
  fi
  if pgrep -f 'Astrologie\\\\Astrologie\.exe|Astrologie/Astrologie\.exe|Astrologie\.exe' >/dev/null 2>&1 \
     || pgrep -af 'astrologie\.exe' 2>/dev/null | grep -qi 'Astrologie\\\\Astrologie\|AstroHoroscope.*Astrologie'; then
    pkill -f 'portrait_scroll_overlay.py' 2>/dev/null || true
    sleep 0.15
    python3 "$OVERLAY" >/tmp/portrait-scroll.log 2>&1 &
    overlay_pid=$!
    echo "[watch-portrait] scroll overlay pid=$overlay_pid"
  fi
}

apply_fix() {
  python3 "$FIX" "$RES/temp.htm" 2>/dev/null || true
}

if command -v inotifywait >/dev/null; then
  echo "[watch] inotify + overlay sur $RES/temp.htm"
  ensure_overlay
  while true; do
    inotifywait -e close_write,moved_to,create "$RES" --include 'temp\.htm$' 2>/dev/null || sleep 1
    sleep 0.35
    apply_fix
    ensure_overlay
    # si plus d'Astrologie, coupe overlay
    if ! pgrep -af '[Aa]strologie\.exe' >/dev/null 2>&1; then
      if [[ "$overlay_pid" -gt 0 ]]; then
        kill "$overlay_pid" 2>/dev/null || true
        overlay_pid=0
      fi
    fi
  done
else
  echo "[watch] polling + overlay"
  last=0
  while true; do
    if [[ -f "$RES/temp.htm" ]]; then
      now=$(stat -c %Y "$RES/temp.htm")
      if [[ "$now" != "$last" ]]; then
        last=$now
        sleep 0.25
        apply_fix
      fi
    fi
    if pgrep -af '[Aa]strologie\.exe' >/dev/null 2>&1; then
      ensure_overlay
    else
      if [[ "$overlay_pid" -gt 0 ]]; then
        kill "$overlay_pid" 2>/dev/null || true
        overlay_pid=0
      fi
    fi
    sleep 1
  done
fi
