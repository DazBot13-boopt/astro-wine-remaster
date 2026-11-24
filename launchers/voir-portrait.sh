#!/usr/bin/env bash
set -euo pipefail
RES="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Astrologie/res"
python3 "$HOME/Documents/Astrologie/windows-apps/tools/fix_temp_htm.py" "$RES/temp.htm" 2>/dev/null || true
HTM="$RES/temp-utf8.html"
[ -f "$HTM" ] || HTM="$RES/temp.htm"
xdg-open "$HTM" >/dev/null 2>&1 || sensible-browser "$HTM"
echo "Ouvert: $HTM"
echo "PDF:    $RES/portrait.pdf  (relancer: ~/Documents/Astrologie/windows-apps/exporter-pdf.sh)"
