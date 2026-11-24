#!/usr/bin/env python3
"""Rename accented Horoscope folders to ASCII and patch launcher EXE paths."""
from __future__ import annotations
import shutil
from pathlib import Path

REPL = [
    (b"Horoscope\\01_B\xe9lier\\", b"Horoscope\\01_Belier\\"),
    (b"Horoscope\\03_G\xe9meaux\\", b"Horoscope\\03_Gemeaux\\"),
]
MAP = {"01_Bélier": "01_Belier", "03_Gémeaux": "03_Gemeaux"}

def main() -> int:
    root = Path.home() / "Documents/Astrologie/windows-apps/AstroHoroscope"
    horo = root / "Horoscope"
    exe = root / "Astrologie & Horoscope.exe"
    for src, dst in MAP.items():
        s, d = horo / src, horo / dst
        if s.is_symlink():
            s.unlink()
        if s.is_dir() and not d.exists():
            s.rename(d)
            print("renamed", src, "->", dst)
        if d.exists() and not (horo / src).exists():
            (horo / src).symlink_to(dst)
    if exe.exists():
        bak = exe.with_suffix(".exe.bak")
        if not bak.exists():
            shutil.copy2(exe, bak)
        data = bytearray(exe.read_bytes())
        for old, new in REPL:
            if old in data:
                data = data.replace(old, new)
                print("patched", old)
        exe.write_bytes(data)
    print("ok")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
