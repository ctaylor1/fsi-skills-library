#!/usr/bin/env python3
"""Deterministic input validation for concentration-risk-monitor.

Validates a concentration monitoring-run file before the deterministic engine evaluates it.
Fails closed on structural problems; warns on data-quality gaps that limit which rules are
evaluable for a book or that disable freshness / deduplication for this run.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  run_id, as_of (YYYY-MM-DD), config_version, max_staleness_days,
  open_alerts[{fingerprint}],                       # previously-open alerts, for dedup
  books[{book_id, book_name, exposures_as_of,
         bases{total_exposure, eligible_capital, ...},   # named denominators
         exposures[{exposure_id, amount, counterparty, counterparty_group, sector,
                    geography, product, cloud_provider, ai_provider,
                    technology_provider, operational_dependency}],
         proposed_exposures[{exposure_id, amount, <same dimension fields>}]}],
  rules[{rule_id, type, scope, basis, limit_pct|limit_amount|min_count,
         warn_buffer_pct, warn_buffer_amount, regulatory}]

The engine is generic over `scope`: any dimension field present on an exposure may be a
concentration/absolute/diversification scope (counterparty, counterparty_group, sector,
geography, product, cloud_provider, ai_provider, technology_provider, operational_dependency).

Usage:
  python validate_input.py run.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("run_id", "as_of", "config_version", "books", "rules")
REQUIRED_BOOK = ("book_id", "bases", "exposures")
REQUIRED_EXPOSURE = ("exposure_id", "amount")
RULE_TYPES = {"concentration", "absolute_cap", "diversification"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _check_exposures(exposures, tag, errors, warnings, label):
    if not isinstance(exposures, list):
        errors.append(f"{tag}: {label} must be a list")
        return
    seen = set()
    for j, e in enumerate(exposures):
        etag = f"{tag}.{label}[{j}] ({e.get('exposure_id','?')})"
        for k in REQUIRED_EXPOSURE:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{etag}: missing '{k}'")
        if _num(e.get("amount")) is None:
            errors.append(f"{etag}: amount not numeric")
        elif _num(e.get("amount")) < 0:
            warnings.append(f"{etag}: negative amount — will net down its bucket")
        eid = e.get("exposure_id")
        if eid in seen:
            warnings.append(f"{etag}: repeated exposure_id — amounts will be aggregated")
        seen.add(eid)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if "max_staleness_days" not in doc:
        warnings.append("no 'max_staleness_days' — freshness is not evaluable this run; alerts may rest on stale exposures")
    if "open_alerts" not in doc:
        warnings.append("no 'open_alerts' baseline — deduplication is disabled; every breach will be reported as new")

    rules = doc.get("rules") or []
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty list")
        return errors, warnings

    rids = set()
    concentration_bases = {}  # rule_id -> basis key that must exist on a book
    for i, r in enumerate(rules):
        tag = f"rules[{i}] ({r.get('rule_id','?')})"
        rid = r.get("rule_id")
        if not rid:
            errors.append(f"{tag}: missing rule_id")
        if rid in rids:
            errors.append(f"{tag}: duplicate rule_id")
        rids.add(rid)
        rtype = r.get("type")
        if rtype not in RULE_TYPES:
            errors.append(f"{tag}: type must be one of {sorted(RULE_TYPES)}, got {rtype!r}")
            continue
        if not r.get("scope"):
            errors.append(f"{tag}: missing 'scope' (the dimension field to aggregate on)")
        if rtype == "concentration":
            if _num(r.get("limit_pct")) is None:
                errors.append(f"{tag}: concentration rule needs numeric limit_pct")
            concentration_bases[rid] = r.get("basis", "total_exposure")
        elif rtype == "absolute_cap":
            if _num(r.get("limit_amount")) is None:
                errors.append(f"{tag}: absolute_cap rule needs numeric limit_amount")
        elif rtype == "diversification":
            if _num(r.get("min_count")) is None:
                errors.append(f"{tag}: diversification rule needs numeric min_count")

    books = doc.get("books") or []
    if not isinstance(books, list) or not books:
        errors.append("books must be a non-empty list")
        return errors, warnings

    bids = set()
    for i, b in enumerate(books):
        tag = f"books[{i}] ({b.get('book_id','?')})"
        for k in REQUIRED_BOOK:
            if k not in b or b[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        bid = b.get("book_id")
        if bid in bids:
            errors.append(f"{tag}: duplicate book_id")
        bids.add(bid)
        bases = b.get("bases")
        if bases is not None and not isinstance(bases, dict):
            errors.append(f"{tag}: bases must be an object of named denominators")
            bases = {}
        bases = bases or {}
        for name, val in bases.items():
            if _num(val) is None or _num(val) <= 0:
                errors.append(f"{tag}: basis '{name}' must be a positive number")
        exposures = b.get("exposures") or []
        if not isinstance(exposures, list) or not exposures:
            errors.append(f"{tag}: exposures must be a non-empty list")
        else:
            _check_exposures(exposures, tag, errors, warnings, "exposures")
        if b.get("proposed_exposures"):
            _check_exposures(b.get("proposed_exposures"), tag, errors, warnings, "proposed_exposures")
        if not b.get("exposures_as_of"):
            warnings.append(f"{tag}: no exposures_as_of — freshness not evaluable for this book")
        # evaluability: concentration rules need their basis present on the book
        for rid, basis_key in concentration_bases.items():
            if basis_key not in bases:
                warnings.append(f"{tag}: concentration rule {rid} not evaluable — basis '{basis_key}' absent from this book's bases")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
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
