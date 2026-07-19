#!/usr/bin/env python3
"""Deterministic, explainable customer-risk-rating recomputation for
customer-risk-rating-reviewer.

Reads a risk-rating case file (see validate_input.py), recomputes the model-derived
(inherent) customer risk band from the approved weighted-factor methodology, challenges it
against the rating of record, evaluates documented overrides, trigger events, and factor
data quality, and emits a machine-readable core of cited FINDINGS plus a recommended
review outcome for a human adjudicator.

IMPORTANT: This produces a recomputation, cited findings, and a *recommendation* only. It
never changes a risk rating, approves an override, disposes of a trigger, closes a case, or
files anything. `adjudication_required` is always true. The band mapping and the review-
outcome precedence are deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py risk_case.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

# Approved methodology defaults. In deployment these come from a versioned config contract
# (see references/source-map.md); they are never tuned to an individual customer.
DEFAULT_CONFIG = {
    "factor_catalog": {
        "customer_type":        {"max_weight": 15, "scale_max": 5, "required": True},
        "geography":            {"max_weight": 20, "scale_max": 5, "required": True},
        "product_channel":      {"max_weight": 15, "scale_max": 5, "required": True},
        "pep_status":           {"max_weight": 15, "scale_max": 5, "required": True, "floor_at_max": "High"},
        "sanctions_nexus":      {"max_weight": 20, "scale_max": 5, "required": True, "floor_at_max": "Prohibited"},
        "adverse_media":        {"max_weight": 10, "scale_max": 5, "required": False},
        "transaction_behavior": {"max_weight": 5,  "scale_max": 5, "required": False},
    },
    # Ascending max_score cut-offs over a 0..100 percentage-of-max score.
    "band_thresholds": [
        {"band": "Low", "max_score": 30},
        {"band": "Medium", "max_score": 60},
        {"band": "High", "max_score": 85},
        {"band": "Prohibited", "max_score": 100},
    ],
    "band_order": ["Low", "Medium", "High", "Prohibited"],
    "staleness_days": 365,        # factor observed_date older than this = stale (data quality)
    "override_max_days": 365,     # informational; expiry_date on the override governs validity
    "trigger_types_requiring_review": [
        "sanctions_hit", "pep_change", "adverse_media", "jurisdiction_change", "monitoring_alert",
    ],
}

DISCLAIMER = (
    "Recommendation and cited evidence only; not a customer risk-rating decision. This review "
    "does not modify the rating of record, validate or approve any override, dispose of any "
    "trigger, close any case, or make any regulatory filing or system-of-record change. A "
    "qualified compliance officer must adjudicate every finding before any rating or case action."
)


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def band_for_score(pct: float, thresholds: list) -> str:
    for t in thresholds:
        if pct <= t["max_score"]:
            return t["band"]
    return thresholds[-1]["band"]


def max_band(a, b, order: list) -> str:
    """Return the more severe of two bands (b may be None)."""
    if not b:
        return a
    if not a:
        return b
    return a if order.index(a) >= order.index(b) else b


def expected_outcome(finding_types: set, floor_band, recomputed_band, record_band) -> str:
    """Deterministic review-outcome precedence (documented in domain-rules.md).

    escalate > remediate > re-rate > align. Kept byte-identical in validate_output.py.
    """
    if floor_band == "Prohibited" or (finding_types & {"expired_override", "undocumented_override", "unassessed_trigger"}):
        return "Escalate-For-Adjudication"
    if "missing_required_factor" in finding_types:
        return "Remediate-Data-First"
    if recomputed_band != record_band:
        return "Re-Rate-Recommended"
    return "Align-No-Change"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    catalog = cfg["factor_catalog"]
    order = cfg["band_order"]
    thresholds = cfg["band_thresholds"]
    as_of = _parse_date(doc["as_of"])
    version = doc.get("methodology_version")
    record = doc.get("rating_of_record") or {}
    record_band = record.get("band")

    provided = {f["factor"]: f for f in doc.get("factors", []) if f.get("factor")}
    findings = []

    def add_finding(ftype, severity, description, evidence):
        findings.append({
            "finding_id": f"CRR-F{len(findings) + 1:02d}",
            "type": ftype, "severity": severity,
            "description": description, "evidence": evidence,
        })

    # --- Score the provided factors (percentage of provided max weight) -------------------
    contribution, provided_weight, floor_band = 0.0, 0.0, None
    factor_detail = []
    for name, spec in catalog.items():
        f = provided.get(name)
        if not f:
            if spec.get("required"):
                add_finding("missing_required_factor", "high",
                            f"required factor '{name}' is absent; recomputation is low-confidence until supplied",
                            [{"citation": f"methodology:{version};required_factor={name}"}])
            continue
        rv = _num(f.get("risk_value"))
        w = _num(f.get("weight"))
        if rv is None or w is None:
            continue
        smax = float(spec.get("scale_max", 5)) or 5.0
        c = (rv / smax) * w
        contribution += c
        provided_weight += w
        factor_detail.append({"factor": name, "risk_value": rv, "weight": w,
                              "contribution": round(c, 2), "citation": _cite(f)})
        # mandatory floor when a floor-bearing factor is at its scale maximum
        if spec.get("floor_at_max") and rv >= smax:
            floor_band = max_band(floor_band, spec["floor_at_max"], order)
            add_finding("mandatory_floor", "high",
                        f"factor '{name}' is at maximum risk and forces a rating floor of "
                        f"'{spec['floor_at_max']}' under the approved methodology",
                        [{"factor": name, "risk_value": rv, "floor": spec["floor_at_max"], "citation": _cite(f)}])
        # staleness
        od = f.get("observed_date")
        if od and (as_of - _parse_date(od)).days > cfg["staleness_days"]:
            add_finding("stale_factor", "medium",
                        f"factor '{name}' was last observed {od}, older than the "
                        f"{cfg['staleness_days']}-day freshness window; refresh before relying on it",
                        [{"factor": name, "observed_date": od, "citation": _cite(f)}])

    score_pct = round(100.0 * contribution / provided_weight, 2) if provided_weight else 0.0
    score_band = band_for_score(score_pct, thresholds)
    recomputed_band = max_band(score_band, floor_band, order)

    # --- Challenge the rating of record ---------------------------------------------------
    if record_band and recomputed_band and record_band != recomputed_band:
        dist = abs(order.index(recomputed_band) - order.index(record_band))
        direction = "under-rated" if order.index(recomputed_band) > order.index(record_band) else "over-rated"
        add_finding("rating_discrepancy", "high" if dist >= 2 else "medium",
                    f"recomputed band '{recomputed_band}' differs from the rating of record "
                    f"'{record_band}' by {dist} band(s); the customer appears {direction}",
                    [{"recomputed_band": recomputed_band, "record_band": record_band,
                      "score_pct": score_pct, "citation": _cite(record, system="kyc")}])

    # --- Evaluate documented overrides ----------------------------------------------------
    for i, ov in enumerate(doc.get("overrides") or []):
        cite = _cite(ov, system="kyc", fallback=f"override_index={i}")
        missing = [k for k in ("approver_role", "rationale") if not str(ov.get(k) or "").strip()]
        if missing:
            add_finding("undocumented_override", "high",
                        f"override lacks {', '.join(missing)}; an undocumented override cannot support "
                        f"the rating of record",
                        [{"override": ov.get("from_band"), "to": ov.get("to_band"),
                          "missing": missing, "citation": cite}])
        exp = ov.get("expiry_date")
        if exp and _parse_date(exp) < as_of:
            add_finding("expired_override", "high",
                        f"override ({ov.get('from_band')} -> {ov.get('to_band')}) expired {exp}; the rating "
                        f"of record may be relying on a lapsed override",
                        [{"override": ov.get("from_band"), "to": ov.get("to_band"),
                          "expiry_date": exp, "approver_role": ov.get("approver_role"), "citation": cite}])

    # --- Evaluate trigger events ----------------------------------------------------------
    review_types = set(cfg["trigger_types_requiring_review"])
    trigger_routes = set()
    for i, ev in enumerate(doc.get("trigger_events") or []):
        ttype, sev = ev.get("type"), str(ev.get("severity", "")).lower()
        cite = _cite(ev, system="tm", fallback=f"trigger_index={i}")
        if ttype in review_types and not ev.get("assessed") and sev in ("high", "medium"):
            add_finding("unassessed_trigger", "high" if sev == "high" else "medium",
                        f"trigger event '{ttype}' ({ev.get('date')}, severity {sev}) has not been assessed "
                        f"and may warrant a re-rating or enhanced due diligence",
                        [{"type": ttype, "date": ev.get("date"), "severity": sev, "citation": cite}])
            trigger_routes.add(ttype)

    # --- Deterministic review outcome -----------------------------------------------------
    ftypes = {f["type"] for f in findings}
    outcome = expected_outcome(ftypes, floor_band, recomputed_band, record_band)

    # --- Recommended next steps (human/specialist routing; never an action) ---------------
    steps = []
    if floor_band == "Prohibited" or "sanctions_hit" in trigger_routes:
        steps.append("Route the sanctions nexus/potential match to sanctions-match-adjudicator (specialist + human).")
    if recomputed_band in ("High", "Prohibited") or (floor_band in ("High", "Prohibited")):
        steps.append("Route to enhanced-due-diligence-packager to assemble source-of-funds/wealth and ownership evidence.")
    if "adverse_media" in trigger_routes:
        steps.append("Route the adverse-media trigger to adverse-media-investigator for entity-resolved assessment.")
    if "monitoring_alert" in trigger_routes:
        steps.append("Route the monitoring alert to transaction-monitoring-alert-investigator.")
    if "missing_required_factor" in ftypes:
        steps.append("Return CDD data gaps to kyc-customer-due-diligence-screener / the case owner to remediate before adjudication.")
    steps.append("A qualified compliance officer / MLRO adjudicates the rating; this skill does not change it.")

    return {
        "review_id": f"crr-{str(doc.get('customer_id','')).replace('*','')}-{doc['as_of']}-0001",
        "customer_id": doc.get("customer_id"),
        "as_of": doc["as_of"],
        "methodology_version": version,
        "rating_of_record": {"band": record_band, "effective_date": record.get("effective_date")},
        "score_pct": score_pct,
        "score_band": score_band,
        "floor_band": floor_band,
        "band_thresholds": thresholds,
        "band_order": order,
        "recomputed_band": recomputed_band,
        "recommended_band": recomputed_band,
        "factor_detail": factor_detail,
        "findings": findings,
        "recommended_review_outcome": outcome,
        "recommended_next_steps": steps,
        "adjudication_required": True,
        "disclaimer": DISCLAIMER,
    }


def _cite(row: dict, system: str = "kyc", fallback: str = "?") -> str:
    ref = row.get("source_ref") or fallback
    date = row.get("observed_date") or row.get("date") or row.get("effective_date") or row.get("approved_date")
    return f"{system}:{ref}" + (f"@{date}" if date else "")


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "risk_case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
