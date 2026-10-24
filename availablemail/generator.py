"""Email generation, scoring, and provider definitions."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

#: Consumer-facing email providers. Domain -> short handle for display.
PROVIDERS: dict[str, str] = {
    "gmail.com": "Gmail",
    "hotmail.com": "Hotmail",
    "outlook.com": "Outlook",
    "live.com": "Live",
    "yahoo.com": "Yahoo",
    "icloud.com": "iCloud",
    "aol.com": "AOL",
    "protonmail.com": "ProtonMail",
    "proton.me": "Proton",
    "tutanota.com": "Tutanota",
    "zoho.com": "Zoho",
    "gmx.com": "GMX",
    "yandex.com": "Yandex",
    "mail.ru": "Mail.ru",
    "rediffmail.com": "Rediff",
}

#: Grouping for filtering.
GROUPS: dict[str, list[str]] = {
    "all": list(PROVIDERS.keys()),
    "google": ["gmail.com"],
    "microsoft": ["hotmail.com", "outlook.com", "live.com"],
    "yahoo": ["yahoo.com"],
    "icloud": ["icloud.com"],
    "proton": ["protonmail.com", "proton.me"],
    "aol": ["aol.com"],
}


def filter_providers(group: str) -> list[str]:
    """Return the provider domains for a named group or an explicit domain."""
    if group in GROUPS:
        return GROUPS[group]
    if group in PROVIDERS:
        return [group]
    # Unknown group -> all providers.
    return list(PROVIDERS.keys())


# ---------------------------------------------------------------------------
# Candidate email
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Candidate:
    """One proposed email address with a professional score."""

    address: str
    local: str  # part before @
    domain: str
    pattern: str  # which template produced it
    score: int  # higher = more professional
    suffixes_used: int  # how many 'dev', 'hello' etc were appended
    digits_used: int  # how many digits were appended


# ---------------------------------------------------------------------------
# Naming patterns
# ---------------------------------------------------------------------------


#: Templates ordered from most to least professional.
#: Each template is a function of (first, last) -> local-part string.
def _patterns() -> list[tuple[str, str]]:
    """Return (template_name, format_string) pairs.

    The format string uses named placeholders like {first}, {last}, {f}, {l},
    {fi}, {li} (initials), {fil}, {lf} (concats).
    """
    return [
        ("first.last", "{first}.{last}"),
        ("first", "{first}"),
        ("firstlast", "{first}{last}"),
        ("first-last", "{first}-{last}"),
        ("f.last", "{fi}.{last}"),
        ("f{last}", "{fi}{last}"),
        ("l{first}", "{li}{first}"),
        ("last.first", "{last}.{first}"),
        ("last", "{last}"),
        ("last-first", "{last}-{first}"),
    ]


def _slugs(first: str, last: str) -> dict[str, str]:
    """Normalise input names to safe email slugs."""

    def slug(s: str) -> str:
        s = s.strip().lower()
        # collapse runs of non-alphanumerics to a single space, then strip
        s = re.sub(r"[^a-z0-9]+", " ", s).strip()
        s = s.replace(" ", "")  # for email, drop internal separators
        return s or "x"

    f = slug(first)
    ln = slug(last) if last else ""
    return {
        "first": f,
        "last": ln,
        "fi": f[0] if f else "",
        "li": ln[0] if ln else "",
        "fil": f"{f[0]}{ln}" if f and ln else "",
        "lf": f"{ln}{f}" if f and ln else "",
    }


def _valid_local(local: str) -> bool:
    """A local part must be 1-64 chars, start with alnum, no leading/trailing dots."""
    if len(local) > 64:
        return False
    if not local[0].isalnum():
        return False
    if not local[-1].isalnum():
        return False
    return ".." not in local


def _is_proton_like(domain: str) -> bool:
    """Proton does not allow dots in the local part for free accounts."""
    return domain.startswith("proton.") or domain in {"protonmail.com", "proton.me"}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

#: Bonus for the most professional patterns. Patterns get a small
#: additive bonus so `first.last` wins ties over `l{first}` even when
#: the latter is shorter.
_PATTERN_BONUS: dict[str, int] = {
    "first.last": 6,   # B2B standard — wins ties
    "first": 3,        # clean, casual
    "firstlast": 2,    # compact
    "first-last": 3,   # legible
    "f.last": 4,       # enterprise-friendly
    "f{last}": 4,      # common at scale
    "l{first}": 1,     # ambiguous
    "last.first": 3,   # formal industries
    "last": 0,         # very ambiguous
    "last-first": 0,
}


def _score(local: str, domain: str, pattern: str, suffixes_used: int,
           digits_used: int) -> int:
    """Score 0-100. Higher is more professional."""
    score = 100

    # Length penalty — shorter local parts read cleaner.
    length = len(local)
    if length > 20:
        score -= 20
    elif length > 16:
        score -= 10
    elif length > 12:
        score -= 4

    # Digit penalty — "anas12345" reads worse than "anas.dev".
    score -= digits_used * 15

    # Suffix penalty — "anas.dev" is fine, "anas.hello.founder" is not.
    score -= suffixes_used * 8

    # Pattern preference — a bare name without dots is a bit informal.
    if pattern in ("first", "last"):
        score -= 5
    else:
        score += _PATTERN_BONUS.get(pattern, 0)

    # Proton + dot = will fail at signup; penalise heavily.
    if _is_proton_like(domain) and "." in local:
        score -= 60

    return max(0, min(100, score))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_candidates(
    first_name: str,
    last_name: str = "",
    *,
    providers: Iterable[str] | str = "all",
    suffixes: list[str] | None = None,
    max_digits: int = 3,
    limit: int = 200,
) -> list[Candidate]:
    """Generate and score candidate email addresses.

    Args:
        first_name: first name (or brand name)
        last_name: optional last name
        providers: provider group ('all', 'google', 'microsoft', 'yahoo', ...)
            or a single domain ('gmail.com')
        suffixes: extra keywords to try as suffixes. None = defaults.
        max_digits: how many trailing digits to try (0 disables digits)
        limit: hard cap on returned candidates

    Returns:
        List of candidates, sorted best-first.
    """
    if not first_name or not first_name.strip():
        raise ValueError("first_name is required")

    provider_domains = filter_providers(providers if isinstance(providers, str) else "all")
    if isinstance(providers, list):
        provider_domains = [d for d in providers if d in PROVIDERS] or providers
    elif isinstance(providers, str):
        provider_domains = filter_providers(providers)

    if suffixes is None:
        suffixes = [
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
        ]

    slugs = _slugs(first_name, last_name)
    templates = _patterns()
    has_last = bool(last_name and last_name.strip())

    seen: set[str] = set()
    raw: list[Candidate] = []

    # 1. Try every template x every domain (no suffixes, no digits).
    for pattern, tmpl in templates:
        # skip templates that require a last name when none was given
        if not has_last and any(t in tmpl for t in ("{last}", "{li}", "{lf}")):
            continue
        try:
            local = tmpl.format(**slugs)
        except KeyError:
            continue
        if not _valid_local(local):
            continue
        for domain in provider_domains:
            address = f"{local}@{domain}"
            if address in seen:
                continue
            seen.add(address)
            raw.append(
                Candidate(
                    address=address,
                    local=local,
                    domain=domain,
                    pattern=pattern,
                    score=_score(local, domain, pattern, 0, 0),
                    suffixes_used=0,
                    digits_used=0,
                )
            )

    # 2. Try with one suffix appended.
    for pattern, tmpl in templates:
        if not has_last and any(t in tmpl for t in ("{last}", "{li}", "{lf}")):
            continue
        try:
            base = tmpl.format(**slugs)
        except KeyError:
            continue
        if not _valid_local(base):
            continue
        for suf in suffixes:
            local = f"{base}.{suf}"
            if not _valid_local(local):
                continue
            for domain in provider_domains:
                address = f"{local}@{domain}"
                if address in seen:
                    continue
                seen.add(address)
                raw.append(
                    Candidate(
                        address=address,
                        local=local,
                        domain=domain,
                        pattern=pattern,
                        score=_score(local, domain, pattern, 1, 0),
                        suffixes_used=1,
                        digits_used=0,
                    )
                )

    # 3. Try with trailing digits (1, 2, ..., 12, 123, 1234).
    digit_seeds = ["1", "2", "3", "7", "9", "10", "12", "17", "23", "24", "123", "1234"]
    for pattern, tmpl in templates:
        if not has_last and any(t in tmpl for t in ("{last}", "{li}", "{lf}")):
            continue
        try:
            base = tmpl.format(**slugs)
        except KeyError:
            continue
        if not _valid_local(base):
            continue
        for d in digit_seeds[:max_digits]:
            local = f"{base}{d}"
            if not _valid_local(local):
                continue
            for domain in provider_domains:
                address = f"{local}@{domain}"
                if address in seen:
                    continue
                seen.add(address)
                raw.append(
                    Candidate(
                        address=address,
                        local=local,
                        domain=domain,
                        pattern=pattern,
                        score=_score(local, domain, pattern, 0, 1),
                        suffixes_used=0,
                        digits_used=1,
                    )
                )

    # 4. Try two suffixes stacked.
    for suf1 in suffixes:
        for suf2 in suffixes:
            if suf1 == suf2:
                continue
            local = f"{slugs['first']}.{suf1}.{suf2}"
            if not _valid_local(local):
                continue
            for domain in provider_domains:
                address = f"{local}@{domain}"
                if address in seen:
                    continue
                seen.add(address)
                raw.append(
                    Candidate(
                        address=address,
                        local=local,
                        domain=domain,
                        pattern="first.suf1.suf2",
                        score=_score(local, domain, "first.suf1.suf2", 2, 0),
                        suffixes_used=2,
                        digits_used=0,
                    )
                )

    # Sort: higher score first, then SHORTER local (within same pattern
    # family, shorter is cleaner), then alphabetical address.
    raw.sort(key=lambda c: (-c.score, len(c.local), c.address))
    return raw[:limit]
