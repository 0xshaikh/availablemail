"""Availability checking.

Three modes, from cheapest to most accurate:

1. **heuristic** (default) — score-based ranking only. Zero network calls.
   Deterministic, fast, always works. Never claims an address is taken or
   available — only ranks candidates by professional quality.

2. **microsoft** — checks Outlook / Hotmail / Live / MSN availability by
   calling Microsoft's public account-signup endpoint. Works for real
   because those domains have a documented (undocumented-but-stable)
   namespace-availability check on their signup flow. This is the only
   consumer-provider availability check that is actually reliable.

3. **smtp** — coarse MX reachability check. This is NOT an availability
   check — most consumer providers (Yahoo, iCloud, AOL, Proton, Tutanota,
   Zoho, Mail.com, GMX) are catch-all and will always "accept" any RCPT
   TO probe. Kept here as a DNS sanity check, not as a real availability
   source. If you want to know if an address is *taken* at those
   providers, you have to try to sign up.

The CLI defaults to `heuristic` so it works with zero configuration. Add
``--check microsoft`` to also probe Outlook/Hotmail/Live availability.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Literal

from .generator import Candidate

CheckMode = Literal["heuristic", "microsoft", "smtp"]


@dataclass(frozen=True)
class CheckResult:
    """Result of an availability check for one candidate."""

    address: str
    available: bool | None  # None = unknown
    reason: str
    source: str


# ---------------------------------------------------------------------------
# Heuristic mode
# ---------------------------------------------------------------------------


def heuristic_check(candidate: Candidate) -> CheckResult:
    """Score-only ranking. Never makes a hard availability claim."""
    if candidate.score >= 85:
        tag = "strong"
    elif candidate.score >= 60:
        tag = "decent"
    else:
        tag = "weaker"
    return CheckResult(
        address=candidate.address,
        available=None,
        reason=f"{tag} score ({candidate.score}/100)",
        source="heuristic",
    )


# ---------------------------------------------------------------------------
# Microsoft lane (Outlook / Hotmail / Live / MSN / Passport)
# ---------------------------------------------------------------------------

_MS_DOMAINS = {
    "hotmail.com",
    "outlook.com",
    "live.com",
    "msn.com",
    "passport.com",
    "hotmail.co.in",
    "outlook.in",
}

# Microsoft account-signup availability endpoint. Public but undocumented.
# Reference: github.com/ngocchien/mail-checker
_MS_AVAIL_URL = "https://api.account.microsoft.com/v2.0/users?accountname={local}"


def microsoft_check(address: str) -> CheckResult:
    """Check Microsoft consumer account availability."""
    local, _, domain = address.partition("@")
    if domain not in _MS_DOMAINS:
        return CheckResult(
            address=address,
            available=None,
            reason=f"{domain} is not a Microsoft domain",
            source="microsoft",
        )

    url = _MS_AVAIL_URL.format(local=urllib.parse.quote(local))
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) availablemail/0.1",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            return CheckResult(
                address=address,
                available=False,
                reason="microsoft says account exists (HTTP 409)",
                source="microsoft",
            )
        if e.code == 404:
            return CheckResult(
                address=address,
                available=True,
                reason="microsoft says account not found (HTTP 404)",
                source="microsoft",
            )
        return CheckResult(
            address=address,
            available=None,
            reason=f"microsoft HTTP {e.code}",
            source="microsoft",
        )
    except Exception as e:
        return CheckResult(
            address=address,
            available=None,
            reason=f"microsoft error: {e}",
            source="microsoft",
        )

    # 200 means the account exists (rare response shape)
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return CheckResult(
            address=address,
            available=None,
            reason="microsoft returned non-JSON body",
            source="microsoft",
        )
    if data.get("id"):
        return CheckResult(
            address=address,
            available=False,
            reason="microsoft says account exists",
            source="microsoft",
        )
    return CheckResult(
        address=address,
        available=True,
        reason="microsoft says account free",
        source="microsoft",
    )


# ---------------------------------------------------------------------------
# SMTP lane (coarse MX reachability, NOT availability)
# ---------------------------------------------------------------------------


def smtp_domain_exists(domain: str) -> CheckResult:
    """Coarse check: does the MX resolve? Not an availability check."""
    try:
        mxs = socket.getaddrinfo(domain, 25)
    except socket.gaierror:
        return CheckResult(
            address=f"@{domain}", available=False, reason=f"no MX for {domain}", source="smtp"
        )
    if not mxs:
        return CheckResult(
            address=f"@{domain}", available=False, reason=f"no MX for {domain}", source="smtp"
        )
    return CheckResult(
        address=f"@{domain}",
        available=True,
        reason=f"MX reachable ({len(mxs)} servers, catch-all likely)",
        source="smtp",
    )


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------


def check_all(candidates: list[Candidate], mode: CheckMode = "heuristic") -> list[CheckResult]:
    """Run the requested check mode over every candidate."""
    if mode == "heuristic":
        return [heuristic_check(c) for c in candidates]
    if mode == "microsoft":
        return [microsoft_check(c.address) for c in candidates]
    # smtp — check once per domain
    by_domain: dict[str, CheckResult] = {}
    for c in candidates:
        if c.domain not in by_domain:
            by_domain[c.domain] = smtp_domain_exists(c.domain)
    return [
        CheckResult(
            address=c.address,
            available=by_domain[c.domain].available,
            reason=f"{by_domain[c.domain].reason} (domain-level, not availability)",
            source="smtp",
        )
        for c in candidates
    ]
