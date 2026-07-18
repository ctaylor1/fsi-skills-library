#!/usr/bin/env python3
"""Deterministic normalization, reconciliation, gap detection, and appetite triage for
submission-intake-triager.

Reads a broker-submission file (see validate_input.py), normalizes platform-extracted
fields to canonical units, reconciles the same field across documents, detects missing
required fields (seeding follow-up requests), applies the approved appetite rules, and maps
the fired-rule set to a **routing recommendation band**. Emits a machine-readable triage
core the SKILL wraps in a plain-language packet.

IMPORTANT: This produces normalized evidence + a routing *recommendation* only. It never
binds, quotes, prices, declines, or issues coverage, and it never closes the submission.
Every band — including "In-appetite" — routes to a human underwriter. The mapping is
deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py submission.json | --selftest
Prints the triage JSON to stdout.
"""
from __future__ import annotations
import json, re, sys
from collections import defaultdict
from pathlib import Path

DEFAULT_CONFIG = {
    "appetite_states": ["CA", "TX", "NY", "IL", "FL", "WA", "AZ", "GA", "NC", "OH"],
    "excluded_classes": ["1389", "2911", "7996"],
    "max_tiv_ceiling": 100000000.0,
    "refer_tiv_threshold": 50000000.0,
    "loss_ratio_refer": 0.60,
    "cat_refer_zones": ["tier1_wind", "high_wildfire", "seismic_high"],
    "required_fields": ["insured_name", "insured_state", "class_code", "effective_date",
                        "total_insured_value", "annual_revenue", "prior_loss_ratio",
                        "building_count", "catastrophe_zone"],
    "critical_fields": ["insured_state", "class_code", "effective_date", "total_insured_value"],
    "reconcile_tolerance": 0.0,
}
DISCLAIMER = ("Triage evidence and routing recommendation only; not a bind, quote, price, "
              "or coverage decision. A licensed underwriter adjudicates; no coverage has "
              "been bound, quoted, priced, declined, or issued.")

# Routing recommendation bands (recommendations for a human underwriter — never decisions).
BAND_OUT = "Out-of-appetite (recommend decline — underwriter adjudicates)"
BAND_INCOMPLETE = "Incomplete — pending broker information"
BAND_REFER = "Refer to underwriter"
BAND_IN = "In-appetite — route to underwriter for standard handling"

# Per-field document authority (highest first); falls back to DEFAULT_AUTHORITY.
DEFAULT_AUTHORITY = ["acord", "sov_spreadsheet", "loss_run", "email", "pdf", "other"]
FIELD_AUTHORITY = {
    "total_insured_value": ["sov_spreadsheet", "acord", "email", "pdf", "other"],
    "prior_loss_ratio": ["loss_run", "acord", "email", "pdf", "other"],
    "loss_count": ["loss_run", "acord", "email", "pdf", "other"],
}
NUMERIC_FIELDS = {"total_insured_value", "annual_revenue", "prior_loss_ratio",
                  "building_count", "loss_count"}
FOLLOWUP_TEMPLATES = {
    "insured_state": "Confirm the insured's primary risk state (2-letter code).",
    "class_code": "Provide the governing class/SIC/NAICS code for the operations.",
    "effective_date": "Confirm the requested policy effective date.",
    "total_insured_value": "Provide the total insured value supported by a current statement of values.",
    "annual_revenue": "Provide the insured's annual revenue.",
    "prior_loss_ratio": "Provide the 5-year loss runs so prior loss ratio can be established.",
    "building_count": "Provide the number of insured buildings/locations.",
    "catastrophe_zone": "Confirm catastrophe exposure zone(s) for the scheduled locations.",
}


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower().replace(",", "").replace("$", "").replace("%", "")
    mult = 1.0
    if s.endswith("k"):
        mult, s = 1e3, s[:-1]
    elif s.endswith("m"):
        mult, s = 1e6, s[:-1]
    elif s.endswith("b"):
        mult, s = 1e9, s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


STATE_NAMES = {"california": "CA", "texas": "TX", "new york": "NY", "florida": "FL",
               "illinois": "IL", "washington": "WA", "arizona": "AZ", "georgia": "GA",
               "north carolina": "NC", "ohio": "OH"}


def _normalize(field: str, value):
    if field in NUMERIC_FIELDS:
        return _num(value)
    if field == "insured_state":
        s = str(value).strip()
        return STATE_NAMES.get(s.lower(), s.upper())
    if field == "catastrophe_zone":
        return str(value).strip().lower()
    return str(value).strip()


def _cite(row: dict) -> str:
    return f"{row['doc_type']}:{row['source_ref']}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    docs = {d["doc_id"]: d for d in doc.get("documents", [])}

    # Group extracted values per canonical field, joining doc_type from documents[].
    groups: dict[str, list] = defaultdict(list)
    for f in doc.get("extracted_fields", []):
        dt = f.get("doc_type") or (docs.get(f.get("doc_id"), {}) or {}).get("doc_type") or "other"
        groups[f["field"]].append({
            "raw": f.get("value"),
            "value": _normalize(f["field"], f.get("value")),
            "doc_id": f.get("doc_id"),
            "doc_type": dt,
            "source_ref": f.get("source_ref"),
            "citation": f"{dt}:{f.get('source_ref')}",
        })

    # Reconciliation + canonical selection (deterministic authority order).
    reconciliation, canon = [], {}
    tol = float(cfg.get("reconcile_tolerance", 0.0))
    for field, rows in groups.items():
        order = FIELD_AUTHORITY.get(field, DEFAULT_AUTHORITY)
        rows_sorted = sorted(rows, key=lambda r: order.index(r["doc_type"]) if r["doc_type"] in order else len(order))
        best = rows_sorted[0]
        canon[field] = best["value"]
        # mismatch detection
        norm_values = [r["value"] for r in rows]
        if len(rows) == 1:
            status = "single_source"
        elif field in NUMERIC_FIELDS:
            nums = [v for v in norm_values if isinstance(v, (int, float))]
            hi, lo = max(nums), min(nums)
            status = "mismatch" if (hi - lo) > tol * max(abs(hi), 1.0) else "match"
        else:
            status = "match" if len({str(v) for v in norm_values}) == 1 else "mismatch"
        reconciliation.append({
            "field": field,
            "canonical_value": best["value"],
            "canonical_source": best["citation"],
            "status": status,
            "values": [{"value": r["value"], "raw": r["raw"], "doc_id": r["doc_id"],
                        "doc_type": r["doc_type"], "citation": r["citation"]} for r in rows],
        })
    reconciliation.sort(key=lambda r: r["field"])

    def evidence_for(field):
        for r in reconciliation:
            if r["field"] == field:
                return [{"field": field, "value": v["value"], "citation": v["citation"]}
                        for v in r["values"]]
        return []

    # Gap detection + follow-up drafting.
    critical = set(cfg["critical_fields"])
    gaps, follow_ups = [], []
    for rf in cfg["required_fields"]:
        present = rf in groups and canon.get(rf) not in (None, "")
        if not present:
            sev = "critical" if rf in critical else "standard"
            gaps.append({"field": rf, "severity": sev,
                         "why": "not extracted from any submission document"})
            follow_ups.append({"field": rf, "severity": sev,
                               "request": FOLLOWUP_TEMPLATES.get(rf, f"Provide {rf.replace('_', ' ')}.")})

    # Appetite rules (deterministic; each cites the evidence behind its canonical value).
    findings = []

    def add(rule, status, reason, field, config_used):
        findings.append({"rule": rule, "status": status, "reason": reason,
                         "evidence": evidence_for(field) if status in ("refer", "out") else [],
                         "config_used": config_used})

    st = canon.get("insured_state")
    if st is None:
        add("state_in_appetite", "not_evaluable", "insured_state not available", "insured_state",
            {"appetite_states": cfg["appetite_states"]})
    elif st in cfg["appetite_states"]:
        add("state_in_appetite", "pass", f"state {st} is within the approved writing territory",
            "insured_state", {"appetite_states": cfg["appetite_states"]})
    else:
        add("state_in_appetite", "out", f"state {st} is outside the approved writing territory",
            "insured_state", {"appetite_states": cfg["appetite_states"]})

    cc = canon.get("class_code")
    if cc is None:
        add("class_in_appetite", "not_evaluable", "class_code not available", "class_code",
            {"excluded_classes": cfg["excluded_classes"]})
    elif str(cc) in {str(x) for x in cfg["excluded_classes"]}:
        add("class_in_appetite", "out", f"class code {cc} is on the excluded-class list",
            "class_code", {"excluded_classes": cfg["excluded_classes"]})
    else:
        add("class_in_appetite", "pass", f"class code {cc} is not on the excluded-class list",
            "class_code", {"excluded_classes": cfg["excluded_classes"]})

    tiv = canon.get("total_insured_value")
    tcfg = {"refer_tiv_threshold": cfg["refer_tiv_threshold"], "max_tiv_ceiling": cfg["max_tiv_ceiling"]}
    if not isinstance(tiv, (int, float)):
        add("tiv_within_capacity", "not_evaluable", "total_insured_value not available", "total_insured_value", tcfg)
    elif tiv > cfg["max_tiv_ceiling"]:
        add("tiv_within_capacity", "out",
            f"TIV {tiv:.0f} exceeds the capacity ceiling {cfg['max_tiv_ceiling']:.0f}", "total_insured_value", tcfg)
    elif tiv > cfg["refer_tiv_threshold"]:
        add("tiv_within_capacity", "refer",
            f"TIV {tiv:.0f} exceeds the auto-route threshold {cfg['refer_tiv_threshold']:.0f}", "total_insured_value", tcfg)
    else:
        add("tiv_within_capacity", "pass",
            f"TIV {tiv:.0f} is within the auto-route threshold {cfg['refer_tiv_threshold']:.0f}", "total_insured_value", tcfg)

    lr = canon.get("prior_loss_ratio")
    lcfg = {"loss_ratio_refer": cfg["loss_ratio_refer"]}
    if not isinstance(lr, (int, float)):
        add("loss_ratio_within_threshold", "not_evaluable", "prior_loss_ratio not available", "prior_loss_ratio", lcfg)
    elif lr > cfg["loss_ratio_refer"]:
        add("loss_ratio_within_threshold", "refer",
            f"prior loss ratio {lr:.2f} exceeds the referral threshold {cfg['loss_ratio_refer']:.2f}", "prior_loss_ratio", lcfg)
    else:
        add("loss_ratio_within_threshold", "pass",
            f"prior loss ratio {lr:.2f} is within the referral threshold {cfg['loss_ratio_refer']:.2f}", "prior_loss_ratio", lcfg)

    cz = canon.get("catastrophe_zone")
    ccfg = {"cat_refer_zones": cfg["cat_refer_zones"]}
    if cz is None:
        add("catastrophe_exposure", "not_evaluable", "catastrophe_zone not available", "catastrophe_zone", ccfg)
    elif cz in {str(x).lower() for x in cfg["cat_refer_zones"]}:
        add("catastrophe_exposure", "refer",
            f"catastrophe zone '{cz}' is a referral zone requiring accumulation review", "catastrophe_zone", ccfg)
    else:
        add("catastrophe_exposure", "pass",
            f"catastrophe zone '{cz}' is not a referral zone", "catastrophe_zone", ccfg)

    statuses = [f["status"] for f in findings]
    fired_flags = [f["rule"] for f in findings if f["status"] in ("refer", "out")]
    critical_gap = any(g["severity"] == "critical" for g in gaps)

    # Deterministic routing recommendation (see references/domain-rules.md).
    if "out" in statuses:
        band = BAND_OUT
    elif critical_gap:
        band = BAND_INCOMPLETE
    elif "refer" in statuses:
        band = BAND_REFER
    else:
        band = BAND_IN

    return {
        "triage_id": f"sit-{doc['submission_id']}-0001",
        "submission_id": doc["submission_id"],
        "received_date": doc["received_date"],
        "config_version": doc.get("config_version"),
        "line_of_business": doc.get("line_of_business"),
        "reconciliation": reconciliation,
        "gaps": gaps,
        "follow_up_requests": follow_ups,
        "appetite_findings": findings,
        "fired_flags": fired_flags,
        "routing_recommendation": band,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "submission_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
