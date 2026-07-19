#!/usr/bin/env python3
"""Deterministic, explainable third-party cyber-risk findings for third-party-cyber-risk-reviewer.

Reads a supplier assessment intake (see validate_input.py), evaluates the configured
findings against the supplier's security evidence, attaches evidence + citations to each
fired finding, and maps the fired-finding profile (severity + engagement context) to a
suggested residual-risk tier. Emits a machine-readable core the SKILL wraps in a
plain-language review.

IMPORTANT (R3): this produces explainable *findings and a suggested tier for human
adjudication* only. It never approves, rejects, onboards, clears, risk-accepts, files,
signs off, or closes a supplier assessment. The tier mapping is deterministic and
documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py assessment.json | --selftest
Prints the review JSON to stdout. With --selftest it also prints a self-check line
ending in "N error(s)" and exits non-zero if the self-check fails.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "mandatory_domains": ["identity", "data-protection", "logging", "vulnerability-mgmt"],
    "control_gap_max_partial_missing": 1,
    "high_vuln_max": 3,
    "vuln_oldest_open_max_days": 30,
    "incident_disclosure_max_days": 3,
    "fourth_party_approved_regions": ["US", "EU", "UK", "CA"],
    "breach_notification_max_hours": 72,
}
DISCLAIMER = ("Findings and evidence only; not a supplier approval, risk acceptance, or "
              "onboarding decision. A human risk owner must adjudicate. No system of record "
              "has been updated.")

ORDER = ["Low", "Moderate", "High", "Critical"]
SEV_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
BASE_BY_TOP = {0: "Low", 1: "Low", 2: "Moderate", 3: "High"}


def _parse(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _cite(ref, as_of) -> str:
    ref = str(ref).strip() if ref else ""
    return f"{ref}@{as_of}" if ref else f"intake@{as_of}"


def amplified(eng: dict) -> bool:
    return (eng.get("criticality") == "critical"
            or bool(eng.get("hosts_regulated_data"))
            or eng.get("data_classification") in ("Highly Confidential", "Restricted"))


def residual_tier(fired_findings: list, is_amplified: bool) -> str:
    """Deterministic mapping documented in references/domain-rules.md.

    Base band is set by the highest fired-finding severity; +1 band if >=4 findings fired,
    +1 band if the engagement is amplified (critical / regulated / highly-confidential).
    Bounded at Critical. Mirrored verbatim in validate_output.py.
    """
    if not fired_findings:
        return "Low"
    top = max(SEV_RANK.get(f.get("severity", "low"), 0) for f in fired_findings)
    idx = ORDER.index(BASE_BY_TOP[top])
    if len(fired_findings) >= 4:
        idx = min(idx + 1, 3)
    if is_amplified:
        idx = min(idx + 1, 3)
    return ORDER[idx]


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of_s = str(doc["as_of"])[:10]
    as_of = _parse(as_of_s)
    eng = doc.get("engagement") or {}
    findings, not_evaluable = [], []

    def add(fid, fired, severity, reason, evidence, detail):
        findings.append({"finding_id": fid, "fired": bool(fired), "severity": severity,
                         "reason": reason, "evidence": evidence, "detail": detail})

    # 1. control_gap — missing/partial controls in mandatory domains
    controls = doc.get("controls") or []
    mandatory = set(cfg["mandatory_domains"])
    for c in controls:
        if c.get("status") == "unknown":
            not_evaluable.append({"item": f"control:{c.get('control_id', '?')}",
                                  "why": "control status unknown / no evidence supplied"})
    gap_rows = [c for c in controls
                if c.get("domain") in mandatory and c.get("status") in ("missing", "partial")]
    any_missing = any(c.get("status") == "missing" for c in gap_rows)
    fired = len(gap_rows) > cfg["control_gap_max_partial_missing"] or any_missing
    add("control_gap", fired, "high" if any_missing else "medium",
        (f"{len(gap_rows)} mandatory-domain control(s) missing/partial"
         f"{' (includes a missing control)' if any_missing else ''}") if fired
        else "mandatory-domain controls implemented",
        [{"control_id": c.get("control_id"), "domain": c.get("domain"), "status": c.get("status"),
          "citation": _cite(c.get("evidence_ref"), c.get("evidence_date") or as_of_s)} for c in gap_rows],
        {"mandatory_domains": sorted(mandatory), "gap_count": len(gap_rows)})

    # 2. stale_or_missing_attestation — no in-scope, in-date SOC2/ISO/etc.
    certs = doc.get("certifications") or []
    valid = [c for c in certs if c.get("scope_covers_service")
             and _parse(c.get("valid_until", "1900-01-01")) >= as_of]
    fired = not valid
    if fired:
        ev = [{"type": c.get("type"), "valid_until": c.get("valid_until"),
               "scope_covers_service": c.get("scope_covers_service"),
               "citation": _cite(c.get("evidence_ref"), c.get("valid_until") or as_of_s)} for c in certs]
        if not ev:
            ev = [{"type": None, "citation": _cite("certifications", as_of_s)}]
    else:
        ev = []
    add("stale_or_missing_attestation", fired, "high",
        "no in-scope, in-date independent attestation (SOC 2 / ISO 27001) on file" if fired
        else "current in-scope attestation on file", ev,
        {"attestations": len(certs), "in_date_in_scope": len(valid)})

    # 3. open_critical_vulnerabilities
    v = doc.get("vulnerabilities") or {}
    crit = int(v.get("critical_open", 0) or 0)
    high = int(v.get("high_open", 0) or 0)
    sla = int(v.get("sla_breaches", 0) or 0)
    oldest = int(v.get("oldest_open_days", 0) or 0)
    fired = crit > 0 or high > cfg["high_vuln_max"] or sla > 0 or oldest > cfg["vuln_oldest_open_max_days"]
    add("open_critical_vulnerabilities", fired, "critical" if crit > 0 else "high",
        (f"{crit} critical / {high} high open; {sla} SLA breach(es); oldest open {oldest}d") if fired
        else "no open critical/high vulnerabilities beyond thresholds",
        [{"critical_open": crit, "high_open": high, "sla_breaches": sla, "oldest_open_days": oldest,
          "citation": _cite(v.get("evidence_ref"), as_of_s)}] if fired else [],
        {"high_vuln_max": cfg["high_vuln_max"], "oldest_open_max_days": cfg["vuln_oldest_open_max_days"]})

    # 4. unresolved_material_incident — affected our data & unresolved, or disclosed late
    incidents = doc.get("incidents") or []
    material = [i for i in incidents if i.get("affected_our_data")]
    unresolved = [i for i in material if not i.get("resolved")]

    def _gap(i):
        if i.get("occurred") and i.get("disclosed"):
            return (_parse(i["disclosed"]) - _parse(i["occurred"])).days
        return None

    late = [i for i in material if (_gap(i) is not None and _gap(i) > cfg["incident_disclosure_max_days"])]
    offending = {i.get("incident_id"): i for i in (unresolved + late)}
    fired = bool(offending)
    add("unresolved_material_incident", fired, "critical" if unresolved else "high",
        ("material incident(s) affecting our data unresolved or disclosed late "
         f"(> {cfg['incident_disclosure_max_days']}d)") if fired else "no unresolved/late material incident",
        [{"incident_id": i.get("incident_id"), "severity": i.get("severity"),
          "resolved": i.get("resolved"), "disclosure_gap_days": _gap(i),
          "citation": _cite(i.get("evidence_ref"), i.get("disclosed") or as_of_s)}
         for i in offending.values()],
        {"material_incidents": len(material), "disclosure_max_days": cfg["incident_disclosure_max_days"]})

    # 5. fourth_party_data_exposure — subcontractors processing our data w/o evidence or in unapproved region
    subs = doc.get("subcontractors") or []
    approved = set(cfg["fourth_party_approved_regions"])
    exposed = [s for s in subs if s.get("processes_our_data")
               and (s.get("region") not in approved or not s.get("evidence_ref"))]
    fired = bool(exposed)
    add("fourth_party_data_exposure", fired, "high",
        "subcontractor(s) process our data in an unapproved region or without evidence" if fired
        else "no unmanaged fourth-party data exposure",
        [{"name": s.get("name"), "region": s.get("region"), "processes_our_data": True,
          "citation": _cite(s.get("evidence_ref") or "subcontractors", as_of_s)} for s in exposed],
        {"approved_regions": sorted(approved), "exposed_count": len(exposed)})

    # 6. contractual_gap — required security obligations absent/weak
    k = doc.get("contract") or {}
    gaps = []
    bn = k.get("breach_notification_hours")
    if bn is None or bn > cfg["breach_notification_max_hours"]:
        gaps.append("breach_notification_sla")
    if not k.get("right_to_audit"):
        gaps.append("right_to_audit")
    if not k.get("data_return_deletion"):
        gaps.append("data_return_deletion")
    fired = bool(gaps) and bool(k)
    add("contractual_gap", fired, "medium",
        f"missing/weak contractual security obligation(s): {', '.join(gaps)}" if fired
        else "core contractual security obligations present",
        [{"gaps": gaps, "breach_notification_hours": bn, "citation": _cite("contract", as_of_s)}] if fired else [],
        {"breach_notification_max_hours": cfg["breach_notification_max_hours"]})
    if not k:
        not_evaluable.append({"item": "contract", "why": "no contract block supplied"})

    # 7. resilience_gap — untested BCP or RTO worse than required for an important/critical service
    r = doc.get("resilience") or {}
    critical_service = eng.get("criticality") in ("critical", "important")
    rto, req = r.get("rto_hours"), r.get("required_rto_hours")
    rto_bad = rto is not None and req is not None and rto > req
    fired = bool(r) and critical_service and (not r.get("bcp_tested") or rto_bad)
    add("resilience_gap", fired, "high" if eng.get("criticality") == "critical" else "medium",
        "important/critical service with untested BCP or RTO worse than required" if fired
        else "resilience posture meets requirement or service not important",
        [{"bcp_tested": r.get("bcp_tested"), "rto_hours": rto, "required_rto_hours": req,
          "citation": _cite(r.get("evidence_ref") or "resilience", as_of_s)}] if fired else [],
        {"critical_service": critical_service})
    if not r:
        not_evaluable.append({"item": "resilience", "why": "no resilience/BCP block supplied"})

    # 8. overdue_remediation — committed items past due and not closed
    rem = doc.get("remediation") or []
    overdue = [x for x in rem if x.get("status") != "closed" and x.get("committed_date")
               and _parse(x["committed_date"]) < as_of]
    fired = bool(overdue)
    sev = "high" if any(x.get("severity") in ("high", "critical") for x in overdue) else "medium"
    add("overdue_remediation", fired, sev,
        f"{len(overdue)} committed remediation item(s) past due and open" if fired
        else "no overdue remediation commitments",
        [{"finding_id": x.get("finding_id"), "severity": x.get("severity"),
          "committed_date": x.get("committed_date"),
          "citation": _cite(x.get("evidence_ref") or "remediation", x.get("committed_date") or as_of_s)}
         for x in overdue],
        {"overdue_count": len(overdue)})

    fired_list = [f for f in findings if f["fired"]]
    is_amp = amplified(eng)
    tier = residual_tier(fired_list, is_amp)

    considerations = []
    if fired_list:
        considerations = [
            "Verify compensating controls (e.g., network segmentation, monitoring) not captured in the intake",
            "Confirm attestation scope and exception dispositions with the supplier before adjudication",
            "Check whether open items already have an accepted remediation plan owned by a named risk owner",
            "Confirm data-classification and criticality ratings match the current engagement",
            "Assess supplier concentration / substitutability separately (see handoffs)",
        ]

    return {
        "review_id": f"tpcr-{str(doc.get('supplier_ref', 'SUP')).replace('*', '')}-{as_of_s}-0001",
        "assessment_id": doc.get("assessment_id"),
        "supplier_ref": doc.get("supplier_ref"),
        "as_of": as_of_s,
        "config_version": doc.get("config_version"),
        "engagement": {
            "data_classification": eng.get("data_classification"),
            "criticality": eng.get("criticality"),
            "hosts_regulated_data": bool(eng.get("hosts_regulated_data")),
            "amplified": is_amp,
        },
        "findings": findings,
        "fired_findings": [f["finding_id"] for f in fired_list],
        "not_evaluable": not_evaluable,
        "suggested_residual_tier": tier,
        "considerations": considerations,
        "disclaimer": DISCLAIMER,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = compute(doc)
    print(json.dumps(out, indent=2))
    errors = []
    # internal consistency invariants
    if out["suggested_residual_tier"] not in ORDER:
        errors.append(f"tier {out['suggested_residual_tier']!r} not in {ORDER}")
    for f in out["findings"]:
        if f["fired"] and not f["evidence"]:
            errors.append(f"fired finding {f['finding_id']} has no evidence")
        if f["fired"] and any(not str(e.get("citation", "")).strip() for e in f["evidence"]):
            errors.append(f"fired finding {f['finding_id']} has an uncited evidence row")
    recomputed = residual_tier([f for f in out["findings"] if f["fired"]], out["engagement"]["amplified"])
    if recomputed != out["suggested_residual_tier"]:
        errors.append("tier is not reproducible from findings")
    for e in errors:
        print("ERROR", e)
    print(f"compute self-check: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
