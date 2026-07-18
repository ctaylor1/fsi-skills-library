#!/usr/bin/env python3
"""Deterministic, explainable merchant-onboarding risk-finding computation.

Reads a merchant onboarding application (see validate_input.py), computes the configured
risk findings across KYB / beneficial ownership / business model / expected activity /
sanctions / adverse media / credit / prohibited-use dimensions, attaches evidence +
citations to each fired finding, checks evidence completeness, and maps the fired-finding
set to a **recommendation band** for a human adjudicator.

IMPORTANT: This produces explainable *findings and a recommendation* only. It is R3
decision-support. It NEVER makes an onboarding decision, boards/declines a merchant, closes
the case, or files/writes any system of record. The recommendation mapping is deterministic
and documented in references/domain-rules.md; a human adjudicator must decide.

Usage:
  python calculate_or_transform.py application.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "prohibited_mccs": ["7801", "7995"],
    "restricted_mccs": ["5967", "5966", "5734", "6211", "4816"],
    "high_risk_countries": ["AF", "IR", "KP", "SY", "MM"],
    "required_ubo_coverage_pct": 75.0,
    "ubo_threshold_pct": 25.0,
    "max_monthly_volume_no_edd": 1000000.0,
    "credit_review_limit": 250000.0,
}
DISCLAIMER = ("Recommendation and evidence only; not an onboarding decision. No approval, "
              "decline, boarding, filing, or system-of-record change has been made. Human "
              "adjudication is required.")

# Finding severities (fixed contract; validate_output re-derives the recommendation from these).
BLOCKING = {"sanctions_screening", "prohibited_business_model"}
INCOMPLETE = {"evidence_incomplete"}
ELEVATED = {
    "restricted_business_model", "adverse_media", "beneficial_ownership_gap",
    "high_risk_geography", "pep_ownership", "expected_activity_outsized",
    "credit_exposure", "website_product_risk",
}

# Human-readable condition for each elevated finding (surfaced when Recommend-Approve-with-Conditions).
CONDITION_BY_FINDING = {
    "restricted_business_model": "Attach restricted-MCC controls (reserve, delivery-timeframe review, refund policy) before boarding",
    "adverse_media": "Obtain adverse-media adjudication (route to adverse-media specialist) before boarding",
    "beneficial_ownership_gap": "Complete beneficial-ownership verification to required coverage before boarding",
    "high_risk_geography": "Apply enhanced due diligence for high-risk jurisdiction exposure before boarding",
    "pep_ownership": "Obtain PEP/EDD sign-off for the politically exposed owner before boarding",
    "expected_activity_outsized": "Confirm expected-activity substantiation and set volume/reserve limits before boarding",
    "credit_exposure": "Obtain credit sign-off and set an exposure/reserve limit before boarding",
    "website_product_risk": "Complete website/product review and confirm no prohibited/undisclosed products",
}
REQUIRED_EVIDENCE = ("kyb_registration", "ubo_verification", "website_review",
                     "expected_activity", "financials")


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    m = doc.get("merchant") or {}
    owners = doc.get("beneficial_owners") or []
    scr = doc.get("screening") or {}
    sanc = scr.get("sanctions") or {}
    am = scr.get("adverse_media") or {}
    credit = doc.get("credit") or {}
    evidence = doc.get("evidence") or {}

    prohibited = {str(x) for x in cfg["prohibited_mccs"]}
    restricted = {str(x) for x in cfg["restricted_mccs"]}
    high_risk = {str(x).upper() for x in cfg["high_risk_countries"]}
    mcc = str(m.get("mcc", ""))

    findings = []

    def add(name, severity, fired, reason, evidence_rows, rule_ref):
        findings.append({
            "finding": name, "severity": severity, "fired": bool(fired),
            "reason": reason, "evidence": evidence_rows if fired else [],
            "rule_ref": rule_ref,
        })

    # 1. sanctions_screening (BLOCKING) — any status other than cleared blocks approval.
    sanc_status = str(sanc.get("status", "pending"))
    add("sanctions_screening", "blocking", sanc_status != "cleared",
        f"sanctions screening status is {sanc_status!r} (not 'cleared')"
        if sanc_status != "cleared" else "sanctions screening cleared",
        [{"detail": f"status={sanc_status}", "citation": f"sanctions:{sanc.get('source_ref','?')}"}],
        "domain-rules.md#sanctions")

    # 2. prohibited_business_model (BLOCKING) — MCC on the prohibited list.
    add("prohibited_business_model", "blocking", mcc in prohibited,
        f"MCC {mcc} is on the prohibited list" if mcc in prohibited
        else f"MCC {mcc} is not prohibited",
        [{"mcc": mcc, "business_model": m.get("business_model"),
          "citation": f"application:{doc.get('case_id','?')};mcc={mcc}"}],
        "domain-rules.md#prohibited-use")

    # 3. restricted_business_model (ELEVATED) — MCC restricted; approvable only with conditions.
    add("restricted_business_model", "elevated", mcc in restricted,
        f"MCC {mcc} is on the restricted list (conditions required)" if mcc in restricted
        else f"MCC {mcc} is not restricted",
        [{"mcc": mcc, "business_model": m.get("business_model"),
          "citation": f"application:{doc.get('case_id','?')};mcc={mcc}"}],
        "domain-rules.md#restricted-use")

    # 4. adverse_media (ELEVATED) — unresolved adverse media.
    am_status = str(am.get("status", "none"))
    add("adverse_media", "elevated", am_status == "unresolved",
        f"unresolved adverse media in categories {am.get('categories', [])}" if am_status == "unresolved"
        else f"adverse media status {am_status!r}",
        [{"categories": am.get("categories", []), "citation": f"adverse_media:{am.get('source_ref','?')}"}],
        "domain-rules.md#adverse-media")

    # 5. beneficial_ownership_gap (ELEVATED) — coverage below required OR a >=threshold owner unverified.
    verified_cov = sum(_num(o.get("ownership_pct"), 0.0) for o in owners if o.get("verified") is True)
    unverified_material = [o for o in owners
                           if _num(o.get("ownership_pct"), 0.0) >= cfg["ubo_threshold_pct"]
                           and o.get("verified") is not True]
    ubo_gap = verified_cov < cfg["required_ubo_coverage_pct"] or bool(unverified_material)
    add("beneficial_ownership_gap", "elevated", ubo_gap,
        f"verified ownership coverage {verified_cov:g}% < required {cfg['required_ubo_coverage_pct']:g}%"
        + (f"; unverified >= {cfg['ubo_threshold_pct']:g}% owner(s): "
           + ", ".join(o.get("name", "?") for o in unverified_material) if unverified_material else "")
        if ubo_gap else f"verified ownership coverage {verified_cov:g}% meets requirement",
        [{"name": o.get("name"), "ownership_pct": o.get("ownership_pct"),
          "verified": o.get("verified"), "citation": f"ubo:{o.get('source_ref','?')}"}
         for o in ([o for o in owners if o.get("verified") is not True] or owners)],
        "domain-rules.md#beneficial-ownership")

    # 6. high_risk_geography (ELEVATED) — merchant or any owner in a high-risk country.
    geo_hits = ([{"scope": "merchant", "country": m.get("country"),
                  "citation": f"application:{doc.get('case_id','?')};country={m.get('country')}"}]
                if str(m.get("country", "")).upper() in high_risk else [])
    geo_hits += [{"scope": "owner", "name": o.get("name"), "country": o.get("country"),
                  "citation": f"ubo:{o.get('source_ref','?')}"}
                 for o in owners if str(o.get("country", "")).upper() in high_risk]
    add("high_risk_geography", "elevated", bool(geo_hits),
        "merchant/owner jurisdiction on the high-risk list" if geo_hits
        else "no high-risk jurisdiction exposure",
        geo_hits, "domain-rules.md#geography")

    # 7. pep_ownership (ELEVATED) — a politically exposed owner not yet adjudicated (verified proxy).
    pep_owners = [o for o in owners if o.get("pep") is True]
    add("pep_ownership", "elevated", bool(pep_owners),
        "politically exposed beneficial owner(s) present" if pep_owners
        else "no politically exposed owners flagged",
        [{"name": o.get("name"), "ownership_pct": o.get("ownership_pct"),
          "citation": f"ubo:{o.get('source_ref','?')}"} for o in pep_owners],
        "domain-rules.md#pep")

    # 8. expected_activity_outsized (ELEVATED) — expected volume above the no-EDD threshold.
    vol = _num(m.get("expected_monthly_volume"), 0.0)
    add("expected_activity_outsized", "elevated", vol > cfg["max_monthly_volume_no_edd"],
        f"expected monthly volume {vol:g} exceeds no-EDD threshold {cfg['max_monthly_volume_no_edd']:g}"
        if vol > cfg["max_monthly_volume_no_edd"] else f"expected monthly volume {vol:g} within threshold",
        [{"expected_monthly_volume": vol, "avg_ticket": m.get("expected_avg_ticket"),
          "citation": f"application:{doc.get('case_id','?')};expected_activity"}],
        "domain-rules.md#expected-activity")

    # 9. credit_exposure (ELEVATED) — requested limit above review limit AND credit not clean.
    req_limit = _num(m.get("requested_processing_limit"), 0.0)
    assessment = str(credit.get("assessment", "not_assessed"))
    credit_hit = req_limit > cfg["credit_review_limit"] and assessment in ("marginal", "fail", "not_assessed")
    add("credit_exposure", "elevated", credit_hit,
        f"requested limit {req_limit:g} exceeds review limit {cfg['credit_review_limit']:g} with credit assessment {assessment!r}"
        if credit_hit else f"credit within appetite (limit {req_limit:g}, assessment {assessment!r})",
        [{"requested_processing_limit": req_limit, "assessment": assessment,
          "citation": f"credit:{credit.get('source_ref','?')}"}],
        "domain-rules.md#credit")

    # 10. website_product_risk (ELEVATED) — website review missing (cannot confirm products/claims).
    website_missing = not m.get("website") or not evidence.get("website_review")
    add("website_product_risk", "elevated", website_missing,
        "website or website-review evidence missing — products/claims cannot be confirmed"
        if website_missing else "website review evidence present",
        [{"website": m.get("website"), "website_review": evidence.get("website_review"),
          "citation": f"application:{doc.get('case_id','?')};website"}],
        "domain-rules.md#website-product")

    # 11. evidence_incomplete (INCOMPLETE) — any required evidence item missing.
    missing = [k for k in REQUIRED_EVIDENCE if not evidence.get(k)]
    add("evidence_incomplete", "incomplete", bool(missing),
        f"missing required evidence: {', '.join(missing)}" if missing else "required evidence present",
        [{"missing": missing, "citation": f"application:{doc.get('case_id','?')};evidence"}],
        "domain-rules.md#evidence-completeness")

    fired = [f["finding"] for f in findings if f["fired"]]
    recommendation = _recommendation(fired)
    conditions = ([CONDITION_BY_FINDING[f] for f in fired if f in CONDITION_BY_FINDING]
                  if recommendation == "Recommend-Approve-with-Conditions" else [])

    present = [k for k in REQUIRED_EVIDENCE if evidence.get(k)]
    return {
        "review_id": f"mor-{doc.get('case_id', 'NA')}-0001",
        "case_id": doc.get("case_id"),
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "merchant_summary": {
            "legal_name": m.get("legal_name"), "country": m.get("country"),
            "mcc": mcc, "business_model": m.get("business_model"),
        },
        "findings": findings,
        "fired_findings": fired,
        "evidence_completeness": {
            "required": list(REQUIRED_EVIDENCE), "present": present, "missing": missing,
        },
        "recommendation": recommendation,
        "conditions": conditions,
        "adjudication_required": True,
        "disclaimer": DISCLAIMER,
    }


def _recommendation(fired: list[str]) -> str:
    """Deterministic mapping documented in references/domain-rules.md."""
    fs = set(fired)
    if BLOCKING & fs:
        return "Recommend-Decline"
    if INCOMPLETE & fs:
        return "Escalate-Insufficient-Evidence"
    if ELEVATED & fs:
        return "Recommend-Approve-with-Conditions"
    return "Recommend-Approve"


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "application_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
