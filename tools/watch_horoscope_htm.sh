#!/usr/bin/env bash
# 1) coo.dat case-fix  2) RTF→HTML Delphi  3) viewer GTK in-app (pas Firefox)
set -euo pipefail
ROOT="${1:-$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope}"
TOOLS="$(cd "$(dirname "$0")" && pwd)"
FIX="$TOOLS/rtf_to_htm.py"
VIEWER="$TOOLS/horoscope_inapp_viewer.py"
echo "[watch-horoscope] in-app GTK viewer + HTML fix → $ROOT"

# Normalise Coo.dat → coo.dat (Wine Linux = sensible à la casse → erreur init)
find "$ROOT" -iname 'coo.dat' ! -name 'coo.dat' -print0 2>/dev/null \
  | while IFS= read -r -d '' f; do mv -f "$f" "$(dirname "$f")/coo.dat"; done

viewer_pid=0
ensure_viewer() {
  if [[ "$viewer_pid" -gt 0 ]] && kill -0 "$viewer_pid" 2>/dev/null; then
    return 0
  fi
  # Horoscope Wine lancé OU texte RTF déjà généré
  if pgrep -f 'Horoscope_[0-9]+\.exe' >/dev/null 2>&1 \
     || find "$ROOT" -path '*/Res_Txt/temp.rtf' -size +80c 2>/dev/null | grep -q .; then
    python3 "$VIEWER" >/tmp/horoscope-viewer.log 2>&1 &
    viewer_pid=$!
    echo "[watch-horoscope] viewer pid $viewer_pid"
  fi
}

# premier affichage immédiat si contenu déjà là
ensure_viewer

while true; do
  find "$ROOT" -iname 'coo.dat' ! -name 'coo.dat' -print0 2>/dev/null \
    | while IFS= read -r -d '' f; do mv -f "$f" "$(dirname "$f")/coo.dat"; done
  python3 "$FIX" "$ROOT" >/tmp/horo-rtf-fix.log 2>&1 || true
  ensure_viewer
  sleep 0.5
done
