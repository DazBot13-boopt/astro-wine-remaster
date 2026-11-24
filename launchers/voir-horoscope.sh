#!/usr/bin/env bash
# Ouvre le lecteur Horoscope intégré (GTK/WebKit), pas Firefox.
set -euo pipefail
export DISPLAY="${DISPLAY:-:0}"
TOOLS="$(cd "$(dirname "$0")/../tools" && pwd)"
ROOT="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope"
python3 "$TOOLS/rtf_to_htm.py" "$ROOT" >/dev/null 2>&1 || true
exec python3 "$TOOLS/horoscope_inapp_viewer.py"
