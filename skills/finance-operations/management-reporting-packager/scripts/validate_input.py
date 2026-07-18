#!/usr/bin/env python3
"""Deterministic input validation for management-reporting-packager.

Validates a management-report package input before assembly. Fails closed on structural
problems; warns on data gaps that will BLOCK the package (unsupported claims, missing
variance baselines, missing reconciliations/approvals) rather than silently drafting them.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, period, entity, reporting_tolerance,
  kpis[{id, name, value, unit, source_ref, budget?, prior?, commentary?,
        commentary_source_ref?}],
  reconciliations[{name, ledger_balance, subledger_balance, tolerance?, source_ref}],
  exceptions[{id, description, severity, source_ref}],
  approvals[{role, approver, status, source_ref?}]

Usage: python validate_input.py package.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "period", "entity", "kpis")
REQUIRED_KPI = ("id", "name", "value", "unit", "source_ref")
REQUIRED_RECON = ("name", "ledger_balance", "subledger_balance")
REQUIRED_APPROVAL_ROLES = {"preparer", "reviewer"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    kpis = doc.get("kpis") or []
    if not isinstance(kpis, list) or not kpis:
        errors.append("kpis must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, k in enumerate(kpis):
        tag = f"kpis[{i}] ({k.get('id', '?')})"
        for f in REQUIRED_KPI:
            if f not in k or k[f] in (None, ""):
                errors.append(f"{tag}: missing '{f}'")
        kid = k.get("id")
        if kid in ids:
            errors.append(f"{tag}: duplicate kpi id")
        ids.add(kid)
        if not isinstance(k.get("value"), (int, float)):
            errors.append(f"{tag}: value must be numeric")
        if k.get("budget") is None and k.get("prior") is None:
            warnings.append(f"{tag}: no budget/prior baseline -> variance will be not-computable")
        if k.get("commentary") and not k.get("commentary_source_ref"):
            warnings.append(f"{tag}: commentary present without commentary_source_ref -> UNSUPPORTED claim (will block)")

    recons = doc.get("reconciliations")
    if not recons:
        warnings.append("no reconciliations provided -> tie-out section will be empty (will block ready-for-review)")
    else:
        for i, r in enumerate(recons):
            rtag = f"reconciliations[{i}] ({r.get('name', '?')})"
            for f in REQUIRED_RECON:
                if f not in r or r[f] in (None, ""):
                    errors.append(f"{rtag}: missing '{f}'")
            for f in ("ledger_balance", "subledger_balance"):
                if f in r and not isinstance(r[f], (int, float)):
                    errors.append(f"{rtag}: {f} must be numeric")

    approvals = doc.get("approvals") or []
    roles = {a.get("role") for a in approvals if isinstance(a, dict)}
    missing_roles = REQUIRED_APPROVAL_ROLES - roles
    if missing_roles:
        warnings.append(f"missing required approval role(s) {sorted(missing_roles)} -> will block ready-for-review")
    for a in approvals:
        if a.get("role") == "delivery" and a.get("status") not in (None, "", "pending", "not-granted", "n/a"):
            warnings.append("delivery approval is pre-marked granted -> draft-only skill keeps delivery pending (human/external action)")

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
