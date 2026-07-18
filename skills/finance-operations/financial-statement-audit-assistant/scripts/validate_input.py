#!/usr/bin/env python3
"""Deterministic input validation for financial-statement-audit-assistant.

Validates a de-identified audit request before a working paper is drafted. Fails closed on
structural problems; warns on data gaps that force follow-up (needs-data) rather than a
guessed result.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version, engagement{entity,period,framework,reporting_currency},
  planning{overall_materiality, performance_materiality, clearly_trivial_threshold,
           tolerable_misstatement, reliability_factor, sample_seed},
  financial_statements[{caption, assertion, fs_amount, tb_accounts[], source_ref}],
  trial_balance[{account, description, balance, source_ref}],
  population{label, assertion, source_ref, items[{item_id, amount, source_ref}]},
  known_misstatements[{finding_id, description, amount, type, source_ref}],
  approvals[{role, name, status, date}]

Usage: python validate_input.py audit_request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "engagement", "planning")
REQUIRED_ENG = ("entity", "period", "framework")
REQUIRED_PLAN = ("overall_materiality", "performance_materiality", "tolerable_misstatement",
                 "reliability_factor")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    eng = doc.get("engagement") or {}
    for k in REQUIRED_ENG:
        if not eng.get(k):
            errors.append(f"engagement missing '{k}'")

    plan = doc.get("planning") or {}
    for k in REQUIRED_PLAN:
        if k not in plan:
            errors.append(f"planning missing '{k}'")
        elif not _num(plan[k]):
            errors.append(f"planning['{k}'] must be numeric")
    if _num(plan.get("reliability_factor")) and plan["reliability_factor"] <= 0:
        errors.append("planning.reliability_factor must be > 0 (used as the MUS divisor)")
    if _num(plan.get("tolerable_misstatement")) and plan["tolerable_misstatement"] <= 0:
        errors.append("planning.tolerable_misstatement must be > 0")
    if (_num(plan.get("performance_materiality")) and _num(plan.get("overall_materiality"))
            and plan["performance_materiality"] > plan["overall_materiality"]):
        errors.append("planning.performance_materiality cannot exceed overall_materiality")
    if "clearly_trivial_threshold" not in plan:
        warnings.append("planning.clearly_trivial_threshold missing -> defaults to 0 (every difference flags)")

    fs = doc.get("financial_statements") or []
    tb_accounts = {r.get("account") for r in (doc.get("trial_balance") or [])}
    if not fs:
        warnings.append("no financial_statements provided -> no tie-outs will be produced")
    for i, f in enumerate(fs):
        tag = f"financial_statements[{i}] ({f.get('caption','?')})"
        for k in ("caption", "fs_amount", "tb_accounts", "source_ref"):
            if k not in f or f[k] in (None, "", []):
                errors.append(f"{tag}: missing '{k}'")
        for a in f.get("tb_accounts") or []:
            if a not in tb_accounts:
                warnings.append(f"{tag}: tb_account '{a}' absent from trial_balance -> tie-out will be 'unmapped' (needs-data)")

    pop = doc.get("population") or {}
    items = pop.get("items") or []
    if not items:
        warnings.append("no population.items provided -> sampling will not be performed")
    else:
        seen = set()
        for j, it in enumerate(items):
            tag = f"population.items[{j}] ({it.get('item_id','?')})"
            if not it.get("item_id"):
                errors.append(f"{tag}: missing item_id")
            if not _num(it.get("amount")):
                errors.append(f"{tag}: amount must be numeric")
            if not it.get("source_ref"):
                warnings.append(f"{tag}: missing source_ref -> selection would be uncitable")
            if it.get("item_id") in seen:
                errors.append(f"{tag}: duplicate item_id")
            seen.add(it.get("item_id"))

    approvals = doc.get("approvals") or []
    roles = {a.get("role") for a in approvals}
    if "Preparer" not in roles:
        warnings.append("approvals missing 'Preparer' -> a draft cannot be reviewer-signed without a preparer")
    if "Reviewer" not in roles:
        warnings.append("approvals missing 'Reviewer' -> engagement review sign-off not recorded")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "audit_request_example.json"
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
