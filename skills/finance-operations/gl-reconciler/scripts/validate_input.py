#!/usr/bin/env python3
"""Deterministic input validation for gl-reconciler.

Validates a reconciliation job (GL side + subledger/source side) before matching. Fails
closed on structural problems; warns on data-quality gaps that limit matching or tie-out.

Input schema (JSON): see references/source-map.md. Key fields:
  entity, account, as_of (YYYY-MM-DD), config_version, currency,
  gl_entries[{entry_id,match_key,account,date,amount,currency,source_ref,description}],
  subledger_entries[{...same shape...}],
  config{amount_tolerance,date_tolerance_days,materiality_threshold,recon_suspense_account}

Usage:
  python validate_input.py reconciliation.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("entity", "account", "as_of", "config_version", "gl_entries", "subledger_entries")
REQUIRED_REC = ("entry_id", "match_key", "date", "amount", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _check_side(name, rows, seen_ids, errors, warnings):
    if not isinstance(rows, list):
        errors.append(f"{name} must be a list")
        return
    for i, r in enumerate(rows):
        tag = f"{name}[{i}] ({r.get('entry_id','?')})"
        if not isinstance(r, dict):
            errors.append(f"{tag}: not an object")
            continue
        for k in REQUIRED_REC:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(r.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        if not DATE_RE.match(str(r.get("date", ""))):
            errors.append(f"{tag}: date must start YYYY-MM-DD, got {r.get('date')!r}")
        eid = r.get("entry_id")
        if eid in seen_ids:
            errors.append(f"{tag}: duplicate entry_id across job (entry_id must be unique)")
        seen_ids.add(eid)
        if not r.get("currency"):
            warnings.append(f"{tag}: no currency — assuming job currency; FX differences not evaluable")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    gl = doc.get("gl_entries") or []
    sl = doc.get("subledger_entries") or []
    if not isinstance(gl, list) or not isinstance(sl, list):
        errors.append("gl_entries and subledger_entries must both be lists")
        return errors, warnings
    if len(gl) + len(sl) == 0:
        errors.append("no records: gl_entries and subledger_entries are both empty")
        return errors, warnings

    seen_ids: set = set()
    _check_side("gl_entries", gl, seen_ids, errors, warnings)
    _check_side("subledger_entries", sl, seen_ids, errors, warnings)

    # matching feasibility
    if not any(r.get("match_key") for r in gl) and gl:
        warnings.append("gl_entries have no match_key values — GL items cannot be matched")
    if not any(r.get("match_key") for r in sl) and sl:
        warnings.append("subledger_entries have no match_key values — subledger items cannot be matched")

    cfg = doc.get("config") or {}
    if not cfg:
        warnings.append("no 'config' block — default tolerances/materiality will be used; record the config_version")
    if not doc.get("currency"):
        warnings.append("no job-level 'currency' — record the reconciliation currency")
    if not gl:
        warnings.append("gl_entries empty — every subledger item will classify as unrecorded_in_gl")
    if not sl:
        warnings.append("subledger_entries empty — every GL item will classify as unsupported_in_gl")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reconciliation_example.json"
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
