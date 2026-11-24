#!/usr/bin/env python3
"""Post-process Astrologie res/temp.htm for Wine/Gecko:
- sommaire → saut fiable (scrollTop, pas seulement hash — Wine ignore souvent #IndexN)
- ancrages IndexN solides
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

FIX_MARK = "astro-fix-v4-jump"

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
    options = ['<option value="">-- Aller a une rubrique --</option>']
    for i in indices:
        label = SECTION_LABELS.get(i, f"Section {i}")
        # href + onclick Wine-safe
        links.append(
            f'<li><a href="#Index{i}" onclick="return goSection({i});">{label}</a></li>'
        )
        options.append(f'<option value="{i}">{label}</option>')
    return (
        f"<!-- {FIX_MARK} -->\n"
        '<a name="index" id="index"></a>\n'
        '<a name="Index" id="Index"></a>\n'
        '<div id="navdrop" class="navdrop">'
        '<b>Aller a :</b> '
        '<select id="jumpSec" name="jumpSec" onchange="onJump(this)">'
        + "".join(options)
        + "</select> "
        '<button type="button" onclick="goPrev()">Haut</button> '
        '<button type="button" onclick="goNext()">Bas</button>'
        "</div>\n"
        '<div id="sommaire" class="sommaire">\n'
        "<h2>SOMMAIRE</h2>\n"
        "<ul>\n"
        + "\n".join(links)
        + "\n</ul>\n"
        '<p class="hint">Clique une rubrique. Tire le trait rouge a droite de la fenetre pour defiler.</p>\n'
        "</div>\n"
    )


CSS = """
<style>
html { scroll-behavior: auto; }
body {
  margin: 0;
  padding: 58px 18px 64px 14px;
  font-family: "Times New Roman", Times, serif;
  font-size: 15px;
  line-height: 1.5;
  color: #1a1510;
  background: #f3ebdd;
}
.navdrop {
  position: absolute;
  top: 0; left: 0; right: 0;
  z-index: 9999;
  background: #2a1c10;
  color: #f5ecd7;
  padding: 8px 10px;
  border-bottom: 2px solid #c4a35a;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 13px;
}
.navdrop select { min-width: 200px; max-width: 70%; padding: 3px; }
.navdrop button {
  padding: 3px 10px; cursor: pointer; font-weight: bold;
  background: #c4a35a; border: 1px solid #8d7340; color: #1a1208;
}
.sommaire {
  background: #fffaf0;
  border: 2px solid #8b281e;
  padding: 12px 16px 14px;
  margin: 12px auto 28px;
  max-width: 520px;
}
.sommaire h2 { margin: 4px 0 10px; text-align: center; color: #8b281e; font-size: 1.35rem; }
.sommaire ul { margin: 0; padding-left: 1.1em; list-style: square; }
.sommaire li { margin: 8px 0; }
.sommaire a {
  color: #8b281e; font-weight: bold; text-decoration: underline;
  font-size: 1.08em; cursor: pointer;
}
.sommaire .hint { font-size: 12px; color: #444; text-align: center; margin-top: 10px; }
.section {
  max-width: 520px;
  margin: 0 auto 32px;
  padding-top: 12px;
  border-top: 1px solid rgba(90,40,20,.18);
}
.jumpmark {
  display: block;
  height: 1px;
  margin: 0;
  padding: 0;
  font-size: 1px;
  line-height: 1px;
  overflow: hidden;
}
</style>
"""

JS = """
<script>
var SECTIONS = [0,1,2,3,4,5,6,7,8,9];

function findAnchor(n) {
  var id = 'Index' + n;
  var el = document.getElementById(id);
  if (el) return el;
  var all = document.getElementsByName(id);
  if (all && all.length) return all[0];
  // fallback lowercase
  el = document.getElementById('index' + n);
  if (el) return el;
  all = document.getElementsByName('index' + n);
  if (all && all.length) return all[0];
  return null;
}

function elementY(el) {
  var y = 0, node = el;
  while (node) {
    y += node.offsetTop || 0;
    node = node.offsetParent;
  }
  // remonte un peu sous la barre nav
  return Math.max(0, y - 8);
}

function setScrollY(y) {
  y = Math.max(0, Math.floor(y));
  // Wine Gecko: essayer tous les conteneurs
  try { window.scrollTo(0, y); } catch (e) {}
  try { document.documentElement.scrollTop = y; } catch (e) {}
  try { document.body.scrollTop = y; } catch (e) {}
  if (document.documentElement) document.documentElement.scrollTop = y;
  if (document.body) document.body.scrollTop = y;
}

function goSection(n) {
  n = parseInt(n, 10);
  var el = findAnchor(n);
  if (!el) {
    // dernier recours hash (parfois marche au 2e essai)
    try { location.hash = 'Index' + n; } catch (e) {}
    return false;
  }
  var y = elementY(el);
  setScrollY(y);
  // retries Wine (layout tardif)
  setTimeout(function(){ setScrollY(elementY(el)); }, 50);
  setTimeout(function(){ setScrollY(elementY(el)); }, 200);
  setTimeout(function(){ setScrollY(elementY(el)); }, 600);
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
  var i = currentIdx(), p = 0;
  for (var k = 0; k < SECTIONS.length; k++) if (SECTIONS[k] < i) p = SECTIONS[k];
  goSection(p);
}
function goNext() {
  var i = currentIdx();
  for (var k = 0; k < SECTIONS.length; k++) {
    if (SECTIONS[k] > i) { goSection(SECTIONS[k]); return; }
  }
}

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

var _lastHash = '';
function watchHash() {
  var h = '';
  try { h = String(location.hash || ''); } catch (e) {}
  if (h !== _lastHash) {
    _lastHash = h;
    bootFromHash();
  }
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


def strip_previous_fix(text: str) -> str:
    text = re.sub(r"(?is)<!-- astro-fix-v\d[^>]*-->\s*", "", text)
    # remove prior injected style/script/nav blocks
    for _ in range(3):
        text = re.sub(r"(?is)<style>.*?</style>\s*", "", text, count=1)
    text = re.sub(r"(?is)<script>.*?function goSection.*?</script>\s*", "", text, count=1)
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
    text = re.sub(r'(?is)<span class="jumpmark"[^>]*>.*?</span>\s*', "", text)
    text = re.sub(r"(?i)</div>\s*</BODY>", "</BODY>", text, count=1)
    return text


def fix(text: str) -> str:
    # déjà la v4 complète
    if FIX_MARK in text and "elementY" in text and "setScrollY" in text and "watchHash" in text:
        return text
    # toujours nettoyer les anciennes injections avant de réécrire
    text = strip_previous_fix(text)
    text = re.sub(r"(?is)<!--\s*astro-fix[^>]*-->\s*", "", text)
    text = re.sub(r"(?is)<script>.*?</script>\s*", "", text)
    # ne garder que le premier style métier éventuel : on retire nos styles injectés
    text = re.sub(
        r"(?is)<style>\s*html\s*\{[^<]*scroll-behavior.*?</style>\s*",
        "",
        text,
    )
    text = re.sub(
        r"(?is)<style>\s*html\s*\{[^<]*scroll-behavior: auto.*?</style>\s*",
        "",
        text,
    )

    if re.search(r"charset=", text, re.I) is None:
        text = re.sub(
            r"(?i)<HEAD>",
            '<HEAD>\n<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">',
            text,
            count=1,
        )

    names = [int(m.group(1)) for m in re.finditer(r'(?i)<A NAME\s*=\s*"Index(\d+)"', text)]
    names = sorted(set(names)) or list(range(0, 10))

    # toujours (ré)injecter CSS+JS
    if "function goSection" not in text:
        text = re.sub(r"(?i)</HEAD>", lambda _m: CSS + JS + "\n</HEAD>", text, count=1)

    def repl_anchor(m: re.Match) -> str:
        n = m.group(1)
        # ancre visible pour Wine + id
        return (
            f'</div>\n'
            f'<div class="section" id="sec{n}">\n'
            f'<a name="Index{n}" id="Index{n}" class="jumpmark">&nbsp;</a>\n'
            f'<a name="index{n}" id="index{n}"></a>\n'
            f'<span class="jumpmark" id="mark{n}"></span>\n'
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
    text = decode(path.read_bytes())
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
