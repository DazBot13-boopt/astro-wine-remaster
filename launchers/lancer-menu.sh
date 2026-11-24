#!/usr/bin/env bash
# Lanceur Linux/Wine UNIQUEMENT — sur Windows réel, double-clique
# "Astrologie & Horoscope.exe" (IE natif = texte dans l'app, pas Chrome).
set -euo pipefail
export WINEPREFIX="${WINEPREFIX:-$HOME/.wine-astro}"
export DISPLAY="${DISPLAY:-:0}"
# Sous Wine le TWebBrowser est souvent noir/1x1 → ouvrir le HTML dans le navigateur.
# ASTRO_OPEN_BROWSER=0 pour désactiver.
export ASTRO_OPEN_BROWSER="${ASTRO_OPEN_BROWSER:-1}"
APP="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope"
TOOLS="$(cd "$(dirname "$0")/../tools" && pwd)"

ln -sfn "$APP/Astrofic32" "$APP/astrofic32"
python3 "$TOOLS/patch_horoscope_paths.py" >/dev/null 2>&1 || true

# Watchers HTML (ne tuent PAS les .exe enfants)
pkill -f 'watch_horoscope_htm.sh' 2>/dev/null || true
pkill -f 'watch_temp_htm.sh' 2>/dev/null || true
nohup bash "$TOOLS/watch_horoscope_htm.sh" >/tmp/watch-horoscope.log 2>&1 &
nohup bash "$TOOLS/watch_temp_htm.sh" >/tmp/watch-portrait.log 2>&1 &

# Une seule session : ferme l'ancienne copie (mauvais dossier / zombies)
# puis relance proprement depuis AstroHoroscope (chemins ASCII).
if pgrep -f 'Astrologie & Horoscope\\Astrologie|Astrologie & Horoscope\\\\Horoscope|AstroHoroscope\\\\' >/dev/null 2>&1 \
   || pgrep -f 'Astrologie\\\\Astrologie\.exe|Horoscope_.*\.exe|Astrologie & Horoscope\.exe' >/dev/null 2>&1; then
  echo "Nettoyage session Wine précédente (évite crash multi-instances)…"
  wineserver -k 2>/dev/null || true
  sleep 1
fi

echo "Linux/Wine: si le cadre dans l'app est noir → ./voir-horoscope.sh"
echo "Windows réel: tout s'affiche DANS l'app (pas besoin de Chrome)."
cd "$APP"
exec wine "./Astrologie & Horoscope.exe" "$@"
