#!/usr/bin/env python3
"""Deterministic input validation for comps-analysis-builder.

Validates a comparable-company-analysis (trading comps) intake bundle before the analysis is
built. Fails closed on structural problems; warns on data gaps that will surface as open items
(missing operating metrics, non-meaningful denominators, stale market data, currency
mismatches, a thin peer set).

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, template_version, analysis_id, as_of_date, currency, units,
  peer_selection_criteria, config{max_price_age_days, min_peers, implied_multiples[], bands{}},
  required_approvals[], approvals[{type, approver_role, approver, status, date, source_ref}],
  subject{...company...}, peers[{...company...}]
Company: ticker, name, include, currency, share_price, diluted_shares, price_date,
  total_debt, cash_and_equivalents, preferred_equity, minority_interest,
  ltm{revenue, ebitda, ebit, eps}, fy1{revenue, ebitda}, source_ref, market_source_ref,
  (peer only) rationale, exclude_reason.

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("config_version", "analysis_id", "as_of_date", "currency", "subject", "peers")
REQUIRED_COMPANY = ("ticker", "share_price", "diluted_shares", "source_ref")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _days_old(as_of, price_date):
    try:
        return (date.fromisoformat(str(as_of)) - date.fromisoformat(str(price_date))).days
    except Exception:
        return None


def _check_company(tag, c, currency, as_of, max_age, errors, warnings, *, is_subject=False):
    for k in REQUIRED_COMPANY:
        if k not in c or c[k] in (None, ""):
            errors.append(f"{tag}: missing '{k}'")
    for k in ("share_price", "diluted_shares"):
        if k in c and not _num(c[k]):
            errors.append(f"{tag}: '{k}' must be numeric")
    if _num(c.get("diluted_shares")) and c.get("diluted_shares", 0) <= 0:
        errors.append(f"{tag}: diluted_shares must be > 0 (equity value would be undefined)")
    if c.get("currency") and currency and c.get("currency") != currency:
        warnings.append(f"{tag}: currency {c.get('currency')!r} != analysis currency {currency!r} "
                        f"-> FX normalization required before multiples are comparable (open-item)")
    ltm = c.get("ltm") or {}
    for m in ("revenue", "ebitda"):
        if not _num(ltm.get(m)):
            warnings.append(f"{tag}: ltm.{m} missing/non-numeric -> some multiples will be non-meaningful (open-item)")
    if _num(ltm.get("ebitda")) and ltm.get("ebitda", 0) <= 0:
        warnings.append(f"{tag}: ltm.ebitda <= 0 -> EV/EBITDA will be flagged non-meaningful (nm)")
    if not is_subject and c.get("include", True) and not c.get("rationale"):
        warnings.append(f"{tag}: included peer has no 'rationale' -> peer-inclusion rationale incomplete")
    if not c.get("include", True) and not c.get("exclude_reason"):
        warnings.append(f"{tag}: excluded peer has no 'exclude_reason' -> exclusion is not human-confirmable")
    pd = c.get("price_date")
    if not pd:
        warnings.append(f"{tag}: no price_date -> market-data freshness cannot be verified (stale/open-item)")
    else:
        age = _days_old(as_of, pd)
        if age is not None and age > max_age:
            warnings.append(f"{tag}: market data is {age}d old (> {max_age}d) -> stale; refresh before use (open-item)")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    currency = doc.get("currency")
    as_of = doc.get("as_of_date")
    cfg = doc.get("config") or {}
    max_age = cfg.get("max_price_age_days", 5)
    min_peers = cfg.get("min_peers", 3)

    subject = doc.get("subject") or {}
    _check_company("subject", subject, currency, as_of, max_age, errors, warnings, is_subject=True)

    peers = doc.get("peers")
    if not isinstance(peers, list) or not peers:
        errors.append("peers must be a non-empty list")
        return errors, warnings

    tickers = set()
    included = 0
    for i, p in enumerate(peers):
        tag = f"peers[{i}] ({p.get('ticker','?')})"
        _check_company(tag, p, currency, as_of, max_age, errors, warnings)
        tk = p.get("ticker")
        if tk in tickers:
            errors.append(f"{tag}: duplicate ticker")
        tickers.add(tk)
        if p.get("include", True):
            included += 1
    if subject.get("ticker") in tickers:
        warnings.append(f"subject ticker {subject.get('ticker')!r} also appears in the peer set -> remove the subject from peers")
    if included < min_peers:
        warnings.append(f"only {included} included peer(s) (< min_peers {min_peers}) -> thin peer set; summary statistics will be flagged")

    for i, a in enumerate(doc.get("approvals") or []):
        if not a.get("type") or not a.get("status"):
            errors.append(f"approvals[{i}]: requires 'type' and 'status'")
        if a.get("status") == "recorded" and not a.get("source_ref"):
            errors.append(f"approvals[{i}] ({a.get('type','?')}): recorded approval missing 'source_ref'")
    if not doc.get("required_approvals"):
        warnings.append("no required_approvals configured -> approval capture limited")
    if doc.get("approvals") is None:
        warnings.append("no approvals provided -> all required approvals will be outstanding")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "comps_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
