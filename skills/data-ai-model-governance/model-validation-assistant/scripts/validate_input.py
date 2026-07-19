#!/usr/bin/env python3
"""Deterministic input validation for model-validation-assistant.

Validates a model-validation intake before the validation-findings pack is drafted. Fails
closed on structural problems (so a pack is never assembled from an ill-formed intake); warns
on data gaps that force a `needs-data` disposition or that strip a control/test of independent
credit.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  framework_version, validation_id, model_id, model_name, model_tier, validation_type,
  intake_ref, areas{ <area>: {status, materiality, independent_evidence, source_ref,
    recommended_action, tests[ {test_id, outcome, evidence_ref} ]} }

The seven required validation areas are: conceptual_soundness, data, performance, outcomes,
limitations, controls, monitoring.

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("framework_version", "validation_id", "model_id", "areas")
REQUIRED_AREAS = (
    "conceptual_soundness", "data", "performance", "outcomes",
    "limitations", "controls", "monitoring",
)
AREA_STATUS = {"pass", "deficiency", "not_tested"}
TEST_OUTCOME = {"pass", "fail", "inconclusive"}
LEVELS = {"Low", "Medium", "High"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, "", {}):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    areas = doc.get("areas") or {}
    if not isinstance(areas, dict):
        errors.append("areas must be a mapping of area -> assessment object")
        return errors, warnings

    for a in REQUIRED_AREAS:
        if a not in areas:
            errors.append(f"missing required validation area '{a}'")

    extra = [a for a in areas if a not in REQUIRED_AREAS]
    for a in extra:
        warnings.append(f"area '{a}' is not one of the seven required areas -> ignored")

    if doc.get("model_tier") not in LEVELS:
        warnings.append("model_tier missing/invalid (expected Low/Medium/High from the model inventory)")

    for name in REQUIRED_AREAS:
        area = areas.get(name)
        if area is None:
            continue
        tag = f"areas.{name}"
        if not isinstance(area, dict):
            errors.append(f"{tag}: must be an object")
            continue
        if area.get("status") not in AREA_STATUS:
            errors.append(f"{tag}: status must be one of {sorted(AREA_STATUS)} (got {area.get('status')!r}) -> needs-data")
        if area.get("materiality") not in LEVELS:
            warnings.append(f"{tag}: materiality missing/invalid (defaults to Medium)")
        if not area.get("source_ref"):
            warnings.append(f"{tag}: no source_ref -> area will lack a citation (needs-data)")
        if area.get("status") == "pass" and not area.get("independent_evidence"):
            warnings.append(f"{tag}: declared pass without independent_evidence -> treated as not independently validated (no credit)")
        tests = area.get("tests")
        if tests is not None and not isinstance(tests, list):
            errors.append(f"{tag}: tests must be a list when present")
            tests = []
        tids = set()
        for j, t in enumerate(tests or []):
            ttag = f"{tag}.tests[{j}] ({(t or {}).get('test_id','?')})"
            if not isinstance(t, dict):
                errors.append(f"{ttag}: must be an object")
                continue
            if not t.get("test_id"):
                errors.append(f"{ttag}: missing test_id")
            elif t.get("test_id") in tids:
                errors.append(f"{ttag}: duplicate test_id")
            tids.add(t.get("test_id"))
            if t.get("outcome") not in TEST_OUTCOME:
                errors.append(f"{ttag}: outcome must be one of {sorted(TEST_OUTCOME)} (got {t.get('outcome')!r})")
            if t.get("outcome") in ("pass", "fail") and not t.get("evidence_ref"):
                warnings.append(f"{ttag}: {t.get('outcome')} test has no evidence_ref -> treated as unproven (no independent credit)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "validation_intake_example.json"
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
