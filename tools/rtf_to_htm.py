#!/usr/bin/env python3
"""Convert Wine/Delphi temp.rtf → temp.htm in the SAME format as Signe.htm
(so TWebBrowser/Gecko inside the app can render it — no external browser)."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def rtf_to_text(rtf: str) -> str:
    def hex_escape(m: re.Match) -> str:
        try:
            return bytes([int(m.group(1), 16)]).decode("cp1252", errors="replace")
        except Exception:
            return ""

    text = re.sub(r"\{\\fonttbl.*?\}", "", rtf, flags=re.S)
    text = re.sub(r"\{\\colortbl.*?\}", "", text, flags=re.S)
    text = re.sub(r"\{\\\*\\generator.*?\}", "", text, flags=re.S)
    text = re.sub(r"\\'([0-9a-fA-F]{2})", hex_escape, text)
    text = text.replace("\\par", "\n").replace("\\tab", "\t")
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)
    text = text.replace("{", "").replace("}", "").replace("\\", "")
    # drop leftover font names spilled by broken RTF
    text = re.sub(r"(?im)^(System|Tahoma|Arial|Lucida Handwriting);?\s*$", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def build_delphi_html(plain: str) -> bytes:
    """Match Res_Txt/Signe.htm / HoroscopeJour.htm (Wine Gecko OK)."""
    parts: list[str] = []
    for line in plain.splitlines():
        line = line.strip()
        if not line:
            parts.append("<BR>")
            continue
        esc = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        # titres RTF souvent en gras / centrés : détecte lignes courtes type aspect
        if len(line) < 90 and re.search(
            r"(conflit|bon rapport|disharmonie|passe sur|brouill)", line, re.I
        ):
            parts.append(f"<B><FONT FACE=\"Arial\">{esc}</FONT></B><BR>")
        else:
            parts.append(f'<FONT FACE="Arial">{esc}</FONT><BR>')
    html = (
        "<HTML>\r\n"
        '<BODY> <LINK rel=stylesheet type="text/css" href="html_uni.css"> </BODY>\r\n'
        '<BODY TEXT="#FFFFFF" BGCOLOR="#0E3A6E" '
        'LINK="#3333FF" VLINK="#999999" ALINK="#FF0000">\r\n'
        + "\r\n".join(parts)
        + "\r\n</BODY>\r\n</HTML>\r\n"
    )
    return html.encode("cp1252", errors="replace")


def body_is_empty(htm: str) -> bool:
    # Wine génère souvent: <TITLE>Z:\...\temp.rtf</TITLE><BODY></BODY>
    m = re.search(r"(?is)<BODY[^>]*>(.*)</BODY>", htm)
    if not m:
        return True
    inner = re.sub(r"(?is)<[^>]+>", "", m.group(1))
    inner = re.sub(r"\s+", "", inner)
    if len(inner) < 20:
        return True
    # titre = chemin fichier = export raté
    if re.search(r"(?is)<TITLE>\s*[A-Z]:\\.*temp\.rtf\s*</TITLE>", htm):
        return True
    return False


def fix_pair(rtf_path: Path) -> bool:
    htm_path = rtf_path.with_name("temp.htm")
    if not rtf_path.is_file():
        return False
    plain = rtf_to_text(rtf_path.read_text("latin-1", errors="replace"))
    if len(plain) < 10:
        return False

    # Toujours réécrire au format Delphi (même si un HTML UTF-8/LibreOffice existe)
    # dès que le RTF est plus récent ou que le HTML est vide / mauvais format.
    need = True
    if htm_path.exists():
        htm = htm_path.read_bytes().replace(b"\x00", b"").decode("cp1252", errors="replace")
        good_fmt = 'href="html_uni.css"' in htm and "FONT FACE" in htm
        if good_fmt and not body_is_empty(htm):
            # saute si RTF pas plus neuf
            if rtf_path.stat().st_mtime <= htm_path.stat().st_mtime + 0.05:
                need = False
    if not need:
        return False

    data = build_delphi_html(plain)
    htm_path.write_bytes(data.replace(b"\x00", b""))
    print("fixed", htm_path, "bytes", len(data))
    return True


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--libreoffice"]
    paths: list[Path] = []
    if args:
        for a in args:
            p = Path(a)
            if p.is_dir():
                paths.extend(p.glob("*/Res_Txt/temp.rtf"))
                paths.extend(p.glob("Res_Txt/temp.rtf"))
            else:
                paths.append(p)
    else:
        root = Path.home() / "Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope"
        paths = list(root.glob("*/Res_Txt/temp.rtf"))
    n = sum(1 for p in paths if fix_pair(p))
    print("updated", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
