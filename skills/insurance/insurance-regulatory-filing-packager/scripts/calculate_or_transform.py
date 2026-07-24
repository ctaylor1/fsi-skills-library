#!/usr/bin/env python3
"""Deterministic filing-completeness checks for insurance-regulatory-filing-packager.

Tests a filing's components/exhibits against the approved checklist: required-component
completeness, required-exhibit presence, rate-change support, and effective-date notice lead.
Emits a gap-evidence packet with a review-only disposition. Never submits, approves, or sets a
rate — evidence only.

Usage: python calculate_or_transform.py filing.json | --selftest
"""
from __future__ import annotations
import datetime as _dt
import json, sys
from pathlib import Path

DISCLAIMER = ("Filing-gap evidence only; not a filing submission or a compliance certification. "
              "No filing has been submitted and no rate has been approved.")


def _date(s):
    try:
        return _dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def compute(doc: dict) -> dict:
    f = doc["filing"]
    ck = doc["checklist"]
    gaps = []

    def gap(rule, expected, found, ref):
        gaps.append({"rule": rule, "expected": expected, "found": found,
                     "citation": f"filing:{ref}"})

    present_types = {c.get("type") for c in doc.get("components", []) if c.get("present")}
    ref_by_type = {c.get("type"): c.get("source_ref", "?") for c in doc.get("components", [])}
    for rc in ck.get("required_components") or []:
        if rc not in present_types:
            gap("component_completeness", "present", "missing",
                f"component={rc};{ref_by_type.get(rc, 'not-attached')}")

    present_exh = {e.get("exhibit_id") for e in doc.get("exhibits", []) if e.get("present")}
    ref_by_exh = {e.get("exhibit_id"): e.get("source_ref", "?") for e in doc.get("exhibits", [])}
    for rx in ck.get("required_exhibits") or []:
        if rx not in present_exh:
            gap("exhibit_presence", "present", "missing",
                f"exhibit={rx};{ref_by_exh.get(rx, 'not-attached')}")

    # rate support
    if f.get("filing_type") == "rate" and ck.get("indicated_rate_change_pct") is not None:
        try:
            filed = float(f.get("proposed_rate_change_pct"))
            indicated = float(ck.get("indicated_rate_change_pct"))
            tol = float(ck.get("rate_tolerance_pct", 0.0))
            if filed > indicated + tol and "rate_justification" not in present_types:
                gap("rate_support", f"<= indicated {indicated}% (+{tol}%) or justification",
                    f"filed {filed}% with no rate_justification component",
                    f"filing={f.get('filing_id')};proposed_rate_change_pct")
        except (TypeError, ValueError):
            pass

    # effective-date notice lead
    d_as_of, d_eff = _date(f.get("as_of")), _date(f.get("effective_date"))
    min_notice = ck.get("min_notice_days")
    if d_as_of and d_eff and min_notice is not None:
        lead = (d_eff - d_as_of).days
        if lead < int(min_notice):
            gap("effective_notice", f">= {min_notice} days lead", f"{lead} days",
                f"filing={f.get('filing_id')};effective_date")

    disposition = "ready-for-review" if not gaps else "gaps-for-review"
    return {
        "packet_id": f"irfp-{f.get('filing_id', 'UNKNOWN')}-0001",
        "filing_id": f.get("filing_id"),
        "filing_type": f.get("filing_type"),
        "checklist_version": ck.get("config_version"),
        "checks_run": ["component_completeness", "exhibit_presence", "rate_support", "effective_notice"],
        "gaps": gaps,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "filing_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
