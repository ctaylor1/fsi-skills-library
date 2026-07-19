#!/usr/bin/env python3
"""Deterministic security-alert triage engine for security-alert-triage-assistant.

Marshals a security-alert batch-intake file into a controlled, source-mapped DRAFT triage
package that maps to assets/output-template.md. For each alert it: enriches (asset, identity,
threat intel, vuln/cloud posture), correlates/deduplicates against open cases (link, never
merge), computes a documented priority, applies ONLY the three approved suppression rules,
and otherwise assembles an analyst-ready investigation-context bundle. It emits the eleven
required template sections, an approval ledger, and advisory routing.

Hard boundaries (fail closed): a `threat_intel.active_compromise` indicator sets
`hard_boundary` and forces `package_status = blocked` with an urgent incident-response route;
a `threat_intel.known_malicious` indicator overrides suppression and forces escalation. This
skill NEVER closes an alert, declares/closes an incident, contains/isolates/blocks/disables
an asset or identity, writes a system of record (SIEM/SOAR/ticketing), or sends/submits the
package. Every decision and response action stays with the human analyst / IR process.

Usage: python calculate_or_transform.py alerts.json | --selftest
Prints the triage-package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Documented priority weights (configuration, not judgement). Override via
# doc["priority_config"]. The band is a triage RANK to inform a human analyst, never a
# verdict, closure, or response decision.
DEFAULT_PRIORITY = {
    "criticality": {"Critical": 4, "High": 3, "Medium": 1, "Low": 0},
    "privilege": {"privileged": 3, "service": 2, "standard": 0},
    "threat_intel": {"known_malicious": 4, "high": 3, "medium": 1, "low": 0, "none": 0},
    "internet_facing": 2,
    "kev_nexus": 3,
    "confidence": {"high": 2, "medium": 1, "low": 0},
    "correlation_per": 1, "correlation_cap": 3,
    "p1_min": 9, "p2_min": 5,
}
APPROVED_SUPPRESSIONS = {"SUP-DUP-01", "SUP-SCANNER-01", "SUP-MAINT-01"}
ROUTE_BY_CLASS = {
    "malware-c2": "cyber-incident-response-coordinator",
    "ransomware-precursor": "cyber-incident-response-coordinator",
    "phishing": "phishing-and-bec-investigator",
    "bec": "phishing-and-bec-investigator",
    "auth-anomaly": "identity-access-reviewer",
    "privilege-escalation": "identity-access-reviewer",
    "brute-force": "identity-access-reviewer",
    "vuln-exploit": "vulnerability-prioritization-assistant",
    "cloud-misconfig": "cloud-security-posture-reviewer",
    "data-exfil": "data-loss-prevention-incident-assistant",
}
DEFAULT_ROUTE = "cyber-incident-response-coordinator"
STANDING_NOTE = (
    "Draft security-alert triage package for analyst investigation only. This package "
    "enriches, prioritizes, correlates, and applies only approved suppression rules to raise "
    "analyst-ready context; it makes no alert-closure, incident, containment, or remediation "
    "decision, isolates/blocks/disables nothing, writes no system of record (SIEM/SOAR/"
    "ticketing), and has not been sent or submitted. Every regulated security decision and "
    "response action remains with the authorized human analyst and incident-response process."
)


def _citations(a: dict) -> list[str]:
    """Map each contributing system to a {system}:{ref}@{date} citation."""
    as_of = a.get("as_of") or "current"
    cites = [f"siem:{a.get('source_ref','?')}@{as_of}"]
    asset = a.get("asset") or {}
    if asset.get("asset_id"):
        cites.append(f"cmdb:asset={asset['asset_id']}@{as_of}")
    ident = a.get("identity") or {}
    if ident.get("identity_ref"):
        cites.append(f"iam:identity={ident['identity_ref']}@{as_of}")
    if a.get("threat_intel"):
        cites.append(f"ti:signature={a.get('signature_id','sig')}@{as_of}")
    if a.get("vuln_posture"):
        cites.append(f"posture:asset={asset.get('asset_id','asset')}@{as_of}")
    return cites


def _enrichment(a: dict) -> dict:
    asset = a.get("asset") or {}
    ident = a.get("identity") or {}
    ti = a.get("threat_intel") or {}
    vp = a.get("vuln_posture") or {}
    return {
        "asset": {"asset_id": asset.get("asset_id"), "asset_ref": asset.get("asset_ref") or "****",
                  "criticality": asset.get("criticality"), "internet_facing": bool(asset.get("internet_facing"))},
        "identity": {"identity_ref": ident.get("identity_ref") or "****", "privilege": ident.get("privilege") or "standard"},
        "threat_intel": {"severity": ti.get("severity") or "none", "known_malicious": bool(ti.get("known_malicious")),
                         "active_compromise": bool(ti.get("active_compromise")), "iocs": list(ti.get("iocs") or [])},
        "vuln_posture": {"kev_nexus": bool(vp.get("kev_nexus")), "exposure": vp.get("exposure")},
    }


def _priority(a: dict, cfg: dict) -> tuple[int, str, list[str], bool]:
    score, why = 0, []
    asset = a.get("asset") or {}
    ident = a.get("identity") or {}
    ti = a.get("threat_intel") or {}
    vp = a.get("vuln_posture") or {}

    c = cfg["criticality"].get(asset.get("criticality"), 0)
    if c:
        score += c; why.append(f"asset {asset.get('criticality')} +{c}")
    pv = cfg["privilege"].get((ident.get("privilege") or "standard"), 0)
    if pv:
        score += pv; why.append(f"identity {ident.get('privilege')} +{pv}")
    known_mal = bool(ti.get("known_malicious"))
    sev = "known_malicious" if known_mal else (ti.get("severity") or "none")
    ti_pts = cfg["threat_intel"].get(sev, 0)
    if ti_pts:
        score += ti_pts; why.append(f"threat-intel {sev} +{ti_pts}")
    if asset.get("internet_facing"):
        score += cfg["internet_facing"]; why.append(f"internet-facing +{cfg['internet_facing']}")
    if vp.get("kev_nexus"):
        score += cfg["kev_nexus"]; why.append(f"known-exploited-vuln nexus +{cfg['kev_nexus']}")
    conf = (a.get("signal_confidence") or "low")
    cf = cfg["confidence"].get(conf, 0)
    if cf:
        score += cf; why.append(f"confidence {conf} +{cf}")
    corr = min(int(a.get("correlated_count") or 0) * cfg["correlation_per"], cfg["correlation_cap"])
    if corr:
        score += corr; why.append(f"correlation +{corr}")

    band = "P1 (Critical)" if (score >= cfg["p1_min"] or known_mal) \
        else "P2 (High)" if score >= cfg["p2_min"] else "P3 (Moderate)"
    return score, band, why, known_mal


def _dup_parent(a: dict, open_cases: list) -> tuple[dict | None, str | None]:
    for c in open_cases:
        if (c.get("asset_id") == (a.get("asset") or {}).get("asset_id")
                and c.get("signature_id") == a.get("signature_id")
                and c.get("window") == a.get("window")):
            shared = set(c.get("signal_ids") or []) & set(a.get("signal_ids") or [])
            if shared and set(a.get("signal_ids") or []) <= set(c.get("signal_ids") or []):
                return c, "exact"      # subset -> exact duplicate
            if shared:
                return c, "correlated"  # overlap -> correlated duplicate (linked, not suppressed)
    return None, None


def _investigation_context(a: dict, case_id: str, enr: dict, band: str, why: list, parent, citations, next_steps) -> dict:
    return {
        "case_id": case_id,
        "asset": enr["asset"],
        "identity": enr["identity"],
        "signature_id": a.get("signature_id"),
        "alert_class": a.get("alert_class"),
        "window": a.get("window"),
        "signal_ids": a.get("signal_ids"),
        "threat_intel": enr["threat_intel"],
        "vuln_posture": enr["vuln_posture"],
        "correlated_cases": [parent.get("case_id")] if parent else [],
        "recommended_priority": band,
        "priority_reason": "; ".join(why),
        "recommended_next_steps": next_steps,
        "citations": citations,
    }


def _next_steps(a: dict, enr: dict, urgent: bool) -> str:
    cls = a.get("alert_class")
    if urgent:
        return ("Recommend the analyst treat this as a potential active compromise and hand to the "
                "incident-response process for scoping; validate the indicators and blast radius. "
                "This skill performs no containment; the IR process decides any response action.")
    if cls in ("malware-c2", "ransomware-precursor"):
        return ("Recommend the analyst review the malicious-signal chain and correlated alerts, confirm "
                "indicator reputation against threat intelligence, and assess blast radius across the "
                "affected asset before incident response determines any response action.")
    if cls in ("auth-anomaly", "privilege-escalation", "brute-force"):
        return ("Recommend the analyst review authentication and sign-in evidence for the affected "
                "identity, compare against baseline behavior, and route to the identity-access review "
                "for a privileged-access assessment.")
    if cls == "vuln-exploit":
        return ("Recommend the analyst confirm exploitability and known-exploited-vulnerability status, "
                "review exposure of the affected asset, and route to vulnerability prioritization.")
    if cls == "cloud-misconfig":
        return ("Recommend the analyst review the cloud-posture finding against the approved baseline and "
                "route to cloud-security-posture review for confirmation.")
    if cls == "data-exfil":
        return ("Recommend the analyst review the data-movement signals and destination reputation, and "
                "route to the data-loss-prevention incident review.")
    return ("Recommend the analyst review the enriched signals and correlated context, and confirm "
            "indicator reputation before determining a route.")


def triage_alert(a: dict, doc: dict, cfg: dict) -> dict:
    case_id = f"SEC-{a.get('alert_id')}"
    enr = _enrichment(a)
    citations = _citations(a)
    asset = a.get("asset") or {}
    ti = a.get("threat_intel") or {}
    active = bool(ti.get("active_compromise"))
    score, band, why, known_mal = _priority(a, cfg)

    rec = {"alert_id": a.get("alert_id"), "case_id": case_id, "alert_class": a.get("alert_class"),
           "priority_score": score, "priority_band": band, "priority_reason": "; ".join(why),
           "ti_known_malicious": known_mal, "enrichment": enr, "citations": citations,
           "suppression": None, "investigation_context": None, "needs": []}

    # needs-data: never clear or package an alert by guessing missing enrichment.
    if asset.get("criticality") not in cfg["criticality"] or not a.get("signal_ids"):
        if asset.get("criticality") not in cfg["criticality"]:
            rec["needs"].append("asset criticality (asset unresolved in CMDB)")
        if not a.get("signal_ids"):
            rec["needs"].append("triggering signal ids")
        rec["disposition"] = "needs-data"
        return rec

    parent, kind = _dup_parent(a, doc.get("open_cases") or [])

    # HARD BOUNDARY: active compromise -> escalate + block the batch; IR process, not this skill.
    if active:
        rec["disposition"] = "prepared-for-investigation"
        rec["hard_boundary_alert"] = True
        rec["urgent"] = True
        rec["route_specialist"] = DEFAULT_ROUTE
        rec["investigation_context"] = _investigation_context(
            a, case_id, enr, band, why, parent, citations, _next_steps(a, enr, True))
        return rec

    # known-malicious threat intel OVERRIDES suppression -> escalate.
    if known_mal:
        rec["disposition"] = "prepared-for-investigation"
        rec["route_specialist"] = ROUTE_BY_CLASS.get(a.get("alert_class"), DEFAULT_ROUTE)
        rec["investigation_context"] = _investigation_context(
            a, case_id, enr, band, why, parent, citations, _next_steps(a, enr, False))
        return rec

    # Approved suppression (the ONLY suppressions permitted), in precedence order.
    if kind == "exact":
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-DUP-01",
                              "evidence": {"parent_case_id": parent.get("case_id"),
                                           "matched_signals": sorted(set(a["signal_ids"]) & set(parent.get("signal_ids", [])))},
                              "rule_set_version": doc.get("config_version")}
        return rec
    scanner = a.get("source_scanner")
    if scanner and scanner in set(doc.get("approved_scanner_sources") or []):
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-SCANNER-01",
                              "evidence": {"scanner_id": scanner, "signal_ids": a["signal_ids"]},
                              "rule_set_version": doc.get("config_version")}
        return rec
    mw = a.get("maintenance_window_id")
    if mw and mw in {w.get("id") for w in (doc.get("approved_maintenance_windows") or [])}:
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-MAINT-01",
                              "evidence": {"window_id": mw, "qualifying_signals": a["signal_ids"]},
                              "rule_set_version": doc.get("config_version")}
        return rec
    if kind == "correlated":
        rec["disposition"] = "correlated-duplicate"
        rec["linked_case_id"] = parent.get("case_id")
        return rec

    # Otherwise: package analyst-ready investigation context.
    rec["disposition"] = "prepared-for-investigation"
    rec["route_specialist"] = ROUTE_BY_CLASS.get(a.get("alert_class"), DEFAULT_ROUTE)
    rec["investigation_context"] = _investigation_context(
        a, case_id, enr, band, why, parent, citations, _next_steps(a, enr, False))
    return rec


def _sections(doc: dict, records: list, status: str) -> dict:
    enr_cites, ctx_cites, all_cites = [], [], []
    enr_items, assets, identities, links, sup_entries, prio_records, ctx_packages, routes = [], {}, {}, [], [], [], [], []

    for r in records:
        all_cites.extend(r.get("citations") or [])
        enr = r.get("enrichment") or {}
        enr_cites.extend(r.get("citations") or [])
        a_id = r["alert_id"]
        asset = enr.get("asset") or {}
        ident = enr.get("identity") or {}
        enr_items.append(f"{a_id} [{r.get('alert_class')}]: asset {asset.get('asset_ref')} "
                         f"({asset.get('criticality')}), identity {ident.get('identity_ref')} ({ident.get('privilege')})")
        if asset.get("asset_id"):
            e = assets.setdefault(asset["asset_id"], {"asset_id": asset["asset_id"], "asset_ref": asset.get("asset_ref"),
                                                       "criticality": asset.get("criticality"),
                                                       "internet_facing": asset.get("internet_facing"), "alert_ids": []})
            e["alert_ids"].append(a_id)
        if ident.get("identity_ref") and ident.get("identity_ref") != "****":
            e = identities.setdefault(ident["identity_ref"], {"identity_ref": ident["identity_ref"],
                                                              "privilege": ident.get("privilege"), "alert_ids": []})
            e["alert_ids"].append(a_id)
        prio_records.append({"alert_id": a_id, "priority_band": r["priority_band"],
                             "priority_score": r["priority_score"], "priority_reason": r["priority_reason"]})
        disp = r["disposition"]
        if disp == "approved-suppressed":
            s = r["suppression"]
            sup_entries.append({"alert_id": a_id, "rule_id": s["rule_id"], "evidence": s["evidence"],
                                "rule_set_version": s.get("rule_set_version")})
        elif disp == "correlated-duplicate":
            links.append({"alert_id": a_id, "relationship": "correlated-duplicate", "parent_case_id": r.get("linked_case_id")})
        elif disp == "prepared-for-investigation":
            ctx = r["investigation_context"]
            ctx_packages.append(ctx)
            ctx_cites.extend(ctx.get("citations") or [])
            routes.append({"alert_id": a_id, "skill": r.get("route_specialist"),
                           "reason": f"{r.get('alert_class')} at {r['priority_band']}",
                           "urgent": bool(r.get("urgent"))})

    # exact-duplicate suppressions also record their parent link for lineage
    for r in records:
        if r["disposition"] == "approved-suppressed" and (r.get("suppression") or {}).get("rule_id") == "SUP-DUP-01":
            links.append({"alert_id": r["alert_id"], "relationship": "exact-duplicate",
                          "parent_case_id": r["suppression"]["evidence"].get("parent_case_id")})

    band_counts = {"P1 (Critical)": 0, "P2 (High)": 0, "P3 (Moderate)": 0}
    for r in records:
        band_counts[r["priority_band"]] = band_counts.get(r["priority_band"], 0) + 1

    sections = {
        "triage_batch_overview": {
            "title": "Triage Batch Overview", "batch_id": doc.get("batch_id"),
            "source_queue": doc.get("source_queue"), "package_status": status,
            "total_alerts": len(records),
            "counts": {
                "prepared_for_investigation": sum(1 for r in records if r["disposition"] == "prepared-for-investigation"),
                "approved_suppressed": sum(1 for r in records if r["disposition"] == "approved-suppressed"),
                "needs_data": sum(1 for r in records if r["disposition"] == "needs-data"),
                "correlated_duplicate": sum(1 for r in records if r["disposition"] == "correlated-duplicate"),
            },
            "config_version": doc.get("config_version"),
            "template_version": doc.get("template_version") or "sec-triage-package-v1",
        },
        "alert_enrichment": {
            "title": "Alert Enrichment", "status": "present" if enr_cites else "empty",
            "items": enr_items, "citations": sorted(set(enr_cites)),
        },
        "asset_identity_map": {
            "title": "Affected Assets & Identities",
            "status": "present" if (assets or identities) else "empty",
            "assets": list(assets.values()), "identities": list(identities.values()),
            "citations": sorted(set(enr_cites)),
        },
        "correlation_deduplication": {
            "title": "Correlation & Deduplication", "links": links,
            "note": "Duplicates are linked to a parent case; they are never merged and never dispositioned here.",
        },
        "prioritization": {
            "title": "Prioritization", "bands": band_counts, "records": prio_records,
            "note": "Deterministic, documented scoring; a triage rank for a human analyst, not a verdict.",
        },
        "suppression_log": {
            "title": "Approved Suppression Log", "entries": sup_entries,
            "note": "Only approved, documented suppression rules; suppression removes known-benign noise, never a genuine alert.",
        },
        "investigation_context": {
            "title": "Analyst-Ready Investigation Context",
            "status": "present" if ctx_packages else "empty",
            "packages": ctx_packages, "citations": sorted(set(ctx_cites)),
        },
        "recommended_routing": {
            "title": "Recommended Routing (advisory)", "routes": routes,
            "note": "Advisory handoffs; the analyst decides and initiates. No route is executed here.",
        },
        "sources_citations": {
            "title": "Sources & Citations", "citations": sorted(set(all_cites)),
            "note": "Every enriched signal is mapped to an approved source above.",
        },
        "standing_note_limitations": {"title": "Standing Note / Limitations", "text": STANDING_NOTE},
    }
    return sections


def _approvals(required: list, recorded: list) -> dict:
    by_role = {r.get("role"): r for r in (recorded or []) if isinstance(r, dict)}
    ledger = []
    for role in required:
        rec = by_role.get(role)
        if rec and rec.get("approver") and rec.get("date"):
            ledger.append({"role": role, "status": "obtained", "approver": rec.get("approver"), "date": rec.get("date")})
        else:
            ledger.append({"role": role, "status": "pending"})
    return {"title": "Approvals & Sign-off", "required": list(required), "ledger": ledger,
            "note": "Draft is queued for analyst adjudication; obtaining these approvals is the human step."}


def triage(doc: dict) -> dict:
    cfg = {**DEFAULT_PRIORITY, **(doc.get("priority_config") or {})}
    records = [triage_alert(a, doc, cfg) for a in doc["alerts"]]

    hard = any(r.get("hard_boundary_alert") for r in records)
    if hard:
        status = "blocked"
    elif any(r["disposition"] == "needs-data" for r in records):
        status = "needs-data"
    else:
        status = "ready-for-analyst"

    sections = _sections(doc, records, status)
    sections["approvals"] = _approvals(doc.get("required_approvals") or [], doc.get("recorded_approvals") or [])

    return {
        "config_version": doc.get("config_version"),
        "template_version": doc.get("template_version") or "sec-triage-package-v1",
        "batch_id": doc.get("batch_id"),
        "package_status": status,
        "hard_boundary": hard,
        "triage": records,
        "sections": sections,
        "standing_note": STANDING_NOTE,
    }


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
