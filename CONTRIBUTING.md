# Contributing

Thanks for considering a contribution. `availablemail` is small and
kept simple on purpose — the goal is a single-file CLI that just works.

## Ways to help

- Report a bug (see [bug template](.github/ISSUE_TEMPLATE/bug_report.md))
- Suggest a pattern or suffix that should be added
- Contribute a test that documents current behaviour
- Fix a typo

## Dev setup

```bash
python 3.10+
pip install -e ".[dev]"
pytest
ruff check .
```

## Style

- Python 3.10+, type hints everywhere
- ruff lint + format (config in `pyproject.toml`)
- No runtime dependencies. Standard library only.
- Tests in `tests/`, one file per module

## What not to add

- Third-party runtime deps. The whole point is that `pip install`
  is a single package with zero transitive deps.
- Network calls in the default path. Heuristic mode must never touch
  the internet.
- Non-ASCII output. The CLI needs to work in every terminal.

## PR checklist

- [ ] `ruff check .` clean
- [ ] `ruff format --check .` clean
- [ ] `pytest` all pass
- [ ] New behaviour is covered by at least one test
- [ ] README updated if user-facing
