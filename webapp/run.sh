#!/usr/bin/env bash
# One-shot local launch for the availablemail Flask app.
# Usage: bash webapp/run.sh  [port]
set -euo pipefail

PORT="${1:-${PORT:-5000}}"
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ] && command -v python3 >/dev/null 2>&1; then
  python3 -m venv .venv
  . .venv/bin/activate
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet -e . -r webapp/requirements.txt
else
  [ -d ".venv" ] && . .venv/bin/activate
fi

echo "availablemail webapp starting on http://localhost:${PORT}"
flask --app webapp.app run --host 0.0.0.0 --port "${PORT}"
