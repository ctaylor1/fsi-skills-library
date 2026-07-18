#!/usr/bin/env python3
"""Deterministic input validation for fee-and-charge-reviewer.

Validates a fee-review file before comparison. Fails closed on structural problems; warns
on data-quality gaps that limit which fees can be compared to disclosed terms.

Input schema (JSON): see references/source-map.md. Key fields:
  account_id, as_of (YYYY-MM-DD), config_version, statement_period{start,end},
  disclosed_terms[{fee_code,label,category,disclosed_amount,currency,cap_per_day,
                   cap_per_period,waiver_conditions[],source_ref}],
  posted_fees[{fee_id,date,amount,currency,fee_code|null,label,source_ref}],
  account_context{waivers_met[]}, config{amount_tolerance,...}

Usage:
  python validate_input.py fee_review.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("account_id", "as_of", "config_version", "statement_period",
                "disclosed_terms", "posted_fees")
REQUIRED_TERM = ("fee_code", "label", "category", "disclosed_amount", "source_ref")
REQUIRED_FEE = ("fee_id", "date", "amount", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    sp = doc.get("statement_period") or {}
    for k in ("start", "end"):
        if not DATE_RE.match(str(sp.get(k, ""))):
            errors.append(f"statement_period.{k} must be YYYY-MM-DD, got {sp.get(k)!r}")

    terms = doc.get("disclosed_terms") or []
    if not isinstance(terms, list) or not terms:
        errors.append("disclosed_terms must be a non-empty list")
        return errors, warnings

    codes = set()
    for i, t in enumerate(terms):
        tag = f"disclosed_terms[{i}] ({t.get('fee_code','?')})"
        for k in REQUIRED_TERM:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(t.get("disclosed_amount")) is None:
            errors.append(f"{tag}: disclosed_amount not numeric")
        code = t.get("fee_code")
        if code in codes:
            errors.append(f"{tag}: duplicate fee_code")
        codes.add(code)
        wc = t.get("waiver_conditions")
        if wc is not None and not isinstance(wc, list):
            errors.append(f"{tag}: waiver_conditions must be a list")

    fees = doc.get("posted_fees") or []
    if not isinstance(fees, list) or not fees:
        errors.append("posted_fees must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, f in enumerate(fees):
        tag = f"posted_fees[{i}] ({f.get('fee_id','?')})"
        for k in REQUIRED_FEE:
            if k not in f or f[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(f.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        if not DATE_RE.match(str(f.get("date", ""))):
            errors.append(f"{tag}: date must be YYYY-MM-DD, got {f.get('date')!r}")
        fid = f.get("fee_id")
        if fid in ids:
            errors.append(f"{tag}: duplicate fee_id")
        ids.add(fid)
        code = f.get("fee_code")
        if code and code not in codes:
            warnings.append(f"{tag}: fee_code {code!r} not in disclosed_terms — will be flagged not_in_schedule")
        elif code in (None, ""):
            warnings.append(f"{tag}: no fee_code — comparison relies on schedule match; likely not_in_schedule")

    ctx = doc.get("account_context") or {}
    wm = ctx.get("waivers_met")
    if wm is not None and not isinstance(wm, list):
        errors.append("account_context.waivers_met must be a list")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "fee_review_example.json"
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
