#!/usr/bin/env python3
"""Deterministic RFQ brief assembly for client-rfq-preparation-brief.

Assembles the brief sections, surfaces suitability/eligibility flags (KYC status, restricted
product, jurisdiction), summarizes prior activity, and checks required-section completeness.
Context + surfaced flags only; never prices, commits, executes, or decides suitability.

Usage: python calculate_or_transform.py rfq.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Preparation brief only; not a quote, a price, a firm bid/offer, or a commitment of "
              "the firm, and not a suitability determination. Nothing has been priced or executed.")


def _mask(cid):
    s = str(cid)
    return "****" + s[-4:] if len(s) >= 4 else s


def compute(doc: dict) -> dict:
    rfq = doc["rfq"]
    ctx = doc["client_context"]
    instr = rfq.get("instrument") or {}
    cid = rfq.get("client_id")
    flags, gaps = [], []

    def cite(field):
        return f"crm:client={_mask(cid)};{field}"

    # suitability/eligibility flags (surfaced, never decided)
    if (ctx.get("kyc_status") or "").lower() != "current":
        flags.append({"flag": "kyc_not_current", "detail": f"kyc_status={ctx.get('kyc_status')}",
                      "citation": cite("field=kyc_status")})
    restricted = {str(x).lower() for x in (ctx.get("restricted_products") or [])}
    if str(instr.get("type", "")).lower() in restricted:
        flags.append({"flag": "restricted_product", "detail": f"instrument type '{instr.get('type')}' on client's restricted list",
                      "citation": cite("field=restricted_products")})
    jrestricted = {str(x).lower() for x in (ctx.get("restricted_jurisdiction_products") or [])}
    if str(instr.get("type", "")).lower() in jrestricted:
        flags.append({"flag": "jurisdiction_restricted", "detail": f"instrument/jurisdiction ({ctx.get('jurisdiction')}) restricted",
                      "citation": cite("field=jurisdiction")})

    # sections built from available data
    available = {
        "instrument_summary": bool(instr.get("type")),
        "client_summary": bool(ctx.get("tier") or ctx.get("jurisdiction")),
        "suitability_review": bool(ctx.get("kyc_status")),
        "prior_activity": "prior_activity" in doc,
    }
    for sec in doc["checklist"].get("required_sections") or []:
        if not available.get(sec, False):
            gaps.append({"section": sec, "reason": "required section data not available",
                         "citation": f"checklist:section={sec}"})

    prior = doc.get("prior_activity") or []
    prior_summary = {"count": len(prior),
                     "instruments": sorted({p.get("instrument") for p in prior if p.get("instrument")})}

    disposition = "ready-for-review" if not flags and not gaps else "review-required"
    return {
        "brief_id": f"crfb-{rfq.get('rfq_id', 'UNKNOWN')}-0001",
        "rfq_id": rfq.get("rfq_id"), "client_masked": _mask(cid),
        "config_version": doc["checklist"].get("config_version"),
        "instrument_summary": {"type": instr.get("type"), "notional": instr.get("notional"),
                               "currency": instr.get("currency"), "side": instr.get("side")},
        "client_summary": {"tier": ctx.get("tier"), "jurisdiction": ctx.get("jurisdiction"),
                           "kyc_status": ctx.get("kyc_status")},
        "prior_activity_summary": prior_summary,
        "suitability_flags": flags,
        "completeness_gaps": gaps,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "rfq_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
