#!/usr/bin/env python3
"""Deterministic, explainable conflict-of-interest analysis for conflicts-of-interest-reviewer.

Reads a matter file (see validate_input.py), classifies each disclosed item against the
conflict taxonomy, computes inherent severity from type + magnitude thresholds, checks the
recorded disclosures / controls / approvals against the per-type requirement set, computes a
deterministic residual-risk band, attaches evidence + citations to each fired finding, and
recommends an adjudication path for a human.

IMPORTANT: This produces explainable *findings, evidence, and recommendations* only. It never
clears/approves/waives a conflict, closes the matter, files anything, or makes a binding
compliance determination. The severity, required-control, residual-risk, and review-path
mappings are deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py matter.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

RANK = {"Low": 1, "Medium": 2, "High": 3}
BAND = {1: "Low", 2: "Medium", 3: "High"}

DISCLAIMER = ("Conflicts review and recommendations only; not a compliance determination, "
              "clearance, waiver, or approval. A qualified human adjudicator must decide. "
              "No matter has been closed and no filing has been made.")

DEFAULT_CONFIG = {
    "gift_deminimis": 100.0,
    "ownership_material_pct": 1.0,
    "annual_value_material": 25000.0,
    "disclosure_staleness_days": 365,
    "requirements": {
        "personal_financial_interest": {"disclosure": ["compliance"], "control": ["recusal"], "approval": ["compliance"]},
        "outside_business_activity": {"disclosure": ["compliance"], "control": ["recusal"], "approval": ["supervisor", "compliance"]},
        "gift_entertainment": {"disclosure": ["compliance"], "control": [], "approval": ["supervisor"]},
        "personal_relationship": {"disclosure": ["supervisor"], "control": ["reassignment"], "approval": ["supervisor"]},
        "personal_trading": {"disclosure": ["compliance"], "control": ["preclearance", "restricted_list"], "approval": ["compliance"]},
        "dual_role": {"disclosure": ["clients", "compliance"], "control": ["information_barrier", "separate_teams"], "approval": ["compliance"]},
        "related_party_transaction": {"disclosure": ["compliance", "board"], "control": ["independent_review"], "approval": ["board"]},
        "incentive_misalignment": {"disclosure": ["clients"], "control": ["supervisory_review"], "approval": ["compliance"]},
        "information_barrier": {"disclosure": ["compliance"], "control": ["wall_cross_log", "restricted_list"], "approval": ["compliance"]},
    },
}

BASE_SEVERITY = {
    "personal_financial_interest": "Medium",
    "outside_business_activity": "Medium",
    "gift_entertainment": "Low",
    "personal_relationship": "Medium",
    "personal_trading": "Medium",
    "dual_role": "High",
    "related_party_transaction": "High",
    "incentive_misalignment": "Medium",
    "information_barrier": "High",
}
MAGNITUDE_TYPES = {"personal_financial_interest", "outside_business_activity", "incentive_misalignment"}


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _cite(row: dict, default_ref: str) -> str:
    ref = row.get("source_ref") or default_ref
    date = row.get("date") or row.get("as_of") or ""
    return f"coi:{ref}@{date}" if date else f"coi:{ref}"


def _inherent(item: dict, cfg: dict) -> str:
    ctype = item["conflict_type"]
    base = BASE_SEVERITY.get(ctype, "Medium")
    mag = item.get("magnitude") or {}
    if ctype == "gift_entertainment":
        gv = _num(mag.get("gift_value")) or 0.0
        if gv >= 5 * cfg["gift_deminimis"]:
            return "High"
        if gv >= cfg["gift_deminimis"]:
            return "Medium"
        return base
    if ctype in MAGNITUDE_TYPES:
        own = _num(mag.get("ownership_pct")) or 0.0
        val = _num(mag.get("annual_value")) or 0.0
        if own >= cfg["ownership_material_pct"] or val >= cfg["annual_value_material"]:
            return "High"
        return base
    if ctype == "personal_trading":
        return "High" if item.get("mnpi_access") else "Medium"
    return base


def _fires(item: dict, cfg: dict) -> bool:
    # Only a sub-de-minimis gift is informational (not fired); everything else fires.
    if item["conflict_type"] == "gift_entertainment":
        gv = _num((item.get("magnitude") or {}).get("gift_value")) or 0.0
        return gv >= cfg["gift_deminimis"]
    return True


def _control_status(item: dict, cfg: dict, as_of: datetime):
    ctype = item["conflict_type"]
    req = cfg["requirements"].get(ctype, {"disclosure": [], "control": [], "approval": []})
    staleness = cfg["disclosure_staleness_days"]

    # disclosure
    disc = item.get("disclosures") or []
    fresh_to, stale_to = set(), set()
    for d in disc:
        to = str(d.get("to", "")).lower()
        dd = d.get("date")
        if dd:
            age = (as_of - _parse_date(dd)).days
            (stale_to if age > staleness else fresh_to).add(to)
        else:
            stale_to.add(to)
    need_d = [r.lower() for r in req["disclosure"]]
    if need_d and all(r in fresh_to for r in need_d):
        disclosure_status = "complete"
    elif need_d and all(r in (fresh_to | stale_to) for r in need_d):
        disclosure_status = "stale"
    elif not need_d:
        disclosure_status = "complete"
    else:
        disclosure_status = "missing"

    # control
    active = {str(c.get("type", "")).lower() for c in (item.get("controls") or []) if str(c.get("status", "")).lower() == "active"}
    need_c = [r.lower() for r in req["control"]]
    if not need_c or all(r in active for r in need_c):
        control_status = "complete"
    elif any(r in active for r in need_c):
        control_status = "partial"
    else:
        control_status = "missing"

    # approval
    approvers = {str(a.get("by", "")).lower() for a in (item.get("approvals") or [])}
    need_a = [r.lower() for r in req["approval"]]
    approval_status = "complete" if (not need_a or all(r in approvers for r in need_a)) else "missing"

    return disclosure_status, control_status, approval_status, req


def _evidence(item: dict) -> list:
    default_ref = item.get("source_ref", f"item={item.get('item_id','?')}")
    ev = [{"kind": "item", "ref": item.get("item_id"), "citation": _cite(item, default_ref)}]
    for d in item.get("disclosures") or []:
        ev.append({"kind": "disclosure", "to": d.get("to"), "date": d.get("date"), "citation": _cite(d, default_ref)})
    for c in item.get("controls") or []:
        ev.append({"kind": "control", "type": c.get("type"), "status": c.get("status"), "citation": _cite(c, default_ref)})
    for a in item.get("approvals") or []:
        ev.append({"kind": "approval", "by": a.get("by"), "date": a.get("date"), "citation": _cite(a, default_ref)})
    return ev


def review_path(matter_residual: str, has_gap: bool) -> str:
    if matter_residual == "High" or has_gap:
        return "Escalate to the conflicts/ethics committee (or designated compliance officer) for adjudication"
    if matter_residual == "Medium":
        return "Route to a compliance officer for review and disposition"
    return "Supervisor attestation and retention in the conflicts register"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    cfg["requirements"] = {**DEFAULT_CONFIG["requirements"], **(cfg.get("requirements") or {})}
    as_of = _parse_date(doc["as_of"])

    findings, open_gaps = [], []
    for item in doc["items"]:
        ctype = item["conflict_type"]
        fired = _fires(item, cfg)
        inherent = _inherent(item, cfg)
        disclosure_status, control_status, approval_status, req = _control_status(item, cfg, as_of)
        gap = fired and not (disclosure_status == "complete" and control_status == "complete" and approval_status == "complete")

        if not fired:
            residual = "Low"
        elif gap:
            residual = inherent  # no mitigation credit
        else:
            residual = BAND[max(1, RANK[inherent] - 1)]  # one band of credit

        finding = {
            "item_id": item.get("item_id"),
            "conflict_type": ctype,
            "fired": fired,
            "inherent_severity": inherent,
            "affected_parties": item.get("affected_parties") or [],
            "incentive": item.get("incentive"),
            "disclosure_status": disclosure_status,
            "control_status": control_status,
            "approval_status": approval_status,
            "open_gap": gap,
            "residual_risk": residual,
            "reason": _reason(item, ctype, fired, inherent, disclosure_status, control_status, approval_status, req),
            "evidence": _evidence(item) if fired else [],
        }
        findings.append(finding)

        if gap:
            for label, status, need in (("disclosure", disclosure_status, req["disclosure"]),
                                        ("control", control_status, req["control"]),
                                        ("approval", approval_status, req["approval"])):
                if status != "complete":
                    open_gaps.append({"item_id": item.get("item_id"), "conflict_type": ctype,
                                      "element": label, "status": status, "required": need})

    fired_findings = [f for f in findings if f["fired"]]
    if fired_findings:
        matter_rank = max(RANK[f["residual_risk"]] for f in fired_findings)
    else:
        matter_rank = 1
    matter_residual = BAND[matter_rank]
    has_gap = any(f["open_gap"] for f in findings)
    path = review_path(matter_residual, has_gap)

    mitigation_prompts = []
    if fired_findings or open_gaps:
        mitigation_prompts = [
            "recusal from the affected matter",
            "reassignment of coverage or supervision",
            "an information barrier / wall-cross log",
            "restricted-list addition and personal-trade preclearance",
            "a refreshed or missing disclosure",
            "independent or second-level review",
            "divestment or holding limits",
            "enhanced supervisory review",
        ]

    subject = doc.get("subject") or {}
    sid = str(subject.get("party_id", "unknown")).replace("*", "")
    return {
        "review_id": f"coi-{doc['matter_id']}-{sid}-0001",
        "matter_id": doc["matter_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "subject": {"party_id": subject.get("party_id"), "role": subject.get("role"),
                    "business_unit": subject.get("business_unit")},
        "findings": findings,
        "fired_conflict_types": [f["conflict_type"] for f in fired_findings],
        "open_gaps": open_gaps,
        "matter_residual_risk": matter_residual,
        "recommended_review_path": path,
        "mitigation_prompts": mitigation_prompts,
        "disclaimer": DISCLAIMER,
    }


def _reason(item, ctype, fired, inherent, disc, ctrl, appr, req):
    if not fired:
        return f"{ctype}: below de-minimis threshold — informational only, not a manageable conflict."
    parts = [f"{ctype} identified (inherent severity {inherent})."]
    if disc != "complete":
        parts.append(f"required disclosure to {req['disclosure']} is {disc}.")
    if ctrl != "complete":
        parts.append(f"required control(s) {req['control']} {ctrl}.")
    if appr != "complete":
        parts.append(f"required approval by {req['approval']} is {appr}.")
    if disc == "complete" and ctrl == "complete" and appr == "complete":
        parts.append("required disclosure, control, and approval are recorded and current (one band of mitigation credit).")
    return " ".join(parts)


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "matter_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
