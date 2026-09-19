#!/usr/bin/env python3
"""Deterministic filing-completeness checks for insurance-rate-form-filing-packager.

Tests a filing's components/exhibits against the approved checklist: required-component
completeness, required-exhibit presence, rate-change support, and effective-date notice lead.
Emits a gap-evidence packet with a review-only disposition. Never submits, approves, or sets a
rate — evidence only.

Usage: python calculate_or_transform.py filing.json | --selftest
"""
from __future__ import annotations
import datetime as _dt
import json, sys
from pathlib import Path

DISCLAIMER = ("Filing-gap evidence only; not a filing submission or a compliance certification. "
              "No filing has been submitted and no rate has been approved.")


def _date(s):
    try:
        return _dt.date.fromisoformat(str(s))
    except (TypeError, ValueError):
        return None


def compute(doc: dict) -> dict:
    from validate_input import validate
    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    f = doc["filing"]
    ck = doc["checklist"]
    gaps = []
    checks_run = ["component_completeness", "exhibit_presence"]
    not_evaluable = []
    not_applicable = []

    def gap(rule, expected, found, ref):
        gaps.append({"rule": rule, "expected": expected, "found": found,
                     "citation": f"filing:{ref}"})

    present_types = {c.get("type") for c in doc.get("components", []) if c.get("present")}
    ref_by_type = {c.get("type"): c.get("source_ref", "?") for c in doc.get("components", [])}
    for rc in ck.get("required_components") or []:
        if rc not in present_types:
            gap("component_completeness", "present", "missing",
                f"component={rc};{ref_by_type.get(rc, 'not-attached')}")

    present_exh = {e.get("exhibit_id") for e in doc.get("exhibits", []) if e.get("present")}
    ref_by_exh = {e.get("exhibit_id"): e.get("source_ref", "?") for e in doc.get("exhibits", [])}
    for rx in ck.get("required_exhibits") or []:
        if rx not in present_exh:
            gap("exhibit_presence", "present", "missing",
                f"exhibit={rx};{ref_by_exh.get(rx, 'not-attached')}")

    # rate support
    if f.get("filing_type") == "rate" and ck.get("indicated_rate_change_pct") is not None:
        try:
            filed = float(f.get("proposed_rate_change_pct"))
            indicated = float(ck.get("indicated_rate_change_pct"))
            tol = float(ck.get("rate_tolerance_pct", 0.0))
            checks_run.append("rate_support")
            if filed > indicated + tol and "rate_justification" not in present_types:
                gap("rate_support", f"<= indicated {indicated}% (+{tol}%) or justification",
                    f"filed {filed}% with no rate_justification component",
                    f"filing={f.get('filing_id')};proposed_rate_change_pct")
        except (TypeError, ValueError):
            not_evaluable.append("rate_support")
    elif f.get("filing_type") == "rate":
        not_evaluable.append("rate_support")
    else:
        not_applicable.append("rate_support")

    # effective-date notice lead
    d_as_of, d_eff = _date(f.get("as_of")), _date(f.get("effective_date"))
    min_notice = ck.get("min_notice_days")
    if d_as_of and d_eff and min_notice is not None:
        checks_run.append("effective_notice")
        lead = (d_eff - d_as_of).days
        if lead < int(min_notice):
            gap("effective_notice", f">= {min_notice} days lead", f"{lead} days",
                f"filing={f.get('filing_id')};effective_date")

    else:
        not_evaluable.append("effective_notice")

    disposition = "incomplete" if not_evaluable else ("ready-for-review" if not gaps else "gaps-for-review")
    return {
        "calculation_inputs": doc,
        "packet_id": f"irfp-{f.get('filing_id', 'UNKNOWN')}-0001",
        "filing_id": f.get("filing_id"),
        "filing_type": f.get("filing_type"),
        "checklist_version": ck.get("config_version"),
        "checks_run": checks_run,
        "not_evaluable": not_evaluable,
        "not_applicable": not_applicable,
        "gaps": gaps,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }



# Bind native result and source snapshot to the portable insurance evidence contract.
_native_compute = compute
def compute(doc):
    from insurance_contract import build_artifact, stable_hash
    result = _native_compute(doc)
    output = result[0] if isinstance(result, tuple) else result
    issues = []
    for field in ("not_evaluable", "data_gaps"):
        for item in output.get(field, []):
            issues.append(str(item))
    if output.get("cost_comparison_status") == "not_comparable":
        issues.append("quotes are not directly comparable; aggregate ranking suppressed")
    for item in output.get("segments", []):
        if not item.get("packageable"):
            issues.append(f"segment {item.get('segment_id')}: {item.get('status')}")
    for item in output.get("profiles", []):
        if item.get("recommended_disposition") == "needs-data":
            issues.append(f"submission {item.get('submission_id')} requires data")
    for item in output.get("reconciliation", []):
        if item.get("status") in {"mismatch", "unparseable"}:
            issues.append(f"unresolved source conflict: {item.get('field')}")
    for key in ("comparison_id", "analysis_id", "review_id", "packet_id", "worksheet_id", "triage_id", "interpretation_id"):
        if key in output:
            output[key] = "filing_review-" + stable_hash(doc)[:24]
    output["artifact"] = build_artifact(doc, output, producer="insurance-rate-form-filing-packager", artifact_type="filing_review",
        completeness="partial" if issues else "complete", evaluability="partial" if issues else "evaluable", issues=issues)
    return result


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "filing_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
