#!/usr/bin/env python3
"""Deterministic enterprise risk-assessment builder for enterprise-risk-assessment-builder.

Transforms a validated risk-assessment input into a DRAFT assessment document that links
risks -> scenarios -> controls -> residual ratings -> indicators -> owners -> evidence ->
treatment actions, using an explainable, documented scoring model:

  inherent score  = likelihood (1-5) x impact (1-5)  -> band (Low/Moderate/High/Critical)
  control credit  = f(tested control effectiveness)   -> band reduction (0 / 1 / 2)
  residual band   = max(Low, inherent band - reduction)
  over appetite   = residual band index > appetite band index for the category

The tool NEVER accepts a residual rating, approves/finalizes the assessment, closes a risk,
signs an attestation, files with a regulator, or writes the risk system of record. It emits
`status: draft-for-review`, leaves every approval `pending`, and only takes control credit
for controls that are tested AND carry evidence (conservative / fail-closed).

Usage: python calculate_or_transform.py assessment.json | --selftest
Prints the draft assessment JSON to stdout. Under --selftest it also runs internal
invariant checks and prints a final line ending "N error(s)" (exit 0 pass / 1 fail).
"""
from __future__ import annotations
import json, sys
from pathlib import Path

BAND_INDEX = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}
INDEX_BAND = {v: k for k, v in BAND_INDEX.items()}
EFF_VALUE = {"Effective": 2, "Partially Effective": 1, "Ineffective": 0}
UNTESTED = {"Not Tested", None, ""}

TEMPLATE_SECTIONS = [
    "Scope & Basis",
    "Risk Inventory",
    "Inherent Risk Assessment",
    "Control Environment",
    "Residual Risk & Appetite",
    "Key Risk Indicators",
    "Treatment Actions",
    "Evidence Register",
    "Limitations & Assumptions",
    "Approvals & Attestations",
]
REQUIRED_APPROVALS = [
    "Risk & Control Owner (1st line)",
    "Enterprise Risk Management (2nd line)",
    "Risk Committee / CRO",
]
STANDING_NOTE = (
    "Draft enterprise risk assessment for human review only; no risk has been accepted, no "
    "residual rating approved, no assessment finalized, and nothing filed or written to the "
    "risk system of record."
)


def _inherent(inh):
    score = int(inh.get("likelihood", 0)) * int(inh.get("impact", 0))
    if score <= 4:
        band = "Low"
    elif score <= 9:
        band = "Moderate"
    elif score <= 15:
        band = "High"
    else:
        band = "Critical"
    return score, band


def _control_environment(risk, controls):
    """Return (records, tier, avg_score, reduction, gaps). Only tested controls WITH
    evidence earn residual credit (fail-closed)."""
    records, gaps = [], []
    linked = [controls.get(cid) for cid in (risk.get("control_ids") or []) if controls.get(cid)]
    credited_scores = []
    for c in linked:
        proven = c.get("design") not in UNTESTED and c.get("operating") not in UNTESTED
        combined = (EFF_VALUE.get(c.get("design"), 0) + EFF_VALUE.get(c.get("operating"), 0)) if proven else None
        has_evidence = bool(c.get("evidence_ref"))
        credited = bool(proven and has_evidence)
        if proven and not has_evidence:
            gaps.append(f"control {c.get('control_id')} effectiveness is not evidenced -> no residual credit")
        if not proven:
            gaps.append(f"control {c.get('control_id')} is not tested -> no residual credit")
        if credited:
            credited_scores.append(combined)
        records.append({
            "control_id": c.get("control_id"),
            "title": c.get("title"),
            "design": c.get("design"),
            "operating": c.get("operating"),
            "combined": combined,
            "proven": proven,
            "credited": credited,
            "evidence_ref": c.get("evidence_ref"),
        })
    if not linked:
        return records, "None", None, 0, ["no linked control -> residual equals inherent"]
    if not credited_scores:
        return records, "Unproven", None, 0, gaps
    avg = round(sum(credited_scores) / len(credited_scores), 2)
    if avg >= 3.5:
        tier, reduction = "Strong", 2
    elif avg >= 2.0:
        tier, reduction = "Moderate", 1
    else:
        tier, reduction = "Weak", 0
    return records, tier, avg, reduction, gaps


def build_risk(risk, doc, controls):
    score, inh_band = _inherent(risk.get("inherent") or {})
    inh_idx = BAND_INDEX[inh_band]
    ctrl_records, tier, avg, reduction, gaps = _control_environment(risk, controls)

    res_idx = max(0, inh_idx - reduction)
    res_band = INDEX_BAND[res_idx]

    appetite = doc.get("appetite") or {}
    app_band = appetite.get(risk.get("category"), appetite.get("default", "Moderate"))
    app_idx = BAND_INDEX.get(app_band, 1)
    over_appetite = res_idx > app_idx

    treatments = risk.get("treatment_action_ids") or []
    if over_appetite and not treatments:
        gaps.append("residual exceeds appetite but no treatment action is recorded -> treatment required")
    if not (risk.get("indicator_ids") or []):
        gaps.append("no linked key risk indicator (KRI)")

    status = "needs-evidence" if any("no residual credit" in g or "not evidenced" in g for g in gaps) else "draft-for-review"

    evidence_refs = list(dict.fromkeys(
        [risk.get("source_ref")]
        + [c.get("evidence_ref") for c in ctrl_records if c.get("evidence_ref")]
    ))

    citations = [f"riskreg:{risk.get('risk_id')}"] + [c.get("evidence_ref") for c in ctrl_records if c.get("evidence_ref")]

    return {
        "risk_id": risk.get("risk_id"),
        "title": risk.get("title"),
        "category": risk.get("category"),
        "owner": risk.get("owner"),
        "inherent": {"likelihood": (risk.get("inherent") or {}).get("likelihood"),
                     "impact": (risk.get("inherent") or {}).get("impact"),
                     "score": score, "band": inh_band, "band_index": inh_idx},
        "controls": ctrl_records,
        "control_environment": {"tier": tier, "avg_score": avg, "reduction": reduction},
        "residual": {"band": res_band, "band_index": res_idx},
        "appetite": {"band": app_band, "band_index": app_idx},
        "over_appetite": over_appetite,
        "indicator_ids": risk.get("indicator_ids") or [],
        "scenario_ids": risk.get("scenario_ids") or [],
        "loss_event_ids": risk.get("loss_event_ids") or [],
        "treatment_action_ids": treatments,
        "evidence_refs": evidence_refs,
        "citations": citations,
        "gaps": gaps,
        "status": status,
    }


def build(doc: dict) -> dict:
    controls = {c.get("control_id"): c for c in (doc.get("controls") or [])}
    risk_records = [build_risk(r, doc, controls) for r in doc.get("risks", [])]
    summary = {
        "total_risks": len(risk_records),
        "over_appetite": sum(1 for r in risk_records if r["over_appetite"]),
        "needs_evidence": sum(1 for r in risk_records if r["status"] == "needs-evidence"),
        "by_residual_band": {b: sum(1 for r in risk_records if r["residual"]["band"] == b)
                             for b in ("Low", "Moderate", "High", "Critical")},
    }
    return {
        "assessment_id": f"ERA-{(doc.get('scope') or {}).get('entity', 'ENTITY')}".replace(" ", "-"),
        "template_version": doc.get("template_version"),
        "config_version": doc.get("config_version"),
        "scope": doc.get("scope"),
        "sections": list(TEMPLATE_SECTIONS),
        "risks": risk_records,
        "summary": summary,
        "approvals": [{"role": role, "status": "pending", "approver": None, "date": None}
                      for role in REQUIRED_APPROVALS],
        "status": "draft-for-review",
        "standing_note": STANDING_NOTE,
    }


def _selftest_invariants(out: dict) -> list[str]:
    errs = []
    for r in out["risks"]:
        exp_res = max(0, r["inherent"]["band_index"] - r["control_environment"]["reduction"])
        if r["residual"]["band_index"] != exp_res:
            errs.append(f"{r['risk_id']}: residual tie-out failed")
        if (r["residual"]["band_index"] > r["appetite"]["band_index"]) != r["over_appetite"]:
            errs.append(f"{r['risk_id']}: over_appetite flag inconsistent")
        if r["control_environment"]["reduction"] > 0:
            credited = [c for c in r["controls"] if c["credited"]]
            if not credited or any(not c["evidence_ref"] for c in credited):
                errs.append(f"{r['risk_id']}: credited control without evidence")
    if out["status"] != "draft-for-review":
        errs.append("assessment status is not draft-for-review")
    if any(a["status"] != "pending" for a in out["approvals"]):
        errs.append("an approval is not pending in a draft")
    # expected dispositions for the bundled golden input
    expected = {"R-001": ("High", True), "R-002": ("Low", False), "R-003": ("High", True),
                "R-004": ("Low", False), "R-005": ("Critical", True), "R-006": ("Low", False)}
    got = {r["risk_id"]: (r["residual"]["band"], r["over_appetite"]) for r in out["risks"]}
    for rid, exp in expected.items():
        if got.get(rid) != exp:
            errs.append(f"{rid}: expected {exp}, got {got.get(rid)}")
    return errs


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_input.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    out = build(doc)
    print(json.dumps(out, indent=2))
    if selftest:
        errs = _selftest_invariants(out)
        for e in errs:
            print("ERROR", e)
        print(f"engine self-test: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
