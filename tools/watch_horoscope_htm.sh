#!/usr/bin/env bash
# Dès que Wine écrit un temp.rtf / temp.htm vide, on régénère le HTML
# et on ouvre le navigateur système (TWebBrowser Wine = souvent noir).
set -euo pipefail
ROOT="${1:-$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope}"
FIX="$(dirname "$0")/rtf_to_htm.py"
OPENER="$(cd "$(dirname "$0")/../launchers" && pwd)/voir-horoscope.sh"
STAMP="/tmp/astro-horoscope-opened.stamp"
echo "[watch-horoscope] $ROOT"
python3 "$FIX" || true

open_if_new() {
  local newest
  newest="$(find "$ROOT" -path '*/Res_Txt/temp.htm' -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 || true)"
  [[ -z "$newest" ]] && return 0
  local mtime path
  mtime="${newest%% *}"
  path="${newest#* }"
  [[ ! -s "$path" ]] && return 0
  # body non vide ?
  if ! python3 -c "
import re,sys
from pathlib import Path
t=Path(sys.argv[1]).read_text('utf-8',errors='replace')
m=re.search(r'(?is)<BODY[^>]*>(.*)</BODY>',t)
inner=re.sub(r'(?is)<[^>]+>','',m.group(1) if m else '')
sys.exit(0 if len(re.sub(r'\s+','',inner))>=20 else 1)
" "$path"; then
    return 0
  fi
  local prev=0
  [[ -f "$STAMP" ]] && prev="$(cat "$STAMP" 2>/dev/null || echo 0)"
  # n'ouvre que si plus récent que le dernier open
  python3 -c "import sys; sys.exit(0 if float(sys.argv[1])>float(sys.argv[2])+0.5 else 1)" "$mtime" "$prev" || return 0
  echo "$mtime" >"$STAMP"
  echo "[watch-horoscope] open $path"
  bash "$OPENER" >/tmp/voir-horoscope.log 2>&1 || true
}

open_if_new || true
while true; do
  python3 "$FIX" >/tmp/horo-rtf-fix.log 2>&1 || true
  open_if_new || true
  sleep 1
done
