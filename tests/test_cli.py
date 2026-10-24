"""CLI smoke tests."""

import csv
import io
import json
from contextlib import redirect_stderr, redirect_stdout

from availablemail.cli import main


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class TestFind:
    def test_minimal(self):
        code, out, _ = _run(["find", "anas"])
        assert code == 0
        assert "anas" in out
        assert "@" in out

    def test_with_last(self):
        code, out, _ = _run(["find", "anas", "shaikh"])
        assert code == 0
        assert "shaikh" in out or "anas" in out

    def test_json_output(self):
        code, out, _ = _run(["find", "anas", "shaikh", "--format", "json", "--limit", "5"])
        assert code == 0
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) == 5
        assert "candidate" in data[0]
        assert "check" in data[0]

    def test_csv_output(self):
        code, out, _ = _run(["find", "anas", "shaikh", "--format", "csv", "--limit", "10"])
        assert code == 0
        rows = list(csv.DictReader(io.StringIO(out)))
        assert len(rows) == 10
        assert "address" in rows[0]
        assert "score" in rows[0]

    def test_provider_filter(self):
        code, out, _ = _run(["find", "anas", "--provider", "google", "--limit", "10"])
        assert code == 0
        address_lines = [line for line in out.splitlines() if "@" in line]
        assert address_lines, "expected at least one address"
        assert all("gmail.com" in line for line in address_lines)

    def test_suffixes(self):
        code, out, _ = _run(["find", "anas", "--suffixes", "dev,hello,founder", "--limit", "30"])
        assert code == 0
        assert ".dev" in out or ".hello" in out or ".founder" in out

    def test_missing_first(self):
        code, _, err = _run(["find"])
        assert code == 2
        assert "first name" in err

    def test_max_digits_zero(self):
        code, _, _ = _run(["find", "anas", "--max-digits", "0", "--limit", "30"])
        assert code == 0

    def test_limit(self):
        code, out, _ = _run(["find", "anas", "--limit", "3"])
        assert code == 0
        numbered = [line for line in out.splitlines() if line[:3].strip().isdigit()]
        assert len(numbered) == 3

    def test_shortcut_no_command(self):
        # 'availablemail anas shaikh' without 'find' subcommand
        code, out, _ = _run(["anas", "shaikh"])
        assert code == 0
        assert "anas" in out

    def test_out_file(self, tmp_path):
        target = tmp_path / "out.txt"
        code, _, err = _run(["find", "anas", "--out", str(target), "--limit", "5"])
        assert code == 0
        assert target.exists()
        assert "Wrote" in err


class TestListProviders:
    def test_basic(self):
        code, out, _ = _run(["list-providers"])
        assert code == 0
        assert "gmail.com" in out
        assert "hotmail.com" in out
        assert "Groups:" in out
