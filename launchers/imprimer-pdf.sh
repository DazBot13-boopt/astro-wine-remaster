#!/usr/bin/env bash
set -euo pipefail
# 1) PDF propre depuis le HTML (recommandé)
~/Documents/Astrologie/windows-apps/exporter-pdf.sh
# 2) dossier des impressions Wine/CUPS
xdg-open /var/tmp/astro-pdf >/dev/null 2>&1 || true
