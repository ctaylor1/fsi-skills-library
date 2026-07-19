#!/usr/bin/env python3
"""Deterministic DLP incident-assessment engine for data-loss-prevention-incident-assistant.

Marshals a DLP event batch-intake file into a controlled, source-mapped DRAFT incident-
assessment package that maps to assets/output-template.md. For each event it: enriches
(actor, asset, destination, channel), classifies the data involved (deterministic taxonomy),
estimates exposure (egress, destination trust, magnitude), correlates/deduplicates against
open cases (link, never merge), computes a documented severity, records evidence references
for chain-of-custody, applies ONLY the three approved suppression rules, and otherwise
assembles a review-ready assessment-context bundle. It emits the required template sections,
an approval ledger, and advisory escalation routing.

Hard boundaries (fail closed): an `active_exfiltration` indicator sets `hard_boundary` and
forces `package_status = blocked` with an urgent incident-response route, and overrides
suppression. This skill NEVER makes a breach determination, dispositions/closes a DLP
incident, decides a notification obligation, blocks/quarantines/revokes a transfer, account,
or destination, deletes/recalls data, writes a system of record (DLP console / case
management / ticketing), or sends/submits the package. Every regulated data-loss decision and
response action stays with the human privacy / incident-response owner.

Usage: python calculate_or_transform.py events.json | --selftest
Prints the assessment-package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Data-classification taxonomy (highest sensitivity first). Configuration, not judgement;
# override via doc["classification_config"] as {label: [data_type, ...]}.
DEFAULT_CLASS_RANK = [
    ("Restricted (PCI/CHD)", ["pci", "chd", "card", "pan"]),
    ("Restricted (PHI)", ["phi", "health", "medical"]),
    ("Restricted (PII/NPI)", ["pii", "npi", "ssn", "account-number", "dob"]),
    ("Confidential (IP/Proprietary)", ["source-code", "trade-secret", "confidential", "ip"]),
    ("Internal", ["internal"]),
    ("Public", ["public"]),
]
REGULATED_PREFIX = "Restricted"

# Documented severity weights (configuration, not judgement). Override via
# doc["severity_config"]. The band is a triage RANK to inform a human reviewer, never a
# verdict, breach determination, closure, or response decision.
DEFAULT_SEVERITY = {
    "classification": {"Restricted (PCI/CHD)": 4, "Restricted (PHI)": 4, "Restricted (PII/NPI)": 4,
                       "Confidential (IP/Proprietary)": 3, "Internal": 1, "Public": 0},
    "egress": 3,
    "destination_trust": {"external-untrusted": 3, "personal": 2, "sanctioned": 0, "internal": 0},
    "record_count": [(10000, 3), (1000, 2), (100, 1)],
    "privilege": {"privileged": 2, "service": 1, "standard": 0},
    "s1_min": 9, "s2_min": 5,
}
APPROVED_SUPPRESSIONS = {"SUP-DUP-01", "SUP-SANCTIONED-01", "SUP-FP-PATTERN-01"}
ROUTE_BY_VECTOR = {
    "phishing": "phishing-and-bec-investigator",
    "bec": "phishing-and-bec-investigator",
    "compromised-identity": "identity-access-reviewer",
    "privilege-abuse": "identity-access-reviewer",
    "cloud-exposure": "cloud-security-posture-reviewer",
    "cloud-sync": "cloud-security-posture-reviewer",
    "third-party": "third-party-cyber-risk-reviewer",
    "vendor": "third-party-cyber-risk-reviewer",
}
DEFAULT_ROUTE = "cyber-incident-response-coordinator"
STANDING_NOTE = (
    "Draft data-loss-prevention incident assessment for privacy/IR review and human "
    "adjudication only. This assessment enriches events, classifies the data involved, "
    "estimates exposure, records evidence references for chain-of-custody, and applies only "
    "approved suppression rules to raise review-ready context. It makes no breach "
    "determination, does not confirm or disposition exfiltration, decides no notification "
    "obligation, blocks/quarantines/revokes nothing, removes or recalls no data, disables no "
    "account, writes no system of record (DLP console / case management / ticketing), and has "
    "not been sent, submitted, or filed. Every regulated data-loss decision, breach "
    "determination, notification, and response action remains with the authorized "
    "privacy/incident-response owner and legal/compliance."
)


def classify(data_types, rank) -> str | None:
    """Return the highest-sensitivity classification label whose types intersect data_types."""
    have = {str(t).lower() for t in (data_types or [])}
    if not have:
        return None
    for label, types in rank:
        if have & set(types):
            return label
    return "Internal"  # typed but unmapped -> treat as Internal, never Public/unclassified


def _rank(doc) -> list:
    cfg = doc.get("classification_config")
    if cfg:
        return [(label, list(types)) for label, types in cfg.items()]
    return DEFAULT_CLASS_RANK


def _citations(e: dict) -> list[str]:
    as_of = e.get("as_of") or "current"
    cites = [f"dlp:{e.get('source_ref','?')}@{as_of}"]
    actor = e.get("actor") or {}
    if actor.get("identity_ref"):
        cites.append(f"iam:identity={actor['identity_ref']}@{as_of}")
    asset = e.get("asset") or {}
    if asset.get("asset_id"):
        cites.append(f"cmdb:asset={asset['asset_id']}@{as_of}")
    dest = e.get("destination") or {}
    if dest.get("dest_ref"):
        cites.append(f"proxy:dest={dest['dest_ref']}@{as_of}")
    if e.get("dlp_rule_id"):
        cites.append(f"dlp:policy={e['dlp_rule_id']}@{as_of}")
    return cites


def _enrichment(e: dict) -> dict:
    actor = e.get("actor") or {}
    asset = e.get("asset") or {}
    dest = e.get("destination") or {}
    return {
        "actor": {"identity_ref": actor.get("identity_ref") or "****",
                  "privilege": actor.get("privilege") or "standard",
                  "department": actor.get("department")},
        "asset": {"asset_id": asset.get("asset_id"), "asset_ref": asset.get("asset_ref") or "****",
                  "managed": bool(asset.get("managed"))},
        "destination": {"dest_ref": dest.get("dest_ref") or "****",
                        "trust": dest.get("trust") or "internal", "category": dest.get("category")},
        "channel": e.get("channel"), "vector": e.get("vector"),
    }


def _exposure(e: dict, classification: str | None) -> dict:
    data = e.get("data") or {}
    dest = e.get("destination") or {}
    regulated = bool(classification and classification.startswith(REGULATED_PREFIX))
    return {
        "classification": classification,
        "contains_regulated": regulated,
        "egress_completed": bool(e.get("egress")),
        "destination_trust": dest.get("trust") or "internal",
        "record_count": int(data.get("record_count") or 0),
        "volume_mb": data.get("volume_mb"),
        "data_types": list(data.get("data_types") or []),
        "regulated_data_left_perimeter": bool(regulated and e.get("egress")
                                              and (dest.get("trust") in ("external-untrusted", "personal"))),
    }


def _severity(e: dict, classification: str | None, cfg: dict) -> tuple[int, str, list[str], bool]:
    score, why = 0, []
    active = bool(e.get("active_exfiltration"))
    cp = cfg["classification"].get(classification, 0) if classification else 0
    if cp:
        score += cp; why.append(f"classification {classification} +{cp}")
    if e.get("egress"):
        score += cfg["egress"]; why.append(f"egress completed +{cfg['egress']}")
    dest = e.get("destination") or {}
    tp = cfg["destination_trust"].get(dest.get("trust"), 0)
    if tp:
        score += tp; why.append(f"destination {dest.get('trust')} +{tp}")
    rc = int((e.get("data") or {}).get("record_count") or 0)
    for thr, pts in cfg["record_count"]:
        if rc >= thr:
            score += pts; why.append(f"records>={thr} +{pts}"); break
    priv = (e.get("actor") or {}).get("privilege") or "standard"
    pp = cfg["privilege"].get(priv, 0)
    if pp:
        score += pp; why.append(f"actor {priv} +{pp}")
    band = "S1 (Critical)" if (score >= cfg["s1_min"] or active) \
        else "S2 (High)" if score >= cfg["s2_min"] else "S3 (Moderate)"
    return score, band, why, active


def _dup_parent(e: dict, open_cases: list) -> tuple[dict | None, str | None]:
    actor_id = (e.get("actor") or {}).get("identity_ref")
    for c in open_cases:
        if (c.get("actor_id") == actor_id and c.get("dlp_rule_id") == e.get("dlp_rule_id")
                and c.get("window") == e.get("window")):
            shared = set(c.get("event_ids") or []) & set(e.get("event_ids") or [])
            if shared and set(e.get("event_ids") or []) <= set(c.get("event_ids") or []):
                return c, "exact"       # subset -> exact duplicate
            if shared:
                return c, "correlated"  # overlap -> correlated duplicate (linked, not suppressed)
    return None, None


def _next_steps(e: dict, urgent: bool) -> str:
    v = e.get("vector")
    if urgent:
        return ("Recommend the privacy/IR owner treat this as a potential active exfiltration of "
                "regulated data, scope the exposure and affected data subjects, and hand to the "
                "incident-response process. This skill performs no containment and makes no breach "
                "determination; the IR and privacy/legal owners decide any response or notification.")
    if v in ("phishing", "bec"):
        return ("Recommend the reviewer corroborate the phishing/BEC vector and message evidence "
                "before assessing whether data was exposed, and route the phishing element for "
                "specialist review.")
    if v in ("compromised-identity", "privilege-abuse"):
        return ("Recommend the reviewer examine the actor's access and entitlements against baseline "
                "and route to the identity-access review for a privileged-access assessment.")
    if v in ("cloud-exposure", "cloud-sync"):
        return ("Recommend the reviewer confirm the cloud destination and posture against the approved "
                "baseline and route to cloud-security-posture review for confirmation.")
    if v in ("third-party", "vendor"):
        return ("Recommend the reviewer confirm the third-party connection and data-sharing agreement "
                "and route to third-party cyber-risk review.")
    return ("Recommend the reviewer corroborate the destination reputation and the classified data "
            "involved, quantify records exposed, and confirm whether a human breach adjudication and "
            "privacy/legal notification review are warranted. This skill performs no containment.")


def _assessment_context(e, case_id, enr, exposure, band, why, parent, citations, next_steps) -> dict:
    return {
        "case_id": case_id,
        "actor": enr["actor"],
        "asset": enr["asset"],
        "destination": enr["destination"],
        "channel": e.get("channel"),
        "vector": e.get("vector"),
        "dlp_rule_id": e.get("dlp_rule_id"),
        "window": e.get("window"),
        "event_ids": e.get("event_ids"),
        "classification": exposure["classification"],
        "exposure": exposure,
        "correlated_cases": [parent.get("case_id")] if parent else [],
        "recommended_severity": band,
        "severity_reason": "; ".join(why),
        "recommended_next_steps": next_steps,
        "citations": citations,
    }


def _evidence_entry(e, case_id, citations) -> dict:
    return {
        "event_id": e.get("event_id"),
        "case_id": case_id,
        "source_ref": e.get("source_ref"),
        "event_ids": e.get("event_ids"),
        "integrity_ref": e.get("evidence_hash") or "reference-recorded",
        "legal_hold": bool(e.get("legal_hold")),
        "custody_note": ("Evidence references recorded to preserve chain-of-custody; this skill "
                         "acquires, alters, and removes nothing."),
        "citations": citations,
    }


def assess_event(e: dict, doc: dict, cfg: dict, rank: list) -> dict:
    case_id = f"DLP-{e.get('event_id')}"
    enr = _enrichment(e)
    citations = _citations(e)
    data = e.get("data") or {}
    active = bool(e.get("active_exfiltration"))
    classification = classify(data.get("data_types"), rank)
    score, band, why, _ = _severity(e, classification, cfg)

    rec = {"event_id": e.get("event_id"), "case_id": case_id, "channel": e.get("channel"),
           "vector": e.get("vector"), "classification": classification,
           "severity_score": score, "severity_band": band, "severity_reason": "; ".join(why),
           "active_exfiltration": active, "enrichment": enr,
           "exposure": _exposure(e, classification), "citations": citations,
           "suppression": None, "assessment_context": None, "evidence": None, "needs": []}

    # needs-data: never classify, clear, or package an event by guessing missing signal.
    if classification is None or not e.get("event_ids"):
        if classification is None:
            rec["needs"].append("data types (unclassified)")
        if not e.get("event_ids"):
            rec["needs"].append("triggering event ids")
        rec["disposition"] = "needs-data"
        return rec

    parent, kind = _dup_parent(e, doc.get("open_cases") or [])

    # HARD BOUNDARY: active exfiltration -> escalate + block the batch; IR/privacy, not this skill.
    if active:
        rec["disposition"] = "prepared-for-review"
        rec["hard_boundary_event"] = True
        rec["urgent"] = True
        rec["route_specialist"] = DEFAULT_ROUTE
        rec["assessment_context"] = _assessment_context(
            e, case_id, enr, rec["exposure"], band, why, parent, citations, _next_steps(e, True))
        rec["evidence"] = _evidence_entry(e, case_id, citations)
        return rec

    # Approved suppression (the ONLY suppressions permitted), in precedence order.
    if kind == "exact":
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-DUP-01",
                              "evidence": {"parent_case_id": parent.get("case_id"),
                                           "matched_events": sorted(set(e["event_ids"]) & set(parent.get("event_ids", [])))},
                              "rule_set_version": doc.get("config_version")}
        return rec
    dest = e.get("destination") or {}
    dest_id = dest.get("destination_id")
    if (dest_id and dest_id in set(doc.get("approved_destinations") or [])
            and not rec["exposure"]["contains_regulated"] and dest.get("trust") in ("sanctioned", "internal")):
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-SANCTIONED-01",
                              "evidence": {"destination_id": dest_id, "classification": classification},
                              "rule_set_version": doc.get("config_version")}
        return rec
    fp = e.get("fp_pattern_id")
    if fp and fp in set(doc.get("approved_fp_patterns") or []):
        rec["disposition"] = "approved-suppressed"
        rec["suppression"] = {"rule_id": "SUP-FP-PATTERN-01",
                              "evidence": {"pattern_id": fp, "qualifying_events": e["event_ids"]},
                              "rule_set_version": doc.get("config_version")}
        return rec
    if kind == "correlated":
        rec["disposition"] = "correlated-duplicate"
        rec["linked_case_id"] = parent.get("case_id")
        rec["evidence"] = _evidence_entry(e, case_id, citations)
        return rec

    # Otherwise: package review-ready assessment context.
    rec["disposition"] = "prepared-for-review"
    rec["route_specialist"] = ROUTE_BY_VECTOR.get(e.get("vector"), DEFAULT_ROUTE)
    rec["assessment_context"] = _assessment_context(
        e, case_id, enr, rec["exposure"], band, why, parent, citations, _next_steps(e, False))
    rec["evidence"] = _evidence_entry(e, case_id, citations)
    return rec


def _sections(doc: dict, records: list, status: str) -> dict:
    enr_cites, cls_cites, exp_cites, ctx_cites, ev_cites, all_cites = [], [], [], [], [], []
    enr_items, cls_items, exp_items, actors, assets = [], [], [], {}, {}
    links, sup_entries, sev_records, ctx_packages, ev_entries, routes = [], [], [], [], [], []

    for r in records:
        all_cites.extend(r.get("citations") or [])
        enr = r.get("enrichment") or {}
        e_id = r["event_id"]
        actor = enr.get("actor") or {}
        asset = enr.get("asset") or {}
        dest = enr.get("destination") or {}
        enr_cites.extend(r.get("citations") or [])
        enr_items.append(f"{e_id} [{r.get('channel')}/{r.get('vector')}]: actor {actor.get('identity_ref')} "
                         f"({actor.get('privilege')}) via asset {asset.get('asset_ref')} -> destination "
                         f"{dest.get('dest_ref')} ({dest.get('trust')})")
        cls_cites.extend(r.get("citations") or [])
        cls_items.append({"event_id": e_id, "classification": r.get("classification"),
                          "data_types": (r.get("exposure") or {}).get("data_types")})
        exp = r.get("exposure") or {}
        exp_cites.extend(r.get("citations") or [])
        exp_items.append({"event_id": e_id, "classification": exp.get("classification"),
                          "contains_regulated": exp.get("contains_regulated"),
                          "egress_completed": exp.get("egress_completed"),
                          "destination_trust": exp.get("destination_trust"),
                          "record_count": exp.get("record_count"),
                          "regulated_data_left_perimeter": exp.get("regulated_data_left_perimeter")})
        if actor.get("identity_ref") and actor.get("identity_ref") != "****":
            a = actors.setdefault(actor["identity_ref"], {"identity_ref": actor["identity_ref"],
                                                          "privilege": actor.get("privilege"), "event_ids": []})
            a["event_ids"].append(e_id)
        if asset.get("asset_id"):
            s = assets.setdefault(asset["asset_id"], {"asset_id": asset["asset_id"],
                                                      "asset_ref": asset.get("asset_ref"), "event_ids": []})
            s["event_ids"].append(e_id)
        sev_records.append({"event_id": e_id, "severity_band": r["severity_band"],
                            "severity_score": r["severity_score"], "severity_reason": r["severity_reason"]})
        disp = r["disposition"]
        if disp == "approved-suppressed":
            sup = r["suppression"]
            sup_entries.append({"event_id": e_id, "rule_id": sup["rule_id"], "evidence": sup["evidence"],
                                "rule_set_version": sup.get("rule_set_version")})
        elif disp == "correlated-duplicate":
            links.append({"event_id": e_id, "relationship": "correlated-duplicate", "parent_case_id": r.get("linked_case_id")})
        elif disp == "prepared-for-review":
            ctx = r["assessment_context"]
            ctx_packages.append(ctx)
            ctx_cites.extend(ctx.get("citations") or [])
            routes.append({"event_id": e_id, "skill": r.get("route_specialist"),
                           "reason": f"{r.get('vector') or r.get('channel')} at {r['severity_band']}",
                           "urgent": bool(r.get("urgent"))})
        if r.get("evidence"):
            ev = r["evidence"]
            ev_entries.append(ev)
            ev_cites.extend(ev.get("citations") or [])

    # exact-duplicate suppressions also record their parent link for lineage
    for r in records:
        if r["disposition"] == "approved-suppressed" and (r.get("suppression") or {}).get("rule_id") == "SUP-DUP-01":
            links.append({"event_id": r["event_id"], "relationship": "exact-duplicate",
                          "parent_case_id": r["suppression"]["evidence"].get("parent_case_id")})

    band_counts = {"S1 (Critical)": 0, "S2 (High)": 0, "S3 (Moderate)": 0}
    for r in records:
        band_counts[r["severity_band"]] = band_counts.get(r["severity_band"], 0) + 1

    sections = {
        "incident_batch_overview": {
            "title": "Incident Batch Overview", "batch_id": doc.get("batch_id"),
            "source_queue": doc.get("source_queue"), "package_status": status,
            "total_events": len(records),
            "counts": {
                "prepared_for_review": sum(1 for r in records if r["disposition"] == "prepared-for-review"),
                "approved_suppressed": sum(1 for r in records if r["disposition"] == "approved-suppressed"),
                "needs_data": sum(1 for r in records if r["disposition"] == "needs-data"),
                "correlated_duplicate": sum(1 for r in records if r["disposition"] == "correlated-duplicate"),
            },
            "config_version": doc.get("config_version"),
            "template_version": doc.get("template_version") or "dlp-incident-package-v1",
        },
        "event_enrichment": {
            "title": "Event Enrichment", "status": "present" if enr_cites else "empty",
            "items": enr_items, "citations": sorted(set(enr_cites)),
        },
        "data_classification": {
            "title": "Data Classification", "status": "present" if cls_cites else "empty",
            "items": cls_items, "citations": sorted(set(cls_cites)),
            "note": "Deterministic taxonomy; the highest-sensitivity detected type sets the label. "
                    "A recommendation for human confirmation, not a legal determination.",
        },
        "exposure_assessment": {
            "title": "Exposure Assessment", "status": "present" if exp_cites else "empty",
            "items": exp_items, "citations": sorted(set(exp_cites)),
            "note": "Estimated exposure from egress, destination trust, and magnitude; whether "
                    "regulated data left the perimeter is a signal for human breach adjudication.",
        },
        "correlation_deduplication": {
            "title": "Correlation & Deduplication", "links": links,
            "note": "Duplicates are linked to a parent case; they are never merged and never dispositioned here.",
        },
        "severity_prioritization": {
            "title": "Severity Prioritization", "bands": band_counts, "records": sev_records,
            "note": "Deterministic, documented scoring; a triage rank for a human reviewer, not a verdict.",
        },
        "suppression_log": {
            "title": "Approved Suppression Log", "entries": sup_entries,
            "note": "Only approved, documented suppression rules; suppression removes known-benign "
                    "or approved-business noise, never a genuine incident.",
        },
        "evidence_preservation": {
            "title": "Evidence Preservation & Chain-of-Custody",
            "status": "present" if ev_entries else "empty",
            "entries": ev_entries, "citations": sorted(set(ev_cites)),
            "note": "Evidence references and legal-hold flags recorded for the human owner; this "
                    "skill acquires, alters, and removes nothing.",
        },
        "escalation_routing": {
            "title": "Escalation Routing (advisory)", "routes": routes,
            "note": "Advisory handoffs to the appropriate specialist skill or the privacy/incident-"
                    "response owner; the human decides and initiates. No route is executed here.",
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
            "note": "Draft is queued for privacy/IR adjudication; obtaining these approvals is the human step."}


def assess(doc: dict) -> dict:
    cfg = {**DEFAULT_SEVERITY, **(doc.get("severity_config") or {})}
    rank = _rank(doc)
    records = [assess_event(e, doc, cfg, rank) for e in doc["events"]]

    hard = any(r.get("hard_boundary_event") for r in records)
    if hard:
        status = "blocked"
    elif any(r["disposition"] == "needs-data" for r in records):
        status = "needs-data"
    else:
        status = "ready-for-review"

    sections = _sections(doc, records, status)
    sections["approvals"] = _approvals(doc.get("required_approvals") or [], doc.get("recorded_approvals") or [])

    return {
        "config_version": doc.get("config_version"),
        "template_version": doc.get("template_version") or "dlp-incident-package-v1",
        "batch_id": doc.get("batch_id"),
        "package_status": status,
        "hard_boundary": hard,
        "assessments": records,
        "sections": sections,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "events_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assess(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
