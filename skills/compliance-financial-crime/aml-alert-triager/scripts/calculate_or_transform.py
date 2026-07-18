#!/usr/bin/env python3
"""Deterministic AML alert triage engine for aml-alert-triager.

For each alert: deduplicate against open cases, compute a documented priority, apply ONLY
the three approved suppression rules, and otherwise assemble an escalation bundle. It never
closes a case, exonerates, files a SAR, or suppresses outside the approved rules. A
sanctions/adverse-media proximity flag overrides suppression and forces escalation.

Usage: python calculate_or_transform.py alerts.json | --selftest
Prints the triage JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_PRIORITY = {
    "risk": {"High": 3, "Medium": 1, "Low": 0},
    "amount": [(100000, 3), (25000, 2), (10000, 1)],
    "sanctions_flag": 4, "typology_hint": 2, "high_risk_geo": 2,
    "velocity_per_prior": 1, "velocity_cap": 3,
    "p1_min": 7, "p2_min": 3,
}
APPROVED_SUPPRESSIONS = {"SUP-DUP-01", "SUP-WL-INTERNAL", "SUP-SEASONAL-01"}
STANDING_NOTE = ("First-line triage only; no case has been closed, no customer exonerated, "
                 "and no SAR filed.")


def _cite(a):
    return f"casemgmt:{a.get('source_ref','?')}"


def _priority(a, cfg):
    score, why = 0, []
    cust = a.get("customer") or {}
    r = cfg["risk"].get(cust.get("risk_rating"), 0)
    if r:
        score += r; why.append(f"risk {cust.get('risk_rating')} +{r}")
    amt = float(a.get("amount_total") or 0)
    for thr, pts in cfg["amount"]:
        if amt >= thr:
            score += pts; why.append(f"amount>={thr} +{pts}"); break
    if (a.get("flags") or {}).get("sanctions_adverse_media"):
        score += cfg["sanctions_flag"]; why.append(f"sanctions/adverse-media +{cfg['sanctions_flag']}")
    if a.get("typology_hint"):
        score += cfg["typology_hint"]; why.append(f"typology hint +{cfg['typology_hint']}")
    if cust.get("high_risk_geo"):
        score += cfg["high_risk_geo"]; why.append(f"high-risk geo +{cfg['high_risk_geo']}")
    vel = min(int(a.get("prior_alerts_90d") or 0) * cfg["velocity_per_prior"], cfg["velocity_cap"])
    if vel:
        score += vel; why.append(f"velocity +{vel}")
    band = "P1 (Elevated)" if (score >= cfg["p1_min"] or (a.get("flags") or {}).get("sanctions_adverse_media")) \
        else "P2 (Standard)" if score >= cfg["p2_min"] else "P3 (Low)"
    return score, band, why


def _dup_parent(a, open_cases):
    for c in open_cases:
        if (c.get("entity_id") == a.get("entity_id") and c.get("rule_id") == a.get("rule_id")
                and c.get("period") == a.get("period")):
            shared = set(c.get("txn_ids") or []) & set(a.get("txn_ids") or [])
            if shared and set(a.get("txn_ids") or []) <= set(c.get("txn_ids") or []):
                return c, "exact"      # subset -> exact duplicate
            if shared:
                return c, "partial"    # overlap -> possible duplicate (linked, not suppressed)
    return None, None


def triage_alert(a, doc, cfg):
    case_id = f"AML-{a.get('alert_id')}"
    citations = [_cite(a)]
    cust = a.get("customer") or {}
    sanctioned = bool((a.get("flags") or {}).get("sanctions_adverse_media"))
    score, band, why = _priority(a, cfg)

    rec = {"alert_id": a.get("alert_id"), "case_id": case_id, "priority_score": score,
           "priority_band": band, "priority_reason": "; ".join(why), "citations": citations,
           "suppression": None, "escalation_bundle": None, "needs": []}

    # needs-data (do not clear an alert by guessing)
    if cust.get("risk_rating") not in cfg["risk"] or not a.get("txn_ids"):
        if cust.get("risk_rating") not in cfg["risk"]:
            rec["needs"].append("customer risk rating")
        if not a.get("txn_ids"):
            rec["needs"].append("triggering transaction ids")
        rec["disposition"] = "needs-data"
        return rec

    parent, kind = _dup_parent(a, doc.get("open_cases") or [])

    # sanctions/adverse-media overrides suppression -> escalate
    if sanctioned:
        rec["disposition"] = "escalate-to-investigation"
        rec["route_specialist"] = "sanctions-match-adjudicator"
    elif kind == "exact":
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-DUP-01",
                              "evidence": {"parent_case_id": parent.get("case_id"),
                                           "matched_txns": sorted(set(a["txn_ids"]) & set(parent.get("txn_ids", [])))},
                              "rule_set_version": doc.get("config_version")}
        return rec
    elif a.get("legs_internal") and set(a.get("leg_accounts") or []) <= set(doc.get("approved_whitelist") or []) and a.get("leg_accounts"):
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-WL-INTERNAL",
                              "evidence": {"whitelisted_accounts": a["leg_accounts"]},
                              "rule_set_version": doc.get("config_version")}
        return rec
    elif a.get("seasonal_pattern_id"):
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-SEASONAL-01",
                              "evidence": {"pattern_id": a["seasonal_pattern_id"], "qualifying_txns": a["txn_ids"]},
                              "rule_set_version": doc.get("config_version")}
        return rec
    elif kind == "partial":
        rec["disposition"] = "possible-duplicate"
        rec["linked_case_id"] = parent.get("case_id")
        return rec
    else:
        rec["disposition"] = "escalate-to-investigation"

    # escalation bundle for escalated alerts
    rec["escalation_bundle"] = {
        "case_id": case_id,
        "entity": a.get("entity_id"),
        "account_ref": a.get("account_ref"),
        "rule_id": a.get("rule_id"),
        "period": a.get("period"),
        "amount_total": a.get("amount_total"),
        "txn_ids": a.get("txn_ids"),
        "kyc": {"risk_rating": cust.get("risk_rating"), "high_risk_geo": cust.get("high_risk_geo")},
        "flags": a.get("flags") or {},
        "typology_hint": a.get("typology_hint"),
        "linked_cases": [parent.get("case_id")] if parent else [],
        "recommended_priority": band,
        "citations": citations,
    }
    return rec


def triage(doc: dict) -> dict:
    cfg = {**DEFAULT_PRIORITY, **(doc.get("priority_config") or {})}
    records = [triage_alert(a, doc, cfg) for a in doc["alerts"]]
    summary = {
        "total": len(records),
        "escalated": sum(1 for r in records if r["disposition"] == "escalate-to-investigation"),
        "approved_suppressed": sum(1 for r in records if r["disposition"] == "approved-suppressed"),
        "needs_data": sum(1 for r in records if r["disposition"] == "needs-data"),
        "possible_duplicate": sum(1 for r in records if r["disposition"] == "possible-duplicate"),
    }
    return {"config_version": doc.get("config_version"), "triage": records,
            "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "alerts_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(triage(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
