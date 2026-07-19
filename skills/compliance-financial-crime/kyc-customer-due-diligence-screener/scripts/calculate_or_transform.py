#!/usr/bin/env python3
"""Deterministic, explainable CDD screening for kyc-customer-due-diligence-screener.

Reads a de-identified KYC case file (see validate_input.py), computes the configured
completeness / identity / risk-factor / beneficial-owner signals, attaches evidence +
citations to each fired signal, and maps the fired set to a **recommended review track**.
Emits a machine-readable core that the SKILL wraps in a plain-language, human-adjudicated
pack.

IMPORTANT (R3 decision support): this produces explainable *findings and a recommended
review track only*. It never approves/rejects/onboards/exits a customer, adjudicates a
sanctions or PEP match, updates a risk rating, closes a case, or files anything. The track
mapping is deterministic and documented in references/domain-rules.md; a qualified analyst
must adjudicate.

Usage:
  python calculate_or_transform.py case.json | --selftest
Prints the screening JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "ubo_threshold_pct": 25.0,
    "ubo_coverage_target_pct": 75.0,
    "high_risk_countries": ["IR", "KP", "SY", "CU", "RU"],
    "high_risk_industries": ["msb", "crypto", "gambling", "precious_metals", "shell_company", "arms"],
    "required_fields_individual": ["legal_name", "date_of_birth", "residential_address", "country"],
    "required_fields_entity": ["legal_name", "registration_number", "formation_date", "registered_address", "country"],
    "required_documents_individual": ["government_id"],
    "required_documents_entity": ["certificate_of_incorporation"],
}

DISCLAIMER = (
    "CDD screening evidence and a recommended review track only; not a KYC/AML decision. "
    "No customer has been onboarded, exited, or risk-rated, no case disposition or closure "
    "has been recorded, and no regulatory filing has been made. A qualified analyst must "
    "adjudicate every finding."
)

# Deterministic recommended-track mapping (see references/domain-rules.md).
SANCTIONS = {"sanctions_potential_match"}
ELEVATED_RISK = {"high_risk_jurisdiction", "high_risk_industry", "pep_flag",
                 "adverse_media_flag", "ubo_below_coverage", "ubo_unverified"}
COMPLETENESS_GAPS = {"missing_required_field", "missing_required_document", "expired_document",
                     "unverified_identity", "identity_mismatch", "ownership_over_100"}


def recommended_track(fired) -> str:
    """Deterministic map fired-signal set -> recommended review track (documented, shared
    verbatim with validate_output.py). Precedence: sanctions escalation > elevated-risk EDD
    > completeness remediation > standard."""
    fs = set(fired)
    if fs & SANCTIONS:
        return "Escalate-For-Adjudication"
    if fs & ELEVATED_RISK:
        return "EDD-Recommended"
    if fs & COMPLETENESS_GAPS:
        return "Remediate-First"
    return "Standard-CDD"


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    case_id = doc["case_id"]
    as_of_raw = doc["as_of"]
    as_of = _parse_date(as_of_raw)
    customer = doc.get("customer") or {}
    ctype = customer.get("customer_type", "individual")
    docs = doc.get("documents") or []
    id_checks = doc.get("identity_checks") or []
    hits = doc.get("screening_hits") or {}
    owners = doc.get("beneficial_owners") or []
    is_entity = ctype == "entity"

    def cite(kind, ref):
        return f"{kind}:{ref}@{as_of_raw}"

    signals, not_evaluable = [], []

    def add(name, fired, reason, evidence, basis, contribution):
        signals.append({"signal": name, "fired": bool(fired), "reason": reason,
                        "evidence": evidence, "basis": basis, "contribution": contribution})

    # --- Completeness: required fields ---------------------------------------------------
    req_fields = cfg["required_fields_entity"] if is_entity else cfg["required_fields_individual"]
    missing_fields = [f for f in req_fields if not str(customer.get(f, "")).strip()]
    add("missing_required_field", bool(missing_fields),
        f"required KYC field(s) not provided: {', '.join(missing_fields)}" if missing_fields
        else "all required KYC fields present",
        [{"field": f, "citation": cite("kyc", f"case={case_id};field={f}")} for f in missing_fields],
        {"required": req_fields, "customer_type": ctype}, len(missing_fields))

    # --- Completeness: required documents ------------------------------------------------
    req_docs = cfg["required_documents_entity"] if is_entity else cfg["required_documents_individual"]
    present_types = {str(d.get("type", "")).lower() for d in docs}
    missing_docs = [d for d in req_docs if d.lower() not in present_types]
    add("missing_required_document", bool(missing_docs),
        f"required document(s) not on file: {', '.join(missing_docs)}" if missing_docs
        else "all required documents present",
        [{"document_type": d, "citation": cite("kyc", f"case={case_id};document={d}")} for d in missing_docs],
        {"required": req_docs, "present": sorted(present_types)}, len(missing_docs))

    # --- Completeness: expired documents -------------------------------------------------
    expired = []
    for d in docs:
        exp = _parse_date(d.get("expiry_date"))
        if exp is not None and as_of is not None and exp < as_of:
            expired.append(d)
    add("expired_document", bool(expired),
        f"{len(expired)} document(s) expired as of {as_of_raw}" if expired else "no expired documents",
        [{"document_type": d.get("type"), "expiry_date": d.get("expiry_date"),
          "citation": cite("kyc", d.get("source_ref", f"case={case_id};document={d.get('type')}"))}
         for d in expired],
        {"as_of": as_of_raw}, len(expired))

    # --- Identity: verification present --------------------------------------------------
    has_verified_id = any(d.get("verified") for d in docs)
    add("unverified_identity", not has_verified_id,
        "no verified identity document on file" if not has_verified_id
        else "at least one verified identity document present",
        [{"note": "no document has verified=true",
          "citation": cite("kyc", f"case={case_id};identity")}] if not has_verified_id else [],
        {"documents_reviewed": len(docs)}, 0 if has_verified_id else 1)

    # --- Identity: cross-source mismatch -------------------------------------------------
    if id_checks:
        mismatches = [c for c in id_checks if c.get("match") is False]
        add("identity_mismatch", bool(mismatches),
            f"{len(mismatches)} identity attribute(s) did not reconcile across sources" if mismatches
            else "identity attributes reconcile across sources",
            [{"attribute": c.get("attribute"), "sources": c.get("sources"),
              "citation": cite("kyc", c.get("source_ref", f"case={case_id};idcheck={c.get('attribute')}"))}
             for c in mismatches],
            {"checks": len(id_checks)}, len(mismatches))
    else:
        not_evaluable.append({"signal": "identity_mismatch", "why": "no identity_checks provided"})

    # --- Risk: high-risk jurisdiction ----------------------------------------------------
    hr_countries = {c.upper() for c in cfg["high_risk_countries"]}
    geo_hits = []
    cust_country = str(customer.get("country", "")).upper()
    if cust_country and cust_country in hr_countries:
        geo_hits.append({"party": "customer", "country": cust_country,
                         "citation": cite("kyc", f"case={case_id};customer;country={cust_country}")})
    for o in owners:
        oc = str(o.get("country", "")).upper()
        if oc and oc in hr_countries:
            geo_hits.append({"party": o.get("name"), "country": oc,
                             "citation": cite("kyc", o.get("source_ref", f"case={case_id};owner={o.get('name')}"))})
    add("high_risk_jurisdiction", bool(geo_hits),
        "customer or beneficial owner tied to a configured higher-risk jurisdiction" if geo_hits
        else "no higher-risk jurisdiction on the configured list",
        geo_hits, {"high_risk_countries": sorted(hr_countries)}, len(geo_hits))

    # --- Risk: high-risk industry (entity only) ------------------------------------------
    if is_entity:
        hr_ind = {i.lower() for i in cfg["high_risk_industries"]}
        industry = str(customer.get("industry", "")).lower()
        fired = industry in hr_ind and bool(industry)
        add("high_risk_industry", fired,
            f"entity industry '{industry}' is on the configured higher-risk list" if fired
            else f"industry '{industry or 'n/a'}' not on higher-risk list",
            [{"industry": industry, "citation": cite("kyc", f"case={case_id};industry={industry}")}] if fired else [],
            {"high_risk_industries": sorted(hr_ind)}, 1 if fired else 0)
    else:
        not_evaluable.append({"signal": "high_risk_industry", "why": "customer_type is individual"})

    # --- Risk: PEP indicator (potential match only) --------------------------------------
    peps = hits.get("pep") or []
    add("pep_flag", bool(peps),
        "PEP indicator(s) present as a potential match — not adjudicated here" if peps
        else "no PEP indicator present",
        [{"party": p.get("party"), "role": p.get("role"),
          "citation": cite("pep", p.get("source_ref", f"case={case_id};pep"))} for p in peps],
        {"note": "potential match; adjudicate via specialist + human"}, len(peps))

    # --- Risk: sanctions / watchlist potential match -------------------------------------
    sanc = hits.get("sanctions") or []
    add("sanctions_potential_match", bool(sanc),
        "potential sanctions/watchlist name match — route to sanctions adjudication" if sanc
        else "no potential sanctions/watchlist match",
        [{"party": s.get("party"), "list": s.get("list"),
          "citation": cite("sanctions", s.get("source_ref", f"case={case_id};sanctions"))} for s in sanc],
        {"note": "potential match only; disposition is adjudicated by a specialist + human"}, len(sanc))

    # --- Risk: adverse media indicator ---------------------------------------------------
    media = hits.get("adverse_media") or []
    add("adverse_media_flag", bool(media),
        "adverse-media indicator(s) present — allegation, not a finding" if media
        else "no adverse-media indicator present",
        [{"party": m.get("party"), "summary": m.get("summary"),
          "citation": cite("media", m.get("source_ref", f"case={case_id};media"))} for m in media],
        {"note": "distinguish allegation from finding; assess relevance/source quality"}, len(media))

    # --- Beneficial ownership (entity only) ----------------------------------------------
    if is_entity:
        threshold = cfg["ubo_threshold_pct"]
        target = cfg["ubo_coverage_target_pct"]
        total = sum(float(o.get("ownership_pct", 0) or 0) for o in owners)

        over = total > 100.0 + 0.01
        add("ownership_over_100", over,
            f"declared ownership sums to {total:.1f}% (> 100%) — data-quality gap" if over
            else f"declared ownership sums to {total:.1f}%",
            [{"name": o.get("name"), "ownership_pct": o.get("ownership_pct"),
              "citation": cite("kyc", o.get("source_ref", f"case={case_id};owner={o.get('name')}"))}
             for o in owners] if over else [],
            {"total_pct": round(total, 1)}, 1 if over else 0)

        below = total < target
        add("ubo_below_coverage", below,
            f"identified ownership {total:.1f}% below coverage target {target:.1f}%" if below
            else f"identified ownership {total:.1f}% meets coverage target {target:.1f}%",
            [{"name": o.get("name"), "ownership_pct": o.get("ownership_pct"),
              "citation": cite("kyc", o.get("source_ref", f"case={case_id};owner={o.get('name')}"))}
             for o in owners] if below else [],
            {"identified_pct": round(total, 1), "coverage_target_pct": target}, 1 if below else 0)

        unverified = [o for o in owners
                      if float(o.get("ownership_pct", 0) or 0) >= threshold and not o.get("verified")]
        add("ubo_unverified", bool(unverified),
            f"{len(unverified)} beneficial owner(s) at/above {threshold:.0f}% not verified" if unverified
            else f"all beneficial owners at/above {threshold:.0f}% verified",
            [{"name": o.get("name"), "ownership_pct": o.get("ownership_pct"),
              "citation": cite("kyc", o.get("source_ref", f"case={case_id};owner={o.get('name')}"))}
             for o in unverified],
            {"ubo_threshold_pct": threshold}, len(unverified))
    else:
        for s in ("ownership_over_100", "ubo_below_coverage", "ubo_unverified"):
            not_evaluable.append({"signal": s, "why": "customer_type is individual"})

    fired_names = [s["signal"] for s in signals if s["fired"]]
    track = recommended_track(fired_names)

    next_steps = []
    if "sanctions_potential_match" in fired_names:
        next_steps.append("Route potential sanctions/watchlist matches to sanctions adjudication (specialist + human).")
    if "pep_flag" in fired_names:
        next_steps.append("Have an analyst adjudicate the PEP potential match and source of wealth.")
    if "adverse_media_flag" in fired_names:
        next_steps.append("Assess adverse-media relevance and source quality before any conclusion.")
    if {"high_risk_jurisdiction", "high_risk_industry", "ubo_below_coverage", "ubo_unverified"} & set(fired_names):
        next_steps.append("If the analyst confirms EDD, assemble an enhanced-due-diligence package.")
    if COMPLETENESS_GAPS & set(fired_names):
        next_steps.append("Remediate completeness/identity gaps before the CDD assessment is finalized.")

    return {
        "screening_id": f"cdd-{case_id}-{as_of_raw}-0001",
        "case_id": case_id,
        "as_of": as_of_raw,
        "config_version": doc.get("config_version"),
        "customer": {
            "customer_id": customer.get("customer_id"),
            "customer_type": ctype,
            "legal_name": customer.get("legal_name"),
            "country": customer.get("country"),
        },
        "signals": signals,
        "fired_signals": fired_names,
        "not_evaluable": not_evaluable,
        "recommended_track": track,
        "adjudication_required": True,
        "recommended_next_steps": next_steps,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
