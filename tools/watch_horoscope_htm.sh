#!/usr/bin/env bash
# 1) coo.dat  2) RTF→HTML  3) viewer OREAC au clic Horoscope seulement
# Fermeture Horoscope → revient au menu "Choisir Astrologie ou Horoscope"
set -euo pipefail
ROOT="${1:-$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope}"
TOOLS="$(cd "$(dirname "$0")" && pwd)"
FIX="$TOOLS/rtf_to_htm.py"
VIEWER="$TOOLS/horoscope_inapp_viewer.py"
export DISPLAY="${DISPLAY:-:0}"
echo "[watch-horoscope] viewer on click; close → menu → $ROOT"

find "$ROOT" -iname 'coo.dat' ! -name 'coo.dat' -print0 2>/dev/null \
  | while IFS= read -r -d '' f; do mv -f "$f" "$(dirname "$f")/coo.dat"; done

viewer_pid=0
last_horo_pids=""
had_horoscope=0

horoscope_pids() {
  pgrep -f 'Horoscope_[0-9]+\.exe' 2>/dev/null | sort -u | tr '\n' ' ' || true
}

focus_app_menu() {
  # Remet le menu principal au premier plan après fermeture Horoscope
  local id
  for name in 'Choisir Astrologie ou Horoscope' 'Astrologie & Horoscope' 'Coordonnées natales'; do
    id=$(xdotool search --name "$name" 2>/dev/null | tail -1 || true)
    if [[ -n "${id:-}" ]]; then
      xdotool windowmap "$id" 2>/dev/null || true
      xdotool windowactivate --sync "$id" 2>/dev/null || true
      xdotool windowraise "$id" 2>/dev/null || true
      echo "[watch-horoscope] focus menu: $name ($id)"
      return 0
    fi
  done
  # fallback: exe menu
  id=$(xdotool search --classname 'astrologie & horoscope.exe' 2>/dev/null | tail -1 || true)
  if [[ -n "${id:-}" ]]; then
    xdotool windowactivate --sync "$id" 2>/dev/null || true
    xdotool windowraise "$id" 2>/dev/null || true
  fi
}

while true; do
  find "$ROOT" -iname 'coo.dat' ! -name 'coo.dat' -print0 2>/dev/null \
    | while IFS= read -r -d '' f; do mv -f "$f" "$(dirname "$f")/coo.dat"; done
  python3 "$FIX" "$ROOT" >/tmp/horo-rtf-fix.log 2>&1 || true

  cur=$(horoscope_pids)
  if [[ -n "$cur" && "$cur" != "$last_horo_pids" ]]; then
    if [[ "$viewer_pid" -gt 0 ]] && kill -0 "$viewer_pid" 2>/dev/null; then
      kill "$viewer_pid" 2>/dev/null || true
    fi
    pkill -f 'horoscope_inapp_viewer.py' 2>/dev/null || true
    sleep 0.2
    python3 "$VIEWER" >/tmp/horoscope-viewer.log 2>&1 &
    viewer_pid=$!
    echo "[watch-horoscope] open viewer pid=$viewer_pid (horoscope=$cur)"
    last_horo_pids="$cur"
    had_horoscope=1
  elif [[ -z "$cur" ]]; then
    if [[ "$viewer_pid" -gt 0 ]] && kill -0 "$viewer_pid" 2>/dev/null; then
      kill "$viewer_pid" 2>/dev/null || true
    fi
    viewer_pid=0
    last_horo_pids=""
    if [[ "$had_horoscope" -eq 1 ]]; then
      had_horoscope=0
      focus_app_menu || true
    fi
  fi

  sleep 0.5
done
