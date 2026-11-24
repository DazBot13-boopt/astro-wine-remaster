#!/usr/bin/env bash
# 1) coo.dat case-fix  2) RTF→HTML  3) viewer OREAC SEULEMENT au clic Horoscope
# Si l'utilisateur ferme OREAC → on ne le rouvre PAS tant qu'un nouveau Horoscope_*.exe n'est pas lancé.
set -euo pipefail
ROOT="${1:-$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope}"
TOOLS="$(cd "$(dirname "$0")" && pwd)"
FIX="$TOOLS/rtf_to_htm.py"
VIEWER="$TOOLS/horoscope_inapp_viewer.py"
echo "[watch-horoscope] viewer only on Horoscope click → $ROOT"

find "$ROOT" -iname 'coo.dat' ! -name 'coo.dat' -print0 2>/dev/null \
  | while IFS= read -r -d '' f; do mv -f "$f" "$(dirname "$f")/coo.dat"; done

viewer_pid=0
last_horo_pids=""

horoscope_pids() {
  pgrep -f 'Horoscope_[0-9]+\.exe' 2>/dev/null | sort -u | tr '\n' ' ' || true
}

while true; do
  find "$ROOT" -iname 'coo.dat' ! -name 'coo.dat' -print0 2>/dev/null \
    | while IFS= read -r -d '' f; do mv -f "$f" "$(dirname "$f")/coo.dat"; done
  python3 "$FIX" "$ROOT" >/tmp/horo-rtf-fix.log 2>&1 || true

  cur=$(horoscope_pids)
  if [[ -n "$cur" && "$cur" != "$last_horo_pids" ]]; then
    # Nouveau process Horoscope (clic menu) → un seul viewer pour cette session
    if [[ "$viewer_pid" -gt 0 ]] && kill -0 "$viewer_pid" 2>/dev/null; then
      kill "$viewer_pid" 2>/dev/null || true
    fi
    # tue d'éventuels vieux viewers orphelins
    pkill -f 'horoscope_inapp_viewer.py' 2>/dev/null || true
    sleep 0.2
    python3 "$VIEWER" >/tmp/horoscope-viewer.log 2>&1 &
    viewer_pid=$!
    echo "[watch-horoscope] open viewer pid=$viewer_pid (horoscope pids=$cur)"
    last_horo_pids="$cur"
  elif [[ -z "$cur" ]]; then
    # plus de Horoscope Wine → ferme le viewer et reset
    if [[ "$viewer_pid" -gt 0 ]] && kill -0 "$viewer_pid" 2>/dev/null; then
      kill "$viewer_pid" 2>/dev/null || true
    fi
    viewer_pid=0
    last_horo_pids=""
  fi
  # Si l'utilisateur a fermé OREAC (viewer_pid mort) mais Horoscope tourne encore :
  # on NE relance PAS — attendre un nouveau clic (= nouveau pid set).

  sleep 0.5
done
