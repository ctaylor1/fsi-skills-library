#!/usr/bin/env python3
"""Deterministic input validation for model-change-impact-analyzer.

Validates a proposed model/agent change record before impact assessment. Fails closed on
structural problems; warns on data-quality gaps that limit which change dimensions are
evaluable or that weaken the evidence behind a finding.

Input schema (JSON): see references/source-map.md. Key fields:
  change_id, as_of (YYYY-MM-DD), config_version,
  model{model_id, materiality (high|moderate|low), regulated_use (bool), is_agent (bool)},
  proposed_change{summary, requested_by, target_deploy},
  dimensions[{dimension, changed (bool), before, after, risk_flags[], evidence_ref}]

Usage:
  python validate_input.py change_record.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("change_id", "as_of", "config_version", "model", "dimensions")
REQUIRED_MODEL = ("model_id", "materiality", "regulated_use", "is_agent")
KNOWN_DIMENSIONS = {
    "scope", "data", "tools", "behavior", "controls", "testing", "users", "regulatory",
}
KNOWN_FLAGS = {
    "data_provenance_changed", "threshold_loosened", "control_weakened", "oversight_removed",
    "autonomy_increased", "regulatory_surface_changed", "scope_expanded", "new_tool_added",
    "permission_broadened", "eval_coverage_reduced",
}
MATERIALITY = {"high", "moderate", "low"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    model = doc.get("model") or {}
    if not isinstance(model, dict):
        errors.append("model must be an object")
        return errors, warnings
    for k in REQUIRED_MODEL:
        if k not in model or model[k] in (None, ""):
            errors.append(f"model: missing '{k}'")
    if model.get("materiality") not in MATERIALITY:
        errors.append(f"model.materiality must be one of {sorted(MATERIALITY)}, got {model.get('materiality')!r}")
    if not isinstance(model.get("regulated_use"), bool):
        errors.append("model.regulated_use must be a boolean")
    if not isinstance(model.get("is_agent"), bool):
        errors.append("model.is_agent must be a boolean")

    dims = doc.get("dimensions") or []
    if not isinstance(dims, list) or not dims:
        errors.append("dimensions must be a non-empty list")
        return errors, warnings

    seen = set()
    changed_count = 0
    has_tools_dim = False
    for i, d in enumerate(dims):
        tag = f"dimensions[{i}] ({d.get('dimension','?')})"
        name = d.get("dimension")
        if name not in KNOWN_DIMENSIONS:
            errors.append(f"{tag}: unknown dimension (allowed: {sorted(KNOWN_DIMENSIONS)})")
        elif name in seen:
            errors.append(f"{tag}: duplicate dimension")
        seen.add(name)
        if name == "tools":
            has_tools_dim = True
        if not isinstance(d.get("changed"), bool):
            errors.append(f"{tag}: 'changed' must be a boolean")
            continue
        flags = d.get("risk_flags") or []
        if not isinstance(flags, list):
            errors.append(f"{tag}: risk_flags must be a list")
            flags = []
        if d.get("changed"):
            changed_count += 1
            if not (str(d.get("evidence_ref") or "").strip()):
                errors.append(f"{tag}: changed dimension missing 'evidence_ref' (evidence is mandatory)")
            if not (str(d.get("before") or "").strip()) or not (str(d.get("after") or "").strip()):
                warnings.append(f"{tag}: changed dimension has thin before/after detail — finding will be low-evidence")
            for f in flags:
                if f not in KNOWN_FLAGS:
                    warnings.append(f"{tag}: unknown risk_flag {f!r} will be ignored in banding")
        else:
            if flags:
                warnings.append(f"{tag}: risk_flags present on an unchanged dimension — ignored")

    for req in sorted(KNOWN_DIMENSIONS):
        if req not in seen:
            warnings.append(f"dimension '{req}' not present — reported as not_evaluable")

    if changed_count == 0:
        warnings.append("no dimension marked changed — assessment will resolve to Low (no material change)")
    if model.get("is_agent") and not has_tools_dim:
        warnings.append("model.is_agent is true but no 'tools' dimension supplied — tool/permission change may be unassessed")
    if not doc.get("config"):
        warnings.append("no 'config' block — default banding thresholds will be used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "change_record_example.json"
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
