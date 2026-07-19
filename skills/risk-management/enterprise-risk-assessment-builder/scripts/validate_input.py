#!/usr/bin/env python3
"""Deterministic input validation for enterprise-risk-assessment-builder.

Validates a risk-assessment input file before the assessment is drafted. Fails closed on
structural problems; warns on completeness gaps that force a `needs-evidence` disposition or
prevent taking control credit.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  template_version, config_version, scope{entity, assessment_period, basis},
  appetite{<category>: band, default: band},
  risks[{risk_id, title, category, owner, inherent{likelihood(1-5), impact(1-5)},
         control_ids[], indicator_ids[], loss_event_ids[], scenario_ids[],
         treatment_action_ids[], source_ref}],
  controls[{control_id, title, design, operating, evidence_ref, owner}],
  indicators[], loss_events[], scenarios[], treatment_actions[]

Usage: python validate_input.py assessment.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("template_version", "scope", "appetite", "risks", "controls")
REQUIRED_RISK = ("risk_id", "title", "category", "owner", "inherent", "source_ref")
EFFECTIVENESS = {"Effective", "Partially Effective", "Ineffective", "Not Tested"}
BANDS = {"Low", "Moderate", "High", "Critical"}
UNTESTED = {"Not Tested", None, ""}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    appetite = doc.get("appetite") or {}
    for cat, band in appetite.items():
        if band not in BANDS:
            errors.append(f"appetite['{cat}']={band!r} not a valid band {sorted(BANDS)}")

    controls = {c.get("control_id"): c for c in (doc.get("controls") or [])}
    for cid, c in controls.items():
        tag = f"controls[{cid}]"
        if c.get("design") not in EFFECTIVENESS:
            errors.append(f"{tag}: design={c.get('design')!r} not in {sorted(EFFECTIVENESS)}")
        if c.get("operating") not in EFFECTIVENESS:
            errors.append(f"{tag}: operating={c.get('operating')!r} not in {sorted(EFFECTIVENESS)}")
        proven = c.get("design") not in UNTESTED and c.get("operating") not in UNTESTED
        if proven and not c.get("evidence_ref"):
            warnings.append(f"{tag}: tested control has no evidence_ref -> effectiveness claim is unsupported (no residual credit)")

    risks = doc.get("risks") or []
    if not isinstance(risks, list) or not risks:
        errors.append("risks must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, r in enumerate(risks):
        tag = f"risks[{i}] ({r.get('risk_id', '?')})"
        for k in REQUIRED_RISK:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        rid = r.get("risk_id")
        if rid in ids:
            errors.append(f"{tag}: duplicate risk_id")
        ids.add(rid)
        inh = r.get("inherent") or {}
        for dim in ("likelihood", "impact"):
            v = inh.get(dim)
            if not isinstance(v, int) or not (1 <= v <= 5):
                errors.append(f"{tag}: inherent.{dim}={v!r} must be an integer 1-5")
        cat = r.get("category")
        if cat and cat not in appetite and "default" not in appetite:
            warnings.append(f"{tag}: no appetite band for category '{cat}' and no default -> cannot assess appetite")
        for cref in r.get("control_ids") or []:
            if cref not in controls:
                errors.append(f"{tag}: references unknown control_id '{cref}'")
        if not (r.get("control_ids") or []):
            warnings.append(f"{tag}: no linked controls -> residual will equal inherent (no credit)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_input.json"
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
