#!/usr/bin/env python3
"""Deterministic EDD package assembler for enhanced-due-diligence-packager.

Marshals an EDD case-intake file into a controlled, source-mapped draft EDD package that
maps to assets/output-template.md. For each required evidence section it records status
(present | gap) and citations; it computes a documented residual-risk indicator from
explainable factors, assembles an approval ledger, and emits an advisory recommendation for
human adjudication.

Hard boundaries (fail closed): a sanctions true-match sets `hard_boundary` and forces
`packaging_status = blocked` with a specialist route. The packager NEVER makes or
communicates an onboarding/retention/exit decision, changes a risk rating of record, closes
a case, files a report, writes a system of record, or sends/submits the package.

Usage: python calculate_or_transform.py case.json | --selftest
Prints the EDD package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Documented residual-risk weights (configuration, not judgement). Override via
# doc["risk_config"]. The band is an INDICATOR to inform human adjudication, never a rating
# of record or a decision.
DEFAULT_RISK = {
    "pep": {"primary": 4, "associate": 2, "family": 2, "none": 0},
    "high_risk_geo_per_nexus": 3, "high_risk_geo_cap": 6,
    "adverse_media": {"severe": 4, "moderate": 2, "low": 1, "none": 0},
    "ownership": {"nominee": 3, "opaque": 3, "layered": 2, "transparent": 0},
    "cash_intensive": 2,
    "channel": {"non-face-to-face": 2, "correspondent": 2, "private-banking": 2, "standard": 0},
    "sof_sow_inconsistency": 3,
    "high_min": 10, "medium_min": 5,
}

REQUIRED_EVIDENCE = (
    "customer_overview", "source_of_funds", "source_of_wealth", "ownership_control",
    "geography_exposure", "adverse_media", "pep_sanctions_screening", "expected_activity",
    "ongoing_monitoring_controls",
)
SECTION_TITLES = {
    "customer_overview": "Case & Customer Overview",
    "source_of_funds": "Source of Funds (SoF)",
    "source_of_wealth": "Source of Wealth (SoW)",
    "ownership_control": "Ownership & Control (UBO)",
    "geography_exposure": "Geographic Exposure",
    "adverse_media": "Adverse Media",
    "pep_sanctions_screening": "PEP & Sanctions Screening",
    "expected_activity": "Expected Activity & Rationale",
    "ongoing_monitoring_controls": "Ongoing Monitoring & Controls",
}
STANDING_NOTE = (
    "Draft EDD package for human adjudication only. This package records evidence, source "
    "citations, and a risk-based recommendation; it makes no onboarding, retention, exit, or "
    "risk-rating decision, files no report, writes no system of record, and has not been sent "
    "or submitted. Every regulated decision and filing remains with the authorized adjudicator."
)


def _evidence_section(sec: str, s: dict | None) -> dict:
    s = s or {}
    present = bool(s.get("present")) and bool(s.get("items")) and bool(s.get("citations"))
    gaps = list(s.get("gaps") or [])
    if not present:
        if not s.get("present"):
            gaps.append("section not provided")
        else:
            if not s.get("items"):
                gaps.append("no evidence items")
            if not s.get("citations"):
                gaps.append("evidence not source-cited")
    return {
        "title": SECTION_TITLES[sec],
        "status": "present" if present else "gap",
        "items": list(s.get("items") or []),
        "citations": list(s.get("citations") or []),
        "gaps": gaps,
    }


def _residual_risk(rf: dict, cfg: dict) -> dict:
    score, factors = 0, []
    pep = (rf.get("pep_status") or "none").lower()
    pep_pts = cfg["pep"].get(pep, 0)
    if pep_pts:
        score += pep_pts; factors.append(f"PEP {pep} +{pep_pts}")
    nexus = rf.get("high_risk_geography_nexus") or []
    geo = min(len(nexus) * cfg["high_risk_geo_per_nexus"], cfg["high_risk_geo_cap"])
    if geo:
        score += geo; factors.append(f"high-risk geography x{len(nexus)} +{geo}")
    am = (rf.get("adverse_media_severity") or "none").lower()
    am_pts = cfg["adverse_media"].get(am, 0)
    if am_pts:
        score += am_pts; factors.append(f"adverse media {am} +{am_pts}")
    own = (rf.get("ownership_opacity") or "transparent").lower()
    own_pts = cfg["ownership"].get(own, 0)
    if own_pts:
        score += own_pts; factors.append(f"ownership {own} +{own_pts}")
    if rf.get("cash_intensive"):
        score += cfg["cash_intensive"]; factors.append(f"cash-intensive +{cfg['cash_intensive']}")
    ch = (rf.get("product_channel_risk") or "standard").lower()
    ch_pts = cfg["channel"].get(ch, 0)
    if ch_pts:
        score += ch_pts; factors.append(f"channel {ch} +{ch_pts}")
    if rf.get("sof_sow_inconsistency"):
        score += cfg["sof_sow_inconsistency"]; factors.append(f"SoF/SoW inconsistency +{cfg['sof_sow_inconsistency']}")

    hard = bool(rf.get("sanctions_true_match"))
    if hard:
        band = "Prohibited-proximity"
    elif score >= cfg["high_min"]:
        band = "High"
    elif score >= cfg["medium_min"]:
        band = "Medium"
    else:
        band = "Low"
    return {
        "title": "Residual Risk Assessment",
        "residual_risk_band": band,
        "score": score,
        "factors": factors,
        "hard_boundary": hard,
        "note": "Deterministic indicator to inform human adjudication; not a risk rating of record.",
    }


def _routes(rf: dict) -> list[dict]:
    routes = []
    if rf.get("sanctions_true_match"):
        routes.append({"skill": "sanctions-match-adjudicator",
                       "reason": "sanctions true-match indicator — adjudicate before any onboarding/retention consideration"})
    if (rf.get("adverse_media_severity") or "none").lower() in ("moderate", "severe"):
        routes.append({"skill": "adverse-media-investigator",
                       "reason": "corroborate adverse-media findings and disposition"})
    if (rf.get("ownership_opacity") or "transparent").lower() in ("layered", "opaque", "nominee"):
        routes.append({"skill": "beneficial-ownership-verifier",
                       "reason": "independently verify UBO / control chain"})
    return routes


def _recommendation(band: str, status: str, hard: bool) -> dict:
    if hard:
        path = "hold-pending-specialist"
        note = ("Hard boundary reached (sanctions true-match indicator). Recommend the package "
                "be held and routed to the sanctions specialist for adjudication before any "
                "onboarding, retention, or exit consideration. No decision, rating change, or "
                "filing is made here.")
    elif status == "needs-evidence":
        path = "return-for-evidence"
        note = ("Evidence gaps remain. Recommend returning the case for the missing evidence "
                "before adjudication; do not proceed on assumptions. No decision is made here.")
    elif band == "High":
        path = "senior-management-adjudication"
        note = ("Residual risk assessed High on documented factors. Recommend senior-management "
                "adjudication with enhanced ongoing monitoring (6-month cadence) and specialist "
                "confirmation of ownership and adverse-media findings before any onboarding or "
                "retention decision. Recommendation only — not a decision, rating change, or filing.")
    elif band == "Medium":
        path = "edd-committee-adjudication"
        note = ("Residual risk assessed Medium. Recommend EDD/onboarding committee adjudication "
                "with defined ongoing-monitoring controls. Recommendation only — not a decision, "
                "rating change, or filing.")
    else:
        path = "standard-adjudication"
        note = ("Residual risk assessed Low after documented mitigation. Recommend standard "
                "adjudication with baseline monitoring. Recommendation only — not a decision, "
                "rating change, or filing.")
    return {"title": "Recommendation for Adjudication", "recommended_review_path": path, "note": note}


def _approvals(required: list, recorded: list) -> dict:
    by_role = {r.get("role"): r for r in (recorded or []) if isinstance(r, dict)}
    ledger = []
    for role in required:
        rec = by_role.get(role)
        if rec and rec.get("approver") and rec.get("date"):
            ledger.append({"role": role, "status": "obtained",
                           "approver": rec.get("approver"), "date": rec.get("date")})
        else:
            ledger.append({"role": role, "status": "pending"})
    return {"title": "Approvals & Sign-off", "required": list(required), "ledger": ledger,
            "note": "Draft is queued for adjudication; obtaining these approvals is the human step."}


def package(doc: dict) -> dict:
    cfg = {**DEFAULT_RISK, **(doc.get("risk_config") or {})}
    cust = doc.get("customer") or {}
    ev = doc.get("evidence") or {}
    rf = doc.get("risk_factors") or {}

    sections: dict = {}
    all_cites: list[str] = []

    # 1. Evidence sections
    for sec in REQUIRED_EVIDENCE:
        built = _evidence_section(sec, ev.get(sec))
        sections[sec] = built
        all_cites.extend(built["citations"])

    # 2. Trigger & scope
    trigger_cite = [f"casemgmt:{doc.get('case_id','?')}@intake"]
    sections["edd_trigger_scope"] = {
        "title": "EDD Trigger & Scope",
        "triggers": list(cust.get("edd_trigger") or []),
        "jurisdiction": doc.get("jurisdiction"),
        "risk_rating_of_record": cust.get("risk_rating_of_record"),
        "citations": trigger_cite,
        "note": "Risk rating of record is carried for context; this package does not change it.",
    }
    all_cites.extend(trigger_cite)

    # 3. Residual risk (deterministic)
    risk = _residual_risk(rf, cfg)
    sections["residual_risk_assessment"] = risk
    hard = risk["hard_boundary"]

    # 4. Packaging status (fail closed on hard boundary; needs-evidence on any gap)
    gaps = [s for s in REQUIRED_EVIDENCE if sections[s]["status"] == "gap"]
    if hard:
        status = "blocked"
    elif gaps:
        status = "needs-evidence"
    else:
        status = "ready-for-adjudication"

    # 5. Recommendation + routes + approvals
    sections["recommendation"] = _recommendation(risk["residual_risk_band"], status, hard)
    routes = _routes(rf)
    sections["approvals"] = _approvals(doc.get("required_approvals") or [], doc.get("recorded_approvals") or [])

    # 6. Sources & citations (aggregate) + standing note
    sections["sources_citations"] = {
        "title": "Sources & Citations",
        "citations": sorted(set(all_cites)),
        "note": "Every asserted evidence item is mapped to an approved source above.",
    }
    sections["standing_note_limitations"] = {
        "title": "Standing Note / Limitations",
        "text": STANDING_NOTE,
    }

    return {
        "config_version": doc.get("config_version"),
        "template_version": doc.get("template_version") or "edd-package-v1",
        "case_id": doc.get("case_id"),
        "customer_ref": cust.get("customer_ref") or "****",
        "jurisdiction": doc.get("jurisdiction"),
        "packaging_status": status,
        "hard_boundary": hard,
        "gaps": gaps,
        "routes": routes,
        "sections": sections,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "edd_case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(package(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
