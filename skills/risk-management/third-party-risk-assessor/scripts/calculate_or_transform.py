#!/usr/bin/env python3
"""Deterministic third-party (vendor) risk-dimension scoring for third-party-risk-assessor.

Reads a vendor assessment file (see validate_input.py), scores the eight documented risk
dimensions (criticality, control evidence, concentration, subcontractors/fourth-party, data,
resilience, financial condition, exit/contingency), attaches evidence + citations to each
material finding, and maps the dimension bands to a SUGGESTED composite risk tier.

IMPORTANT: This produces explainable *findings, evidence, and a suggested tier plus
remediation recommendations* only. It is R3 decision support: it NEVER approves, rejects,
onboards, renews, terminates, or risk-accepts a vendor, NEVER closes/files the assessment,
and NEVER writes a system of record. The band and tier mappings are deterministic and
documented in references/domain-rules.md. Every band is a recommendation for the accountable
human/committee to adjudicate.

Usage:
  python calculate_or_transform.py assessment.json   # prints the assessment JSON
  python calculate_or_transform.py --selftest        # runs on the bundled fixture + checks
Prints the assessment JSON to stdout. In --selftest also prints a line ending "N error(s)".
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

# Severity ladder: 0 Low, 1 Moderate, 2 High, 3 Critical.
BANDS = {0: "Low", 1: "Moderate", 2: "High", 3: "Critical"}
GAP_STATUSES = {"partial", "ineffective", "missing"}
DISCLAIMER = ("Assessment evidence and recommendations only; not an approval, rejection, or "
              "risk-acceptance decision. Human adjudication and sign-off are required before any "
              "onboarding, renewal, termination, or system-of-record change.")

DEFAULT_CONFIG = {
    "critical_substitution_days": 30, "high_substitution_days": 14, "moderate_substitution_days": 7,
    "material_spend": 1000000.0, "moderate_spend": 250000.0,
    "control_test_max_days": 365, "high_gap_count": 3,
    "critical_control_domains": ["encryption", "access", "resilience"],
    "critical_share": 0.75, "high_share": 0.5, "moderate_share": 0.25,
    "elevated_risk_jurisdictions": ["XX", "YY"],
    "critical_records": 100000,
    "max_rto_hours": 24, "high_rto_hours": 8, "bcp_test_max_days": 365, "sla_min": 0.999,
    "critical_current_ratio": 1.0, "moderate_current_ratio": 1.5, "high_debt_to_equity": 3.0,
    "distressed_ratings": ["CCC", "CC", "C", "D"], "speculative_ratings": ["BB", "B"],
    "high_dimension_count": 3,
}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _stale(last_tested, as_of, max_days):
    lt, ao = _parse_date(last_tested), _parse_date(as_of)
    if lt is None or ao is None:
        return last_tested in (None, "")  # missing date treated as a gap
    return (ao - lt).days > max_days


def _cite(source_ref, as_of):
    return f"tpr:{source_ref or '?'}@{as_of}"


def _high_dimension_count(cfg) -> int:
    """The configured High-dimension escalation threshold, coerced to a positive int.

    Reads the merged pack config so a tightened deployment value is honored; falls back to
    the default for missing/invalid values so the mapping never crashes or silently disables.
    """
    hdc = (cfg or {}).get("high_dimension_count", DEFAULT_CONFIG["high_dimension_count"])
    if isinstance(hdc, bool) or not isinstance(hdc, int) or hdc < 1:
        return DEFAULT_CONFIG["high_dimension_count"]
    return hdc


def suggested_tier(severities, cfg=None):
    """Deterministic composite mapping (see references/domain-rules.md).

    ``cfg`` is the merged pack config; the High-dimension escalation threshold is read from
    it (``high_dimension_count``) so a tightened config escalates rather than under-escalates.
    """
    sevs = [s for s in severities if s is not None]
    if not sevs:
        return "Low", 0
    mx = max(sevs)
    n_high = sum(1 for s in sevs if s >= 2)
    high_dimension_count = _high_dimension_count(cfg)
    if mx == 3:
        return "Critical", mx
    if mx == 2:
        return ("Critical" if n_high >= high_dimension_count else "High"), mx
    if mx == 1:
        return "Moderate", mx
    return "Low", mx


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = doc.get("as_of")
    dims, not_evaluable = [], []

    crit_in = doc.get("criticality") or {}
    supports_critical = bool(crit_in.get("supports_critical_operation"))

    def add(name, sev, reason, evidence, inputs):
        dims.append({"dimension": name, "band": BANDS[sev], "severity": sev,
                     "fired": sev >= 2, "reason": reason, "evidence": evidence, "inputs": inputs})

    # ---- criticality ---------------------------------------------------------
    if crit_in:
        sub = _num(crit_in.get("substitutability_days")) or 0.0
        spend = _num(crit_in.get("annual_spend")) or 0.0
        if supports_critical and sub >= cfg["critical_substitution_days"]:
            sev = 3
        elif supports_critical or sub >= cfg["high_substitution_days"] or spend >= cfg["material_spend"]:
            sev = 2
        elif spend >= cfg["moderate_spend"] or sub >= cfg["moderate_substitution_days"]:
            sev = 1
        else:
            sev = 0
        add("criticality", sev,
            f"supports_critical_operation={supports_critical}, substitutability={sub:.0f}d, annual_spend={spend:.0f}",
            [{"ref": crit_in.get("source_ref"), "citation": _cite(crit_in.get("source_ref"), as_of),
              "value": {"supports_critical_operation": supports_critical, "substitutability_days": sub, "annual_spend": spend}}] if sev >= 2 else [],
            {"substitutability_days": sub, "annual_spend": spend})
    else:
        not_evaluable.append({"dimension": "criticality", "why": "missing 'criticality' block"})

    # ---- control evidence ----------------------------------------------------
    controls = doc.get("controls")
    if controls:
        crit_domains = {str(d).lower() for d in cfg["critical_control_domains"]}
        gaps = []
        for c in controls:
            status = str(c.get("status", "")).lower()
            is_gap = status in GAP_STATUSES or _stale(c.get("last_tested"), as_of, cfg["control_test_max_days"])
            if is_gap:
                gaps.append(c)
        crit_gap = [c for c in gaps if str(c.get("domain", "")).lower() in crit_domains]
        if crit_gap:
            sev = 3
        elif len(gaps) >= cfg["high_gap_count"]:
            sev = 2
        elif gaps:
            sev = 1
        else:
            sev = 0
        add("control_evidence", sev,
            f"{len(gaps)} control gap(s) of {len(controls)}; {len(crit_gap)} in critical domain(s)",
            [{"ref": c.get("source_ref"), "citation": _cite(c.get("source_ref"), as_of),
              "value": {"control_id": c.get("control_id"), "domain": c.get("domain"), "status": c.get("status"), "last_tested": c.get("last_tested")}}
             for c in gaps] if sev >= 2 else [],
            {"controls_evaluated": len(controls), "gaps": len(gaps), "critical_domain_gaps": len(crit_gap)})
    else:
        not_evaluable.append({"dimension": "control_evidence", "why": "no 'controls' provided"})

    # ---- concentration -------------------------------------------------------
    conc_in = doc.get("concentration") or {}
    if conc_in:
        share = _num(conc_in.get("vendor_share_of_function")) or 0.0
        spof = bool(conc_in.get("single_point_of_failure"))
        if spof and share >= cfg["critical_share"]:
            sev = 3
        elif share >= cfg["high_share"] or spof:
            sev = 2
        elif share >= cfg["moderate_share"]:
            sev = 1
        else:
            sev = 0
        add("concentration", sev,
            f"vendor_share_of_function={share:.2f}, single_point_of_failure={spof}",
            [{"ref": conc_in.get("source_ref"), "citation": _cite(conc_in.get("source_ref"), as_of),
              "value": {"vendor_share_of_function": share, "single_point_of_failure": spof, "function": conc_in.get("function")}}] if sev >= 2 else [],
            {"vendor_share_of_function": share, "single_point_of_failure": spof})
    else:
        not_evaluable.append({"dimension": "concentration", "why": "missing 'concentration' block"})

    # ---- subcontractors (fourth-party) --------------------------------------
    subs = doc.get("subcontractors")
    if subs is not None:
        elevated = {str(j).upper() for j in cfg["elevated_risk_jurisdictions"]}
        crit_subs = [s for s in subs if s.get("critical")]
        crit_elevated = [s for s in crit_subs if str(s.get("country", "")).upper() in elevated]
        undisclosed = [s for s in subs if s.get("disclosed") is False]
        if crit_elevated:
            sev = 3
        elif crit_subs or undisclosed:
            sev = 2
        elif subs:
            sev = 1
        else:
            sev = 0
        flagged = crit_elevated or crit_subs or undisclosed
        add("subcontractors", sev,
            f"{len(subs)} subcontractor(s); {len(crit_subs)} critical, {len(crit_elevated)} in elevated jurisdiction, {len(undisclosed)} undisclosed",
            [{"ref": s.get("source_ref"), "citation": _cite(s.get("source_ref"), as_of),
              "value": {"name": s.get("name"), "country": s.get("country"), "critical": s.get("critical"), "disclosed": s.get("disclosed")}}
             for s in flagged] if sev >= 2 else [],
            {"count": len(subs), "critical": len(crit_subs), "critical_in_elevated_jurisdiction": len(crit_elevated)})
    else:
        not_evaluable.append({"dimension": "subcontractors", "why": "missing 'subcontractors' block"})

    # ---- data ----------------------------------------------------------------
    data_in = doc.get("data") or {}
    if data_in:
        cls = str(data_in.get("classification", "")).lower()
        pii = bool(data_in.get("pii"))
        records = _num(data_in.get("records_count")) or 0.0
        if cls == "restricted" or (pii and records >= cfg["critical_records"]):
            sev = 3
        elif cls == "confidential" or pii:
            sev = 2
        elif cls == "internal":
            sev = 1
        else:
            sev = 0
        add("data", sev,
            f"classification={cls or 'n/a'}, pii={pii}, records={records:.0f}, cross_border={bool(data_in.get('cross_border_transfer'))}",
            [{"ref": data_in.get("source_ref"), "citation": _cite(data_in.get("source_ref"), as_of),
              "value": {"classification": cls, "pii": pii, "records_count": records, "cross_border_transfer": bool(data_in.get("cross_border_transfer"))}}] if sev >= 2 else [],
            {"classification": cls, "pii": pii, "records_count": records})
    else:
        not_evaluable.append({"dimension": "data", "why": "missing 'data' block"})

    # ---- resilience ----------------------------------------------------------
    res_in = doc.get("resilience") or {}
    if res_in:
        rto = _num(res_in.get("rto_hours"))
        bcp_tested = bool(res_in.get("bcp_tested"))
        bcp_stale = _stale(res_in.get("last_bcp_test"), as_of, cfg["bcp_test_max_days"])
        sla = _num(res_in.get("sla_uptime"))
        if supports_critical and (not bcp_tested or (rto is not None and rto > cfg["max_rto_hours"])):
            sev = 3
        elif (not bcp_tested) or bcp_stale or (rto is not None and rto > cfg["high_rto_hours"]):
            sev = 2
        elif sla is not None and sla < cfg["sla_min"]:
            sev = 1
        else:
            sev = 0
        add("resilience", sev,
            f"rto_hours={rto}, bcp_tested={bcp_tested}, bcp_stale={bcp_stale}, sla_uptime={sla}",
            [{"ref": res_in.get("source_ref"), "citation": _cite(res_in.get("source_ref"), as_of),
              "value": {"rto_hours": rto, "bcp_tested": bcp_tested, "last_bcp_test": res_in.get("last_bcp_test"), "sla_uptime": sla}}] if sev >= 2 else [],
            {"rto_hours": rto, "bcp_tested": bcp_tested, "sla_uptime": sla})
    else:
        not_evaluable.append({"dimension": "resilience", "why": "missing 'resilience' block"})

    # ---- financial condition -------------------------------------------------
    fin_in = doc.get("financials") or {}
    if fin_in:
        going_concern = bool(fin_in.get("going_concern_flag"))
        rating = str(fin_in.get("credit_rating", "")).upper()
        cr = _num(fin_in.get("current_ratio"))
        dte = _num(fin_in.get("debt_to_equity"))
        nm = _num(fin_in.get("net_margin"))
        distressed = {r.upper() for r in cfg["distressed_ratings"]}
        speculative = {r.upper() for r in cfg["speculative_ratings"]}
        if going_concern or rating in distressed or (cr is not None and cr < cfg["critical_current_ratio"]):
            sev = 3
        elif (nm is not None and nm < 0) or (dte is not None and dte > cfg["high_debt_to_equity"]) or rating in speculative:
            sev = 2
        elif cr is not None and cr < cfg["moderate_current_ratio"]:
            sev = 1
        else:
            sev = 0
        add("financial_condition", sev,
            f"going_concern={going_concern}, credit_rating={rating or 'n/a'}, current_ratio={cr}, debt_to_equity={dte}, net_margin={nm}",
            [{"ref": fin_in.get("source_ref"), "citation": _cite(fin_in.get("source_ref"), as_of),
              "value": {"going_concern_flag": going_concern, "credit_rating": rating, "current_ratio": cr, "debt_to_equity": dte, "net_margin": nm}}] if sev >= 2 else [],
            {"going_concern_flag": going_concern, "credit_rating": rating, "current_ratio": cr})
    else:
        not_evaluable.append({"dimension": "financial_condition", "why": "missing 'financials' block"})

    # ---- exit / contingency --------------------------------------------------
    exit_in = doc.get("exit_plan") or {}
    if exit_in:
        documented = bool(exit_in.get("documented"))
        tested = bool(exit_in.get("tested"))
        alternate = bool(exit_in.get("alternate_provider_identified"))
        if supports_critical and not documented:
            sev = 3
        elif not documented or not alternate:
            sev = 2
        elif not tested:
            sev = 1
        else:
            sev = 0
        add("exit_contingency", sev,
            f"documented={documented}, tested={tested}, alternate_provider_identified={alternate}",
            [{"ref": exit_in.get("source_ref"), "citation": _cite(exit_in.get("source_ref"), as_of),
              "value": {"documented": documented, "tested": tested, "alternate_provider_identified": alternate}}] if sev >= 2 else [],
            {"documented": documented, "tested": tested, "alternate_provider_identified": alternate})
    else:
        not_evaluable.append({"dimension": "exit_contingency", "why": "missing 'exit_plan' block"})

    severities = [d["severity"] for d in dims]
    tier, _mx = suggested_tier(severities, cfg)
    material = [d["dimension"] for d in dims if d["fired"]]

    # Remediation recommendations (for human adjudication; never a decision/action).
    rec_map = {
        "criticality": "Confirm criticality tiering and substitutability with the business owner and reflect it in the vendor inventory.",
        "control_evidence": "Obtain remediation evidence and independent assurance for gapped controls; route deep control testing to the third-party-cyber-risk-reviewer.",
        "concentration": "Track vendor/function concentration and single-points-of-failure via the concentration-risk-monitor.",
        "subcontractors": "Obtain fourth-party (subcontractor) disclosures and flow-down control evidence for critical or elevated-jurisdiction subs.",
        "data": "Verify data-protection, retention, and cross-border transfer safeguards for sensitive data; consider the enhanced-due-diligence-packager for elevated exposure.",
        "resilience": "Require evidence of a recently tested BCP/DR within tolerance; route scenario testing to the operational-resilience-scenario-tester.",
        "financial_condition": "Refresh the financial-condition review; route vendor financials to the financial-spreading-assistant. Factual solvency indicators only, not investment advice.",
        "exit_contingency": "Require a tested exit plan with an identified alternate provider; extract exit/termination obligations via the contract-obligation-extractor.",
    }
    recommended_actions = [rec_map[d] for d in material if d in rec_map]
    recommended_actions.append(
        "These are recommendations and evidence for the accountable third-party-risk committee to adjudicate; no vendor decision has been made.")

    evidence_gaps = list(not_evaluable)

    vid = str(doc.get("vendor_id", "V-UNKNOWN")).replace("*", "")
    return {
        "assessment_id": f"tpr-{vid}-{as_of}-0001",
        "vendor_id": doc.get("vendor_id"),
        "vendor_name": doc.get("vendor_name"),
        "as_of": as_of,
        "config_version": doc.get("config_version"),
        "framework_version": doc.get("framework_version"),
        "config": cfg,
        "dimensions": dims,
        "material_findings": material,
        "not_evaluable": not_evaluable,
        "evidence_gaps": evidence_gaps,
        "suggested_risk_tier": tier,
        "recommended_actions": recommended_actions,
        "disclaimer": DISCLAIMER,
    }


def _selftest_checks(pack: dict) -> list:
    """Internal consistency checks so --selftest can return an exit code."""
    errs = []
    sevs = [d["severity"] for d in pack.get("dimensions", [])]
    exp, _ = suggested_tier(sevs, pack.get("config"))
    if pack.get("suggested_risk_tier") != exp:
        errs.append(f"suggested_risk_tier {pack.get('suggested_risk_tier')!r} != expected {exp!r}")
    for d in pack.get("dimensions", []):
        if d.get("fired") and not d.get("evidence"):
            errs.append(f"material finding {d['dimension']} lacks evidence")
    if pack.get("disclaimer") != DISCLAIMER:
        errs.append("disclaimer text mismatch")
    return errs


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    pack = compute(doc)
    print(json.dumps(pack, indent=2))
    if selftest:
        errs = _selftest_checks(pack)
        for e in errs:
            print("ERROR", e)
        print(f"compute selftest: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
