#!/usr/bin/env python3
"""Lecteur Horoscope intégré (GTK) — remplace le TWebBrowser Wine cassé.

Wine écrit souvent un temp.htm VIDE (titre = chemin .rtf, body vide).
On lit donc temp.rtf en priorité, sinon temp.htm.
"""
from __future__ import annotations

import html as htmlmod
import os
import re
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango  # noqa: E402

ROOT = Path.home() / "Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope"
POLL_MS = 500


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
    text = re.sub(
        r"(?im)^(System|Tahoma|Arial|Lucida Handwriting);?\s*$", "", text
    )
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def html_to_text(raw: bytes) -> str:
    raw = raw.replace(b"\x00", b"")
    m = re.search(br"charset=([a-zA-Z0-9_-]+)", raw, re.I)
    cs = (m.group(1).decode() if m else "cp1252").lower().replace(
        "windows-1252", "cp1252"
    )
    if cs in ("utf-8", "utf8"):
        text = raw.decode("utf-8", errors="replace")
    else:
        text = raw.decode("cp1252", errors="replace")
    body = re.search(r"(?is)<body[^>]*>(.*)</body>", text)
    chunk = body.group(1) if body else text
    chunk = re.sub(r"(?is)<br\s*/?>", "\n", chunk)
    chunk = re.sub(r"(?is)</p\s*>", "\n\n", chunk)
    chunk = re.sub(r"(?is)<[^>]+>", "", chunk)
    chunk = htmlmod.unescape(chunk)
    return re.sub(r"\n{3,}", "\n\n", chunk).strip()


def newest_pair() -> tuple[Path | None, Path | None]:
    """Return (rtf, htm) for the most recently touched sign folder."""
    best_m = 0.0
    best: tuple[Path | None, Path | None] = (None, None)
    for d in ROOT.glob("*/Res_Txt"):
        rtf = d / "temp.rtf"
        htm = d / "temp.htm"
        times = []
        if rtf.is_file():
            times.append(rtf.stat().st_mtime)
        if htm.is_file():
            times.append(htm.stat().st_mtime)
        if not times:
            continue
        m = max(times)
        if m >= best_m:
            best_m = m
            best = (rtf if rtf.is_file() else None, htm if htm.is_file() else None)
    return best


def load_text() -> tuple[str, str]:
    rtf, htm = newest_pair()
    label = "Horoscope"
    if rtf:
        label = rtf.parent.parent.name
        plain = rtf_to_text(rtf.read_text("latin-1", errors="replace"))
        if len(plain) >= 20:
            return label, plain
    if htm:
        label = htm.parent.parent.name
        plain = html_to_text(htm.read_bytes())
        if len(plain) >= 20:
            return label, plain
    return label, (
        "En attente du texte Horoscope…\n"
        "Clique Horoscope dans le menu Wine, puis une rubrique."
    )


class Viewer(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="Horoscope — OREAC")
        self.set_default_size(860, 640)
        self.set_position(Gtk.WindowPosition.CENTER)
        self._stamp = ""

        css = Gtk.CssProvider()
        css.load_from_data(
            b"""
            window, box, scrolledwindow, textview, textview text {
              background-color: #0E3A6E;
              color: #FFFFFF;
            }
            """
        )
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.buf = Gtk.TextBuffer()
        self.view = Gtk.TextView(buffer=self.buf)
        self.view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.view.set_editable(False)
        self.view.set_cursor_visible(False)
        self.view.set_left_margin(18)
        self.view.set_right_margin(18)
        self.view.set_top_margin(14)
        self.view.set_bottom_margin(14)
        try:
            self.view.override_font(Pango.FontDescription("Arial 13"))
        except Exception:
            pass

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.view)
        self.add(scroll)
        self.connect("destroy", Gtk.main_quit)

        GLib.timeout_add(POLL_MS, self._tick)
        self._tick()

    def _tick(self) -> bool:
        rtf, htm = newest_pair()
        stamp = ""
        for p in (rtf, htm):
            if p and p.is_file():
                stamp += f"{p}:{p.stat().st_mtime};"
        if stamp == self._stamp and self._stamp:
            return True
        self._stamp = stamp
        label, plain = load_text()
        self.set_title(f"Horoscope — {label}")
        self.buf.set_text(plain)
        return True


def main() -> int:
    os.environ.setdefault("DISPLAY", ":0")
    win = Viewer()
    win.show_all()
    win.present()
    win.resize(860, 640)
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
