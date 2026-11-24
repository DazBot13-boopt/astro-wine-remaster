#!/usr/bin/env python3
"""Lecteur Horoscope intégré (GTK) — remplace le TWebBrowser Wine cassé.

Fenêtre dédiée OREAC (pas Firefox/Chrome), style bleu d'origine.
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
POLL_MS = 700


def newest_htm() -> Path | None:
    cands = [p for p in ROOT.glob("*/Res_Txt/temp.htm") if p.is_file()]
    if not cands:
        return None
    cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0]


def html_to_text(path: Path) -> str:
    raw = path.read_bytes().replace(b"\x00", b"")
    m = re.search(br"charset=([a-zA-Z0-9_-]+)", raw, re.I)
    cs = (m.group(1).decode() if m else "cp1252").lower().replace("windows-1252", "cp1252")
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
    chunk = re.sub(r"[ \t]+\n", "\n", chunk)
    chunk = re.sub(r"\n{3,}", "\n\n", chunk)
    return chunk.strip()


class Viewer(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="Horoscope — OREAC")
        self.set_default_size(860, 640)
        self.set_position(Gtk.WindowPosition.CENTER)
        self._mtime = 0.0
        self._path: Path | None = None

        css = Gtk.CssProvider()
        css.load_from_data(
            b"""
            window, box, scrolledwindow, textview, textview text {
              background-color: #0E3A6E;
              color: #FFFFFF;
            }
            textview {
              font-family: Arial, Helvetica, sans-serif;
              font-size: 14pt;
              padding: 16px;
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
        self.view.override_font(Pango.FontDescription("Arial 13"))

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.view)
        self.add(scroll)
        self.connect("destroy", Gtk.main_quit)

        GLib.timeout_add(POLL_MS, self._tick)
        self._tick()

    def _tick(self) -> bool:
        p = newest_htm()
        if not p:
            if self._path is None:
                self.buf.set_text(
                    "En attente du Horoscope Wine…\n"
                    "Clique Horoscope dans le menu, choisis un signe."
                )
            return True
        try:
            mt = p.stat().st_mtime
        except OSError:
            return True
        if p == self._path and mt <= self._mtime:
            return True
        self._path = p
        self._mtime = mt
        try:
            plain = html_to_text(p)
            self.set_title(f"Horoscope — {p.parent.parent.name}")
            self.buf.set_text(plain if plain else "(texte vide)")
        except Exception as e:
            self.buf.set_text(f"Erreur: {e}")
        return True


def main() -> int:
    os.environ.setdefault("DISPLAY", ":0")
    win = Viewer()
    win.show_all()
    win.present()
    # force size (certains WM laissent 10x10)
    win.resize(860, 640)
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
