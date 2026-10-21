#!/usr/bin/env python3
"""Deterministic input validation for privacy-impact-assessment-assistant.

Validates a privacy / data-protection impact assessment (PIA/DPIA) intake file before a
draft assessment is assembled. Fails closed on structural problems; warns on evidence gaps
that force a `needs-information` draft (never a guess). Stdlib-only, self-contained, operates
on a documented JSON schema — no live calls.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, template_version, jurisdiction, assessment_id,
  processing{processing_id, name, business_owner_role, dpia_trigger[], processing_ref},
  required_approvals[], recorded_approvals[{role, approver, date}],
  risk_factors{special_category_data, criminal_offence_data, children_or_vulnerable_subjects,
    large_scale_processing, systematic_monitoring, automated_decision_making_legal_effect,
    novel_technology, international_transfer_high_risk[], data_matching_combining,
    retention_exceeds_policy, has_processors,
    no_lawful_basis, special_category_no_condition, international_transfer_no_mechanism},
  evidence{<section>: {present, items[], citations[], gaps[]}}

Usage: python validate_input.py case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys, math
from datetime import date
from pathlib import Path
from native_integrity import canonical_hash

REQUIRED_TOP = ("config_version", "assessment_id", "processing", "evidence", "required_approvals")
REQUIRED_PROCESSING = ("processing_id", "name", "dpia_trigger")
# The eight evidence sections a PIA/DPIA must marshal (purpose, data, legal basis, sharing,
# retention, security, rights, mitigations). A missing/gap section does not fail validation;
# it forces a `needs-information` draft downstream.
REQUIRED_EVIDENCE = (
    "processing_purpose", "data_inventory", "legal_basis", "data_sharing",
    "retention", "security", "data_subject_rights", "mitigations",
)


def _validate_impl(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if not isinstance(doc, dict): return ["input must be an object"], warnings
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not doc.get("jurisdiction") or not doc.get("legal_profile"):
        warnings.append("jurisdiction/legal profile unresolved; needs-information, no inferred GDPR applicability")
    profile = doc.get("legal_profile", {})
    if not isinstance(profile, dict): errors.append("legal_profile must be an object")
    elif profile.get("applicability_status") == "supplied-reviewed" and not all(profile.get(k) for k in ("framework", "rationale", "source_ref", "reviewed_by")):
        errors.append("reviewed legal profile needs framework, rationale, source_ref and reviewed_by")
    if not isinstance(doc.get("source_registry", {}), dict): errors.append("source_registry must be an object")
    proc = doc.get("processing") or {}
    if not isinstance(proc, dict):
        errors.append("processing must be an object")
    else:
        for k in REQUIRED_PROCESSING:
            if k not in proc or proc[k] in (None, "", []):
                errors.append(f"processing: missing '{k}'")
        if proc.get("dpia_trigger") and not isinstance(proc["dpia_trigger"], list):
            errors.append("processing.dpia_trigger must be a list")

    req_appr = doc.get("required_approvals")
    if not isinstance(req_appr, list) or not req_appr or any(not isinstance(role, str) or not role.strip() for role in req_appr):
        errors.append("required_approvals must be a non-empty list of approver roles")

    ev = doc.get("evidence")
    if not isinstance(ev, dict):
        errors.append("evidence must be an object of sections")
        return errors, warnings

    for sec in REQUIRED_EVIDENCE:
        s = ev.get(sec)
        if s is None:
            warnings.append(f"evidence.{sec} absent -> assessment will mark this section a gap (needs-information)")
            continue
        if not isinstance(s, dict):
            errors.append(f"evidence.{sec} must be an object")
            continue
        for field in ("items", "citations", "gaps"):
            if field in s and not isinstance(s[field], list): errors.append(f"evidence.{sec}.{field} must be a list")
        present = bool(s.get("present"))
        has_items = bool(s.get("items"))
        has_cites = bool(s.get("citations"))
        if present and not has_items:
            warnings.append(f"evidence.{sec}: marked present but no items -> gap (needs-information)")
        if present and not has_cites:
            warnings.append(f"evidence.{sec}: present items without citations -> unsupported; will be a gap (needs-information)")
        if not present:
            warnings.append(f"evidence.{sec}: not present -> gap (needs-information)")

    rf = doc.get("risk_factors")
    if rf is None:
        warnings.append("no risk_factors provided -> privacy-risk indicator is Unknown; needs-information")
    elif not isinstance(rf, dict):
        errors.append("risk_factors must be an object")
    else:
        if rf.get("international_transfer_high_risk") is not None and not isinstance(rf["international_transfer_high_risk"], list):
            errors.append("risk_factors.international_transfer_high_risk must be a list of transfer nexuses")
        for key, value in rf.items():
            if key != "international_transfer_high_risk" and value is not None and type(value) is not bool:
                errors.append(f"risk_factors.{key} must be boolean or null")
        for hb, msg in (
            ("no_lawful_basis", "no lawful basis identified"),
            ("special_category_no_condition", "special-category data without an Article 9 condition"),
            ("international_transfer_no_mechanism", "restricted international transfer without a valid transfer mechanism"),
        ):
            if rf.get(hb) is True:
                warnings.append(f"risk_factors.{hb} is true -> HARD BOUNDARY ({msg}): assessment will be blocked and routed to privacy counsel; no decision is made here")

    cfg = doc.get("risk_config", {})
    if not isinstance(cfg, dict): errors.append("risk_config must be an object")
    else:
        for key, value in cfg.items():
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                errors.append(f"risk_config.{key} must be finite and nonnegative")
        if cfg.get("medium_min", 4) >= cfg.get("high_min", 8): errors.append("medium_min must be below high_min")
    records = doc.get("recorded_approvals", [])
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records): errors.append("recorded_approvals must be a list of objects")
    if doc.get("recorded_approvals") is None:
        warnings.append("no recorded_approvals -> approval ledger will list all required approvals as pending (expected for a draft)")
    return errors, warnings


def validate(doc):
    try:
        canonical_hash(doc)  # Reject non-finite and non-JSON values anywhere, before the method.
        return _validate_impl(doc)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        return ["malformed input: " + str(exc)], []


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pia_case_example.json"
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
