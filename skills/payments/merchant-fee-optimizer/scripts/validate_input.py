#!/usr/bin/env python3
"""Deterministic input validation for merchant-fee-optimizer.

Validates a de-identified merchant processing statement before fee analysis. Fails closed on
structural problems; warns on data-quality gaps that limit which opportunities are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  merchant_id, statement_period (YYYY-MM), config_version, currency, pricing_model,
  processor{monthly_fees[]}, contract{end_date,auto_renew,notice_days,early_termination_fee},
  config{...benchmarks...},
  transactions[{txn_id, amount, card_type, entry_mode, level, interchange_fee, assessment_fee,
                processor_fee, downgraded, qualified_interchange_fee, interchange_category,
                source_ref}]

Usage:
  python validate_input.py statement.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")
PRICING_MODELS = {"tiered", "blended", "flat", "interchange_plus", "surcharge"}
REQUIRED_TOP = ("merchant_id", "statement_period", "config_version", "pricing_model", "transactions")
REQUIRED_TXN = ("txn_id", "amount", "card_type", "interchange_fee", "assessment_fee",
                "processor_fee", "source_ref")
COMMERCIAL_HINT = ("commercial", "corporate", "purchasing", "business")


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

    if not PERIOD_RE.match(str(doc["statement_period"])):
        errors.append(f"statement_period must be YYYY-MM, got {doc['statement_period']!r}")
    if doc["pricing_model"] not in PRICING_MODELS:
        errors.append(f"pricing_model must be one of {sorted(PRICING_MODELS)}, got {doc['pricing_model']!r}")

    txns = doc.get("transactions") or []
    if not isinstance(txns, list) or not txns:
        errors.append("transactions must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, t in enumerate(txns):
        tag = f"transactions[{i}] ({t.get('txn_id', '?')})"
        for k in REQUIRED_TXN:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        for fld in ("amount", "interchange_fee", "assessment_fee", "processor_fee"):
            if fld in t and _num(t.get(fld)) is None:
                errors.append(f"{tag}: {fld} not numeric")
        amt = _num(t.get("amount"))
        if amt is not None and amt <= 0:
            errors.append(f"{tag}: amount must be positive (settled card sale)")
        tid = t.get("txn_id")
        if tid in ids:
            errors.append(f"{tag}: duplicate txn_id")
        ids.add(tid)

        if not t.get("entry_mode"):
            warnings.append(f"{tag}: no entry_mode — card-present/CNP mix not evaluable for this row")
        if t.get("downgraded") and t.get("qualified_interchange_fee") in (None, ""):
            warnings.append(f"{tag}: downgraded but no qualified_interchange_fee — downgrade recovery not evaluable for this row")
        ctype = str(t.get("card_type", "")).lower()
        if any(h in ctype for h in COMMERCIAL_HINT) and not t.get("level"):
            warnings.append(f"{tag}: commercial/corporate card with no 'level' — Level 2/3 evaluability limited")

    if len(txns) < 5:
        warnings.append(f"thin data ({len(txns)} txns) — effective-rate and markup estimates are low-confidence")
    if not (doc.get("processor") or {}).get("monthly_fees"):
        warnings.append("no processor.monthly_fees — fixed monthly costs excluded from analysis")
    if not doc.get("contract"):
        warnings.append("no 'contract' block — early-termination/auto-renew flags not evaluable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default benchmarks will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "statement_example.json"
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
