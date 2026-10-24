"""Tests for the generator."""

import pytest

from availablemail.generator import (
    PROVIDERS,
    Candidate,
    _is_proton_like,
    _score,
    _slugs,
    filter_providers,
    generate_candidates,
)


class TestFilterProviders:
    def test_all_returns_everything(self):
        assert len(filter_providers("all")) == len(PROVIDERS)

    def test_google_group(self):
        assert filter_providers("google") == ["gmail.com"]

    def test_microsoft_group(self):
        assert "hotmail.com" in filter_providers("microsoft")
        assert "outlook.com" in filter_providers("microsoft")

    def test_unknown_falls_back_to_all(self):
        assert len(filter_providers("doesnotexist")) == len(PROVIDERS)


class TestSlugs:
    def test_basic(self):
        s = _slugs("Anas", "Shaikh")
        assert s["first"] == "anas"
        assert s["last"] == "shaikh"
        assert s["fi"] == "a"
        assert s["li"] == "s"

    def test_strips_non_alpha(self):
        s = _slugs("Anas-O", "Shaikh#1")
        assert s["first"] == "anaso"
        assert s["last"] == "shaikh1"

    def test_empty_last_is_safe(self):
        s = _slugs("Anas", "")
        assert s["last"] == ""
        assert s["li"] == ""

    def test_empty_first_raises_sentinel(self):
        s = _slugs("!!!", "")
        assert s["first"] == "x"


class TestIsProtonLike:
    def test_proton_domains(self):
        assert _is_proton_like("protonmail.com")
        assert _is_proton_like("proton.me")
        assert not _is_proton_like("gmail.com")


class TestScore:
    def test_simple_name_scores_high(self):
        s = _score("anas", "gmail.com", "first", 0, 0)
        assert s >= 90

    def test_dots_only_minor_penalty(self):
        s = _score("anas.shaikh", "gmail.com", "first.last", 0, 0)
        assert s >= 85

    def test_digits_penalised(self):
        s = _score("anas12345", "gmail.com", "first", 0, 1)
        assert s < 90

    def test_suffix_stack_penalised(self):
        s = _score("anas.hello.founder", "gmail.com", "first.suf1.suf2", 2, 0)
        assert s < 85

    def test_proton_dot_heavy_penalty(self):
        s = _score("anas.shaikh", "protonmail.com", "first.last", 0, 0)
        # Should be far below the gmail equivalent
        gmail_score = _score("anas.shaikh", "gmail.com", "first.last", 0, 0)
        assert s < gmail_score

    def test_score_never_negative(self):
        s = _score("x.y.z", "protonmail.com", "first.suf1.suf2", 2, 1)
        assert s >= 0


class TestGenerate:
    def test_requires_first_name(self):
        with pytest.raises(ValueError):
            generate_candidates("")

    def test_returns_list_of_candidates(self):
        out = generate_candidates("anas", "shaikh", limit=10)
        assert isinstance(out, list)
        assert len(out) <= 10
        assert all(isinstance(c, Candidate) for c in out)

    def test_sorted_best_first(self):
        out = generate_candidates("anas", "shaikh", limit=200)
        scores = [c.score for c in out]
        assert scores == sorted(scores, reverse=True)

    def test_all_have_valid_address_shape(self):
        out = generate_candidates("anas", "shaikh")
        for c in out:
            assert "@" in c.address
            local, domain = c.address.split("@")
            assert local and domain

    def test_provider_filter_google_only(self):
        out = generate_candidates("anas", "shaikh", providers="google")
        assert all(c.domain == "gmail.com" for c in out)

    def test_provider_filter_single_domain(self):
        out = generate_candidates("anas", "shaikh", providers="yahoo.com")
        assert all(c.address.endswith("@yahoo.com") for c in out)

    def test_suffixes_appear(self):
        out = generate_candidates("anas", suffixes=["dev", "hello"], providers="google")
        assert any("dev" in c.local for c in out)
        assert any("hello" in c.local for c in out)

    def test_no_duplicate_addresses(self):
        out = generate_candidates("anas", "shaikh", limit=500)
        addrs = [c.address for c in out]
        assert len(addrs) == len(set(addrs))

    def test_last_name_optional(self):
        out = generate_candidates("anas", "")
        assert out
        assert all("shaikh" not in c.address for c in out)

    def test_max_digits_zero_disables_digits(self):
        out = generate_candidates("anas", "shaikh", max_digits=0, limit=500)
        for c in out:
            # local part should have no trailing digit-only suffix
            # (dots/hyphens are still fine)
            import re

            assert not re.search(r"\d+$", c.local) or c.suffixes_used > 0

    def test_limit_respected(self):
        for n in [1, 5, 20, 100]:
            out = generate_candidates("anas", "shaikh", limit=n)
            assert len(out) == min(n, 500)

    def test_proton_candidates_without_dots_preferred(self):
        out = generate_candidates("anas", "shaikh", providers="proton", limit=100)
        no_dots = [c for c in out if "." not in c.local]
        assert no_dots, "expected at least one proton candidate without a dot"

    def test_all_providers_present_when_all_selected(self):
        out = generate_candidates("anas", "shaikh", providers="all", limit=2000)
        domains = {c.domain for c in out}
        assert len(domains) >= 5

    def test_brand_name_only(self):
        out = generate_candidates("ecomclaim", providers="google")
        assert out
        assert out[0].address.startswith("ecomclaim")

    def test_special_characters_sanitised(self):
        out = generate_candidates("Anas O'Brien", "Shaikh-Johnson")
        for c in out:
            local = c.address.split("@")[0]
            assert "'" not in local
            assert " " not in local
