#!/usr/bin/env python3
"""Export portrait astral HTML to a clean PDF (Chromium headless, fallback WeasyPrint)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "Documents/Astrologie/windows-apps/AstroHoroscope/Astrologie/res"


def main() -> int:
    html = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "temp-utf8.html"
    if not html.is_file():
        # build from temp.htm
        fix = Path(__file__).with_name("fix_temp_htm.py")
        subprocess.check_call([sys.executable, str(fix), str(ROOT / "temp.htm")])
        html = ROOT / "temp-utf8.html"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "portrait.pdf"

    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if chrome:
        cmd = [
            chrome,
            "--headless",
            "--disable-gpu",
            f"--print-to-pdf={out}",
            "--no-pdf-header-footer",
            html.resolve().as_uri(),
        ]
        print("run", " ".join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and out.is_file() and out.stat().st_size > 1000:
            print("PDF OK", out, out.stat().st_size, "bytes")
            return 0
        print("chromium failed", r.returncode, r.stderr[-500:], file=sys.stderr)

    # WeasyPrint fallback
    try:
        from weasyprint import HTML

        HTML(filename=str(html)).write_pdf(str(out))
        print("PDF OK (weasyprint)", out, out.stat().st_size, "bytes")
        return 0
    except Exception as e:
        print("weasyprint failed", e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
