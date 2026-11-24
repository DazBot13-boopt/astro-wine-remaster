#!/usr/bin/env python3
"""Convert Wine/Delphi temp.rtf → temp.htm when WebBrowser HTML export is empty."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def rtf_to_text_fallback(rtf: str) -> str:
    def hex_escape(m: re.Match) -> str:
        try:
            return bytes([int(m.group(1), 16)]).decode("cp1252", errors="replace")
        except Exception:
            return ""

    # drop font/color tables
    text = re.sub(r"\{\\fonttbl.*?\}", "", rtf, flags=re.S)
    text = re.sub(r"\{\\colortbl.*?\}", "", text, flags=re.S)
    text = re.sub(r"\{\\\*\\generator.*?\}", "", text, flags=re.S)
    text = re.sub(r"\\'([0-9a-fA-F]{2})", hex_escape, text)
    text = text.replace("\\par", "\n").replace("\\tab", "\t")
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)
    text = text.replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def build_html_from_text(plain: str, css: str) -> bytes:
    parts = []
    for line in plain.splitlines():
        line = line.strip()
        if not line:
            parts.append("<BR>")
            continue
        esc = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts.append(f"<P>{esc}</P>")
    html = (
        "<HTML>\r\n<HEAD>\r\n"
        '<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">\r\n'
        f'<LINK rel=stylesheet type="text/css" href="{css}">\r\n'
        "<TITLE>Horoscope</TITLE>\r\n</HEAD>\r\n"
        '<BODY TEXT="#000000" BGCOLOR="#FFFFFF">\r\n'
        + "\r\n".join(parts)
        + "\r\n</BODY>\r\n</HTML>\r\n"
    )
    return html.encode("cp1252", errors="replace")


def libreoffice_html(rtf_path: Path) -> bytes | None:
    if not shutil.which("libreoffice"):
        return None
    with tempfile.TemporaryDirectory(prefix="astro-rtf-") as td:
        try:
            subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "html:HTML",
                    "--outdir",
                    td,
                    str(rtf_path),
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except Exception:
            return None
        outs = list(Path(td).glob("*.html"))
        if not outs:
            return None
        raw = outs[0].read_text("utf-8", errors="replace")
        # keep body, force light page + css
        m = re.search(r"(?is)<body[^>]*>(.*)</body>", raw)
        body = m.group(1) if m else raw
        css = "html_uni.css"
        if not (rtf_path.parent / css).exists():
            css = "html_journalier.css"
        html = (
            "<HTML>\r\n<HEAD>\r\n"
            '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\r\n'
            f'<LINK rel=stylesheet type="text/css" href="{css}">\r\n'
            "<TITLE>Horoscope</TITLE>\r\n</HEAD>\r\n"
            '<BODY TEXT="#000000" BGCOLOR="#FFFFFF">\r\n'
            f"{body}\r\n</BODY>\r\n</HTML>\r\n"
        )
        return html.encode("utf-8", errors="replace")


def body_is_empty(htm: str) -> bool:
    m = re.search(r"(?is)<BODY[^>]*>(.*)</BODY>", htm)
    if not m:
        return True
    inner = re.sub(r"(?is)<[^>]+>", "", m.group(1))
    inner = re.sub(r"\s+", "", inner)
    return len(inner) < 20


def fix_pair(rtf_path: Path) -> bool:
    htm_path = rtf_path.with_name("temp.htm")
    if not rtf_path.is_file():
        return False
    htm = htm_path.read_text("cp1252", errors="replace") if htm_path.exists() else ""
    if htm and not body_is_empty(htm):
        return False

    data = libreoffice_html(rtf_path)
    if data is None:
        plain = rtf_to_text_fallback(rtf_path.read_text("latin-1", errors="replace"))
        if len(plain) < 10:
            return False
        css = "html_uni.css" if (rtf_path.parent / "html_uni.css").exists() else "html_journalier.css"
        data = build_html_from_text(plain, css)

    htm_path.write_bytes(data)
    print("fixed", htm_path, "bytes", len(data))
    return True


def main() -> int:
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    else:
        root = Path.home() / "Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope"
        paths = list(root.glob("*/Res_Txt/temp.rtf"))
    n = sum(1 for p in paths if fix_pair(p))
    print("updated", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
