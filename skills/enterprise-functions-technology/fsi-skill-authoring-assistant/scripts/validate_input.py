#!/usr/bin/env python3
"""Deterministic input validation for fsi-skill-authoring-assistant.

Validates a skill-authoring build request BEFORE a package plan is drafted. Fails closed on
structural problems (so a plan is never assembled from an ill-formed spec) and warns on gaps
that force a `needs-data`, `metadata-incomplete`, or `missing-components` status downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  build_standard_version, as_of_date, skills[
    {skill_id, name, directory, category, archetype, risk_tier, action_mode,
     human_approval, scheduled_agent, skill_type,
     applies_domain_rules?, has_deterministic_computation?,
     metadata{aws-fsi-* string map}, components_present[],
     claims[{statement, approval_id}]?, approvals[{approval_id, role, status}]?}]

This validator reads a documented JSON schema and bundled de-identified fixtures only; it
opens no network connections and calls no live system.

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("build_standard_version", "skills")
REQUIRED_SKILL = ("skill_id", "name", "directory", "archetype", "risk_tier")
NAME_RE = re.compile(r"^(?!-)(?!.*--)[a-z0-9-]+(?<!-)$")
RISK_TIERS = {"R1", "R2", "R3", "R4"}
ARCHETYPES = {
    "Explain & summarize", "Analyze & review", "Model & calculate", "Draft & package",
    "Reconcile & validate", "Monitor & alert", "Investigate & casework", "Domain workflow",
    "Orchestrate & resolve",
}


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

    skills = doc.get("skills") or []
    if not isinstance(skills, list) or not skills:
        errors.append("skills must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, s in enumerate(skills):
        tag = f"skills[{i}] ({s.get('skill_id','?')})"
        for k in REQUIRED_SKILL:
            if k not in s or s[k] in (None, "", [], {}):
                errors.append(f"{tag}: missing '{k}'")
        sid = s.get("skill_id")
        if sid in ids:
            errors.append(f"{tag}: duplicate skill_id")
        ids.add(sid)

        name = s.get("name")
        if name and (not NAME_RE.match(str(name)) or len(str(name)) > 64):
            errors.append(f"{tag}: name {name!r} violates spec constraints (lowercase a-z 0-9 -, no leading/trailing/consecutive hyphens, <=64)")
        directory = s.get("directory")
        if name and directory and Path(str(directory)).name != name:
            errors.append(f"{tag}: name {name!r} must equal the directory basename ({Path(str(directory)).name!r})")

        rt = s.get("risk_tier")
        if rt and rt not in RISK_TIERS:
            errors.append(f"{tag}: risk_tier {rt!r} not one of {sorted(RISK_TIERS)}")
        arch = s.get("archetype")
        if arch and arch not in ARCHETYPES:
            warnings.append(f"{tag}: archetype {arch!r} not a known build archetype -> map it before packaging")

        meta = s.get("metadata")
        if meta is None:
            warnings.append(f"{tag}: no metadata block supplied -> metadata-incomplete")
        elif not isinstance(meta, dict):
            errors.append(f"{tag}: metadata must be an object (string->string map)")
        else:
            for mk, mv in meta.items():
                if not isinstance(mv, str):
                    errors.append(f"{tag}: metadata['{mk}'] must be a string (spec), got {type(mv).__name__}")

        comps = s.get("components_present")
        if comps is None:
            warnings.append(f"{tag}: no components_present listed -> all required components will read as missing")
        elif not isinstance(comps, list):
            errors.append(f"{tag}: components_present must be a list")

        for c in s.get("claims") or []:
            if not c.get("statement"):
                errors.append(f"{tag}: a claim is missing its 'statement'")
            if "approval_id" not in c:
                warnings.append(f"{tag}: claim {c.get('statement','?')!r} has no approval_id -> unsupported claim")

        seen_app = set()
        for a in s.get("approvals") or []:
            aid = a.get("approval_id")
            if not aid or not a.get("role"):
                errors.append(f"{tag}: an approval entry needs approval_id and role")
            if aid in seen_app:
                errors.append(f"{tag}: duplicate approval_id {aid!r}")
            seen_app.add(aid)
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "requests_example.json"
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
