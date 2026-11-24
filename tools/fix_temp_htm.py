#!/usr/bin/env python3
"""Post-process Astrologie res/temp.htm for Wine/Gecko:
- clickable sommaire (fixes menu landing always on Calcul du ciel)
- smoother scrolling
- print-friendly CSS
- charset windows-1252
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

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


def build_toc(indices: list[int]) -> str:
    links = []
    options = ['<option value="">— Aller à une rubrique —</option>']
    for i in indices:
        label = SECTION_LABELS.get(i, f"Section {i}")
        links.append(
            f'<li><a href="#Index{i}" onclick="return goSection({i})">{label}</a></li>'
        )
        options.append(f'<option value="{i}">{label}</option>')
    return (
        '<a name="index" id="index"></a>\n'
        '<a name="Index" id="Index"></a>\n'
        '<div id="navdrop" class="navdrop">'
        '<label for="jumpSec"><b>Navigation :</b></label> '
        '<select id="jumpSec" name="jumpSec" onchange="onJump(this)">'
        + "".join(options)
        + "</select> "
        '<button type="button" onclick="goPrev()" title="Rubrique précédente">▲</button> '
        '<button type="button" onclick="goNext()" title="Rubrique suivante">▼</button>'
        "</div>\n"
        '<div id="sommaire" class="sommaire">\n'
        "<h2>SOMMAIRE</h2>\n"
        "<ul>\n"
        + "\n".join(links)
        + "\n</ul>\n"
        '<p class="hint">Liste déroulante en haut, ou cliquez une rubrique. Molette pour défiler.</p>\n'
        "</div>\n"
    )


CSS = """
<style>
html { scroll-behavior: smooth; }
body {
  margin: 0;
  padding: 52px 16px 48px;
  font-family: "Times New Roman", Times, serif;
  font-size: 15px;
  line-height: 1.45;
  color: #1a1a1a;
}
.navdrop {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 9999;
  background: #3a2a18;
  color: #f5ecd7;
  padding: 8px 12px;
  border-bottom: 2px solid #c4a35a;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 13px;
}
.navdrop select {
  min-width: 220px;
  max-width: 70%;
  padding: 4px 6px;
  font-size: 13px;
}
.navdrop button {
  padding: 3px 10px;
  cursor: pointer;
  font-size: 14px;
}
.sommaire {
  background: rgba(255,252,245,.92);
  border: 1px solid #8a6a3a;
  padding: 10px 16px 14px;
  margin: 8px auto 24px;
  max-width: 540px;
}
.sommaire h2 { margin: 4px 0 8px; text-align: center; font-size: 1.25rem; }
.sommaire ul { margin: 0; padding-left: 1.2em; }
.sommaire li { margin: 4px 0; }
.sommaire a { color: #5a1a12; font-weight: bold; text-decoration: none; }
.sommaire a:hover { text-decoration: underline; }
.sommaire .hint { font-size: 12px; color: #555; text-align: center; }
.section {
  max-width: 540px;
  margin: 0 auto 28px;
  padding-top: 8px;
  scroll-margin-top: 56px;
  border-top: 1px solid rgba(0,0,0,.12);
}
@media print {
  .navdrop { display: none !important; }
  body { background: #fff !important; padding-top: 12px; }
  .sommaire { break-after: page; }
  .section { break-inside: avoid; border: none; }
  a[href]::after { content: ""; }
}
</style>
"""

JS = """
<script>
var SECTIONS = [0,1,2,3,4,5,6,7,8,9];
function goSection(n) {
  n = parseInt(n, 10);
  var el = document.getElementById('Index' + n) || document.getElementsByName('Index' + n)[0];
  if (el) {
    if (el.scrollIntoView) el.scrollIntoView(true);
    else location.hash = 'Index' + n;
  } else {
    location.hash = 'Index' + n;
  }
  var sel = document.getElementById('jumpSec');
  if (sel) sel.value = String(n);
  return false;
}
function onJump(sel) {
  if (sel && sel.value !== '') goSection(sel.value);
}
function currentIdx() {
  var sel = document.getElementById('jumpSec');
  if (sel && sel.value !== '') return parseInt(sel.value, 10);
  return 0;
}
function goPrev() {
  var i = currentIdx();
  var p = 0;
  for (var k = 0; k < SECTIONS.length; k++) if (SECTIONS[k] < i) p = SECTIONS[k];
  goSection(p);
}
function goNext() {
  var i = currentIdx();
  for (var k = 0; k < SECTIONS.length; k++) {
    if (SECTIONS[k] > i) { goSection(SECTIONS[k]); return; }
  }
}
window.onload = function () {
  var h = (location.hash || '').replace(/^#/, '');
  if (!h || h.toLowerCase() === 'index') {
    var s = document.getElementById('sommaire');
    if (s && s.scrollIntoView) s.scrollIntoView(true);
  } else if (/^Index\\d+$/i.test(h)) {
    goSection(h.replace(/\\D/g, ''));
  }
};
</script>
"""


def strip_previous_fix(text: str) -> str:
    """Remove prior injector blocks so we can re-apply a newer fix."""
    text = re.sub(r"(?is)<style>.*?</style>", "", text, count=1) if "scroll-behavior" in text else text
    text = re.sub(r"(?is)<script>.*?function goSection.*?</script>", "", text, count=1)
    text = re.sub(r'(?is)<div id="navdrop"[^>]*>.*?</div>\s*', "", text, count=1)
    text = re.sub(r'(?is)<div id="sommaire"[^>]*>.*?</div>\s*', "", text, count=1)
    text = re.sub(r'(?is)<a name="index"[^>]*>\s*</a>\s*', "", text)
    text = re.sub(r'(?is)<a name="Index"[^>]*>\s*</a>\s*', "", text)
    # unwrap section wrappers
    text = re.sub(r'(?is)</div>\s*<div class="section"[^>]*>\s*', "", text)
    text = re.sub(r'(?is)<div class="section"[^>]*>\s*', "", text)
    text = re.sub(r'(?i)<a name="index\d+"[^>]*>\s*</a>\s*', "", text)
    text = re.sub(r'(?i)\s*id="Index(\d+)"', "", text)
    text = re.sub(r'(?i)\s*id="index\d+"', "", text)
    text = re.sub(r"(?i)</div>\s*</BODY>", "</BODY>", text, count=1)
    return text


def fix(text: str) -> str:
    # already has latest UI (dropdown)
    if 'id="navdrop"' in text and "onJump" in text:
        return text
    # upgrade older fix
    if 'id="sommaire"' in text or "goSection" in text:
        text = strip_previous_fix(text)

    # charset
    if re.search(r"charset=", text, re.I) is None:
        text = re.sub(
            r"(?i)<HEAD>",
            '<HEAD>\n<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">',
            text,
            count=1,
        )

    # collect IndexN
    names = [int(m.group(1)) for m in re.finditer(r'(?i)<A NAME\s*=\s*"Index(\d+)"', text)]
    names = sorted(set(names))
    if not names:
        names = list(range(0, 10))

    # inject CSS/JS once (lambda: JS contains \d — not a re template)
    if 'id="sommaire"' not in text:
        text = re.sub(r"(?i)</HEAD>", lambda _m: CSS + JS + "\n</HEAD>", text, count=1)

    # wrap each anchor as section + add id= + lowercase name alias
    def repl_anchor(m: re.Match) -> str:
        n = m.group(1)
        return (
            f'</div>\n'
            f'<div class="section" id="sec{n}">\n'
            f'<a name="Index{n}" id="Index{n}"></a>\n'
            f'<a name="index{n}" id="index{n}"></a>\n'
        )

    # First closing stray: prepend open before first index
    text2 = re.sub(
        r'(?i)<A NAME\s*=\s*"Index(\d+)"\s*>\s*</A>',
        repl_anchor,
        text,
    )
    # remove leading </div> before first section
    text2 = re.sub(r"(?i)(<BODY[^>]*>)\s*</div>", r"\1", text2, count=1)

    # insert TOC after <BODY...>
    if 'id="sommaire"' not in text2:
        toc = build_toc([n for n in names if n in SECTION_LABELS or n <= 9])
        text2 = re.sub(r"(?i)(<BODY[^>]*>)", r"\1\n" + toc, text2, count=1)

    if not re.search(r"(?i)</div>\s*</BODY>", text2):
        text2 = re.sub(r"(?i)</BODY>", "</div>\n</BODY>", text2, count=1)

    return text2


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
    raw = path.read_bytes()
    # skip if already fixed and source stamp matches via marker
    text = decode(raw)
    fixed = fix(text)
    out = fixed.encode("cp1252", errors="replace")
    path.write_bytes(out)
    # also write utf-8 mirror for modern browsers / PDF
    utf8_path = path.with_name("temp-utf8.html")
    utf8 = fixed
    utf8 = re.sub(
        r'charset=windows-1252',
        "charset=utf-8",
        utf8,
        count=1,
        flags=re.I,
    )
    utf8_path.write_text(utf8, encoding="utf-8")
    print("fixed", path, "bytes", len(out))
    print("mirror", utf8_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
