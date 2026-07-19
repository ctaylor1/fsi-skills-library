#!/usr/bin/env python3
"""Deterministic underwriting workbench compiler for underwriting-workbench-assistant.

For each submission it: assesses data completeness across the required risk sections, checks
source freshness against per-section SLAs (measured against the review as_of_date, never the
system clock), applies the APPROVED, versioned underwriting rule set (appetite, binding
authority, capacity, loss experience, catastrophe accumulation, third-party risk, financial
strength), and assembles a DRAFT underwriter-ready risk profile with a recommended
disposition and a decision-rationale draft.

It NEVER binds, quotes, declines, or issues coverage, NEVER writes a system of record, and
always leaves the accept / quote / decline decision to a licensed human underwriter. The
recommended disposition is advisory decision support, not an underwriting decision.

Usage: python calculate_or_transform.py submissions.json | --selftest
Prints the compiled workbench JSON to stdout (exit 0).
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_SECTIONS = ["entity", "property", "exposure", "loss_history",
                     "catastrophe", "financial", "third_party"]
TEMPLATE_SECTIONS = ["Risk Summary", "Data Completeness", "Source Freshness",
                     "Rule Findings & Exceptions", "Draft Decision Rationale",
                     "Human Adjudication", "Standing Note"]
DEFAULT_RULES = {
    "loss_ratio_threshold": 0.70,
    "cat_accum_threshold": 0.80,
    "fin_min_credit": 50,
    "freshness_default_days": 180,
    "freshness_sla_days": {
        "entity": 365, "property": 180, "exposure": 180, "loss_history": 400,
        "catastrophe": 120, "financial": 365, "third_party": 90,
    },
    "critical_sections": ["property", "catastrophe", "exposure"],
}
STANDING_NOTE = ("Draft underwriting risk profile and decision support only; no coverage has "
                 "been bound, quoted, declined, or issued, and no system of record has been "
                 "updated. The underwriting decision remains with a licensed human underwriter.")


def _cfg(doc):
    rc = doc.get("rules_config") or {}
    cfg = {**DEFAULT_RULES, **rc}
    cfg["freshness_sla_days"] = {**DEFAULT_RULES["freshness_sla_days"],
                                 **(rc.get("freshness_sla_days") or {})}
    cfg["critical_sections"] = rc.get("critical_sections", DEFAULT_RULES["critical_sections"])
    return cfg


def _age_days(as_of, ref):
    try:
        return (date.fromisoformat(ref) - date.fromisoformat(as_of)).days
    except Exception:
        return None


def _present(sec):
    return isinstance(sec, dict) and sec.get("present") is not False \
        and sec.get("source_ref") and sec.get("as_of")


def compile_profile(sub, doc, cfg):
    sid = sub.get("submission_id")
    sections = sub.get("risk_sections") or {}
    ref_date = doc.get("as_of_date")
    auth = doc.get("authority") or {}
    citations, findings = [], []

    # 1. Completeness -----------------------------------------------------------------
    present, missing, sec_status = [], [], {}
    for name in REQUIRED_SECTIONS:
        sec = sections.get(name)
        if _present(sec):
            present.append(name)
            citations.append(sec["source_ref"])
        else:
            missing.append(name)
            sec_status[name] = {"status": "missing"}

    # 2. Source freshness -------------------------------------------------------------
    freshness, stale_critical = [], []
    for name in present:
        sec = sections[name]
        sla = cfg["freshness_sla_days"].get(name, cfg["freshness_default_days"])
        age = _age_days(sec["as_of"], ref_date)
        status = "unknown" if age is None else ("stale" if age > sla else "fresh")
        freshness.append({"section": name, "as_of": sec["as_of"], "age_days": age,
                          "sla_days": sla, "status": status})
        sec_status[name] = {"status": "present", "as_of": sec["as_of"],
                            "freshness": status, "citation": sec["source_ref"]}
        if status == "stale":
            if name in cfg["critical_sections"]:
                stale_critical.append(name)
            else:
                findings.append({"rule_id": "UW-FRESHNESS", "severity": "exception",
                                 "message": f"{name} source stale ({age}d > {sla}d SLA)",
                                 "evidence": [sec["source_ref"]], "route": None})

    def has(name):
        return name in present

    # 3. Approved underwriting rules (applied only to present data) -------------------
    tiv = sub.get("tiv")
    if tiv is not None and auth.get("binding_authority_tiv") is not None \
            and tiv > auth["binding_authority_tiv"]:
        findings.append({"rule_id": "UW-AUTH-TIV", "severity": "referral",
                         "message": f"TIV {tiv} above binding authority {auth['binding_authority_tiv']}",
                         "evidence": [f"submission:{sid};tiv"], "route": None})
    req = sub.get("requested_limit")
    if req is not None and auth.get("binding_authority_limit") is not None \
            and req > auth["binding_authority_limit"]:
        findings.append({"rule_id": "UW-CAPACITY", "severity": "referral",
                         "message": f"Requested limit {req} above authority limit {auth['binding_authority_limit']}",
                         "evidence": [f"submission:{sid};requested_limit"],
                         "route": "reinsurance-treaty-interpreter"})
    occ = sub.get("occupancy_class")
    if occ is not None and auth.get("appetite_classes") is not None \
            and occ not in auth["appetite_classes"]:
        findings.append({"rule_id": "UW-APPETITE-CLASS", "severity": "referral",
                         "message": f"Occupancy class '{occ}' outside documented appetite",
                         "evidence": [f"submission:{sid};occupancy_class"], "route": None})
    if has("loss_history"):
        lr = sections["loss_history"].get("loss_ratio_3yr")
        if lr is not None and lr > cfg["loss_ratio_threshold"]:
            findings.append({"rule_id": "UW-LOSS-RATIO", "severity": "referral",
                             "message": f"3yr loss ratio {lr} above {cfg['loss_ratio_threshold']} threshold",
                             "evidence": [sections["loss_history"]["source_ref"]], "route": None})
    if has("catastrophe"):
        acc = sections["catastrophe"].get("accumulation_pct")
        if acc is not None and acc >= cfg["cat_accum_threshold"]:
            findings.append({"rule_id": "UW-CAT-ACCUM", "severity": "referral",
                             "message": f"Catastrophe accumulation {acc} at/above {cfg['cat_accum_threshold']} threshold",
                             "evidence": [sections["catastrophe"]["source_ref"]],
                             "route": "catastrophe-exposure-monitor"})
    if has("third_party") and sections["third_party"].get("adverse_flag"):
        ft = sections["third_party"].get("flag_type") or "unspecified"
        findings.append({"rule_id": "UW-THIRD-PARTY", "severity": "referral",
                         "message": f"Adverse third-party risk flag ({ft}) — route to referral authority",
                         "evidence": [sections["third_party"]["source_ref"]], "route": None})
    if has("financial"):
        cs = sections["financial"].get("credit_score")
        if cs is not None and cs < cfg["fin_min_credit"]:
            findings.append({"rule_id": "UW-FIN-STRENGTH", "severity": "exception",
                             "message": f"Financial strength score {cs} below {cfg['fin_min_credit']} minimum",
                             "evidence": [sections["financial"]["source_ref"]], "route": None})

    # 4. Disposition (advisory only) --------------------------------------------------
    if missing or stale_critical:
        disposition = "needs-data"
    elif findings:
        disposition = "refer-to-underwriter"
    else:
        disposition = "ready-for-underwriter-review"

    applied = sorted({f["rule_id"] for f in findings})
    routes = sorted({f["route"] for f in findings if f.get("route")})

    if disposition == "needs-data":
        need = missing + [f"{s} (stale)" for s in stale_critical]
        recommendation = ("Recommendation for underwriter adjudication: profile incomplete — "
                          f"obtain {', '.join(need)} before underwriting. No underwriting "
                          "decision has been drafted.")
    elif disposition == "refer-to-underwriter":
        recommendation = ("Recommendation for underwriter adjudication: refer to a senior "
                          f"underwriter / referral authority — {len(findings)} rule finding(s) "
                          f"require human judgment ({', '.join(applied)}). Draft rationale and "
                          "evidence attached; the accept / quote / decline decision remains "
                          "with the underwriter.")
    else:
        recommendation = ("Recommendation for underwriter adjudication: profile complete and "
                          "within documented appetite on the applied rules; forward to the "
                          "underwriter for the accept / quote / decline decision. This is "
                          "decision support only — no decision has been made.")

    approver = "senior underwriter / referral authority" \
        if disposition == "refer-to-underwriter" else "underwriter"

    return {
        "submission_id": sid,
        "workbench_id": f"UWB-{sid}",
        "insured": {"name_masked": sub.get("insured_name_masked"),
                    "occupancy_class": occ, "line_of_business": sub.get("line_of_business")},
        "completeness": {"required": REQUIRED_SECTIONS, "present": present, "missing": missing,
                         "complete": not missing, "section_status": sec_status},
        "source_freshness": freshness,
        "rule_findings": findings,
        "recommended_disposition": disposition,
        "decision_rationale": {"recommendation": recommendation, "applied_rules": applied,
                               "routes": routes, "citations": sorted(set(citations)),
                               "unsupported_claims": []},
        "human_adjudication": {"status": "pending", "required_approver": approver,
                               "underwriter_id": auth.get("underwriter_id"),
                               "decision": None, "decided_at": None},
    }


def compile_workbench(doc):
    cfg = _cfg(doc)
    profiles = [compile_profile(s, doc, cfg) for s in doc.get("submissions") or []]
    summary = {
        "total": len(profiles),
        "ready_for_underwriter_review": sum(1 for p in profiles if p["recommended_disposition"] == "ready-for-underwriter-review"),
        "refer_to_underwriter": sum(1 for p in profiles if p["recommended_disposition"] == "refer-to-underwriter"),
        "needs_data": sum(1 for p in profiles if p["recommended_disposition"] == "needs-data"),
    }
    return {"config_version": doc.get("config_version"), "as_of_date": doc.get("as_of_date"),
            "authority_ref": (doc.get("authority") or {}).get("underwriter_id"),
            "profiles": profiles, "summary": summary,
            "template_sections_present": TEMPLATE_SECTIONS, "standing_note": STANDING_NOTE}


# Expected outcomes for the bundled fixture — the self-test ties the engine to a golden.
_EXPECTED = {
    "SUB-88101": {"disposition": "ready-for-underwriter-review", "rules": []},
    "SUB-88102": {"disposition": "refer-to-underwriter",
                  "rules": ["UW-CAT-ACCUM", "UW-LOSS-RATIO", "UW-THIRD-PARTY"]},
    "SUB-88103": {"disposition": "refer-to-underwriter",
                  "rules": ["UW-AUTH-TIV", "UW-CAPACITY"]},
    "SUB-88104": {"disposition": "needs-data", "rules": []},
}


def _selftest_check(result):
    errors = []
    by_id = {p["submission_id"]: p for p in result.get("profiles", [])}
    for sid, exp in _EXPECTED.items():
        p = by_id.get(sid)
        if not p:
            errors.append(f"{sid}: missing from compiled output")
            continue
        if p["recommended_disposition"] != exp["disposition"]:
            errors.append(f"{sid}: disposition {p['recommended_disposition']!r} != expected {exp['disposition']!r}")
        if p["decision_rationale"]["applied_rules"] != exp["rules"]:
            errors.append(f"{sid}: applied_rules {p['decision_rationale']['applied_rules']} != expected {exp['rules']}")
        if p["human_adjudication"]["status"] != "pending" or p["human_adjudication"]["decision"] is not None:
            errors.append(f"{sid}: human_adjudication must stay pending with no autonomous decision")
    return errors


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "submissions_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    result = compile_workbench(doc)
    print(json.dumps(result, indent=2))
    if selftest:
        errors = _selftest_check(result)
        for e in errors:
            print("ERROR", e)
        print(f"compile self-test: {len(errors)} error(s)")
        return 1 if errors else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
