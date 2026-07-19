#!/usr/bin/env python3
"""Deterministic independent model-validation engine for model-validation-assistant.

For each of the seven required validation areas (conceptual_soundness, data, performance,
outcomes, limitations, controls, monitoring) this derives an *independent* validated status
from the declared status, the independence of the supporting evidence, and the recorded test
outcomes; generates open validation findings; rolls up the highest finding severity; maps a
NON-decisional recommended disposition and the correct approver routing; and emits a
validation-outcome block set to `pending`. It never approves, certifies, or authorizes a
model for use, makes no final validation decision, closes no finding, and assembles no
governed model documentation pack.

Independence rule (SR 11-7): a declared `pass` counts as validated only when the validator
holds independent evidence (`independent_evidence: true` AND a `source_ref`). A pass that is
only developer-attested, or contradicted by a failed test, gets no credit and is surfaced as
a coverage/independence gap or a deficiency — never silently accepted.

Rules: references/domain-rules.md.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the validation-report JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_AREAS = (
    "conceptual_soundness", "data", "performance", "outcomes",
    "limitations", "controls", "monitoring",
)
LEVELS = {"Low", "Medium", "High"}
SEV_ORDER = {"None": 0, "Low": 1, "Medium": 2, "High": 3}
AREA_OWNER = {
    "conceptual_soundness": "Model Development",
    "data": "Data Governance",
    "performance": "Model Development",
    "outcomes": "Model Owner",
    "limitations": "Model Owner",
    "controls": "Model Risk Controls",
    "monitoring": "Model Monitoring / MLOps",
}
DEFAULT_REMEDIATION = {
    "conceptual_soundness": "Document and evidence the conceptual-soundness / design gap for independent review.",
    "data": "Remediate the data-quality/lineage gap and provide independent evidence.",
    "performance": "Complete independent performance/benchmark testing and evidence the results.",
    "outcomes": "Perform and document outcomes analysis / back-testing over the required window.",
    "limitations": "Document model limitations and the compensating use restrictions.",
    "controls": "Implement and independently evidence the missing model control.",
    "monitoring": "Stand up ongoing monitoring with documented thresholds and triggers.",
}
STANDING_NOTE = (
    "Draft independent model-validation findings for human review only; this skill does not "
    "approve, certify, or authorize any model for use, makes no final validation decision, "
    "closes no findings, assembles no governed model documentation pack, and every finding and "
    "recommended disposition requires review and adjudication by the model validation lead and "
    "approver before any decision."
)


def _is_independent(area: dict) -> bool:
    """A claim is independently supported only with independent_evidence AND a source_ref."""
    return bool(area.get("independent_evidence")) and bool(area.get("source_ref"))


def _validated_status(area: dict) -> str:
    """Deterministic effective status: pass | deficiency | not_tested.

    - Any failed test -> deficiency (evidence contradicts the declared status).
    - Declared pass -> validated only if independent AND no inconclusive test; else not_tested.
    - Declared deficiency -> deficiency.
    - Anything else (not_tested / unknown / inconclusive-only) -> not_tested.
    """
    tests = area.get("tests") or []
    outcomes = [t.get("outcome") for t in tests if isinstance(t, dict)]
    if "fail" in outcomes:
        return "deficiency"
    declared = area.get("status")
    if declared == "pass":
        if not _is_independent(area):
            return "not_tested"        # developer-attested only -> no credit (independence)
        if "inconclusive" in outcomes:
            return "not_tested"        # unresolved test -> not independently validated
        return "pass"
    if declared == "deficiency":
        return "deficiency"
    return "not_tested"


def _citations(area: dict) -> list:
    cites = []
    if area.get("source_ref"):
        cites.append(area["source_ref"])
    for t in area.get("tests") or []:
        if isinstance(t, dict) and t.get("evidence_ref"):
            cites.append(t["evidence_ref"])
    return cites


def score_area(name: str, area: dict) -> dict:
    validated = _validated_status(area)
    materiality = area.get("materiality") if area.get("materiality") in LEVELS else "Medium"
    return {
        "area": name,
        "materiality": materiality,
        "declared_status": area.get("status"),
        "validated_status": validated,
        "independent_evidence": bool(area.get("independent_evidence")),
        # Carry the SR 11-7 independence decision explicitly (independent_evidence AND a
        # source_ref) so the output guardrail enforces the *same* gate the engine used and the
        # two definitions cannot diverge. `independent_evidence` alone or a citation drawn only
        # from a test working paper is NOT independent sourcing.
        "independently_sourced": _is_independent(area),
        "citations": _citations(area),
        "tests": area.get("tests") or [],
    }


def _make_finding(rec: dict, area: dict, idx: int) -> dict:
    name = rec["area"]
    validated = rec["validated_status"]
    ftype = "deficiency" if validated == "deficiency" else "coverage-gap"
    severity = rec["materiality"]  # severity tracks the materiality of the area to model use
    remediation = area.get("recommended_action") or DEFAULT_REMEDIATION.get(name, "Remediate the identified gap.")
    sources = list(rec["citations"])
    return {
        "finding_id": f"VF-{idx:03d}",
        "area": name,
        "finding_type": ftype,
        "severity": severity,
        "recommended_remediation": remediation,
        "owner": AREA_OWNER.get(name, "Model Risk"),
        "source_refs": sources,
        "status": "open",
        "adjudication_required": True,
    }


def _route(overall: str) -> list:
    if overall == "High":
        return ["Model Risk Committee", "Chief Risk Officer (or delegate)"]
    if overall == "Medium":
        return ["Head of Model Validation", "Model Owner"]
    return ["Head of Model Validation"]


DISPOSITION = {
    "High": "material-findings-remediation-required",
    "Medium": "findings-remediation-recommended",
    "Low": "minor-findings-noted",
    "None": "no-findings-open",
}


def build_report(doc: dict) -> dict:
    areas_in = doc.get("areas") or {}
    area_recs, findings, idx = [], [], 1
    for name in REQUIRED_AREAS:
        area = areas_in.get(name)
        if not isinstance(area, dict):
            continue
        rec = score_area(name, area)
        if rec["validated_status"] in ("deficiency", "not_tested"):
            f = _make_finding(rec, area, idx)
            rec["finding_id"] = f["finding_id"]
            findings.append(f)
            idx += 1
        else:
            rec["finding_id"] = None
        area_recs.append(rec)

    overall = "None"
    for f in findings:
        if SEV_ORDER[f["severity"]] > SEV_ORDER[overall]:
            overall = f["severity"]

    complete = len(area_recs) == len(REQUIRED_AREAS)
    summary = {
        "findings_high": sum(1 for f in findings if f["severity"] == "High"),
        "findings_medium": sum(1 for f in findings if f["severity"] == "Medium"),
        "findings_low": sum(1 for f in findings if f["severity"] == "Low"),
        "areas_passed": sum(1 for r in area_recs if r["validated_status"] == "pass"),
        "areas_deficient": sum(1 for r in area_recs if r["validated_status"] == "deficiency"),
        "areas_not_tested": sum(1 for r in area_recs if r["validated_status"] == "not_tested"),
    }
    return {
        "validation_id": doc.get("validation_id"),
        "model_id": doc.get("model_id"),
        "model_name": doc.get("model_name"),
        "model_tier": doc.get("model_tier"),
        "validation_type": doc.get("validation_type"),
        "framework_version": doc.get("framework_version"),
        "report_status": "draft-validation-report" if complete else "needs-data",
        "areas": area_recs,
        "findings": findings,
        "summary": summary,
        "overall_finding_severity": overall,
        "recommended_disposition": DISPOSITION[overall],
        "validation_outcome": {
            "status": "pending",
            "required_approvers": _route(overall),
            "adjudication_required": True,
        },
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "validation_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_report(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
