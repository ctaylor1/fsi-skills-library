#!/usr/bin/env python3
"""Deterministic output validation for model-validation-assistant.

Enforces the R3 "Draft & package" guardrails before independent model-validation findings are
handed to a human for review and adjudication:
  1. Template fidelity: all seven required validation areas are present.
  2. Source mapping / no unsupported claim: every area is cited; every finding carries a
     source ref and a recommended remediation; any area asserted `pass` (validated) is
     independently sourced (the `independently_sourced` flag the engine carried =
     independent_evidence AND an independent source_ref) AND cited (an unverified,
     developer-attested, or working-paper-only "pass" is an unsupported/unapproved claim and
     is rejected).
  3. Deterministic tie-out: each area's declared validated_status equals the recomputed
     status from declared_status + independence + test outcomes, using the SAME independence
     gate the engine used (the carried `independently_sourced` flag, not a re-derived proxy);
     every `deficiency`/`not_tested` area carries an open finding; the overall severity equals
     the highest finding severity.
  4. Approval discipline: validation_outcome.status is `pending`, adjudication is required,
     and the routed approvers are consistent with the overall severity. Findings are `open`.
  5. No autonomous validation-decision / approval / certification / model-use-clearance /
     finding-closure / filing / documentation-assembly language.
  6. The standing disclaimer is present.

Fails closed on any miss so a defective or overreaching pack cannot be presented as a
completed, approved, or filed validation.

Usage: python validate_output.py report.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_AREAS = {
    "conceptual_soundness", "data", "performance", "outcomes",
    "limitations", "controls", "monitoring",
}
SEV_ORDER = {"None": 0, "Low": 1, "Medium": 2, "High": 3}
STANDING_NOTE = (
    "Draft independent model-validation findings for human review only; this skill does not "
    "approve, certify, or authorize any model for use, makes no final validation decision, "
    "closes no findings, assembles no governed model documentation pack, and every finding and "
    "recommended disposition requires review and adjudication by the model validation lead and "
    "approver before any decision."
)
ROUTING = {
    "High": ["Model Risk Committee", "Chief Risk Officer (or delegate)"],
    "Medium": ["Head of Model Validation", "Model Owner"],
    "Low": ["Head of Model Validation"],
    "None": ["Head of Model Validation"],
}
DECISION_PATTERNS = [
    r"\bmodel (is )?approved (for|to)\b",
    r"\bapproved for (use|production|deployment|release)\b",
    r"\bvalidation (approved|passed|complete and approved|signed off)\b",
    r"\bcleared (to|for) (use|deploy|deployment|production|launch|release)\b",
    r"\bauthorized for (use|deployment|production|release)\b",
    r"\bfit for (use|purpose|production|deployment)\b",
    r"\bno (further |additional )?(human )?(review|validation) (is )?(required|needed)\b",
    r"\bwe (hereby )?certify\b",
    r"\brisk (is )?accepted\b",
    r"\bfinal (validation )?(determination|decision|rating)\b",
    r"\bsign-?off (is )?complete\b",
    r"\bauto-?approved\b",
    r"\bfinding(s)? (closed|resolved|remediated|waived|cleared)\b",
    r"\bno action (required|needed)\b",
    # separation from documentation assembly / no system-of-record write
    r"\bdocumentation pack (assembled|finalized|filed|updated|written)\b",
    r"\b(filed|submitted) (the )?validation report\b",
    r"\bwritten to the (model )?(inventory|system of record)\b",
]


def _recompute_status(area: dict) -> str:
    """Recompute validated_status from declared_status + independence + test outcomes.

    Independence uses the same SR 11-7 gate the engine applied: the explicit
    `independently_sourced` flag it carries (independent_evidence AND an independent
    source_ref). A missing/false flag is treated as NOT independent (fail closed) so the
    engine and this guardrail cannot diverge — a citation drawn only from a test working
    paper does not, by itself, make a `pass` independently sourced.
    """
    tests = area.get("tests")
    outcomes = []
    if isinstance(tests, list):
        outcomes = [t.get("outcome") for t in tests if isinstance(t, dict)]
    declared = area.get("declared_status")
    indep = bool(area.get("independently_sourced"))
    if "fail" in outcomes:
        return "deficiency"
    if declared == "pass":
        if not indep:
            return "not_tested"
        if "inconclusive" in outcomes:
            return "not_tested"
        return "pass"
    if declared == "deficiency":
        return "deficiency"
    return "not_tested"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    areas = doc.get("areas") or []
    if not areas:
        return ["validation output has no area scoring"]

    present = {a.get("area") for a in areas}
    for a in sorted(REQUIRED_AREAS - present):
        errors.append(f"missing required validation area '{a}' (template fidelity)")

    finding_areas = {f.get("area") for f in (doc.get("findings") or [])}
    for area in areas:
        name = area.get("area", "?")
        validated = area.get("validated_status")
        if not area.get("citations"):
            errors.append(f"{name}: no citations (unsupported validation assertion - every area must map to a source)")
        # unsupported/unapproved 'pass' claim: a credited pass must be independently sourced
        # (independent_evidence AND an independent source_ref) AND cited. Use the explicit
        # `independently_sourced` gate the engine carried so the two cannot diverge; a citation
        # from a test working paper alone does not make a pass independent. Fail closed if the
        # flag is missing.
        if validated == "pass" and not (area.get("independently_sourced") and area.get("citations")):
            errors.append(f"{name}: asserted pass without independent sourcing + citation (unsupported/unapproved validated claim)")
        expected = _recompute_status(area)
        if validated != expected:
            errors.append(f"{name}: validated_status {validated!r} != expected {expected!r} (deterministic tie-out)")
        band = validated if validated in ("pass", "deficiency", "not_tested") else expected
        if band in ("deficiency", "not_tested") and name not in finding_areas:
            errors.append(f"{name}: validated_status {band!r} but no open finding (must be surfaced for adjudication)")

    findings = doc.get("findings") or []
    computed_overall = "None"
    for f in findings:
        fid = f.get("finding_id", "?")
        if not f.get("recommended_remediation"):
            errors.append(f"{fid} ({f.get('area')}): finding missing recommended_remediation")
        if not f.get("source_refs"):
            errors.append(f"{fid} ({f.get('area')}): finding missing source reference (unsupported assertion)")
        if f.get("status") != "open":
            errors.append(f"{fid} ({f.get('area')}): finding status must be 'open' (this skill does not close findings)")
        sev = f.get("severity")
        if sev not in SEV_ORDER:
            errors.append(f"{fid} ({f.get('area')}): invalid severity {sev!r}")
        elif SEV_ORDER[sev] > SEV_ORDER[computed_overall]:
            computed_overall = sev

    declared_overall = doc.get("overall_finding_severity")
    if declared_overall != computed_overall:
        errors.append(f"overall_finding_severity {declared_overall!r} != expected {computed_overall!r} (highest finding severity)")

    outcome = doc.get("validation_outcome") or {}
    if outcome.get("status") != "pending":
        errors.append(f"validation_outcome.status must be 'pending' (this skill never approves/certifies a model), got {outcome.get('status')!r}")
    if not outcome.get("adjudication_required"):
        errors.append("validation_outcome.adjudication_required must be true (R3 mandatory human adjudication)")
    approvers = outcome.get("required_approvers") or []
    if not approvers:
        errors.append("validation_outcome.required_approvers is empty (no routing)")
    else:
        exp_route = ROUTING.get(computed_overall, [])
        if set(approvers) != set(exp_route):
            errors.append(f"required_approvers {approvers} != expected {exp_route} for overall {computed_overall!r}")

    scan = json.dumps(areas) + " " + json.dumps(findings) + " " + str(doc.get("narrative", "")) + " " + str(doc.get("recommended_disposition", ""))
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited autonomous-decision language detected: {m.group(0)!r} (this skill never approves/certifies/clears a model, closes findings, files, or assembles the documentation pack)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "validation_report_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
