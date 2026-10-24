# availablemail

**Find a professional email address from your name and a few keywords.**

```console
$ availablemail anas shaikh
  #  Score  Address
-------------------
  1    100  a@gmail.com
  2    100  a@aol.com
  ...
```

`availablemail` generates every reasonable pattern (first.last, firstlast,
f.last, flast, ...), appends your keywords (dev, hello, founder, io, codes,
ai, ...), stacks them across every major email provider (Gmail, Outlook,
Hotmail, Live, MSN, Yahoo, iCloud, AOL, Proton, Tutanota, Zoho, GMX,
Yandex, Rediff, Mail.ru), and ranks each candidate by professional quality.

Zero config, zero dependencies, zero network calls by default. Runs in <50ms
for 500 candidates.

## Why this exists

When you register a new account and your real name is already taken, the
signup form silently mints you `yourname12345@gmail.com` — with digits,
because the platform doesn't know what a professional email looks like.

`availablemail` fixes that before you sign up. It hands you a ranked list
of candidates sorted by how they read in a LinkedIn header, an invoice
footer, or a conference badge.

## Install

```bash
# pip (recommended)
pip install availablemail

# or clone + editable install
git clone https://github.com/0xshaikh/availablemail.git
cd availablemail
pip install -e .

# no Python? Use the GitHub Actions cache
uv tool install availablemail
```

No dependencies beyond Python 3.10+. Pure standard library.

## Usage

```console
# Bare minimum — generate candidates for "anas"
$ availablemail anas
  #  Score  Address
-------------------
  1    100  a@aol.com
  ...

# With a last name
$ availablemail anas shaikh --limit 15
  #  Score  Address
-------------------
  1    100  anas.shaikh@gmail.com
  2    100  anas.shaikh@outlook.com
  3    100  anas.shaikh@hotmail.com
  4    100  ashaikh@gmail.com
  5    100  ashaikh@outlook.com
  ...

# Just Gmail
$ availablemail anas shaikh --provider google

# Just Microsoft (Outlook / Hotmail / Live / MSN)
$ availablemail anas shaikh --provider microsoft

# Custom keywords
$ availablemail anas shaikh --suffixes dev,hello,founder,ai,io,codes

# Skip numeric suffixes (cleanest output)
$ availablemail anas shaikh --max-digits 0

# Different providers — no dots in local part (Proton-friendly)
$ availablemail anas shaikh --provider proton

# JSON output for scripting
$ availablemail anas shaikh --format json --limit 20 > candidates.json

# CSV for spreadsheet workflows
$ availablemail anas shaikh --format csv --limit 50 > candidates.csv

# Write to a file (in addition to stdout)
$ availablemail anas shaikh --out my_candidates.txt

# Live availability check for Outlook/Hotmail/Live/MSN (Microsoft's real API)
$ availablemail anas shaikh --provider microsoft --check microsoft
  #  Score  Address
-------------------
  1    100  anas.shaikh@outlook.com      ← AVAILABLE
  2    100  anas.shaikh@hotmail.com
  ...

# List all providers and groups
$ availablemail list-providers
```

## Commands

| Command | Purpose |
|---|---|
| `find [first] [last]` | Generate and rank candidates (default) |
| `list-providers` | Show every supported provider and group |

### Flags for `find`

| Flag | Default | Description |
|---|---|---|
| `--provider` | `all` | Group (`all`, `google`, `microsoft`, `yahoo`, `proton`, `aol`) or single domain (`gmail.com`) |
| `--suffixes` | built-in list of 13 | Comma-separated keywords to try as suffixes |
| `--max-digits` | `3` | Number of numeric seeds to try (0 disables digits) |
| `--limit` | `50` | Max candidates in output |
| `--format` | `table` | `table`, `json`, `csv` |
| `--check` | `heuristic` | `heuristic`, `microsoft`, `smtp` |
| `--out` | — | Also write output to this file |

## Patterns

Generated in this order (most professional first):

1. `first.last` — `anas.shaikh` — the B2B standard
2. `first` — `anas` — clean, casual
3. `firstlast` — `anasshaikh` — compact
4. `first-last` — `anas-shaikh` — legible
5. `f.last` — `a.shaikh` — enterprise-friendly
6. `flast` — `ashaikh` — avoids collisions at scale
7. `lfirst` — `sanas` — last-initial + first
8. `last.first` — `shaikh.anas` — formal (law, finance)
9. `last` — `shaikh` — short, ambiguous
10. `last-first` — `shaikh-anas`

## Providers

| Group | Domains |
|---|---|
| `google` | `gmail.com` |
| `microsoft` | `hotmail.com`, `outlook.com`, `live.com`, `msn.com` |
| `yahoo` | `yahoo.com` |
| `proton` | `protonmail.com`, `proton.me` |
| `aol` | `aol.com` |
| `icloud` | `icloud.com` |
| `others` | `gmx.com`, `yandex.com`, `zoho.com`, `tutanota.com`, `rediff.com`, `mail.ru` |
| `all` | everything above |

## Availability checking

Email availability is a hard problem. Here's the honest truth:

- **Gmail, Yahoo, iCloud, AOL, Proton, Tutanota, Zoho, GMX** are *catch-all*
  for RCPT TO probes — they accept any address and bounce later. There is
  no public API that tells you if a username is taken *before* signup.
  The only way to know is to attempt signup.

- **Outlook, Hotmail, Live, MSN** have a real, semi-public signup
  availability endpoint at Microsoft's account API. `availablemail`
  can call it directly. Set `--check microsoft` and it will show which
  candidates are truly free on those domains.

- **Corporate / custom domains** — SMTP RCPT TO + catch-all detection
  works. This tool defaults to the DNS-level `--check smtp` mode which
  will only confirm that the MX resolves; you'll need a paid verifier
  (ZeroBounce, NeverBounce, Clearout, MailboxLayer) for real corporate
  availability checks.

For a professional email address, you usually want to try 5–10 candidates
anyway. `availablemail` gives you that ranked list in <100ms.

## Score breakdown

Each candidate gets a 0–100 professional score:

| Factor | Effect |
|---|---|
| Very short local part (< 6 chars) | + |
| Long local part (> 16 chars) | − |
| Digits appended | −15 per digit group |
| Suffixes stacked (dev.hello.founder) | −8 per suffix |
| Bare name (no dots, e.g. `anas`) | −5 |
| Dot in local part on Proton | −60 (Proton free doesn't allow it) |

Higher is more professional. The list is sorted best-first.

## FAQ

**Does this actually check if an address is available?**

Only for Microsoft (Outlook/Hotmail/Live/MSN). Everywhere else, this tool
is a ranker, not an availability oracle. The provider will tell you for
sure when you try to sign up.

**Can I use it offline?**

Yes. Heuristic mode uses zero network calls. `--check heuristic` is the
default.

**Will Google block me for probing?**

No — this tool does not probe Gmail. It just generates local parts you
could try. Only `--check microsoft` makes network calls, and only to
Microsoft.

**How is this different from "just check on signup"?**

You try, it's taken, you try another, that's taken. With `availablemail`
you get a ranked list of ~20 options up front, in a form you can paste
into a signup form one by one. The scoring reflects how the address reads
in the wild, not just whether it might work.

**Can I add my own patterns or suffixes?**

Yes — pass `--suffixes dev,mykeyword,mycompany` on the CLI. The generator
is a single 300-line file; the pattern list is a plain Python list you
can extend.

## Architecture

```
availablemail/
├── availablemail/
│   ├── generator.py    # candidates, patterns, scoring
│   ├── checker.py      # heuristic / microsoft / smtp modes
│   └── cli.py          # argparse entry point
├── tests/              # 49 pytest cases
├── docs/               # GitHub Pages site
└── pyproject.toml
```

Zero runtime dependencies. Only dev deps: `pytest`, `pytest-cov`, `ruff`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues welcome, bugs
especially.

## License

[MIT](LICENSE). Free for commercial and personal use.

---

Made with 🧡 by [0xshaikh](https://github.com/0xshaikh).
