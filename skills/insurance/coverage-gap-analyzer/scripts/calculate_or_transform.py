#!/usr/bin/env python3
"""Deterministic, explainable coverage-gap computation for coverage-gap-analyzer.

Reads a needs-and-policy file (see validate_input.py), compares each stated exposure
against the policy's coverages, limits, exclusions, deductibles, and endorsements, and
attaches evidence + dual citations (exposure source + policy source) to each fired gap.
It then maps the fired-gap set to a review-priority band.

IMPORTANT: This produces explainable *coverage gaps and a triage suggestion* only. It never
produces a coverage/eligibility/claim determination and never gives insurance or legal
advice. The priority mapping is deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py needs_and_policy.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "deductible_burden_ratio": 0.10,   # deductible > ratio * exposure value => burden flag
    "limit_shortfall_tolerance": 0.0,  # exposure value must exceed limit by > tolerance
}
DISCLAIMER = ("Coverage-gap analysis only; not a coverage, eligibility, or claim "
              "determination and not insurance or legal advice. Consult a licensed "
              "insurance professional before acting.")
# Escalating gap types — see references/domain-rules.md.
ESCALATORS = {"missing_coverage", "exclusion_match"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ex_cite(e: dict, as_of: str) -> str:
    return f"needs:{e.get('source_ref', '?')}@{as_of}"


def _pol_cite(ref) -> str:
    return f"policy:{ref}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = doc["as_of"]
    exposures = doc["exposures"]
    policy = doc["policy"]
    coverages = policy.get("coverages") or []
    cov_by_type = {}
    for c in coverages:
        cov_by_type.setdefault(str(c.get("type", "")).lower(), c)
    excluded = {str(x.get("peril", "")).lower(): x for x in (policy.get("exclusions") or [])}
    bought_back = {str(en.get("adds", "")).lower() for en in (policy.get("endorsements") or [])}
    present_endorsements = {str(en.get("adds", "")).lower() for en in (policy.get("endorsements") or [])}
    schedule_cite = _pol_cite(f"{policy.get('policy_number', '?')}#coverage-schedule")

    gaps: list[dict] = []
    not_evaluable: list[dict] = []

    def add(gap_type, fired, reason, evidence, basis):
        gaps.append({"gap_type": gap_type, "fired": bool(fired), "reason": reason,
                     "evidence": evidence, "basis": basis, "contribution": len(evidence) if fired else 0})

    # 1. missing_coverage (escalator) — a stated required_coverage has no matching policy coverage.
    ev = []
    evaluable = False
    for e in exposures:
        req = e.get("required_coverage")
        if not req:
            continue
        evaluable = True
        if str(req).lower() not in cov_by_type:
            ev.append({"exposure_id": e["exposure_id"], "required_coverage": req,
                       "citation": _ex_cite(e, as_of), "policy_citation": schedule_cite})
    if evaluable:
        add("missing_coverage", bool(ev),
            "stated exposure has no matching coverage type in the policy schedule" if ev
            else "every stated required_coverage has a matching coverage type", ev,
            {"coverage_types_present": sorted(cov_by_type)})
    else:
        not_evaluable.append({"gap_type": "missing_coverage", "why": "no exposure declares required_coverage"})

    # 2. exclusion_match (escalator) — an exposure peril is excluded with no buy-back endorsement.
    ev = []
    evaluable = False
    for e in exposures:
        peril = e.get("peril")
        if not peril:
            continue
        evaluable = True
        pk = str(peril).lower()
        if pk in excluded and pk not in bought_back:
            ev.append({"exposure_id": e["exposure_id"], "peril": peril,
                       "citation": _ex_cite(e, as_of),
                       "policy_citation": _pol_cite(excluded[pk].get("source_ref", "?"))})
    if evaluable:
        add("exclusion_match", bool(ev),
            "exposure peril is named in a policy exclusion with no buy-back endorsement" if ev
            else "no stated exposure peril matches an unbought-back exclusion", ev,
            {"exclusions": sorted(excluded), "buy_backs": sorted(bought_back)})
    else:
        not_evaluable.append({"gap_type": "exclusion_match", "why": "no exposure declares a peril"})

    # 3. limit_shortfall — exposure value exceeds the applicable coverage limit.
    ev = []
    tol = cfg["limit_shortfall_tolerance"]
    for e in exposures:
        req = e.get("required_coverage")
        val = _num(e.get("value"))
        cov = cov_by_type.get(str(req).lower()) if req else None
        if cov is None or val is None:
            continue
        lim = _num(cov.get("limit"))
        if lim is None:
            continue
        if val - lim > tol:
            ev.append({"exposure_id": e["exposure_id"], "exposure_value": val,
                       "coverage_type": cov.get("type"), "limit": lim, "shortfall": round(val - lim, 2),
                       "citation": _ex_cite(e, as_of), "policy_citation": _pol_cite(cov.get("source_ref", "?"))})
    add("limit_shortfall", bool(ev),
        "stated exposure value exceeds the matching coverage limit" if ev
        else "no stated exposure exceeds its matching coverage limit", ev,
        {"tolerance": tol})

    # 4. sublimit_shortfall — a category sublimit is below the exposure value.
    ev = []
    evaluable = any(c.get("sublimits") for c in coverages)
    for e in exposures:
        cat = e.get("sublimit_category")
        req = e.get("required_coverage")
        val = _num(e.get("value"))
        cov = cov_by_type.get(str(req).lower()) if req else None
        if not cat or cov is None or val is None:
            continue
        subs = cov.get("sublimits") or {}
        sub = _num(subs.get(cat))
        if sub is None:
            continue
        if val > sub:
            ev.append({"exposure_id": e["exposure_id"], "sublimit_category": cat, "sublimit": sub,
                       "exposure_value": val, "shortfall": round(val - sub, 2),
                       "citation": _ex_cite(e, as_of), "policy_citation": _pol_cite(cov.get("source_ref", "?"))})
    if evaluable:
        add("sublimit_shortfall", bool(ev),
            "stated exposure value exceeds the applicable category sublimit" if ev
            else "no stated exposure exceeds an applicable sublimit", ev, {})
    else:
        not_evaluable.append({"gap_type": "sublimit_shortfall", "why": "no coverage declares sublimits"})

    # 5. coinsurance_shortfall — insured limit below the coinsurance requirement.
    ev = []
    evaluable = any(_num(c.get("coinsurance")) is not None for c in coverages)
    for e in exposures:
        req = e.get("required_coverage")
        val = _num(e.get("value"))
        cov = cov_by_type.get(str(req).lower()) if req else None
        if cov is None or val is None:
            continue
        pct = _num(cov.get("coinsurance"))
        lim = _num(cov.get("limit"))
        if pct is None or lim is None:
            continue
        required = pct * val
        if lim < required:
            ev.append({"exposure_id": e["exposure_id"], "coinsurance": pct, "replacement_value": val,
                       "required_limit": round(required, 2), "carried_limit": lim,
                       "citation": _ex_cite(e, as_of), "policy_citation": _pol_cite(cov.get("source_ref", "?"))})
    if evaluable:
        add("coinsurance_shortfall", bool(ev),
            "carried limit is below the coinsurance requirement (penalty exposure)" if ev
            else "carried limit meets the coinsurance requirement", ev, {})
    else:
        not_evaluable.append({"gap_type": "coinsurance_shortfall", "why": "no coverage declares a coinsurance clause"})

    # 6. deductible_burden — deductible exceeds a configured share of the exposure value (informational).
    ev = []
    ratio = cfg["deductible_burden_ratio"]
    for e in exposures:
        req = e.get("required_coverage")
        val = _num(e.get("value"))
        cov = cov_by_type.get(str(req).lower()) if req else None
        if cov is None or val is None or val <= 0:
            continue
        ded = _num(cov.get("deductible"))
        if ded is None:
            continue
        if ded > ratio * val:
            ev.append({"exposure_id": e["exposure_id"], "deductible": ded, "exposure_value": val,
                       "share": round(ded / val, 4), "threshold_ratio": ratio,
                       "citation": _ex_cite(e, as_of), "policy_citation": _pol_cite(cov.get("source_ref", "?"))})
    add("deductible_burden", bool(ev),
        f"deductible exceeds {ratio:.0%} of the stated exposure value" if ev
        else f"no deductible exceeds {ratio:.0%} of its exposure value", ev, {"threshold_ratio": ratio})

    # 7. endorsement_gap — a recommended endorsement for an exposure is not attached.
    ev = []
    evaluable = any(e.get("recommended_endorsement") for e in exposures)
    for e in exposures:
        rec = e.get("recommended_endorsement")
        if not rec:
            continue
        if str(rec).lower() not in present_endorsements:
            ev.append({"exposure_id": e["exposure_id"], "recommended_endorsement": rec,
                       "citation": _ex_cite(e, as_of), "policy_citation": schedule_cite})
    if evaluable:
        add("endorsement_gap", bool(ev),
            "a recommended endorsement for a stated exposure is not attached to the policy" if ev
            else "every recommended endorsement is attached", ev,
            {"endorsements_present": sorted(present_endorsements)})
    else:
        not_evaluable.append({"gap_type": "endorsement_gap", "why": "no exposure declares a recommended_endorsement"})

    fired_names = [g["gap_type"] for g in gaps if g["fired"]]
    # deterministic priority mapping (see references/domain-rules.md)
    if len(fired_names) >= 3 or (ESCALATORS & set(fired_names)):
        priority = "Elevated"
    elif len(fired_names) >= 1:
        priority = "Review"
    else:
        priority = "Informational"

    review_prompts = []
    if fired_names:
        review_prompts = [
            "Stated exposure values are client-provided and unverified; confirm replacement cost vs. actual-cash-value basis.",
            "Other policies (umbrella, standalone/NFIP flood, scheduled personal-articles, auto) may already cover the exposure.",
            "A high deductible or a lower limit may be an intentional premium trade-off the client chose.",
            "Blanket, agreed-value, or extended-replacement-cost provisions may apply instead of scheduled limits.",
            "Statutory minimums, lender, or lease requirements may govern the required limits in this jurisdiction.",
        ]

    return {
        "analysis_id": f"cga-{str(doc['profile_id']).replace('*', '')}-{as_of}-0001",
        "profile_id": doc["profile_id"],
        "as_of": as_of,
        "jurisdiction": doc.get("jurisdiction"),
        "config_version": doc.get("config_version"),
        "policy_number": policy.get("policy_number"),
        "gaps": gaps,
        "fired_gaps": fired_names,
        "not_evaluable": not_evaluable,
        "review_priority": priority,
        "review_prompts": review_prompts,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "needs_and_policy_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
