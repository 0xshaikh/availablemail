"""Tests for the checker."""

from availablemail.checker import (
    CheckResult,
    check_all,
    heuristic_check,
)
from availablemail.generator import Candidate


def _cand(address: str, score: int = 90) -> Candidate:
    local, domain = address.split("@")
    return Candidate(
        address=address,
        local=local,
        domain=domain,
        pattern="first.last",
        score=score,
        suffixes_used=0,
        digits_used=0,
    )


class TestHeuristic:
    def test_high_score(self):
        r = heuristic_check(_cand("anas.shaikh@gmail.com", score=95))
        assert r.source == "heuristic"
        assert "95/100" in r.reason

    def test_medium_score(self):
        r = heuristic_check(_cand("anas123@gmail.com", score=60))
        assert r.source == "heuristic"
        assert "60/100" in r.reason

    def test_low_score(self):
        r = heuristic_check(_cand("anas.hello.founder@gmail.com", score=30))
        assert r.source == "heuristic"
        assert "30/100" in r.reason

    def test_never_claims_unavailable(self):
        r = heuristic_check(_cand("anything@gmail.com", score=10))
        assert r.available is None  # heuristic never makes a hard call


class TestCheckAll:
    def test_heuristic_mode(self):
        cands = [_cand(f"anas{i}@gmail.com", score=80 - i) for i in range(5)]
        results = check_all(cands, mode="heuristic")
        assert len(results) == 5
        assert all(r.source == "heuristic" for r in results)
        assert all(r.available is None for r in results)

    def test_result_shape(self):
        r = heuristic_check(_cand("anas@gmail.com"))
        assert isinstance(r, CheckResult)
        assert r.address == "anas@gmail.com"
        assert r.source == "heuristic"
