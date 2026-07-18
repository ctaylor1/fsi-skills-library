#!/usr/bin/env python3
"""Deterministic input validation for financials-normalizer.

Validates a source financial-statement extract before normalization runs. Fails closed on
structural problems; warns on data-quality gaps that will surface as findings (untraceable
provenance, unmapped lines, missing balance-sheet identity anchors) or limit which tie-outs
are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  entity_id, as_of (YYYY-MM-DD), config_version, reporting_framework, currency,
  mapping[{source_label,std_account,statement,normal_sign}],
  line_items[{line_id,raw_label,statement,period,value,source_ref,
              is_subtotal,components[],role}],
  adjustments[{adj_id,std_account,type,period,amount,rationale,source_ref,approver}],
  config{...thresholds...}

Usage:
  python validate_input.py financials.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("entity_id", "as_of", "config_version", "reporting_framework", "currency",
                "mapping", "line_items")
STATEMENTS = {"income_statement", "balance_sheet", "cash_flow"}
ROLES = {"total_assets", "total_liabilities", "total_equity"}


def _num(v):
    try:
        return float(str(v).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None


def _missing(v) -> bool:
    """True if a required field is absent or an empty/whitespace string."""
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() == ""
    return False


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    mapping = doc.get("mapping") or []
    if not isinstance(mapping, list) or not mapping:
        errors.append("mapping must be a non-empty list")
    mapped_keys = set()
    for i, m in enumerate(mapping):
        tag = f"mapping[{i}] ({m.get('source_label','?')})"
        for k in ("source_label", "std_account", "statement"):
            if _missing(m.get(k)):
                errors.append(f"{tag}: missing '{k}'")
        if m.get("statement") and m["statement"] not in STATEMENTS:
            errors.append(f"{tag}: statement must be one of {sorted(STATEMENTS)}")
        ns = str(m.get("normal_sign", "")).lower()
        if ns and ns not in ("positive", "negative"):
            warnings.append(f"{tag}: normal_sign should be 'positive' or 'negative'")
        mapped_keys.add((str(m.get("source_label")), str(m.get("statement"))))

    lines = doc.get("line_items") or []
    if not isinstance(lines, list) or not lines:
        errors.append("line_items must be a non-empty list")
        return errors, warnings

    ids = set()
    detail_labels_unmapped = 0
    roles_present = set()
    for i, ln in enumerate(lines):
        tag = f"line_items[{i}] ({ln.get('line_id','?')})"
        for k in ("line_id", "raw_label", "statement", "period"):
            if _missing(ln.get(k)):
                errors.append(f"{tag}: missing '{k}'")
        if _num(ln.get("value")) is None:
            errors.append(f"{tag}: value not numeric")
        if ln.get("statement") and ln["statement"] not in STATEMENTS:
            errors.append(f"{tag}: statement must be one of {sorted(STATEMENTS)}")
        lid = ln.get("line_id")
        if lid in ids:
            errors.append(f"{tag}: duplicate line_id")
        ids.add(lid)

        if ln.get("is_subtotal"):
            comps = ln.get("components")
            role = ln.get("role")
            if role in ROLES:
                roles_present.add(role)
            elif not comps:
                warnings.append(f"{tag}: subtotal has neither 'components' nor an identity 'role' — not tie-out-checkable")
        else:
            if not (ln.get("source_ref") or "").strip():
                warnings.append(f"{tag}: no source_ref — missing_provenance will fire (untraceable)")
            if (str(ln.get("raw_label")), str(ln.get("statement"))) not in mapped_keys:
                detail_labels_unmapped += 1

    # subtotal component references must resolve
    for ln in lines:
        if ln.get("is_subtotal") and ln.get("components"):
            for c in ln["components"]:
                if c not in ids:
                    errors.append(f"line_items ({ln.get('line_id')}): component {c!r} not a known line_id")

    if detail_labels_unmapped:
        warnings.append(f"{detail_labels_unmapped} detail line(s) have no mapping — unmapped_line_item will fire")
    if not (ROLES <= roles_present):
        missing = sorted(ROLES - roles_present)
        warnings.append(f"balance-sheet identity anchors missing ({', '.join(missing)}) — balance_sheet_identity_break not evaluable")
    for j, a in enumerate(doc.get("adjustments") or []):
        if not (a.get("rationale") or "").strip() or not (a.get("source_ref") or "").strip():
            warnings.append(f"adjustments[{j}] ({a.get('adj_id','?')}): missing rationale/source — will be flagged")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "financials_example.json"
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
