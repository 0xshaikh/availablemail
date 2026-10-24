# Changelog

## 0.1.0 — 2026-10-24

Initial release.

### Added

- `availablemail find` — generate and rank candidate email addresses
- `availablemail list-providers` — show all supported providers
- 10 naming patterns (first.last, first, firstlast, first-last, f.last, flast, lfirst, last.first, last, last-first)
- 14 email providers across 6 groups (google, microsoft, yahoo, proton, aol, others)
- 13 default suffixes (dev, hello, founder, io, codes, works, build, digital, ai, in, tech, hub, official)
- Three check modes:
  - `heuristic` (default, zero network)
  - `microsoft` (real Outlook/Hotmail/Live/MSN availability via Microsoft's public API)
  - `smtp` (coarse MX reachability)
- Four output formats: `table`, `json`, `csv`, file
- Professional 0–100 scoring (length, digit penalty, suffix penalty, pattern weight, Proton dot penalty)
- 49 pytest tests, MIT license, zero runtime dependencies
