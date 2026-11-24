#!/usr/bin/env bash
set -euo pipefail
export WINEPREFIX="${WINEPREFIX:-$HOME/.wine-astro}"
export DISPLAY="${DISPLAY:-:0}"
APP="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope"
ln -sfn "$APP/Astrofic32" "$APP/astrofic32"
python3 "$(dirname "$0")/../tools/patch_horoscope_paths.py" >/dev/null 2>&1 || true
cd "$APP"
exec wine "./Astrologie & Horoscope.exe" "$@"
