#!/usr/bin/env bash
# Run the availablemail Flask app locally with a public port forward.
#
# Prereqs:
#   - cloudflared (https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
#   OR a Python 3.10+ environment.
#
# Usage: bash deploy/local.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2
  exit 1
fi

# Set up venv once
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e . -r webapp/requirements.txt

PORT="${PORT:-5000}"

echo ""
echo "─── availablemail Flask app ───"
echo "Local:  http://localhost:${PORT}"
echo "Health: http://localhost:${PORT}/health"
echo ""

if command -v cloudflared >/dev/null 2>&1; then
  echo "Public tunnel (temporary, no account required):"
  cloudflared tunnel --url "http://localhost:${PORT}" 2>&1 | grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1 | xargs -I{} echo "  {}" || true
  echo "(waiting for tunnel URL above...)"
fi

exec flask --app webapp.app run --host 0.0.0.0 --port "${PORT}"
