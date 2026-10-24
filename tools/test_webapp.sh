#!/usr/bin/env bash
# Test the availablemail Flask webapp end-to-end.
set -u
cd "$(dirname "$0")/.."
. .venv/bin/activate

flask --app webapp.app run --host 127.0.0.1 --port 5000 > /tmp/flask.log 2>&1 &
FLASK_PID=$!

# Wait for readiness
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:5000/health > /dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

echo "=== /health ==="
curl -s http://127.0.0.1:5000/health
echo ""

echo "=== /api/patterns (truncated) ==="
curl -s http://127.0.0.1:5000/api/patterns | python3 -c "import json,sys; d=json.load(sys.stdin); print('providers:', len(d['providers'])); print('groups:', list(d['groups'].keys()))"

echo "=== /api/search basic (gmail, limit 5) ==="
curl -s -X POST http://127.0.0.1:5000/api/search -H 'Content-Type: application/json' -d '{"first_name":"Anas","last_name":"Shaikh","provider":"gmail.com","limit":5}' | python3 -m json.tool | head -40

echo "=== /api/search all providers with suffixes (limit 3) ==="
curl -s -X POST http://127.0.0.1:5000/api/search -H 'Content-Type: application/json' -d '{"first_name":"Anas","last_name":"Shaikh","provider":"all","limit":3,"suffixes":"dev,hello,founder"}' | python3 -c "import json,sys; d=json.load(sys.stdin); print('ok:', d['ok']); print('count:', d['count']); print('elapsed_ms:', d['elapsed_ms']); [print(' -', r['candidate']['address'], r['candidate']['score'], r['candidate']['pattern']) for r in d['results']]"

echo "=== /api/search error (missing first_name) ==="
curl -s -X POST http://127.0.0.1:5000/api/search -H 'Content-Type: application/json' -d '{}'

echo ""
echo "=== / (static index, first 120 bytes) ==="
curl -s http://127.0.0.1:5000/ | head -c 120
echo ""

echo "=== /assets/find_google_demo.png (HEAD) ==="
curl -sI http://127.0.0.1:5000/assets/find_google_demo.png | head -3

kill $FLASK_PID 2>/dev/null
wait $FLASK_PID 2>/dev/null
echo "=== DONE ==="
