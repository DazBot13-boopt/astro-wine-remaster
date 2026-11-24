#!/usr/bin/env bash
set -euo pipefail
TOOLS="$HOME/Documents/Astrologie/windows-apps/tools"
RES="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Astrologie/res"
python3 "$TOOLS/fix_temp_htm.py" "$RES/temp.htm"
python3 "$TOOLS/export_portrait_pdf.py" "$RES/temp-utf8.html" "$RES/portrait.pdf"
OUT="$RES/portrait.pdf"
echo "PDF: $OUT"
xdg-open "$OUT" >/dev/null 2>&1 || true
