#!/usr/bin/env bash
# Affiche le dernier Horoscope dans le navigateur (Wine TWebBrowser = souvent vide).
set -euo pipefail
ROOT="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope"
TOOLS="$(cd "$(dirname "$0")/../tools" && pwd)"
python3 "$TOOLS/rtf_to_htm.py" "$ROOT" >/dev/null 2>&1 || true

HTM="$(find "$ROOT" -path '*/Res_Txt/temp.htm' -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)"
if [[ -z "${HTM:-}" || ! -s "$HTM" ]]; then
  echo "Aucun temp.htm. Clique d'abord une rubrique Horoscope dans l'app."
  exit 1
fi

OUT="/tmp/astro-horoscope-latest.html"
python3 - <<PY
from pathlib import Path
import re
src = Path(r"""$HTM""")
raw = src.read_bytes().replace(b"\x00", b"")
# détecte charset déclaré, sinon cp1252 (Delphi)
m = re.search(br"charset=([a-zA-Z0-9_-]+)", raw, re.I)
cs = (m.group(1).decode() if m else "cp1252").lower().replace("windows-1252", "cp1252")
if cs in ("utf-8", "utf8"):
    text = raw.decode("utf-8", errors="replace")
else:
    text = raw.decode("cp1252", errors="replace")
base = src.parent.as_uri() + "/"
if re.search(r"(?i)<base\s", text) is None:
    text = re.sub(r"(?i)<head>", f'<head>\\n<base href="{base}">', text, count=1)
# force UTF-8 + fond clair lisible
text = re.sub(
    r'(?i)<meta[^>]+charset=[^>]+>',
    '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
    text,
    count=1,
)
text = re.sub(r'(?i)<body([^>]*)>', r'<body\1 bgcolor="#FFFFFF" style="color:#111;background:#fff">', text, count=1)
Path(r"""$OUT""").write_text(text, encoding="utf-8")
print(src)
PY

# Navigateur dédié (évite de se perdre derrière un onglet GitHub)
if command -v firefox >/dev/null; then
  firefox --new-window "file://$OUT" >/dev/null 2>&1 &
elif command -v google-chrome >/dev/null; then
  google-chrome --new-window "file://$OUT" >/dev/null 2>&1 &
else
  xdg-open "$OUT" >/dev/null 2>&1 &
fi
echo "Ouvert: $OUT"
echo "Source: $HTM"
echo "(Sous Wine le cadre dans l'app reste souvent noir — le texte est ici.)"
