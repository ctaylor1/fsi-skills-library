#!/usr/bin/env python3
"""Deterministic input validation for financial-spreading-assistant.

Validates a spreading-input file before the spread/ratio/cash-flow model is built. Fails
closed on structural problems; warns on data-quality gaps that limit the spread (ambiguous
mappings that will require human resolution, single-period inputs that make cash flow and
trends not evaluable, missing citations or reported anchors).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  borrower_id, as_of (YYYY-MM-DD), template_version, classification_map_version,
  config_version, config{tolerance, classification_map{raw_label->code}},
  periods[str] (oldest -> newest),
  line_items[{period, statement, raw_label, code?, amount, source_ref}],
  reported_totals[{period, statement, key, amount, source_ref}],
  adjustments[{id, statement, period, code, amount, direction, reason, provenance, citation}]

Usage:
  python validate_input.py spread_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("borrower_id", "as_of", "template_version", "classification_map_version",
                "config_version", "periods", "line_items", "reported_totals")
REQUIRED_LINE = ("period", "statement", "raw_label", "amount", "source_ref")
STATEMENTS = ("balance_sheet", "income_statement")
REPORTED_KEYS = ("total_assets", "total_liabilities", "total_equity", "net_income")

TAXONOMY = {
    # balance sheet
    "cash", "accounts_receivable", "inventory", "other_current_assets",
    "net_fixed_assets", "intangibles", "other_noncurrent_assets",
    "accounts_payable", "current_portion_ltd", "accrued_liabilities",
    "other_current_liabilities", "long_term_debt", "other_noncurrent_liabilities",
    "common_equity", "retained_earnings",
    # income statement
    "revenue", "cogs", "operating_expenses", "depreciation_amortization",
    "interest_expense", "taxes", "other_income_expense",
}
IS_CODES = {"revenue", "cogs", "operating_expenses", "depreciation_amortization",
            "interest_expense", "taxes", "other_income_expense"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _resolve(item, class_map):
    code = (item.get("code") or "").strip()
    if code and code in TAXONOMY:
        return code
    if not code:
        mapped = class_map.get(str(item.get("raw_label", "")).strip().lower())
        if mapped in TAXONOMY:
            return mapped
    return None  # ambiguous / unknown code


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    periods = doc.get("periods") or []
    if not isinstance(periods, list) or not periods:
        errors.append("periods must be a non-empty list (oldest -> newest)")
        return errors, warnings
    if len(set(periods)) != len(periods):
        errors.append("periods contains duplicates")

    class_map = {str(k).strip().lower(): v
                 for k, v in ((doc.get("config") or {}).get("classification_map") or {}).items()}

    lines = doc.get("line_items") or []
    if not isinstance(lines, list) or not lines:
        errors.append("line_items must be a non-empty list")
        return errors, warnings

    ambiguous = 0
    missing_cite = 0
    for i, it in enumerate(lines):
        tag = f"line_items[{i}] ({it.get('raw_label','?')})"
        for k in REQUIRED_LINE:
            if k not in it or it[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if it.get("statement") not in STATEMENTS:
            errors.append(f"{tag}: statement must be one of {STATEMENTS}")
        if it.get("period") not in periods:
            errors.append(f"{tag}: period {it.get('period')!r} not in declared periods")
        if _num(it.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        if not it.get("source_ref"):
            missing_cite += 1
        if _resolve(it, class_map) is None:
            ambiguous += 1

    # reported anchors
    seen_anchor = set()
    for i, r in enumerate(doc.get("reported_totals") or []):
        tag = f"reported_totals[{i}] ({r.get('key','?')})"
        if r.get("statement") not in STATEMENTS:
            errors.append(f"{tag}: statement must be one of {STATEMENTS}")
        if r.get("key") not in REPORTED_KEYS:
            errors.append(f"{tag}: key must be one of {REPORTED_KEYS}")
        if r.get("period") not in periods:
            errors.append(f"{tag}: period {r.get('period')!r} not in declared periods")
        if _num(r.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        seen_anchor.add((r.get("period"), r.get("statement"), r.get("key")))

    # adjustments (optional)
    for i, a in enumerate(doc.get("adjustments") or []):
        tag = f"adjustments[{i}] ({a.get('id','?')})"
        if not a.get("id"):
            errors.append(f"{tag}: missing 'id'")
        if a.get("statement") != "income_statement":
            errors.append(f"{tag}: statement must be 'income_statement' (only income-statement add-backs are modelled)")
        if a.get("period") not in periods:
            errors.append(f"{tag}: period {a.get('period')!r} not in declared periods")
        if a.get("code") not in IS_CODES:
            errors.append(f"{tag}: code {a.get('code')!r} must be an income-statement code {sorted(IS_CODES)}")
        if _num(a.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        if a.get("direction") not in ("add", "subtract"):
            errors.append(f"{tag}: direction must be 'add' or 'subtract'")
        if not (a.get("provenance") or "").strip():
            warnings.append(f"{tag}: no provenance; every adjustment must be documented before delivery")
        if not (a.get("citation") or "").strip():
            warnings.append(f"{tag}: no citation; every adjustment must cite its supporting document")

    # data-quality warnings
    if ambiguous:
        warnings.append(f"{ambiguous} line item(s) have no resolvable taxonomy code — they will be "
                        f"flagged as ambiguous mappings and require human resolution before the spread is used")
    if missing_cite:
        warnings.append(f"{missing_cite} line item(s) have no source_ref — spreading requires a citation per line")
    if len(periods) < 2:
        warnings.append("only one period supplied — cash-flow proxy and period-over-period trends are not evaluable")
    for p in periods:
        for stmt, keys in (("balance_sheet", ("total_assets", "total_liabilities", "total_equity")),
                           ("income_statement", ("net_income",))):
            for key in keys:
                if (p, stmt, key) not in seen_anchor:
                    warnings.append(f"no reported anchor for {p} {stmt} {key} — that tie-out cannot be checked against the borrower's own totals")
    if not doc.get("config"):
        warnings.append("no 'config' block — default tolerance and an empty classification map will be used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "spread_input_example.json"
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
