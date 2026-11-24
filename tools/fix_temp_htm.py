#!/usr/bin/env python3
"""Post-process Astrologie res/temp.htm for Wine/Gecko.

- Assure un <HEAD> (Delphi exporte souvent HTML sans HEAD)
- Sauts sommaire fiables via scrollTop (Wine ignore souvent #IndexN)
- Ancres IndexN préservées / recréées
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

FIX_MARK = "astro-fix-v5"

SECTION_LABELS = {
    0: "PORTRAIT",
    1: "CALCUL DU CIEL",
    2: "ASPECTS",
    3: "DOMINANTE",
    4: "CARACTÉROLOGIE",
    5: "TYPOLOGIE PLANÉTAIRE",
    6: "ASTROPSYCHANALYSE",
    7: "PLANÈTES EN MAISONS",
    8: "LUNE NOIRE",
    9: "ÉTUDE KARMIQUE",
}


def decode(raw: bytes) -> str:
    for enc in ("cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("latin-1", errors="replace")


CSS = """
<style>
/* astro-fix-v5 */
html { scroll-behavior: auto; }
body {
  margin: 0;
  padding: 54px 16px 48px 12px;
  font-family: "Times New Roman", Times, serif;
  font-size: 15px;
  line-height: 1.5;
  color: #1a1510;
  background: #f3ebdd;
}
.navdrop {
  position: absolute; top: 0; left: 0; right: 0; z-index: 9999;
  background: #2a1c10; color: #f5ecd7;
  padding: 8px 10px; border-bottom: 2px solid #c4a35a;
  font-family: Arial, Helvetica, sans-serif; font-size: 13px;
}
.navdrop select { min-width: 180px; max-width: 70%; }
.navdrop button {
  padding: 3px 10px; font-weight: bold; cursor: pointer;
  background: #c4a35a; border: 1px solid #8d7340; color: #1a1208;
}
.sommaire {
  background: #fffaf0; border: 2px solid #8b281e;
  padding: 12px 16px; margin: 10px auto 24px; max-width: 520px;
}
.sommaire h2 { margin: 0 0 10px; text-align: center; color: #8b281e; }
.sommaire ul { margin: 0; padding-left: 1.1em; }
.sommaire li { margin: 7px 0; }
.sommaire a { color: #8b281e; font-weight: bold; text-decoration: underline; cursor: pointer; }
.sommaire .hint { font-size: 12px; color: #444; text-align: center; }
.section { max-width: 520px; margin: 0 auto 28px; padding-top: 8px; }
</style>
"""

JS = """
<script>
/* astro-fix-v5 */
function findAnchor(n) {
  var id = 'Index' + n;
  var el = document.getElementById(id);
  if (el) return el;
  var all = document.getElementsByName(id);
  if (all && all.length) return all[0];
  el = document.getElementById('index' + n);
  if (el) return el;
  all = document.getElementsByName('index' + n);
  if (all && all.length) return all[0];
  el = document.getElementById('sec' + n);
  return el || null;
}
function elementY(el) {
  var y = 0, node = el;
  while (node) { y += (node.offsetTop || 0); node = node.offsetParent; }
  return (y > 8) ? (y - 8) : 0;
}
function setScrollY(y) {
  y = Math.floor(y);
  if (y < 0) y = 0;
  try { window.scrollTo(0, y); } catch (e0) {}
  try { document.documentElement.scrollTop = y; } catch (e1) {}
  try { document.body.scrollTop = y; } catch (e2) {}
}
function goSection(n) {
  n = parseInt(n, 10);
  var el = findAnchor(n);
  if (!el) { try { location.hash = 'Index' + n; } catch (e) {} return false; }
  var y = elementY(el);
  setScrollY(y);
  setTimeout(function(){ setScrollY(elementY(el)); }, 80);
  setTimeout(function(){ setScrollY(elementY(el)); }, 250);
  setTimeout(function(){ setScrollY(elementY(el)); }, 700);
  var sel = document.getElementById('jumpSec');
  if (sel) sel.value = String(n);
  return false;
}
function onJump(sel) { if (sel && sel.value !== '') goSection(sel.value); }
function currentIdx() {
  var sel = document.getElementById('jumpSec');
  if (sel && sel.value !== '') return parseInt(sel.value, 10);
  return 0;
}
function goPrev() {
  var i = currentIdx(), p = 0, k;
  for (k = 0; k < SECTIONS.length; k++) if (SECTIONS[k] < i) p = SECTIONS[k];
  goSection(p);
}
function goNext() {
  var i = currentIdx(), k;
  for (k = 0; k < SECTIONS.length; k++) if (SECTIONS[k] > i) { goSection(SECTIONS[k]); return; }
}
var _lastHash = '';
function bootFromHash() {
  var h = '';
  try { h = (location.hash || '').replace(/^#/, ''); } catch (e) {}
  if (!h || h.toLowerCase() === 'index') {
    var s = document.getElementById('sommaire');
    if (s) setScrollY(elementY(s));
    return;
  }
  var m = h.match(/index\\s*(\\d+)/i);
  if (m) goSection(m[1]);
}
function watchHash() {
  var h = '';
  try { h = String(location.hash || ''); } catch (e) {}
  if (h !== _lastHash) { _lastHash = h; bootFromHash(); }
}
window.onload = function () {
  bootFromHash();
  setTimeout(bootFromHash, 300);
  setTimeout(bootFromHash, 900);
  setInterval(watchHash, 400);
  try { window.onhashchange = bootFromHash; } catch (e) {}
};
</script>
"""


def strip_injected(text: str) -> str:
    text = re.sub(r"(?is)<!--\s*astro-fix[^>]*-->\s*", "", text)
    text = re.sub(r"(?is)<style>\s*/\*\s*astro-fix.*?</style>\s*", "", text)
    text = re.sub(r"(?is)<script>\s*/\*\s*astro-fix.*?</script>\s*", "", text)
    text = re.sub(r'(?is)<div id="navdrop"[^>]*>.*?</div>\s*', "", text, count=1)
    text = re.sub(r'(?is)<div id="scrollrail"[^>]*>.*?</div>\s*', "", text, count=1)
    text = re.sub(r'(?is)<div id="sommaire"[^>]*>.*?</div>\s*', "", text, count=1)
    text = re.sub(r'(?is)<a name="index"[^>]*>\s*</a>\s*', "", text)
    text = re.sub(r'(?is)<a name="Index"[^>]*>\s*</a>\s*', "", text)
    # unwrap our section wrappers but keep original anchors
    text = re.sub(r'(?is)</div>\s*<div class="section"[^>]*>\s*', "", text)
    text = re.sub(r'(?is)<div class="section"[^>]*>\s*', "", text)
    text = re.sub(r"(?is)<span class=\"jumpmark\"[^>]*>.*?</span>\s*", "", text)
    text = re.sub(r"(?i)</div>\s*</BODY>", "</BODY>", text, count=1)
    return text


def ensure_head(text: str) -> str:
    if re.search(r"(?i)<HEAD", text):
        return text
    # Delphi: <HTML><BODY...> → insert HEAD
    text = re.sub(
        r"(?i)<HTML>\s*",
        '<HTML>\r\n<HEAD>\r\n'
        '<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">\r\n'
        "<TITLE>Astrologie</TITLE>\r\n"
        "</HEAD>\r\n",
        text,
        count=1,
    )
    return text


def collect_indices(text: str) -> list[int]:
    names = [int(m.group(1)) for m in re.finditer(r'(?i)(?:name|id)\s*=\s*"Index(\d+)"', text)]
    return sorted(set(names))


def inject_heading_anchors(text: str) -> tuple[str, list[tuple[int, str]]]:
    """Si pas d'IndexN, crée des ancres sur les titres FONT SIZE=+1."""
    found: list[tuple[int, str]] = []

    def repl(m: re.Match) -> str:
        title = re.sub(r"\s+", " ", m.group(2)).strip()
        if len(title) < 3:
            return m.group(0)
        n = len(found)
        found.append((n, title[:80]))
        return (
            f'<a name="Index{n}" id="Index{n}"></a>'
            f'<a name="index{n}" id="index{n}"></a>'
            f"{m.group(1)}{m.group(2)}{m.group(3)}"
        )

    text2 = re.sub(
        r"(?is)(<FONT SIZE=\+1>)([^<]{3,120})(</FONT>)",
        repl,
        text,
    )
    return text2, found


def enrich_existing_anchors(text: str) -> str:
    def repl(m: re.Match) -> str:
        n = m.group(1)
        return (
            f'<a name="Index{n}" id="Index{n}"></a>'
            f'<a name="index{n}" id="index{n}"></a>'
        )

    return re.sub(r'(?i)<A\s+NAME\s*=\s*"Index(\d+)"\s*>\s*</A>', repl, text)


def build_toc(entries: list[tuple[int, str]]) -> str:
    links = []
    options = ['<option value="">-- Aller a une rubrique --</option>']
    for n, label in entries:
        links.append(
            f'<li><a href="#Index{n}" onclick="return goSection({n});">{label}</a></li>'
        )
        options.append(f'<option value="{n}">{label}</option>')
    nums = ",".join(str(n) for n, _ in entries) or "0"
    return (
        f"<!-- {FIX_MARK} -->\n"
        f"<script>var SECTIONS=[{nums}];</script>\n"
        '<a name="index" id="index"></a>\n'
        '<div id="navdrop" class="navdrop">'
        "<b>Aller a :</b> "
        '<select id="jumpSec" onchange="onJump(this)">'
        + "".join(options)
        + "</select> "
        '<button type="button" onclick="goPrev()">Haut</button> '
        '<button type="button" onclick="goNext()">Bas</button>'
        "</div>\n"
        '<div id="sommaire" class="sommaire">\n'
        "<h2>SOMMAIRE</h2>\n<ul>\n"
        + "\n".join(links)
        + "\n</ul>\n"
        '<p class="hint">Clique une rubrique pour y aller. Molette ou pyramides pour defiler.</p>\n'
        "</div>\n"
    )


def fix(text: str) -> str:
    if FIX_MARK in text and "elementY" in text and "watchHash" in text and "function goSection" in text:
        return text

    text = strip_injected(text)
    text = ensure_head(text)

    # charset
    if re.search(r"charset=", text, re.I) is None and re.search(r"(?i)<HEAD", text):
        text = re.sub(
            r"(?i)(<HEAD[^>]*>)",
            r'\1\n<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">',
            text,
            count=1,
        )

    text = enrich_existing_anchors(text)
    indices = collect_indices(text)
    entries: list[tuple[int, str]]
    if indices:
        entries = [(i, SECTION_LABELS.get(i, f"Section {i}")) for i in indices]
    else:
        text, found = inject_heading_anchors(text)
        entries = found if found else [(0, "Debut")]

    # inject CSS+JS before </HEAD>
    if "function goSection" not in text:
        if re.search(r"(?i)</HEAD>", text):
            text = re.sub(r"(?i)</HEAD>", lambda _m: CSS + JS + "\n</HEAD>", text, count=1)
        else:
            text = CSS + JS + text

    # TOC after <BODY>
    if 'id="sommaire"' not in text:
        toc = build_toc(entries)
        text = re.sub(r"(?i)(<BODY[^>]*>)", r"\1\n" + toc, text, count=1)

    return text


def main() -> int:
    path = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else Path.home()
        / "Documents/Astrologie/windows-apps/AstroHoroscope/Astrologie/res/temp.htm"
    )
    if not path.is_file():
        print("missing", path, file=sys.stderr)
        return 1
    fixed = fix(decode(path.read_bytes()))
    out = fixed.encode("cp1252", errors="replace")
    path.write_bytes(out)
    utf8_path = path.with_name("temp-utf8.html")
    utf8 = re.sub(r"charset=windows-1252", "charset=utf-8", fixed, count=1, flags=re.I)
    utf8_path.write_text(utf8, encoding="utf-8")
    print("fixed", path, "bytes", len(out))
    print("mirror", utf8_path)
    print("has_js", "elementY" in fixed, "anchors", len(collect_indices(fixed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
