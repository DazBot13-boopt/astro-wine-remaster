#!/usr/bin/env bash
# Régénère temp.htm depuis temp.rtf (rapide, sans LibreOffice).
# Ouvre le navigateur SEULEMENT si ASTRO_OPEN_BROWSER=1.
set -euo pipefail
ROOT="${1:-$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope}"
# Aussi le vieux dossier si encore utilisé
ROOT_OLD="$HOME/Documents/Astrologie/windows-apps/Astrologie & Horoscope/Horoscope"
FIX="$(dirname "$0")/rtf_to_htm.py"
OPENER="$(cd "$(dirname "$0")/../launchers" && pwd)/voir-horoscope.sh"
STAMP="/tmp/astro-horoscope-opened.stamp"
echo "[watch-horoscope] $ROOT (open_browser=${ASTRO_OPEN_BROWSER:-0})"
python3 "$FIX" "$ROOT" >/dev/null 2>&1 || true
[[ -d "$ROOT_OLD" ]] && python3 "$FIX" "$ROOT_OLD" >/dev/null 2>&1 || true

open_if_new() {
  [[ "${ASTRO_OPEN_BROWSER:-0}" == "1" ]] || return 0
  local newest
  newest="$(find "$ROOT" "$ROOT_OLD" -path '*/Res_Txt/temp.htm' -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 || true)"
  [[ -z "$newest" ]] && return 0
  local mtime path
  mtime="${newest%% *}"
  path="${newest#* }"
  [[ ! -s "$path" ]] && return 0
  python3 -c "
import re,sys
from pathlib import Path
t=Path(sys.argv[1]).read_text('utf-8',errors='replace')
m=re.search(r'(?is)<BODY[^>]*>(.*)</BODY>',t)
inner=re.sub(r'(?is)<[^>]+>','',m.group(1) if m else '')
sys.exit(0 if len(re.sub(r'\s+','',inner))>=20 else 1)
" "$path" || return 0
  local prev=0
  [[ -f "$STAMP" ]] && prev="$(cat "$STAMP" 2>/dev/null || echo 0)"
  python3 -c "import sys; sys.exit(0 if float(sys.argv[1])>float(sys.argv[2])+0.5 else 1)" "$mtime" "$prev" || return 0
  echo "$mtime" >"$STAMP"
  echo "[watch-horoscope] open $path"
  bash "$OPENER" >/tmp/voir-horoscope.log 2>&1 || true
}

while true; do
  python3 "$FIX" "$ROOT" >/tmp/horo-rtf-fix.log 2>&1 || true
  [[ -d "$ROOT_OLD" ]] && python3 "$FIX" "$ROOT_OLD" >>/tmp/horo-rtf-fix.log 2>&1 || true
  open_if_new || true
  sleep 1
done
