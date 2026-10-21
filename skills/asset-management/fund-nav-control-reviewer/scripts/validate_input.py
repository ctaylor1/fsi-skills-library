#!/usr/bin/env python3
"""Deterministic input validation for fund-nav-control-reviewer.

Validates a NAV tie-out job before matching. A job carries the NAV components a fund
accountant reconciles — positions, prices, accruals, income, expenses, shares, and cash —
each recorded from one or more sources (book of record, custodian, administrator, approved
pricing source). Fails closed on structural problems; warns on data-quality gaps that limit
matching or the tie-out.

Input schema (JSON): see references/source-map.md. Key fields:
  fund, share_class (optional), as_of (YYYY-MM-DD), base_currency, config_version,
  lines[{line_id, component, key, source, value, currency, as_of, source_ref, description}],
  config{tolerances{}, date_tolerance_days, materiality{}, component_sources{}}

component in {position, price, cash, accrual, income, expense, shares};
source   in {book, custodian, administrator, pricing}.

Usage:
  python validate_input.py tie_out_job.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("fund", "as_of", "config_version", "base_currency", "lines")
REQUIRED_LINE = ("line_id", "component", "key", "source", "value", "source_ref")
COMPONENTS = {"position", "price", "cash", "accrual", "income", "expense", "shares"}
SOURCES = {"book", "custodian", "administrator", "pricing"}
DEFAULT_COMPONENT_SOURCES = {
    "position": "custodian", "price": "pricing", "cash": "custodian",
    "accrual": "administrator", "income": "administrator", "expense": "administrator",
    "shares": "administrator",
}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _validate_shape(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    lines = doc.get("lines")
    if not isinstance(lines, list):
        errors.append("'lines' must be a list")
        return errors, warnings
    if not lines:
        errors.append("no records: 'lines' is empty")
        return errors, warnings

    seen_ids: set = set()
    # component -> {source_role -> count}
    present: dict = {}
    for i, r in enumerate(lines):
        tag = f"lines[{i}] ({r.get('line_id', '?')})"
        if not isinstance(r, dict):
            errors.append(f"{tag}: not an object")
            continue
        for k in REQUIRED_LINE:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        comp = r.get("component")
        if comp not in COMPONENTS:
            errors.append(f"{tag}: component {comp!r} not in {sorted(COMPONENTS)}")
        src = r.get("source")
        if src not in SOURCES:
            errors.append(f"{tag}: source {src!r} not in {sorted(SOURCES)}")
        if _num(r.get("value")) is None:
            errors.append(f"{tag}: value not numeric ({r.get('value')!r})")
        if r.get("as_of") and not DATE_RE.match(str(r.get("as_of"))):
            errors.append(f"{tag}: as_of must start YYYY-MM-DD, got {r.get('as_of')!r}")
        lid = r.get("line_id")
        if lid in seen_ids:
            errors.append(f"{tag}: duplicate line_id across job (line_id must be unique)")
        seen_ids.add(lid)
        if not r.get("currency"):
            warnings.append(f"{tag}: no currency — assuming base_currency; FX/aggregation may be limited")
        if comp in COMPONENTS and src in SOURCES:
            present.setdefault(comp, {}).setdefault(src, 0)
            present[comp][src] += 1

    # matching feasibility: each component needs both a book side and its verifier side
    cfg = doc.get("config") or {}
    comp_sources = {**DEFAULT_COMPONENT_SOURCES, **(cfg.get("component_sources") or {})}
    for comp, by_src in present.items():
        verifier = comp_sources.get(comp)
        if "book" not in by_src:
            warnings.append(f"component '{comp}': no book-of-record lines — cannot reconcile, only verifier evidence")
        if verifier and verifier not in by_src:
            warnings.append(f"component '{comp}': no '{verifier}' lines — book values cannot be tied out for this component")

    if not cfg:
        warnings.append("no 'config' block — default tolerances/materiality/component-sources will be used; record config_version")
    if not doc.get("share_class"):
        warnings.append("no 'share_class' — tie-out will be at the fund level; record the class if NAV is struck per class")

    return errors, warnings


def validate(doc):
    from native_integrity import canonical_hash
    errors, warnings = [], []
    try:
        canonical_hash(doc)
        errors, warnings = _validate_shape(doc)
        if not errors:
            from calculate_or_transform import compute
            compute(doc)
    except (ValueError, TypeError, KeyError, ArithmeticError, AttributeError) as exc:
        errors.append("unsupported or invalid native input: " + str(exc))
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "tie_out_example.json"
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
