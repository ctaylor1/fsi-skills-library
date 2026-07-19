#!/usr/bin/env python3
"""Deterministic input validation for risk-control-self-assessment-assistant.

Validates a first-line RCSA input before scoring. Fails closed on structural problems;
warns on data gaps that would force an evidence gap, an owner-TBD remediation, or a
statement challenge downstream.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, entity, assessment_period{from,to}, as_of_date, risk_appetite,
  risks[{risk_id, statement, category, inherent_impact(1-5), inherent_likelihood(1-5),
    controls[{control_id, description, design_rating, operating_rating, evidence[]}],
    remediation{action, owner, due_date} (optional)}]

Usage: python validate_input.py rcsa_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "entity", "assessment_period", "as_of_date",
                "risk_appetite", "risks")
REQUIRED_RISK = ("risk_id", "statement", "inherent_impact", "inherent_likelihood")
RATINGS = {"Effective", "Partially Effective", "Ineffective"}
APPETITE = {"Low", "Medium", "High", "Critical"}


def _int_1_5(v):
    return isinstance(v, int) and 1 <= v <= 5


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if doc.get("risk_appetite") not in APPETITE:
        errors.append(f"risk_appetite must be one of {sorted(APPETITE)}")
    per = doc.get("assessment_period") or {}
    if not (per.get("from") and per.get("to")):
        errors.append("assessment_period requires 'from' and 'to'")

    risks = doc.get("risks") or []
    if not isinstance(risks, list) or not risks:
        errors.append("risks must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, r in enumerate(risks):
        tag = f"risks[{i}] ({r.get('risk_id','?')})"
        for k in REQUIRED_RISK:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        rid = r.get("risk_id")
        if rid in ids:
            errors.append(f"{tag}: duplicate risk_id")
        ids.add(rid)
        if not _int_1_5(r.get("inherent_impact")):
            errors.append(f"{tag}: inherent_impact must be an integer 1-5")
        if not _int_1_5(r.get("inherent_likelihood")):
            errors.append(f"{tag}: inherent_likelihood must be an integer 1-5")

        controls = r.get("controls") or []
        if not controls:
            warnings.append(f"{tag}: no controls mapped -> residual will equal inherent (challenge)")
        cids = set()
        for j, c in enumerate(controls):
            ctag = f"{tag} control[{j}] ({c.get('control_id','?')})"
            if not c.get("control_id"):
                errors.append(f"{ctag}: missing control_id")
            elif c.get("control_id") in cids:
                errors.append(f"{ctag}: duplicate control_id within risk")
            cids.add(c.get("control_id"))
            for dim in ("design_rating", "operating_rating"):
                if c.get(dim) is not None and c.get(dim) not in RATINGS:
                    errors.append(f"{ctag}: {dim}={c.get(dim)!r} not in {sorted(RATINGS)}")
            credited = c.get("design_rating") in RATINGS and c.get("operating_rating") in RATINGS
            if credited and not c.get("evidence"):
                warnings.append(f"{ctag}: rated without evidence -> will be Unsubstantiated (evidence gap)")

        rem = r.get("remediation")
        if rem and not rem.get("owner"):
            warnings.append(f"{tag}: remediation provided without owner -> owner will be TBD")

    if doc.get("as_of_date") and per.get("to") and str(doc["as_of_date"]) < str(per["to"]):
        warnings.append("as_of_date precedes assessment period end -> remediation aging may be premature")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "rcsa_input.json"
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
