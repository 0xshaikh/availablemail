"""Flask web app for availablemail.

Serves the static demo UI and a JSON API that calls the availablemail
Python package. Runs anywhere a Python 3.10+ environment will.
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from availablemail.checker import check_all
from availablemail.generator import GROUPS, PROVIDERS, generate_candidates

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

BASE = Path(__file__).resolve().parent
REPO = BASE.parent  # repo root (where docs/ and assets/ live)
DOCS = REPO / "docs" / "demo"
STATIC = REPO / "assets"

app = Flask(
    __name__,
    static_folder=str(REPO / "static"),
    static_url_path="/static",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_payload(payload: dict) -> dict:
    """Normalise a request payload to generator kwargs."""
    first = str(payload.get("first_name") or payload.get("first") or "").strip()
    last = str(payload.get("last_name") or payload.get("last") or "").strip()
    provider = str(payload.get("provider") or "all").strip() or "all"
    limit = int(payload.get("limit") or 50)
    suffixes = payload.get("suffixes") or None
    if isinstance(suffixes, str):
        suffixes = [s.strip().lower() for s in suffixes.split(",") if s.strip()]
    elif suffixes is not None and not isinstance(suffixes, list):
        suffixes = None
    max_digits = int(payload.get("max_digits", 3))
    check_mode = payload.get("check") or "heuristic"

    if not first:
        raise ValueError("first_name is required")
    return {
        "first_name": first,
        "last_name": last,
        "provider": provider,
        "limit": max(1, min(limit, 500)),
        "suffixes": suffixes,
        "max_digits": max(0, max_digits),
        "check_mode": check_mode,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def index():
    """Serve the demo UI (the same HTML that ships on GitHub Pages)."""
    demo_path = DOCS / "index.html"
    if demo_path.exists():
        return send_from_directory(str(DOCS), "index.html")
    return (
        "availablemail webapp — docs/demo/index.html not found. "
        "Serve it externally or check out the repo root.",
        404,
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok", "version": "0.1.0"})


@app.get("/api/patterns")
def api_patterns():
    """List providers, groups, and pattern templates."""
    return jsonify(
        {
            "providers": PROVIDERS,
            "groups": GROUPS,
            "notes": {
                "default_suffixes": [
                    "dev",
                    "hello",
                    "founder",
                    "io",
                    "codes",
                    "works",
                    "build",
                    "digital",
                    "ai",
                    "in",
                    "tech",
                    "hub",
                    "official",
                ],
                "digit_seeds": [
                    "1",
                    "2",
                    "3",
                    "7",
                    "9",
                    "10",
                    "12",
                    "17",
                    "23",
                    "24",
                    "123",
                    "1234",
                ],
                "check_modes": ["heuristic", "microsoft", "smtp"],
            },
        }
    )


@app.get("/api/providers")
def api_providers():
    return jsonify({"providers": PROVIDERS, "groups": GROUPS})


@app.post("/api/search")
def api_search():
    """Accept a name + options, return ranked candidates."""
    started = time.perf_counter()
    try:
        payload = request.get_json(silent=True) or {}
    except Exception:
        payload = {}
    try:
        args = _parse_payload(payload)
    except ValueError as e:
        return jsonify({"error": str(e), "ok": False}), 400

    try:
        candidates = generate_candidates(
            first_name=args["first_name"],
            last_name=args["last_name"],
            providers=args["provider"],
            suffixes=args["suffixes"],
            max_digits=args["max_digits"],
            limit=args["limit"],
        )
        checks = check_all(candidates, mode=args["check_mode"])
    except Exception as e:  # pragma: no cover — surfaced as JSON
        return jsonify({"error": f"generation failed: {e}", "ok": False}), 500

    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

    results = []
    for c, r in zip(candidates, checks, strict=True):
        results.append(
            {
                "candidate": asdict(c),
                "check": asdict(r),
            }
        )

    return jsonify(
        {
            "ok": True,
            "count": len(results),
            "elapsed_ms": elapsed_ms,
            "results": results,
        }
    )


# Serve the assets (screenshots) too
@app.get("/assets/<path:name>")
def assets(name):
    return send_from_directory(str(STATIC), name)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    port = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
