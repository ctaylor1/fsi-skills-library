#!/usr/bin/env python3
"""Deterministic input validation for model-risk-documenter.

Validates a model-documentation intake before the documentation / validation-evidence pack
is assembled. Fails closed on structural problems (so a pack is never built from an ill-formed
intake); warns on data gaps that force a `needs-data` or `gap` section disposition or that make
a cited source untraceable (an artifact without a version).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  template_version, framework_version, model_id, model_name, model_tier, model_version,
  sections{ <section>: {content_ref, source_artifacts[{artifact_id, artifact_type, version,
    date}], coverage[]} }, findings[{finding_id, section, severity, status,
    recommended_remediation, source_refs[]}], approvals[{approval_id, approver_role, decision,
    scope, date, reference}]

The ten required sections are: purpose, methodology, data, performance, limitations, controls,
monitoring, changes, approvals, traceability.

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("template_version", "model_id", "model_name", "sections")
REQUIRED_SECTIONS = (
    "purpose", "methodology", "data", "performance", "limitations",
    "controls", "monitoring", "changes", "approvals", "traceability",
)
TIERS = {"Tier 1", "Tier 2", "Tier 3"}
FINDING_SEVERITY = {"Low", "Medium", "High"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, "", {}):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    sections = doc.get("sections") or {}
    if not isinstance(sections, dict):
        errors.append("sections must be a mapping of section -> content object")
        return errors, warnings

    for s in REQUIRED_SECTIONS:
        if s not in sections:
            errors.append(f"missing required documentation section '{s}'")

    extra = [s for s in sections if s not in REQUIRED_SECTIONS]
    for s in extra:
        warnings.append(f"section '{s}' is not one of the ten required sections -> ignored")

    if doc.get("model_tier") not in TIERS:
        warnings.append("model_tier missing/invalid (expected Tier 1/2/3 from model-inventory-maintainer) -> default routing")
    if not doc.get("framework_version"):
        warnings.append("no framework_version -> cannot pin the model-risk framework the pack is documented against")

    for name in REQUIRED_SECTIONS:
        sec = sections.get(name)
        if sec is None:
            continue
        tag = f"sections.{name}"
        if not isinstance(sec, dict):
            errors.append(f"{tag}: must be an object")
            continue
        if not sec.get("content_ref"):
            warnings.append(f"{tag}: no content_ref -> section is needs-data (missing documentation)")
        artifacts = sec.get("source_artifacts")
        if artifacts is None:
            artifacts = []
        if not isinstance(artifacts, list):
            errors.append(f"{tag}: source_artifacts must be a list")
            artifacts = []
        aids = set()
        for j, a in enumerate(artifacts):
            atag = f"{tag}.source_artifacts[{j}] ({a.get('artifact_id','?')})"
            if not isinstance(a, dict):
                errors.append(f"{atag}: must be an object")
                continue
            if not a.get("artifact_id"):
                errors.append(f"{atag}: missing artifact_id")
            elif a.get("artifact_id") in aids:
                errors.append(f"{atag}: duplicate artifact_id in section")
            aids.add(a.get("artifact_id"))
            if not a.get("version"):
                warnings.append(f"{atag}: no version -> artifact is untraceable (no citation credit; section becomes a gap)")

    findings = doc.get("findings")
    if findings is not None:
        if not isinstance(findings, list):
            errors.append("findings must be a list")
        else:
            fids = set()
            for j, f in enumerate(findings):
                ftag = f"findings[{j}] ({f.get('finding_id','?')})"
                if not f.get("finding_id"):
                    errors.append(f"{ftag}: missing finding_id")
                elif f.get("finding_id") in fids:
                    errors.append(f"{ftag}: duplicate finding_id")
                fids.add(f.get("finding_id"))
                if f.get("severity") not in FINDING_SEVERITY:
                    warnings.append(f"{ftag}: severity missing/invalid (expected Low/Medium/High)")
                if f.get("status") and f.get("status") != "open":
                    errors.append(f"{ftag}: input finding status is {f.get('status')!r}; this skill packages OPEN findings and never closes them")
                if not f.get("recommended_remediation"):
                    warnings.append(f"{ftag}: no recommended_remediation -> pack will flag an unremediated finding")
                if not f.get("source_refs"):
                    warnings.append(f"{ftag}: no source_refs -> finding will lack a citation")

    approvals = doc.get("approvals")
    if approvals is not None:
        if not isinstance(approvals, list):
            errors.append("approvals must be a list")
        else:
            for j, a in enumerate(approvals):
                atag = f"approvals[{j}] ({a.get('approval_id','?')})"
                if not a.get("reference"):
                    warnings.append(f"{atag}: no reference -> unsupported approval attestation; it will be flagged, not recorded as evidence")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_doc_example.json"
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
