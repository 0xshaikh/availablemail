"""Tests for the CLI entry point."""

from availablemail.cli import main


def test_version():
    try:
        main(["--version"])
    except SystemExit as e:
        assert e.code == 0
    else:
        raise AssertionError("expected SystemExit")
