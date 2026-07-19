#!/usr/bin/env python3
"""Deterministic data-quality investigation engine for data-quality-issue-investigator.

For each data-quality issue it: quantifies impact (failure rate, affected consumers),
computes a documented severity band, builds a chronology from timestamped events, resolves
the parties, and assembles a cited evidence bundle with a durable case_id. It then emits a
RECOMMENDATION disposition only. It never closes an issue, confirms a root cause, marks data
remediated, or files anything — a material/regulated impact forces an incident-escalation
recommendation and an overlap with an open case is linked as a possible duplicate (never
auto-merged or closed).

Usage: python calculate_or_transform.py dq_issues.json | --selftest
Prints the investigation JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_SEVERITY = {
    "failure_rate": [(0.20, 3), (0.05, 2), (0.01, 1)],
    "regulatory_report": 4, "material_model": 3, "regulated_decision": 3,
    "classification": {"Restricted": 2, "Confidential": 1, "Internal": 0, "Public": 0},
    "consumer_per": 1, "consumer_cap": 3,
    "recurrence_per_prior": 1, "recurrence_cap": 2,
    "s1_min": 9, "s2_min": 5, "s3_min": 2,
}
MATERIAL_MODEL_LEVELS = {"High", "Critical"}
DEFECT_TYPES = {"completeness", "validity", "uniqueness", "consistency", "timeliness", "accuracy"}
STANDING_NOTE = ("Investigation evidence and recommendations only; no data-quality issue has "
                 "been closed, no root cause confirmed, and no data remediated, waived, or "
                 "signed off.")


def _cite(it):
    return f"catalog:{it.get('source_ref','?')}"


def _consumers(it):
    c = it.get("consumers") or {}
    reg = list(c.get("regulatory_reports") or [])
    internal = list(c.get("internal_reports") or [])
    models = list(c.get("models") or [])
    decisions = list(c.get("regulated_decisions") or [])
    material_models = [m for m in models if (m or {}).get("materiality") in MATERIAL_MODEL_LEVELS]
    return reg, internal, models, decisions, material_models


def _severity(it, cfg):
    score, why = 0, []
    tot = it.get("total_records") or 0
    fail = it.get("failing_records") or 0
    rate = (fail / tot) if tot else 0.0
    for thr, pts in cfg["failure_rate"]:
        if rate >= thr:
            score += pts; why.append(f"failure_rate>={thr} +{pts}"); break
    reg, internal, models, decisions, material_models = _consumers(it)
    if reg:
        score += cfg["regulatory_report"]; why.append(f"regulatory report +{cfg['regulatory_report']}")
    if material_models:
        score += cfg["material_model"]; why.append(f"material model +{cfg['material_model']}")
    if decisions:
        score += cfg["regulated_decision"]; why.append(f"regulated decision +{cfg['regulated_decision']}")
    cls = cfg["classification"].get(it.get("data_classification"), 0)
    if cls:
        score += cls; why.append(f"classification {it.get('data_classification')} +{cls}")
    n_consumers = len(reg) + len(internal) + len(models) + len(decisions)
    cpts = min(n_consumers * cfg["consumer_per"], cfg["consumer_cap"])
    if cpts:
        score += cpts; why.append(f"downstream consumers +{cpts}")
    rpts = min(int(it.get("prior_issues_90d") or 0) * cfg["recurrence_per_prior"], cfg["recurrence_cap"])
    if rpts:
        score += rpts; why.append(f"recurrence +{rpts}")
    band = _band(score, bool(reg), cfg)
    is_material = bool(reg or material_models or decisions)
    return score, band, why, rate, is_material


def _band(score, has_reg_report, cfg):
    if score >= cfg["s1_min"] or has_reg_report:
        return "S1 (Critical)"
    if score >= cfg["s2_min"]:
        return "S2 (High)"
    if score >= cfg["s3_min"]:
        return "S3 (Moderate)"
    return "S4 (Low)"


def _chronology(it):
    events = sorted((it.get("events") or []), key=lambda e: e.get("ts") or "")
    return [{"ts": e.get("ts"), "type": e.get("type"),
             "citation": f"catalog:{e.get('ref','?')}"} for e in events]


def _dup_parent(it, open_cases):
    for c in open_cases:
        if (c.get("dataset_id") == it.get("dataset_id") and c.get("rule_id") == it.get("rule_id")
                and c.get("period") == it.get("period")):
            shared = set(c.get("record_keys") or []) & set(it.get("record_keys") or [])
            if shared:
                return c
    return None


def investigate_issue(it, doc, cfg):
    case_id = f"DQI-{it.get('issue_id')}"
    citations = [_cite(it)]
    rec = {"issue_id": it.get("issue_id"), "case_id": case_id, "citations": citations,
           "severity_score": 0, "severity_band": "S4 (Low)", "severity_reason": "",
           "evidence_bundle": None, "needs": []}

    # needs-data: never profile a defect by guessing missing counts / defect type
    if it.get("defect_type") not in DEFECT_TYPES:
        rec["needs"].append("defect_type")
    if not isinstance(it.get("total_records"), (int, float)) or not isinstance(it.get("failing_records"), (int, float)):
        rec["needs"].append("total_records/failing_records")
    if rec["needs"]:
        rec["disposition"] = "needs-data"
        return rec

    # duplicate of an open case -> link for human confirmation (never auto-merge/close)
    parent = _dup_parent(it, doc.get("open_cases") or [])
    if parent:
        rec["disposition"] = "possible-duplicate"
        rec["linked_case_id"] = parent.get("case_id")
        return rec

    score, band, why, rate, is_material = _severity(it, cfg)
    rec["severity_score"] = score
    rec["severity_band"] = band
    rec["severity_reason"] = "; ".join(why)

    reg, internal, models, decisions, material_models = _consumers(it)
    # recommendation only (an investigation recommends; it never decides or closes)
    if is_material or band == "S1 (Critical)":
        rec["disposition"] = "recommend-incident-escalation"
        rec["route_specialist"] = "ai-incident-investigator"
    elif it.get("upstream_suspected"):
        rec["disposition"] = "recommend-upstream-trace"
        rec["route_specialist"] = "data-lineage-documenter"
    else:
        rec["disposition"] = "recommend-remediation"

    tot = it.get("total_records") or 0
    fail = it.get("failing_records") or 0
    rec["evidence_bundle"] = {
        "case_id": case_id,
        "dataset_id": it.get("dataset_id"),
        "field": it.get("field"),
        "rule_id": it.get("rule_id"),
        "defect_type": it.get("defect_type"),
        "period": it.get("period"),
        "parties": {
            "data_owner": (it.get("owners") or {}).get("data_owner"),
            "steward": (it.get("owners") or {}).get("steward"),
            "upstream_owner": (it.get("owners") or {}).get("upstream_owner"),
        },
        "amounts": {
            "total_records": tot,
            "failing_records": fail,
            "failure_rate": round(rate, 4),
            "affected_regulatory_reports": len(reg),
            "affected_internal_reports": len(internal),
            "affected_models": len(models),
            "affected_regulated_decisions": len(decisions),
            "monetary_exposure": it.get("monetary_exposure", 0),
        },
        "consumers": {"regulatory_reports": reg, "internal_reports": internal,
                      "models": models, "regulated_decisions": decisions},
        "chronology": _chronology(it),
        "recommended_severity": band,
        "citations": citations,
    }
    return rec


def investigate(doc: dict) -> dict:
    cfg = {**DEFAULT_SEVERITY, **(doc.get("severity_config") or {})}
    records = [investigate_issue(it, doc, cfg) for it in doc["issues"]]
    summary = {
        "total": len(records),
        "recommend_incident_escalation": sum(1 for r in records if r["disposition"] == "recommend-incident-escalation"),
        "recommend_remediation": sum(1 for r in records if r["disposition"] == "recommend-remediation"),
        "recommend_upstream_trace": sum(1 for r in records if r["disposition"] == "recommend-upstream-trace"),
        "needs_data": sum(1 for r in records if r["disposition"] == "needs-data"),
        "possible_duplicate": sum(1 for r in records if r["disposition"] == "possible-duplicate"),
    }
    return {"config_version": doc.get("config_version"),
            "severity_config": doc.get("severity_config"), "investigation": records,
            "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "dq_issues_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(investigate(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
