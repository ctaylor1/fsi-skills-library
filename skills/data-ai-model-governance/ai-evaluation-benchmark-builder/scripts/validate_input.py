#!/usr/bin/env python3
"""Deterministic input validation for ai-evaluation-benchmark-builder.

Validates an evaluation-benchmark build request before a benchmark package is drafted. Fails
closed on structural problems (so a benchmark is never assembled from an ill-formed request);
warns on data gaps that will force a `needs-data`, `needs-calibration`, or `insufficient-sample`
disposition on individual evaluations.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  spec_version, as_of_date?, system_under_eval{model_id, name?, version?, use_case?,
    risk_rating(High|Medium|Low), registry_ref?}, approved_sources[
    {source_id, type(policy|model_card|regulation|risk_appetite|sla|standard), ref, owner?}],
  requirements[
    {eval_id, dimension(task|trigger|regression|safety|robustness|latency|cost),
     description?, dataset_ref?, metric, sample_size?,
     threshold{operator(>=|<=|>|<|==), value, source_id?}?,
     baseline{value, source_id?}?}]

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("spec_version", "system_under_eval", "requirements")
REQUIRED_REQ = ("eval_id", "dimension", "metric")
KNOWN_DIMENSIONS = {"task", "trigger", "regression", "safety", "robustness", "latency", "cost"}
RISK = {"High", "Medium", "Low"}
OPERATORS = {">=", "<=", ">", "<", "=="}


def _is_iso_date(v) -> bool:
    try:
        date.fromisoformat(str(v))
        return True
    except Exception:
        return False


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if doc.get("as_of_date") and not _is_iso_date(doc.get("as_of_date")):
        errors.append("as_of_date is not an ISO date (YYYY-MM-DD)")

    sue = doc.get("system_under_eval") or {}
    if not isinstance(sue, dict):
        errors.append("system_under_eval must be an object")
    else:
        if not sue.get("model_id"):
            errors.append("system_under_eval.model_id is required (identify the system under evaluation)")
        if sue.get("risk_rating") not in RISK:
            errors.append(f"system_under_eval.risk_rating must be one of {sorted(RISK)} (drives required coverage)")

    approved = doc.get("approved_sources") or []
    source_ids = set()
    for i, s in enumerate(approved):
        if not s.get("source_id"):
            errors.append(f"approved_sources[{i}]: missing source_id")
        else:
            source_ids.add(s["source_id"])
    if not approved:
        warnings.append("no approved_sources supplied -> every threshold/baseline will be 'proposed' (needs-calibration)")

    reqs = doc.get("requirements") or []
    if not isinstance(reqs, list) or not reqs:
        errors.append("requirements must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, r in enumerate(reqs):
        tag = f"requirements[{i}] ({r.get('eval_id','?')})"
        for k in REQUIRED_REQ:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        eid = r.get("eval_id")
        if eid in ids:
            errors.append(f"{tag}: duplicate eval_id")
        ids.add(eid)

        dim = r.get("dimension")
        if dim and dim not in KNOWN_DIMENSIONS:
            warnings.append(f"{tag}: dimension {dim!r} not in taxonomy {sorted(KNOWN_DIMENSIONS)} -> needs-data")

        if not r.get("dataset_ref"):
            warnings.append(f"{tag}: no dataset_ref -> no representative dataset (needs-data)")
        if r.get("sample_size") in (None, ""):
            warnings.append(f"{tag}: no sample_size -> treated as 0 (insufficient-sample)")

        for key in ("threshold", "baseline"):
            spec = r.get(key)
            if spec is None:
                continue
            if not isinstance(spec, dict) or spec.get("value") in (None, ""):
                errors.append(f"{tag}: {key} must be an object carrying a numeric 'value'")
                continue
            if key == "threshold" and spec.get("operator") not in OPERATORS:
                errors.append(f"{tag}: threshold.operator must be one of {sorted(OPERATORS)}")
            sid = spec.get("source_id")
            if not sid:
                warnings.append(f"{tag}: {key} has a value but no source_id -> 'proposed' (needs-calibration)")
            elif source_ids and sid not in source_ids:
                warnings.append(f"{tag}: {key}.source_id {sid!r} not in approved_sources -> 'proposed' (needs-calibration)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "benchmark_request_example.json"
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
