#!/usr/bin/env python3
"""Draft claims complexity, urgency and specialist routing from supplied facts. as_of drives clocks; unknown liability never suppresses urgency or specialist routes. All outputs require human review.

Usage: python calculate_or_transform.py input.json | --selftest
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from insurance_contract import build_artifact

DEFAULT_CONFIG = {
    "exposure": [(250000, 3), (100000, 2), (25000, 1)],
    "injuries": 2,
    "fatality": 3,
    "litigation": 3,
    "coverage_question": 2,
    "multi_party": 1,
    "s1_min": 7,
    "s2_min": 3,
    "u_fatality": 3,
    "u_injuries": 2,
    "u_catastrophe": 2,
    "u_statutory": 2,
    "u_business_interruption": 2,
    "u_vulnerability": 1,
    "u1_min": 5,
    "u2_min": 2,
    "statutory_window_days": 60,
    "sla": {"U1 (Immediate)": "4 hours", "U2 (Prompt)": "1 business day", "U3 (Routine)": "3 business days"},
    "currency": "USD",
}
DEFAULT_SEVERITY_MAP = {
    "bodily_injury_liability": 3,
    "general_liability": 3,
    "auto_liability": 3,
    "products_liability": 3,
    "professional_liability": 3,
    "property_damage": 2,
    "business_interruption": 2,
    "auto_physical_damage": 1,
    "theft": 1,
    "other": 1,
}
LIABILITY_TYPES = {
    "bodily_injury_liability",
    "general_liability",
    "auto_liability",
    "products_liability",
    "professional_liability",
}
CLAIM_TYPE_HUMAN = {
    "bodily_injury_liability": "a bodily-injury liability claim",
    "general_liability": "a general-liability claim",
    "auto_liability": "an auto-liability claim",
    "products_liability": "a products-liability claim",
    "professional_liability": "a professional-liability claim",
    "property_damage": "a property-damage claim",
    "business_interruption": "a business-interruption claim",
    "auto_physical_damage": "an auto physical-damage claim",
    "theft": "a theft claim",
    "other": "a claim",
}
REQUIRED_SECTIONS = [
    "Claim summary",
    "Severity and complexity",
    "Urgency and service level",
    "Coverage questions to resolve",
    "Recommended routing",
    "Human adjudication required",
]
STANDING_NOTE = (
    "Draft claims triage only: severity, urgency, coverage questions, and "
    "routing are recommendations for human review. No coverage decision, "
    "reserve, payment, assignment, or claim closure has been made."
)


def _cite(system, ref):
    return f"{system}:{ref}" if ref else f"{system}:?"


def _days(d_from, d_to):
    return (date.fromisoformat(d_to) - date.fromisoformat(d_from)).days


def _severity(c, base, cov_q, cfg):
    score, why = base, [f"claim type {c.get('claim_type')} +{base}"]
    amt = float(c.get("estimated_exposure") or 0)
    for thr, pts in cfg["exposure"]:
        if amt >= thr:
            score += pts
            why.append(f"exposure>={thr} +{pts}")
            break
    if c.get("injuries"):
        score += cfg["injuries"]
        why.append(f"injuries +{cfg['injuries']}")
    if c.get("fatality"):
        score += cfg["fatality"]
        why.append(f"fatality +{cfg['fatality']}")
    if c.get("litigation"):
        score += cfg["litigation"]
        why.append(f"litigation +{cfg['litigation']}")
    if cov_q:
        score += cfg["coverage_question"]
        why.append(f"coverage question +{cfg['coverage_question']}")
    if len(c.get("parties") or []) > 2:
        score += cfg["multi_party"]
        why.append(f"multiple parties +{cfg['multi_party']}")
    band = "S1 (Complex)" if score >= cfg["s1_min"] else "S2 (Moderate)" if score >= cfg["s2_min"] else "S3 (Standard)"
    return score, band, why


def _urgency(c, cfg):
    score, why = 0, []
    if c.get("fatality"):
        score += cfg["u_fatality"]
        why.append(f"fatality +{cfg['u_fatality']}")
    if c.get("injuries"):
        score += cfg["u_injuries"]
        why.append(f"injuries +{cfg['u_injuries']}")
    if c.get("catastrophe_code"):
        score += cfg["u_catastrophe"]
        why.append(f"catastrophe +{cfg['u_catastrophe']}")
    sd = c.get("statutory_deadline_date")
    if sd and cfg.get("as_of"):
        try:
            if _days(cfg["as_of"], sd) <= cfg["statutory_window_days"]:
                score += cfg["u_statutory"]
                why.append(f"statutory deadline due or overdue as of {cfg['as_of']} +{cfg['u_statutory']}")
        except Exception:
            pass
    if c.get("business_interruption"):
        score += cfg["u_business_interruption"]
        why.append(f"business interruption +{cfg['u_business_interruption']}")
    if (c.get("claimant") or {}).get("vulnerability_flag"):
        score += cfg["u_vulnerability"]
        why.append(f"vulnerable claimant +{cfg['u_vulnerability']}")
    band = "U1 (Immediate)" if score >= cfg["u1_min"] else "U2 (Prompt)" if score >= cfg["u2_min"] else "U3 (Routine)"
    return score, band, why


def _coverage_questions(c):
    q = []
    per = c.get("policy_period") or {}
    if str(c.get("policy_status")).lower() == "lapsed":
        q.append(
            "policy shown as not in force (status 'lapsed') — confirm whether cover was in force at the date of loss"
        )
    ld = c.get("loss_date")
    if ld and per.get("from") and per.get("to"):
        try:
            if not (per["from"] <= ld <= per["to"]):
                q.append(
                    f"loss date {ld} falls outside the policy period {per['from']}..{per['to']} — confirm whether cover was in force"
                )
        except Exception:
            pass
    for hit in c.get("exclusion_hits") or []:
        q.append(f"possible exclusion '{hit}' may be relevant — a human must assess whether it applies")
    return q


def _routes(c, severity_band, cov_q):
    routes = []
    if c.get("fraud_indicators"):
        routes.append(
            {
                "target": "insurance-fraud-referral-reviewer",
                "kind": "skill",
                "reason": f"fraud indicators present ({', '.join(c['fraud_indicators'])}) — SIU referral for human assessment; triage makes no fraud determination",
            }
        )
    if c.get("subrogation_potential"):
        routes.append(
            {
                "target": "subrogation-opportunity-screener",
                "kind": "skill",
                "reason": "possible third-party recovery — screen subrogation potential; responsibility remains for human review",
            }
        )
    if cov_q:
        routes.append(
            {
                "target": "coverage specialist (human)",
                "kind": "human",
                "reason": "open coverage question(s) surfaced — human coverage analysis required; triage makes no coverage determination",
            }
        )
    if c.get("catastrophe_code"):
        routes.append(
            {
                "target": "catastrophe major-loss unit (human)",
                "kind": "human",
                "reason": f"catastrophe event {c['catastrophe_code']} — route to the CAT/major-loss unit",
            }
        )
    if (c.get("claimant") or {}).get("vulnerability_flag"):
        routes.append(
            {
                "target": "vulnerable-claimant support (human)",
                "kind": "human",
                "reason": "vulnerability indicator present — accommodation review before contact",
            }
        )
    if c.get("litigation"):
        routes.append(
            {
                "target": "litigation / claims counsel (human)",
                "kind": "human",
                "reason": "matter is in litigation — route to legal counsel",
            }
        )
    if severity_band == "S1 (Complex)":
        routes.append(
            {
                "target": "claim-file-quality-reviewer",
                "kind": "skill",
                "reason": "complex / large-loss claim — deeper claim-file review recommended",
            }
        )
    return routes


def _summary_body(c, sev, urg, sla, cov_q, routes, cfg):
    ct = CLAIM_TYPE_HUMAN.get(c.get("claim_type"), "a claim")
    lines = [
        "DRAFT - CLAIMS TRIAGE SUMMARY, FOR INTERNAL REVIEW - NOT A COVERAGE OR LIABILITY DECISION",
        "",
        f"Claim: {c.get('claim_id')} | Policy: {c.get('policy_id')} | Product: {c.get('product')}",
        "",
        "## Claim summary",
        f"{ct.capitalize()} reported on {c.get('reported_date', '(date)')} for a loss dated "
        f"{c.get('loss_date', '(date)')}. Estimated exposure {cfg['currency']} "
        f"{c.get('estimated_exposure') if c.get('estimated_exposure') is not None else 'unknown'}. Parties on file: {len(c.get('parties') or [])}. "
        "This summary supports triage only.",
        "",
        "## Severity and complexity",
        f"Recommended severity band: {sev[1]} (score {sev[0]}). Drivers: {'; '.join(sev[2])}.",
        "",
        "## Urgency and service level",
        f"Recommended urgency band: {urg[1]} (score {urg[0]}); suggested first-touch service "
        f"level: {sla}. Drivers: {'; '.join(urg[2]) or 'none'}.",
        "",
        "## Coverage questions to resolve",
    ]
    if cov_q:
        lines.append(
            "Triage screens surfaced the following open QUESTIONS for a human to resolve "
            "(triage makes no coverage determination):"
        )
        lines += [f"- {q}" for q in cov_q]
    else:
        lines.append(
            "No coverage question was surfaced by the triage screens; a human still "
            "confirms the coverage position before the claim is worked."
        )
    lines += ["", "## Recommended routing"]
    if routes:
        lines += [f"- {r['target']}: {r['reason']}" for r in routes]
    else:
        lines.append(
            "Standard claims queue at the recommended severity and urgency; no "
            "specialist referral is indicated by the triage screens."
        )
    lines += [
        "",
        "## Human adjudication required",
        "Coverage determination, liability assessment, reserve setting, queue and adjuster "
        "assignment, and any payment remain with the claims supervisor and adjuster of record. "
        "This triage recommends only and decides nothing.",
        "",
        STANDING_NOTE,
    ]
    return "\n".join(lines)


def process(c, cfg, sev_map):
    cid = c.get("claim_id")
    citations = [_cite("claims", c.get("source_ref")), _cite("policy", c.get("policy_id"))]
    rec = {
        "claim_id": cid,
        "policy_id": c.get("policy_id"),
        "product": c.get("product"),
        "claim_type": c.get("claim_type"),
        "severity_score": None,
        "severity_band": None,
        "severity_reason": "",
        "urgency_score": None,
        "urgency_band": None,
        "urgency_reason": "",
        "service_level": None,
        "coverage_questions": [],
        "routes": [],
        "human_adjudication_required": True,
        "citations": citations,
        "approvals": {
            "triage_lead_review": {"role": "Claims triage lead", "status": "pending", "by": "", "date": ""},
            "claims_supervisor_approval": {
                "role": "Claims supervisor / adjuster of record",
                "status": "pending",
                "by": "",
                "date": "",
            },
        },
        "draft_summary": None,
        "needs": [],
    }

    base = sev_map.get(c.get("claim_type"))
    if base is None:
        rec["needs"].append(f"severity mapping for claim_type {c.get('claim_type')!r} (unmapped)")
        rec["disposition"] = "needs-data"

    cov_q = _coverage_questions(c)
    rec["coverage_questions"] = cov_q
    sev = _severity(c, base or 0, cov_q, cfg)
    urg = _urgency(c, cfg)
    sla = cfg["sla"].get(urg[1], "")
    rec.update(
        {
            "severity_score": sev[0],
            "severity_band": sev[1],
            "severity_reason": "; ".join(sev[2]),
            "urgency_score": urg[0],
            "urgency_band": urg[1],
            "urgency_reason": "; ".join(urg[2]),
            "service_level": sla,
        }
    )
    if cov_q:
        citations.append(_cite("policy", f"{c.get('policy_id')}:period"))

    # fail closed: third-party-liability claim with undetermined liability -> human adjudication
    if c.get("claim_type") in LIABILITY_TYPES and c.get("liability_clear") is None:
        rec["needs"].append("liability unresolved; investigation can proceed without a liability decision")

    if c.get("estimated_exposure") is None:
        rec["needs"].append("estimated exposure unknown; severity is provisional")
    if base is None:
        rec["severity_score"] = rec["severity_band"] = None
        sev = (None, "Unknown", ["claim-type mapping unavailable"])
    routes = _routes(c, sev[1] if base is not None else None, cov_q)
    if c.get("claim_type") in LIABILITY_TYPES and c.get("liability_clear") is None:
        routes.append(
            {
                "target": "claims investigation (human)",
                "kind": "human",
                "reason": "resolve liability while preserving urgent specialist support",
            }
        )
    rec["as_of"] = cfg["as_of"]
    sd = c.get("statutory_deadline_date")
    rec["days_to_deadline"] = _days(cfg["as_of"], sd) if sd else None
    rec["deadline_overdue"] = rec["days_to_deadline"] is not None and rec["days_to_deadline"] < 0
    rec["routes"] = routes
    rec["human_adjudication_required"] = True
    rec["draft_summary"] = {
        "required_sections": REQUIRED_SECTIONS,
        "body": _summary_body(c, sev, urg, sla, cov_q, routes, cfg),
    }
    rec["classification_status"] = "partial" if rec["needs"] else "complete"
    rec["disposition"] = "refer-specialist" if routes else "needs-data" if rec["needs"] else "draft-ready"
    return rec


def _calculate(doc: dict) -> dict:
    date.fromisoformat(doc["as_of"])
    cfg = {**DEFAULT_CONFIG, **(doc.get("triage_config") or {}), "as_of": doc["as_of"]}
    cfg["sla"] = {**DEFAULT_CONFIG["sla"], **(cfg.get("sla") or {})}
    sev_map = {**DEFAULT_SEVERITY_MAP, **(doc.get("severity_map") or {})}
    records = [process(c, cfg, sev_map) for c in doc.get("claims", [])]
    summary = {
        "total": len(records),
        "draft_ready": sum(1 for r in records if r["disposition"] == "draft-ready"),
        "refer_specialist": sum(1 for r in records if r["disposition"] == "refer-specialist"),
        "needs_data": sum(1 for r in records if r["disposition"] == "needs-data"),
        "needs_review": sum(1 for r in records if r["disposition"] == "needs-review"),
    }
    # Record the effective band cutoffs the engine actually used so downstream
    # validation ties bands out against the SAME thresholds (no hardcoded divergence).
    band_cfg = {k: cfg[k] for k in ("s1_min", "s2_min", "u1_min", "u2_min")}
    return {
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "triage_config": band_cfg,
        "triage": records,
        "summary": summary,
        "standing_note": STANDING_NOTE,
    }


def _self_check(out: dict) -> list[str]:
    errs = []
    # Tie band consistency to the effective cutoffs the engine recorded, not to
    # hardcoded literals, so the check tracks any triage_config override.
    tc = out.get("triage_config") or {}
    s1_min = tc.get("s1_min", DEFAULT_CONFIG["s1_min"])
    s2_min = tc.get("s2_min", DEFAULT_CONFIG["s2_min"])
    for r in out.get("triage", []):
        cid = r.get("claim_id", "?")
        if r["disposition"] in ("draft-ready", "refer-specialist"):
            body = (r.get("draft_summary") or {}).get("body", "")
            if not body:
                errs.append(f"{cid}: draft disposition but no draft_summary.body")
            for s in REQUIRED_SECTIONS:
                if s not in body:
                    errs.append(f"{cid}: draft summary missing section {s!r}")
            if not r.get("citations"):
                errs.append(f"{cid}: draft with no citations")
            # band consistency
            ss, sb = r.get("severity_score"), r.get("severity_band")
            if ss is not None:
                exp = "S1 (Complex)" if ss >= s1_min else "S2 (Moderate)" if ss >= s2_min else "S3 (Standard)"
                if sb != exp:
                    errs.append(f"{cid}: severity_band {sb!r} != expected {exp!r} for score {ss}")
    return errs


def triage(doc: dict) -> dict:
    from validate_input import validate

    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    output = _calculate(doc)
    issues = [r["claim_id"] + ": " + n for r in output["triage"] for n in r.get("needs", [])]
    output["artifact"] = build_artifact(
        doc,
        output,
        producer="claims-triage-assistant",
        artifact_type="claims-triage-assistant-review",
        completeness="partial" if issues else "complete",
        evaluability="partial" if issues else "evaluable",
        issues=issues,
    )
    return output


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claims_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    out = triage(doc)
    print(json.dumps(out, indent=2))
    if selftest:
        errs = _self_check(out)
        for e in errs:
            print("ERROR", e)
        print(f"self-test: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
