#!/usr/bin/env python3
"""Deterministic input validation for regulatory-reporting-data-validator.

Validates a regulatory-report package before the checks run. Fails closed on structural
problems; warns on data-quality gaps that limit which checks are evaluable (missing required
cells, missing lineage, missing prior period, missing config, edit-check/reconciliation
references to unknown cells).

Input schema (JSON): see references/source-map.md. Key fields:
  report_code, period_end (YYYY-MM-DD), as_of, due_date, config_version, config{...},
  required_cells[], cells[{cell_id, value, source_refs[]}],
  edit_checks[{check_id, target, components[], op, tolerance}],
  reconciliations[{recon_id, cell_id, source_value, reported_value, tolerance}],
  prior_period{period_end, cells{}}, sign_offs[{role, signed_at, name}]

Usage:
  python validate_input.py package.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("report_code", "period_end", "as_of", "due_date", "config_version",
                "required_cells", "cells")
REQUIRED_CELL = ("cell_id", "value")


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

    for k in ("period_end", "as_of", "due_date"):
        if not DATE_RE.match(str(doc[k])):
            errors.append(f"{k} must start YYYY-MM-DD, got {doc[k]!r}")

    cells = doc.get("cells") or []
    if not isinstance(cells, list) or not cells:
        errors.append("cells must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, c in enumerate(cells):
        tag = f"cells[{i}] ({c.get('cell_id','?')})"
        for k in REQUIRED_CELL:
            if k not in c:
                errors.append(f"{tag}: missing '{k}'")
        if _num(c.get("value")) is None:
            errors.append(f"{tag}: value not numeric")
        cid = c.get("cell_id")
        if cid in ids:
            errors.append(f"{tag}: duplicate cell_id")
        ids.add(cid)
        refs = c.get("source_refs")
        if refs is None:
            warnings.append(f"{tag}: no 'source_refs' — lineage_completeness will fire for this cell")
        elif not isinstance(refs, list):
            errors.append(f"{tag}: 'source_refs' must be a list")

    req = doc.get("required_cells") or []
    if not isinstance(req, list):
        errors.append("required_cells must be a list")
    else:
        for rc in req:
            if rc not in ids:
                warnings.append(f"required cell {rc!r} not in cells — completeness will fire")

    for i, ec in enumerate(doc.get("edit_checks") or []):
        tag = f"edit_checks[{i}] ({ec.get('check_id','?')})"
        for k in ("check_id", "target", "components", "op"):
            if k not in ec:
                errors.append(f"{tag}: missing '{k}'")
        if ec.get("op") not in (None, "sum"):
            warnings.append(f"{tag}: op {ec.get('op')!r} unsupported — check will be not_evaluable")
        if _num(ec.get("tolerance", 0.0)) is None:
            errors.append(f"{tag}: tolerance not numeric")
        for ref in [ec.get("target")] + list(ec.get("components") or []):
            if ref is not None and ref not in ids:
                warnings.append(f"{tag}: references unknown cell {ref!r} — check will be not_evaluable")

    for i, r in enumerate(doc.get("reconciliations") or []):
        tag = f"reconciliations[{i}] ({r.get('recon_id','?')})"
        for k in ("recon_id", "cell_id", "source_value", "reported_value"):
            if k not in r:
                errors.append(f"{tag}: missing '{k}'")
        for k in ("source_value", "reported_value", "tolerance"):
            if k in r and _num(r.get(k)) is None:
                errors.append(f"{tag}: {k} not numeric")

    for i, s in enumerate(doc.get("sign_offs") or []):
        tag = f"sign_offs[{i}] ({s.get('role','?')})"
        for k in ("role", "signed_at"):
            if k not in s or s[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")

    if not doc.get("sign_offs"):
        warnings.append("no 'sign_offs' — sign_off_completeness will fire")
    if not doc.get("prior_period"):
        warnings.append("no 'prior_period' — variance_vs_prior is not_evaluable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_example.json"
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
