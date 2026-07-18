#!/usr/bin/env python3
"""Deterministic surveillance alert triage engine for surveillance-alert-triager.

For each trade- or e-comms-surveillance alert: deduplicate against open cases, compute a
documented priority, apply ONLY the three approved suppression rules, and otherwise assemble
a durable-case-ID evidence bundle (chronology + parties + amounts + citations). It never
closes a case, makes a market-abuse determination, exonerates, or files anything, and never
suppresses outside the approved rules. A restricted-list / watch-list proximity flag
overrides suppression and forces escalation.

Usage: python calculate_or_transform.py alerts.json | --selftest
Prints the triage JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_PRIORITY = {
    "risk": {"High": 3, "Medium": 1, "Low": 0},
    "notional": [(1000000, 3), (250000, 2), (50000, 1)],
    "restricted_flag": 4, "scenario_hint": 2, "cross_product": 2,
    "velocity_per_prior": 1, "velocity_cap": 3,
    "p1_min": 7, "p2_min": 3,
}
APPROVED_SUPPRESSIONS = {"SUP-DUP-01", "SUP-WL-KNOWN", "SUP-CALIB-01"}
STANDING_NOTE = ("First-line triage only; no case has been closed, no determination of "
                 "market abuse has been made, and nothing has been filed.")


def _cite(a):
    return f"casemgmt:{a.get('source_ref','?')}"


def _chronology(a):
    """Deterministic, sorted event chronology; every event carries its own citation."""
    chrono = []
    for e in sorted(a.get("events") or [], key=lambda x: str(x.get("ts", ""))):
        chrono.append({
            "ts": e.get("ts"),
            "detail": e.get("detail"),
            "cite": f"{e.get('system','?')}:{e.get('ref','?')}",
        })
    return chrono


def _priority(a, cfg):
    score, why = 0, []
    acct = a.get("account") or {}
    r = cfg["risk"].get(acct.get("risk_rating"), 0)
    if r:
        score += r; why.append(f"risk {acct.get('risk_rating')} +{r}")
    notional = float(a.get("notional_total") or 0)
    for thr, pts in cfg["notional"]:
        if notional >= thr:
            score += pts; why.append(f"notional>={thr} +{pts}"); break
    if (a.get("flags") or {}).get("restricted_list_proximity"):
        score += cfg["restricted_flag"]; why.append(f"restricted-list proximity +{cfg['restricted_flag']}")
    if a.get("scenario_hint"):
        score += cfg["scenario_hint"]; why.append(f"scenario hint +{cfg['scenario_hint']}")
    if acct.get("cross_product_linkage"):
        score += cfg["cross_product"]; why.append(f"cross-product linkage +{cfg['cross_product']}")
    vel = min(int(a.get("prior_alerts_90d") or 0) * cfg["velocity_per_prior"], cfg["velocity_cap"])
    if vel:
        score += vel; why.append(f"velocity +{vel}")
    restricted = bool((a.get("flags") or {}).get("restricted_list_proximity"))
    band = "P1 (Elevated)" if (score >= cfg["p1_min"] or restricted) \
        else "P2 (Standard)" if score >= cfg["p2_min"] else "P3 (Low)"
    return score, band, why


def _dup_parent(a, open_cases):
    for c in open_cases:
        if (c.get("entity_id") == a.get("entity_id") and c.get("scenario_id") == a.get("scenario_id")
                and c.get("period") == a.get("period")):
            shared = set(c.get("evidence_ids") or []) & set(a.get("evidence_ids") or [])
            if shared and set(a.get("evidence_ids") or []) <= set(c.get("evidence_ids") or []):
                return c, "exact"      # subset -> exact duplicate
            if shared:
                return c, "partial"    # overlap -> possible duplicate (linked, not suppressed)
    return None, None


def triage_alert(a, doc, cfg):
    case_id = f"SURV-{a.get('alert_id')}"
    citations = [_cite(a)]
    acct = a.get("account") or {}
    restricted = bool((a.get("flags") or {}).get("restricted_list_proximity"))
    score, band, why = _priority(a, cfg)

    rec = {"alert_id": a.get("alert_id"), "case_id": case_id,
           "surveillance_type": a.get("surveillance_type"),
           "priority_score": score, "priority_band": band,
           "priority_reason": "; ".join(why), "citations": citations,
           "suppression": None, "escalation_bundle": None, "needs": []}

    # needs-data (never clear an alert by guessing)
    if acct.get("risk_rating") not in cfg["risk"] or not a.get("evidence_ids"):
        if acct.get("risk_rating") not in cfg["risk"]:
            rec["needs"].append("account risk rating")
        if not a.get("evidence_ids"):
            rec["needs"].append("triggering order/message evidence ids")
        rec["disposition"] = "needs-data"
        return rec

    parent, kind = _dup_parent(a, doc.get("open_cases") or [])

    # restricted-list / watch-list proximity overrides suppression -> escalate
    if restricted:
        rec["disposition"] = "escalate-to-investigation"
    elif kind == "exact":
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-DUP-01",
                              "evidence": {"parent_case_id": parent.get("case_id"),
                                           "matched_evidence": sorted(set(a["evidence_ids"]) & set(parent.get("evidence_ids", [])))},
                              "rule_set_version": doc.get("config_version")}
        return rec
    elif a.get("legs_whitelisted") and set(a.get("whitelist_accounts") or []) <= set(doc.get("approved_whitelist") or []) and a.get("whitelist_accounts"):
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-WL-KNOWN",
                              "evidence": {"whitelisted_accounts": a["whitelist_accounts"]},
                              "rule_set_version": doc.get("config_version")}
        return rec
    elif a.get("calibration_pattern_id"):
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-CALIB-01",
                              "evidence": {"pattern_id": a["calibration_pattern_id"], "qualifying_evidence": a["evidence_ids"]},
                              "rule_set_version": doc.get("config_version")}
        return rec
    elif kind == "partial":
        rec["disposition"] = "possible-duplicate"
        rec["linked_case_id"] = parent.get("case_id")
        return rec
    else:
        rec["disposition"] = "escalate-to-investigation"

    # e-comms escalations also flag the disclosure/supervision aspect to comms compliance
    if a.get("surveillance_type") == "ecomms":
        rec["route_specialist"] = "communications-compliance-reviewer"

    # durable evidence bundle for escalated alerts
    rec["escalation_bundle"] = {
        "case_id": case_id,
        "entity": a.get("entity_id"),
        "account_ref": a.get("account_ref"),
        "scenario_id": a.get("scenario_id"),
        "surveillance_type": a.get("surveillance_type"),
        "period": a.get("period"),
        "notional_total": a.get("notional_total"),
        "evidence_ids": a.get("evidence_ids"),
        "chronology": _chronology(a),
        "parties": a.get("parties") or [],
        "account": {"risk_rating": acct.get("risk_rating"), "cross_product_linkage": acct.get("cross_product_linkage")},
        "flags": a.get("flags") or {},
        "scenario_hint": a.get("scenario_hint"),
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
