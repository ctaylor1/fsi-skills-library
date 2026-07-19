#!/usr/bin/env python3
"""Deterministic output validation for payment-exception-investigator.

Enforces the R3 casework guardrails before an investigation package is presented:
  1. Every investigation carries a durable case_id (PEI-<id>).
  2. disposition is one of the RECOMMENDATION-only states (no closure/determination/filing).
  3. Every evidence item is cited: bundle citations non-empty and each chronology event cited.
  4. Recommendations are flagged requires_approval; decision_authority stays with a human.
  5. route-specialist targets a known specialist skill.
  6. priority_band ties out to priority_score using the same thresholds/config the builder used
     (priority_thresholds) and the same fraud/sanctions risk override the builder applied.
  7. No case-closure / determination / fund-movement / filing language anywhere.
  8. The standing note is present.
Fails closed (exit 1) on any miss.

Usage: python validate_output.py investigation.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

CASE_ID_RE = re.compile(r"^PEI-[A-Za-z0-9._-]+$")
ALLOWED_DISPOSITIONS = {
    "recommend-repair-and-resubmit", "recommend-return-to-originator",
    "recommend-honor-recall", "recommend-reject-recall", "recommend-request-information",
    "route-specialist", "needs-data", "possible-duplicate",
}
ALLOWED_ROUTES = {
    "sanctions-match-adjudicator", "payment-fraud-case-investigator", "dispute-operations-assistant",
}
FORBIDDEN_STATUS = {"closed", "filed", "settled", "posted", "determined", "returned", "released", "repaired"}
STANDING_NOTE = ("Investigation evidence and recommendations only; no case has been closed, "
                 "no determination made, no payment repaired, returned, or released, and no "
                 "filing performed. Every next step requires human adjudication and approval.")

# Executed-action / decision / closure / filing language that must never appear in output.
FORBIDDEN_PATTERNS = [
    r"\bcase closed\b", r"\bclose the (case|exception)\b", r"\bclosed the (case|exception)\b",
    r"\bmark(ed)? (the )?(case|exception) (as )?closed\b",
    r"\bfinal determination\b", r"\bwe have determined\b", r"\bhereby determine\b",
    r"\badjudicated\b", r"\bno further action\b", r"\bexonerat",
    r"\bfunds (were|have been|are) returned\b", r"\breturned the funds\b",
    r"\bpayment (was|has been) (returned|reissued|released|repaired|resubmitted)\b",
    r"\breissued the payment\b", r"\brepaired and resubmitted\b", r"\bresubmitted the payment\b",
    r"\breleased the payment\b", r"\bhonored the recall\b", r"\brecall (was|has been) honored\b",
    r"\bdebited\b", r"\bcredited the\b", r"\bposted (the|to)\b",
    r"\bfiled (a|the|with)\b", r"\bsubmitted the (return|recall|report)\b",
    r"\breport(ed)? to (fincen|ofac|the regulator)\b",
]


DEFAULT_P1_MIN = 6
DEFAULT_P2_MIN = 3


def _expected_band(score, risk, p1_min, p2_min):
    if score >= p1_min or risk:
        return "P1 (Critical)"
    return "P2 (Standard)" if score >= p2_min else "P3 (Low)"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    records = doc.get("investigations") or []
    if not records:
        return ["investigation output has no records"]

    # Read the same priority thresholds the builder used (falling back to the engine defaults),
    # so the band tie-out never diverges from the engine on a non-default priority_config.
    thresholds = doc.get("priority_thresholds") or {}
    p1_min = thresholds.get("p1_min", DEFAULT_P1_MIN)
    p2_min = thresholds.get("p2_min", DEFAULT_P2_MIN)

    for r in records:
        eid = r.get("exception_id", "?")
        cid = r.get("case_id")
        if not cid or not CASE_ID_RE.match(str(cid)):
            errors.append(f"{eid}: missing durable case_id (expected PEI-<id>), got {cid!r}")

        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{eid}: disallowed disposition {disp!r} (closure/determination/filing not permitted)")

        if r.get("decision_authority") != "human-adjudication-required":
            errors.append(f"{eid}: decision_authority must be 'human-adjudication-required'")
        if r.get("case_status") in FORBIDDEN_STATUS or r.get("executed_action") or r.get("system_write"):
            errors.append(f"{eid}: output records an autonomous action/closure (forbidden at R3)")

        if disp == "needs-data":
            if not r.get("needs"):
                errors.append(f"{eid}: needs-data must list what is missing")
            continue

        reco = r.get("disposition_recommendation") or {}
        if not reco:
            errors.append(f"{eid}: missing disposition_recommendation")
        else:
            if reco.get("requires_approval") is not True:
                errors.append(f"{eid}: disposition_recommendation.requires_approval must be true")
            if not reco.get("rationale"):
                errors.append(f"{eid}: disposition_recommendation missing rationale")

        if disp == "route-specialist":
            route = r.get("route_specialist") or reco.get("route_specialist")
            if route not in ALLOWED_ROUTES:
                errors.append(f"{eid}: route-specialist target {route!r} not a known specialist skill")

        bundle = r.get("evidence_bundle") or {}
        if not bundle:
            errors.append(f"{eid}: {disp} requires an evidence_bundle")
        else:
            if not bundle.get("citations"):
                errors.append(f"{eid}: evidence_bundle missing citations")
            for ev in bundle.get("chronology") or []:
                if not ev.get("cite"):
                    errors.append(f"{eid}: chronology event seq={ev.get('seq')} is uncited")
            if not (bundle.get("chronology")):
                errors.append(f"{eid}: evidence_bundle has no chronology")

        # priority tie-out — mirror the builder exactly. The band is escalated to P1 only by a
        # fraud_indicator/sanctions_hold risk override (carried as the explicit
        # priority_risk_override flag, or the 'fraud/sanctions signal' marker in priority_reason),
        # NOT by the route-specialist disposition itself; thresholds come from priority_thresholds.
        risk = bool(r.get("priority_risk_override")) or \
            "fraud/sanctions signal" in str(r.get("priority_reason", ""))
        exp = _expected_band(r.get("priority_score", 0), risk, p1_min, p2_min)
        if r.get("priority_band") != exp:
            errors.append(f"{eid}: priority_band {r.get('priority_band')!r} != expected {exp!r} for score {r.get('priority_score')}")

    scan = json.dumps(records) + " " + str(doc.get("narrative", "")) + " " + str(doc.get("standing_note", ""))
    for pat in FORBIDDEN_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"execution/decision/closure language detected: {m.group(0)!r} (R3 recommends only)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "investigation_output_example.json"
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
