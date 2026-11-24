#!/usr/bin/env bash
# Ouvre le dernier Horoscope généré dans le navigateur système
# (le TWebBrowser Wine reste souvent noir / 1×1 / OOM).
set -euo pipefail
ROOT="$HOME/Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope"
TOOLS="$(cd "$(dirname "$0")/../tools" && pwd)"
python3 "$TOOLS/rtf_to_htm.py" >/dev/null 2>&1 || true

HTM="$(find "$ROOT" -path '*/Res_Txt/temp.htm' -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)"
if [[ -z "${HTM:-}" || ! -s "$HTM" ]]; then
  echo "Aucun temp.htm Horoscope. Clique d'abord une rubrique dans l'app Wine."
  exit 1
fi

# Copie UTF-8 lisible (évite soucis file:// + accents chemin)
OUT="/tmp/astro-horoscope-latest.html"
python3 - <<PY
from pathlib import Path
src = Path(r"""$HTM""")
raw = src.read_bytes()
text = raw.decode("utf-8", errors="strict") if raw.startswith(b"<HTML>\r\n<HEAD>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">") else raw.decode("cp1252", errors="replace")
# rebase images/css relatifs
base = src.parent.as_uri() + "/"
if "<base " not in text.lower():
    text = text.replace("<HEAD>", f'<HEAD>\n<base href="{base}">', 1).replace("<head>", f'<head>\n<base href="{base}">', 1)
Path(r"""$OUT""").write_text(text, encoding="utf-8")
print(src)
PY

xdg-open "$OUT" >/dev/null 2>&1 || sensible-browser "$OUT"
echo "Ouvert: $OUT"
echo "Source: $HTM"
