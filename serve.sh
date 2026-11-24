#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${PORT:-8766}"
echo "http://127.0.0.1:${PORT}/astro-wine-remaster/viewer/"
echo "Portrait: http://127.0.0.1:${PORT}/astro-wine-remaster/viewer/portrait.html"
exec python3 -m http.server "$PORT"
