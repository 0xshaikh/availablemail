# Security Policy

`availablemail` is a local CLI that does not by default make any network
calls. Please read the [Checker docs](availablemail/checker.py) before
enabling live checks.

## Reporting a vulnerability

If you find a way to make `availablemail` leak local data, execute
arbitrary code, or otherwise misbehave, please report it via
[security@0xshaikh.dev](mailto:security@0xshaikh.dev) rather than a
public issue.

Please do not include real email addresses, API keys, or signup data in
the report.

## Live-check safety

When you run with `--check microsoft`, the tool sends the local part of
each Microsoft candidate to `api.account.microsoft.com`. This is the
same endpoint Microsoft itself uses for signup availability, but it
does leave a small trace on Microsoft's servers. If you want to avoid
that, stick with `--check heuristic` (the default).

`--check smtp` performs DNS lookups on the MX record for each provider
domain. This is not a per-user call.

## Scope

In scope:
- Remote code execution from untrusted input
- Path traversal via `--out`
- Credential or PII leaks in default output

Out of scope:
- The availability of a candidate address (providers lie to probe
  traffic; see [checker docs](availablemail/checker.py))
- Rate-limiting by third parties
- Social engineering or phishing use
