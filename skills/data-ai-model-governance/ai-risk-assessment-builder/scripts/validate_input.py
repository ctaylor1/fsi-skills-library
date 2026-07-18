#!/usr/bin/env python3
"""Deterministic input validation for ai-risk-assessment-builder.

Validates an AI risk-assessment intake before the pack is drafted. Fails closed on
structural problems (so a pack is never assembled from an ill-formed intake); warns on data
gaps that force a `needs-data` disposition or reduce a control's credit.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  framework_version, assessment_id, system_name, use_case, inherent_risk_tier, intake_ref,
  model_ref, domains{ <domain>: {likelihood, impact, source_ref, controls[
    {control_id, name, status, evidence_ref, recommended_action}]} }

The ten required domains are: data, model, fairness, explainability, security, privacy,
third_party, human_oversight, resilience, monitoring.

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("framework_version", "assessment_id", "system_name", "domains")
REQUIRED_DOMAINS = (
    "data", "model", "fairness", "explainability", "security",
    "privacy", "third_party", "human_oversight", "resilience", "monitoring",
)
LEVELS = {"Low", "Medium", "High"}
CONTROL_STATUS = {"implemented", "partial", "missing", "not_applicable"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, "", {}):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    domains = doc.get("domains") or {}
    if not isinstance(domains, dict):
        errors.append("domains must be a mapping of domain -> scoring object")
        return errors, warnings

    missing_domains = [d for d in REQUIRED_DOMAINS if d not in domains]
    for d in missing_domains:
        errors.append(f"missing required risk domain '{d}'")

    extra = [d for d in domains if d not in REQUIRED_DOMAINS]
    for d in extra:
        warnings.append(f"domain '{d}' is not one of the ten required domains -> ignored")

    if doc.get("inherent_risk_tier") not in LEVELS:
        warnings.append("inherent_risk_tier missing/invalid (expected from ai-use-case-intake-classifier)")

    for name in REQUIRED_DOMAINS:
        dom = domains.get(name)
        if dom is None:
            continue
        tag = f"domains.{name}"
        if not isinstance(dom, dict):
            errors.append(f"{tag}: must be an object")
            continue
        if dom.get("likelihood") not in LEVELS:
            errors.append(f"{tag}: likelihood must be Low/Medium/High (got {dom.get('likelihood')!r}) -> needs-data")
        if dom.get("impact") not in LEVELS:
            errors.append(f"{tag}: impact must be Low/Medium/High (got {dom.get('impact')!r}) -> needs-data")
        if not dom.get("source_ref"):
            warnings.append(f"{tag}: no source_ref -> domain will lack a citation (needs-data)")
        controls = dom.get("controls")
        if not isinstance(controls, list) or not controls:
            warnings.append(f"{tag}: no controls listed -> coverage is None (residual = inherent)")
            controls = []
        cids = set()
        for j, c in enumerate(controls):
            ctag = f"{tag}.controls[{j}] ({c.get('control_id','?')})"
            if not c.get("control_id"):
                errors.append(f"{ctag}: missing control_id")
            elif c.get("control_id") in cids:
                errors.append(f"{ctag}: duplicate control_id")
            cids.add(c.get("control_id"))
            if c.get("status") not in CONTROL_STATUS:
                errors.append(f"{ctag}: status must be one of {sorted(CONTROL_STATUS)} (got {c.get('status')!r})")
            if c.get("status") in ("implemented", "partial") and not c.get("evidence_ref"):
                warnings.append(f"{ctag}: {c.get('status')} control has no evidence_ref -> treated as unproven (no coverage credit)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "intake_example.json"
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
