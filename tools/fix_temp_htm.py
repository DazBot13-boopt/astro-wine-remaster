#!/usr/bin/env python3
"""Post-process Astrologie res/temp.htm for Wine/Gecko:
- sommaire cliquable
- barre de défilement avec trait (thumb) cliquable/tirable
- navigation rubriques
- charset windows-1252
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

FIX_MARK = "astro-fix-v3-scrollbar"

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
        f'<!-- {FIX_MARK} -->\n'
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
        '<div id="scrollrail" class="scrollrail" title="Tirer pour défiler">'
        '<div id="scrollthumb" class="scrollthumb"></div>'
        "</div>\n"
        '<div id="sommaire" class="sommaire">\n'
        "<h2>SOMMAIRE</h2>\n"
        "<ul>\n"
        + "\n".join(links)
        + "\n</ul>\n"
        '<p class="hint">Molette, ▲▼, ou tirez le trait à droite pour défiler.</p>\n'
        "</div>\n"
    )


CSS = """
<style>
html { scroll-behavior: smooth; }
html, body { height: auto; }
body {
  margin: 0;
  padding: 56px 28px 56px 16px;
  font-family: "Times New Roman", Times, serif;
  font-size: 15px;
  line-height: 1.5;
  color: #1a1510;
  background: #f3ebdd;
}
.navdrop {
  position: fixed;
  top: 0; left: 0; right: 22px;
  z-index: 9999;
  background: #2a1c10;
  color: #f5ecd7;
  padding: 8px 12px;
  border-bottom: 2px solid #c4a35a;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 13px;
}
.navdrop select {
  min-width: 200px;
  max-width: 65%;
  padding: 4px 6px;
  font-size: 13px;
}
.navdrop button {
  padding: 3px 10px;
  cursor: pointer;
  font-size: 14px;
  background: #c4a35a;
  border: 1px solid #8d7340;
  color: #1a1208;
  font-weight: bold;
}
/* Trait de défilement cliquable / tirable (style app) */
.scrollrail {
  position: fixed;
  top: 52px;
  right: 4px;
  bottom: 8px;
  width: 14px;
  z-index: 10000;
  background: rgba(60, 30, 20, 0.18);
  border: 1px solid rgba(139, 40, 30, 0.45);
  border-radius: 8px;
  cursor: pointer;
}
.scrollthumb {
  position: absolute;
  left: 1px;
  width: 10px;
  min-height: 36px;
  background: linear-gradient(180deg, #c45a4a 0%, #8b281e 55%, #6a1a14 100%);
  border: 1px solid #5a120e;
  border-radius: 7px;
  cursor: grab;
  box-shadow: 0 1px 3px rgba(0,0,0,.35);
}
.scrollthumb:active { cursor: grabbing; }
.sommaire {
  background: rgba(255,252,245,.95);
  border: 1px solid #8a6a3a;
  padding: 10px 16px 14px;
  margin: 8px auto 24px;
  max-width: 540px;
}
.sommaire h2 { margin: 4px 0 8px; text-align: center; font-size: 1.25rem; color: #5a1a12; }
.sommaire ul { margin: 0; padding-left: 1.2em; }
.sommaire li { margin: 6px 0; }
.sommaire a { color: #8b281e; font-weight: bold; text-decoration: none; font-size: 1.05em; }
.sommaire a:hover { text-decoration: underline; }
.sommaire .hint { font-size: 12px; color: #555; text-align: center; }
.section {
  max-width: 540px;
  margin: 0 auto 28px;
  padding-top: 10px;
  scroll-margin-top: 60px;
  border-top: 1px solid rgba(90,40,20,.15);
}
@media print {
  .navdrop, .scrollrail { display: none !important; }
  body { background: #fff !important; padding: 12px; }
  .sommaire { break-after: page; }
  .section { break-inside: avoid; border: none; }
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
  syncThumb();
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

/* ===== Scrollbar thumb (tirer le trait) ===== */
function docScrollMax() {
  var se = document.documentElement, b = document.body;
  var sh = Math.max(se.scrollHeight, b.scrollHeight);
  var ch = se.clientHeight || window.innerHeight || 600;
  return Math.max(1, sh - ch);
}
function syncThumb() {
  var rail = document.getElementById('scrollrail');
  var thumb = document.getElementById('scrollthumb');
  if (!rail || !thumb) return;
  var se = document.documentElement;
  var ch = se.clientHeight || window.innerHeight || 600;
  var sh = Math.max(se.scrollHeight, document.body.scrollHeight);
  var max = Math.max(1, sh - ch);
  var railH = rail.clientHeight || 1;
  var thumbH = Math.max(36, Math.floor(railH * ch / sh));
  thumb.style.height = thumbH + 'px';
  var maxTop = Math.max(0, railH - thumbH);
  var top = Math.floor((window.pageYOffset || se.scrollTop || 0) / max * maxTop);
  thumb.style.top = top + 'px';
}
function initScrollThumb() {
  var rail = document.getElementById('scrollrail');
  var thumb = document.getElementById('scrollthumb');
  if (!rail || !thumb) return;
  var dragging = false, startY = 0, startTop = 0;

  function setFromThumbTop(top) {
    var se = document.documentElement;
    var ch = se.clientHeight || window.innerHeight || 600;
    var sh = Math.max(se.scrollHeight, document.body.scrollHeight);
    var max = Math.max(1, sh - ch);
    var railH = rail.clientHeight || 1;
    var thumbH = thumb.offsetHeight || 36;
    var maxTop = Math.max(0, railH - thumbH);
    if (top < 0) top = 0;
    if (top > maxTop) top = maxTop;
    thumb.style.top = top + 'px';
    var y = maxTop > 0 ? (top / maxTop) * max : 0;
    window.scrollTo(0, y);
  }

  thumb.onmousedown = function (e) {
    dragging = true;
    startY = e.clientY;
    startTop = parseInt(thumb.style.top || '0', 10) || 0;
    if (e.preventDefault) e.preventDefault();
    return false;
  };
  document.onmousemove = function (e) {
    if (!dragging) return;
    setFromThumbTop(startTop + (e.clientY - startY));
  };
  document.onmouseup = function () { dragging = false; };

  rail.onclick = function (e) {
    if (e.target === thumb) return;
    var rect = rail.getBoundingClientRect();
    var thumbH = thumb.offsetHeight || 36;
    setFromThumbTop(e.clientY - rect.top - thumbH / 2);
  };

  if (window.addEventListener) {
    window.addEventListener('scroll', syncThumb, false);
    window.addEventListener('resize', syncThumb, false);
  } else {
    window.onscroll = syncThumb;
    window.onresize = syncThumb;
  }
  syncThumb();
  setTimeout(syncThumb, 300);
  setTimeout(syncThumb, 1000);
}

window.onload = function () {
  var h = (location.hash || '').replace(/^#/, '');
  if (!h || h.toLowerCase() === 'index') {
    var s = document.getElementById('sommaire');
    if (s && s.scrollIntoView) s.scrollIntoView(true);
  } else if (/^Index\\d+$/i.test(h)) {
    goSection(h.replace(/\\D/g, ''));
  }
  initScrollThumb();
};
</script>
"""


def strip_previous_fix(text: str) -> str:
    text = re.sub(r"(?is)<!-- astro-fix-v\d[^>]*-->\s*", "", text)
    text = re.sub(r"(?is)<style>.*?scroll-behavior.*?</style>", "", text, count=1)
    text = re.sub(r"(?is)<style>.*?</style>", "", text, count=1) if "scrollrail" in text else text
    text = re.sub(r"(?is)<script>.*?function goSection.*?</script>", "", text, count=1)
    text = re.sub(r'(?is)<div id="navdrop"[^>]*>.*?</div>\s*', "", text, count=1)
    text = re.sub(r'(?is)<div id="scrollrail"[^>]*>.*?</div>\s*', "", text, count=1)
    text = re.sub(r'(?is)<div id="sommaire"[^>]*>.*?</div>\s*', "", text, count=1)
    text = re.sub(r'(?is)<a name="index"[^>]*>\s*</a>\s*', "", text)
    text = re.sub(r'(?is)<a name="Index"[^>]*>\s*</a>\s*', "", text)
    text = re.sub(r'(?is)</div>\s*<div class="section"[^>]*>\s*', "", text)
    text = re.sub(r'(?is)<div class="section"[^>]*>\s*', "", text)
    text = re.sub(r'(?i)<a name="index\d+"[^>]*>\s*</a>\s*', "", text)
    text = re.sub(r'(?i)\s*id="Index(\d+)"', "", text)
    text = re.sub(r'(?i)\s*id="index\d+"', "", text)
    text = re.sub(r"(?i)</div>\s*</BODY>", "</BODY>", text, count=1)
    return text


def fix(text: str) -> str:
    if FIX_MARK in text and 'id="scrollrail"' in text and "initScrollThumb" in text:
        return text
    if 'id="sommaire"' in text or "goSection" in text or "scroll-behavior" in text:
        text = strip_previous_fix(text)

    if re.search(r"charset=", text, re.I) is None:
        text = re.sub(
            r"(?i)<HEAD>",
            '<HEAD>\n<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">',
            text,
            count=1,
        )

    names = [int(m.group(1)) for m in re.finditer(r'(?i)<A NAME\s*=\s*"Index(\d+)"', text)]
    names = sorted(set(names)) or list(range(0, 10))

    if FIX_MARK not in text:
        text = re.sub(r"(?i)</HEAD>", lambda _m: CSS + JS + "\n</HEAD>", text, count=1)

    def repl_anchor(m: re.Match) -> str:
        n = m.group(1)
        return (
            f'</div>\n'
            f'<div class="section" id="sec{n}">\n'
            f'<a name="Index{n}" id="Index{n}"></a>\n'
            f'<a name="index{n}" id="index{n}"></a>\n'
        )

    text2 = re.sub(r'(?i)<A NAME\s*=\s*"Index(\d+)"\s*>\s*</A>', repl_anchor, text)
    text2 = re.sub(r"(?i)(<BODY[^>]*>)\s*</div>", r"\1", text2, count=1)

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
    text = decode(raw)
    fixed = fix(text)
    out = fixed.encode("cp1252", errors="replace")
    path.write_bytes(out)
    utf8_path = path.with_name("temp-utf8.html")
    utf8 = re.sub(r"charset=windows-1252", "charset=utf-8", fixed, count=1, flags=re.I)
    utf8_path.write_text(utf8, encoding="utf-8")
    print("fixed", path, "bytes", len(out))
    print("mirror", utf8_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
