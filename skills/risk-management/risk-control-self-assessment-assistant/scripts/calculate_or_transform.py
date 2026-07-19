#!/usr/bin/env python3
"""Deterministic RCSA scoring + draft-package assembler for risk-control-self-assessment-assistant.

Takes a first-line RCSA input (risks, mapped controls, ratings, evidence) and produces a
DRAFT RCSA package: inherent risk scored from impact x likelihood, control effectiveness
derived from design + operating ratings, residual risk after control mitigation, evidence
map, statement/control challenges, and a remediation plan for residual risk above appetite.

Guardrails baked in (see references/domain-rules.md and references/controls.md):
  - A control effectiveness conclusion is only credited toward residual reduction when the
    control carries EVIDENCE. A rated-but-unevidenced control is marked "Unsubstantiated",
    is NOT credited, and its evidence gap is surfaced as a challenge (no unsupported claim).
  - The package is DRAFT-only. It records the human approvals REQUIRED (control owner,
    first-line sign-off, second-line challenge) as `pending`; it never marks them obtained,
    never accepts risk, attests, closes, or writes a system of record.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, entity, assessment_period{from,to}, as_of_date, risk_appetite,
  scoring_config{} (optional overrides), risks[
    {risk_id, statement, category, inherent_impact(1-5), inherent_likelihood(1-5),
     loss_events[], controls[
       {control_id, description, control_type, frequency,
        design_rating, operating_rating, evidence[{type,ref,date,result}]}],
     remediation{action, owner, due_date} (optional)}]

Usage: python calculate_or_transform.py rcsa_input.json | --selftest
Prints the DRAFT RCSA package JSON to stdout. Exit 0.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# ---- documented scoring configuration (a versioned contract, not judgment) ----
DEFAULT_CFG = {
    # inherent score (impact x likelihood, 1..25) -> level 1..4
    "inherent_bands": [(4, 1), (9, 2), (14, 3), (25, 4)],  # (max_score, level)
    # control effectiveness rating -> inherent-level reduction
    "effect_reduction": {"Effective": 2, "Partially Effective": 1,
                         "Ineffective": 0, "Unsubstantiated": 0, "None": 0},
}
RATING_VALUES = {"Effective", "Partially Effective", "Ineffective"}
LEVEL_BAND = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}
BAND_LEVEL = {b: l for l, b in LEVEL_BAND.items()}
# conclusions that DIRECTLY assert control mitigation and therefore require evidence
CREDITED = {"Effective", "Partially Effective"}
REQUIRED_APPROVALS = [
    "Control / process owner (accuracy attestation)",
    "First-line business management (assessment sign-off)",
    "Second-line operational risk (independent challenge / validation)",
]
STANDING_NOTE = (
    "DRAFT RCSA prepared for first-line and independent human review only. No assessment "
    "sign-off, independent challenge, control attestation, or risk-acceptance decision has "
    "been completed by this assistant, and nothing has been written to the GRC system of "
    "record."
)


def _inherent_level(score, cfg):
    for max_score, level in cfg["inherent_bands"]:
        if score <= max_score:
            return level
    return 4


def _control_effectiveness(ctrl):
    """Overall effectiveness from design + operating, gated by evidence.

    Effective only if BOTH dimensions Effective; Ineffective if EITHER is Ineffective;
    otherwise Partially Effective. A crediting conclusion with no evidence is downgraded to
    'Unsubstantiated' so the draft never asserts an unevidenced control benefit."""
    d = ctrl.get("design_rating")
    o = ctrl.get("operating_rating")
    if d not in RATING_VALUES or o not in RATING_VALUES:
        return "Unsubstantiated", False
    if d == "Ineffective" or o == "Ineffective":
        overall = "Ineffective"
    elif d == "Effective" and o == "Effective":
        overall = "Effective"
    else:
        overall = "Partially Effective"
    has_evidence = bool(ctrl.get("evidence"))
    if overall in CREDITED and not has_evidence:
        return "Unsubstantiated", False
    return overall, has_evidence


def _remediation_status(due_date, as_of):
    if not due_date:
        return "unplanned"
    return "overdue" if str(due_date) < str(as_of) else "open"


def assess_risk(risk, cfg, as_of, appetite_level):
    rid = risk.get("risk_id")
    impact = int(risk.get("inherent_impact") or 0)
    likelihood = int(risk.get("inherent_likelihood") or 0)
    inh_score = impact * likelihood
    inh_level = _inherent_level(inh_score, cfg)

    controls_out, challenges, needs, evidence_rows = [], [], [], []
    best_reduction = 0
    best_effect = "None"
    # any_ineffective is tracked independently of best-control selection so an Ineffective
    # control is never masked by an earlier zero-reduction control (e.g. Unsubstantiated).
    any_ineffective = False
    for c in risk.get("controls") or []:
        overall, has_ev = _control_effectiveness(c)
        reduction = cfg["effect_reduction"].get(overall, 0)
        if overall == "Ineffective":
            any_ineffective = True
        if reduction > best_reduction:
            best_reduction = reduction
            best_effect = overall
        elif best_effect == "None":
            best_effect = overall
        controls_out.append({
            "control_id": c.get("control_id"),
            "description": c.get("description"),
            "control_type": c.get("control_type"),
            "design_rating": c.get("design_rating"),
            "operating_rating": c.get("operating_rating"),
            "overall_effectiveness": overall,
            "evidence": c.get("evidence") or [],
        })
        for ev in c.get("evidence") or []:
            evidence_rows.append({"risk_id": rid, "control_id": c.get("control_id"),
                                  "type": ev.get("type"), "ref": ev.get("ref"),
                                  "date": ev.get("date"), "result": ev.get("result")})
        # challenge: crediting conclusion downgraded for want of evidence
        if c.get("design_rating") in RATING_VALUES and c.get("operating_rating") in RATING_VALUES \
                and overall == "Unsubstantiated":
            challenges.append(f"{c.get('control_id')}: rated but unevidenced -> not credited "
                              f"(evidence gap); confirm with a control test or attestation")
            needs.append(f"evidence for {c.get('control_id')}")

    # challenge: no controls on a material inherent risk
    if not risk.get("controls"):
        challenges.append(f"{rid}: no controls mapped to a {LEVEL_BAND[inh_level]} inherent risk")
    # challenge: loss event contradicts an 'Effective' claim
    if risk.get("loss_events") and best_effect in ("Effective", "Partially Effective"):
        challenges.append(f"{rid}: loss event(s) recorded while a key control reads "
                          f"'{best_effect}' -- corroborate effectiveness before sign-off")

    residual_level = max(1, inh_level - best_reduction)
    remediation_required = residual_level > appetite_level or any_ineffective

    rec = {
        "risk_id": rid,
        "statement": risk.get("statement"),
        "category": risk.get("category"),
        "inherent_impact": impact,
        "inherent_likelihood": likelihood,
        "inherent_score": inh_score,
        "inherent_level": inh_level,
        "inherent_band": LEVEL_BAND[inh_level],
        "controls": controls_out,
        "overall_control_effectiveness": best_effect,
        "control_effect_reduction": best_reduction,
        "any_control_ineffective": any_ineffective,
        "residual_level": residual_level,
        "residual_band": LEVEL_BAND[residual_level],
        "within_appetite": residual_level <= appetite_level,
        "remediation_required": remediation_required,
        "challenges": challenges,
        "needs": needs,
    }
    return rec, evidence_rows


def build_remediation(rec, risk, as_of):
    if not rec["remediation_required"]:
        return None
    rem = risk.get("remediation") or {}
    owner = rem.get("owner") or "TBD -- assign owner (human)"
    due = rem.get("due_date")
    reason = "residual above appetite" if not rec["within_appetite"] else "mapped control ineffective"
    return {
        "risk_id": rec["risk_id"],
        "residual_band": rec["residual_band"],
        "reason": reason,
        "action": rem.get("action") or "TBD -- define remediation action (human)",
        "owner": owner,
        "due_date": due,
        "status": _remediation_status(due, as_of),
    }


def build_package(doc: dict) -> dict:
    cfg = {**DEFAULT_CFG, **(doc.get("scoring_config") or {})}
    as_of = doc.get("as_of_date")
    appetite_band = doc.get("risk_appetite") or "Medium"
    appetite_level = BAND_LEVEL.get(appetite_band, 2)

    assessments, evidence_map, remediation_plan = [], [], []
    for risk in doc.get("risks") or []:
        rec, ev_rows = assess_risk(risk, cfg, as_of, appetite_level)
        assessments.append(rec)
        evidence_map.extend(ev_rows)
        rem = build_remediation(rec, risk, as_of)
        if rem:
            remediation_plan.append(rem)

    challenges = [{"risk_id": r["risk_id"], "challenge": ch}
                  for r in assessments for ch in r["challenges"]]

    residual_summary = {
        "total_risks": len(assessments),
        "by_residual_band": {b: sum(1 for r in assessments if r["residual_band"] == b)
                             for b in ("Low", "Medium", "High", "Critical")},
        "above_appetite": sum(1 for r in assessments if not r["within_appetite"]),
        "remediation_items": len(remediation_plan),
        "evidence_gaps": sum(1 for r in assessments if r["needs"]),
        "risk_appetite": appetite_band,
    }

    approvals = [{"role": role, "status": "pending", "approver": None, "date": None}
                 for role in REQUIRED_APPROVALS]

    return {
        "template_id": "RCSA-PKG-v1",
        "config_version": doc.get("config_version"),
        "sections": {
            "assessment_scope": {
                "entity": doc.get("entity"),
                "assessment_period": doc.get("assessment_period"),
                "as_of_date": as_of,
                "risk_appetite": appetite_band,
                "scoring_config_version": doc.get("config_version"),
            },
            "risk_and_control_assessment": assessments,
            "residual_risk_summary": residual_summary,
            "evidence_map": evidence_map,
            "challenges_and_gaps": challenges,
            "remediation_plan": remediation_plan,
            "approvals": approvals,
        },
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "rcsa_input.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_package(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
