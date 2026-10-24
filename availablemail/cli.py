"""CLI entry point."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .checker import check_all
from .generator import PROVIDERS, generate_candidates


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="availablemail",
        description="Find a professional email address from your name + a few keywords.",
        epilog=(
            "Examples:\n"
            "  availablemail find anas shaikh\n"
            "  availablemail find anas --provider google --limit 20\n"
            "  availablemail find anas --provider all --suffixes dev,hello,founder\n"
            "  availablemail list-providers\n"
            "  availablemail find anas --provider microsoft --check microsoft\n"
            "  availablemail find anas --format json --limit 10 > out.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version", version=f"availablemail {__version__}")

    sub = p.add_subparsers(dest="command", required=True, metavar="COMMAND")

    # ---- find -------------------------------------------------------------
    f = sub.add_parser(
        "find",
        help="generate candidate email addresses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Generate and score candidate email addresses.",
    )
    f.add_argument("first", nargs="?", help="first name or brand name (also positional)")
    f.add_argument("last", nargs="?", default="", help="last name (optional)")
    f.add_argument(
        "--provider",
        default="all",
        help="provider group (all|google|microsoft|yahoo|proton|aol) "
        "or a domain like gmail.com (default: all)",
    )
    f.add_argument(
        "--suffixes", default=None, help="comma-separated extra suffixes (dev,hello,founder,...)"
    )
    f.add_argument(
        "--max-digits",
        type=int,
        default=3,
        help="how many digit-seeds to try (0 disables, default: 3)",
    )
    f.add_argument("--limit", type=int, default=50, help="max candidates to show (default: 50)")
    f.add_argument(
        "--format",
        default="table",
        choices=["table", "json", "csv"],
        help="output format (default: table)",
    )
    f.add_argument(
        "--check",
        default="heuristic",
        choices=["heuristic", "microsoft", "smtp"],
        help="availability check mode (default: heuristic). "
        "'microsoft' calls the real Microsoft signup API for "
        "outlook/hotmail/live/msn only. Most other providers "
        "are catch-all and only confirmable at signup.",
    )
    f.add_argument(
        "--out", default=None, help="write full output to a file (in addition to stdout)"
    )

    # Also support a top-level "first [last]" shortcut (handled in main())
    sub.add_parser(
        "list-providers",
        help="list supported email providers",
    )
    return p


def _run_find(args: argparse.Namespace) -> int:
    if not args.first:
        print("error: first name is required", file=sys.stderr)
        return 2

    suffixes = None
    if args.suffixes:
        suffixes = [s.strip().lower() for s in args.suffixes.split(",") if s.strip()]

    # When the user supplies suffixes, they want them — bump the internal
    # candidate pool generously so suffix variants aren't squeezed out.
    generate_pool = args.limit * 8 if suffixes else args.limit * 4
    candidates = generate_candidates(
        first_name=args.first,
        last_name=args.last or "",
        providers=args.provider,
        suffixes=suffixes,
        max_digits=args.max_digits,
        limit=generate_pool,
    )

    # Trim to limit after scoring
    candidates = candidates[: args.limit]

    results = check_all(candidates, mode=args.check)  # type: ignore[arg-type]

    pairs = list(zip(candidates, results, strict=True))

    output_text = _format(pairs, args.format, check_mode=args.check)
    print(output_text)
    if args.out:
        Path(args.out).write_text(output_text, encoding="utf-8")
        print(f"\\nWrote {args.out}", file=sys.stderr)

    # Exit codes: 0 always (this tool never 'fails', it just reports)
    return 0


def _format(pairs, fmt: str, check_mode: str) -> str:
    if fmt == "json":
        return json.dumps(
            [{"candidate": asdict(c), "check": asdict(r)} for c, r in pairs],
            indent=2,
            ensure_ascii=False,
        )
    if fmt == "csv":
        rows = []
        for c, r in pairs:
            rows.append(
                {
                    "address": c.address,
                    "score": c.score,
                    "pattern": c.pattern,
                    "provider": PROVIDERS.get(c.domain, c.domain),
                    "available": r.available if r.available is not None else "",
                    "reason": r.reason,
                }
            )
        buf = Path("_buf.csv")
        with buf.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(
                fh, fieldnames=["address", "score", "pattern", "provider", "available", "reason"]
            )
            w.writeheader()
            w.writerows(rows)
        text = buf.read_text(encoding="utf-8")
        buf.unlink(missing_ok=True)
        return text

    # ---- table (default) --------------------------------------------------
    lines: list[str] = []
    header = f"{'#':>3}  {'Score':>5}  Address"
    lines.append(header)
    lines.append("-" * len(header))
    for i, (c, r) in enumerate(pairs, 1):
        marker = ""
        if check_mode != "heuristic" and r.available is True:
            marker = "  ← AVAILABLE"
        lines.append(f"{i:>3}  {c.score:>5}  {c.address}{marker}")
    return "\n".join(lines)


def _run_list_providers(_args: argparse.Namespace) -> int:
    print("All providers:")
    for domain, name in PROVIDERS.items():
        print(f"  {domain:<20} {name}")
    print("\nGroups:")
    for group, domains in [
        ("all", list(PROVIDERS.keys())),
        ("google", ["gmail.com"]),
        ("microsoft", ["hotmail.com", "outlook.com", "live.com"]),
        ("yahoo", ["yahoo.com"]),
        ("proton", ["protonmail.com", "proton.me"]),
        ("aol", ["aol.com"]),
    ]:
        print(f"  {group:<12} {', '.join(domains)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()

    if argv is None:
        argv = sys.argv[1:]

    # Handle --version / -h first (argparse errors before we get here otherwise)
    if argv and argv[0] in ("--version", "-h", "--help"):
        try:
            args = parser.parse_args(argv)
        except SystemExit:
            raise
        return 0

    # Handle the "first [last]" shortcut (no command)
    if argv and argv[0] not in ("find", "list-providers"):
        first = argv[0]
        rest = argv[1:]
        args = parser.parse_args(["find", first, *rest])
        return _run_find(args)

    args = parser.parse_args(argv)
    if args.command == "find":
        return _run_find(args)
    if args.command == "list-providers":
        return _run_list_providers(args)
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
