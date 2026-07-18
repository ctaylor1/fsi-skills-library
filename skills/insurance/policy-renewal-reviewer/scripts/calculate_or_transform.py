#!/usr/bin/env python3
"""Deterministic renewal-comparison engine for policy-renewal-reviewer.

Reads a renewal comparison file (expiring vs. proposed terms + loss history; see
validate_input.py), computes explainable **material-change findings**, attaches evidence +
citations to each fired finding, maps the fired set to a suggested review disposition band,
and drafts deterministic renewal-question stubs.

IMPORTANT: This produces explainable *findings, questions, and a triage suggestion* only. It
NEVER produces a renewal decision (renew / non-renew / decline), a price/rate, a coverage or
claim determination, or a customer commitment. The disposition mapping is deterministic and
documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py renewal.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "premium_change_pct": 10.0,        # material if abs(premium delta %) >= this
    "exposure_change_pct": 10.0,       # material if abs(exposure delta %) >= this
    "deductible_increase_pct": 20.0,   # material if deductible up >= this % (0 -> any increase)
    "loss_ratio_threshold": 0.70,      # incurred / (expiring premium * years) >= this
    "large_claim_incurred": 100000.0,  # a single claim at/above this is large
    "rate_exposure_tolerance_pct": 5.0,# premium% vs primary-exposure% divergence tolerance
    "primary_exposure_basis": "TIV",   # basis used for rate-vs-exposure divergence
    "min_years": 1,
}
DISCLAIMER = ("Comparison and review evidence only; not a renewal, pricing, or coverage "
              "determination. No renewal decision or notice has been issued.")
ESCALATORS = {"coverage_removed", "loss_ratio_flag"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _cite(term: dict, as_of: str) -> str:
    return f"pas:{term.get('source_ref', '?')}@{as_of}"


def _claim_cite(c: dict) -> str:
    return f"claims:{c.get('source_ref', '?')}@{c.get('date_of_loss', '?')}"


def _cov_map(term: dict) -> dict:
    out = {}
    for c in term.get("coverages") or []:
        if c.get("coverage"):
            out[str(c["coverage"])] = c
    return out


def _exp_map(term: dict) -> dict:
    out = {}
    for e in term.get("exposures") or []:
        if e.get("basis") is not None and _num(e.get("value")) is not None:
            out[str(e["basis"])] = _num(e["value"])
    return out


def _forms_map(term: dict) -> dict:
    out = {}
    for f in term.get("forms") or []:
        if f.get("form_id"):
            out[str(f["form_id"])] = str(f.get("edition", ""))
    return out


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = str(doc["as_of"])
    exp, prop = doc["expiring"], doc["proposed"]
    claims = doc.get("claims") or []
    findings, not_evaluable = [], []

    def add(name, fired, reason, evidence, basis, contribution):
        findings.append({"finding": name, "fired": bool(fired), "reason": reason,
                         "evidence": evidence, "basis": basis, "contribution": contribution})

    ep, pp = _num(exp.get("annual_premium")), _num(prop.get("annual_premium"))
    prem_pct = None

    # premium_change --------------------------------------------------------------
    if ep is not None and pp is not None and ep > 0:
        prem_pct = round((pp - ep) / ep * 100, 2)
        fired = abs(prem_pct) >= cfg["premium_change_pct"]
        add("premium_change", fired,
            f"annual premium {ep:.2f} -> {pp:.2f} ({prem_pct:+.2f}%), threshold {cfg['premium_change_pct']}%"
            if fired else f"premium change {prem_pct:+.2f}% within {cfg['premium_change_pct']}%",
            [{"term": "expiring", "annual_premium": ep, "citation": _cite(exp, as_of)},
             {"term": "proposed", "annual_premium": pp, "citation": _cite(prop, as_of)}],
            {"delta_pct": prem_pct, "threshold_pct": cfg["premium_change_pct"]},
            1 if fired else 0)
    else:
        not_evaluable.append({"finding": "premium_change", "why": "premium missing/zero on a term"})

    # exposure_change -------------------------------------------------------------
    exp_e, exp_p = _exp_map(exp), _exp_map(prop)
    common_exp = [b for b in exp_e if b in exp_p and exp_e[b] > 0]
    if common_exp:
        hits = []
        for b in common_exp:
            d = round((exp_p[b] - exp_e[b]) / exp_e[b] * 100, 2)
            if abs(d) >= cfg["exposure_change_pct"]:
                hits.append({"basis": b, "expiring": exp_e[b], "proposed": exp_p[b],
                             "delta_pct": d, "citation": _cite(prop, as_of)})
        add("exposure_change", bool(hits),
            f"{len(hits)} exposure basis change(s) exceed {cfg['exposure_change_pct']}%" if hits
            else f"no exposure basis change exceeds {cfg['exposure_change_pct']}%",
            hits, {"bases_compared": common_exp, "threshold_pct": cfg["exposure_change_pct"]},
            len(hits))
    else:
        not_evaluable.append({"finding": "exposure_change", "why": "no common exposure basis on both terms"})

    # limit_reduced ---------------------------------------------------------------
    cov_e, cov_p = _cov_map(exp), _cov_map(prop)
    lim_hits = []
    for name, c in cov_e.items():
        le, lp = _num(c.get("limit")), _num((cov_p.get(name) or {}).get("limit"))
        if name in cov_p and le is not None and lp is not None and lp < le:
            lim_hits.append({"coverage": name, "expiring_limit": le, "proposed_limit": lp,
                             "citation": _cite(prop, as_of)})
    add("limit_reduced", bool(lim_hits),
        f"{len(lim_hits)} coverage limit reduction(s)" if lim_hits else "no coverage limit reduced",
        lim_hits, {"coverages_compared": sorted(cov_e.keys() & cov_p.keys())}, len(lim_hits))

    # deductible_increased --------------------------------------------------------
    ded_hits = []
    for name, c in cov_e.items():
        de, dp = _num(c.get("deductible")), _num((cov_p.get(name) or {}).get("deductible"))
        if name in cov_p and de is not None and dp is not None and dp > de:
            pct = ((dp - de) / de * 100) if de > 0 else float("inf")
            if pct >= cfg["deductible_increase_pct"]:
                ded_hits.append({"coverage": name, "expiring_deductible": de, "proposed_deductible": dp,
                                 "delta_pct": round(pct, 2) if de > 0 else "new", "citation": _cite(prop, as_of)})
    add("deductible_increased", bool(ded_hits),
        f"{len(ded_hits)} deductible increase(s) >= {cfg['deductible_increase_pct']}%" if ded_hits
        else f"no deductible increase >= {cfg['deductible_increase_pct']}%",
        ded_hits, {"threshold_pct": cfg["deductible_increase_pct"]}, len(ded_hits))

    # coverage_removed (ESCALATOR) ------------------------------------------------
    removed = [{"coverage": n, "expiring_limit": _num(cov_e[n].get("limit")), "citation": _cite(exp, as_of)}
               for n in cov_e if n not in cov_p]
    add("coverage_removed", bool(removed),
        f"{len(removed)} coverage(s) on expiring term absent from proposed term" if removed
        else "no coverage removed", removed, {}, len(removed))

    # coverage_added --------------------------------------------------------------
    added = [{"coverage": n, "proposed_limit": _num(cov_p[n].get("limit")), "citation": _cite(prop, as_of)}
             for n in cov_p if n not in cov_e]
    add("coverage_added", bool(added),
        f"{len(added)} coverage(s) on proposed term not on expiring term" if added
        else "no coverage added", added, {}, len(added))

    # form_endorsement_change -----------------------------------------------------
    fe, fp = _forms_map(exp), _forms_map(prop)
    if fe or fp:
        changes = []
        for fid in sorted(set(fe) | set(fp)):
            if fid not in fp:
                changes.append({"form_id": fid, "change": "removed", "expiring_edition": fe[fid],
                                "citation": _cite(exp, as_of)})
            elif fid not in fe:
                changes.append({"form_id": fid, "change": "added", "proposed_edition": fp[fid],
                                "citation": _cite(prop, as_of)})
            elif fe[fid] != fp[fid]:
                changes.append({"form_id": fid, "change": "edition", "expiring_edition": fe[fid],
                                "proposed_edition": fp[fid], "citation": _cite(prop, as_of)})
        add("form_endorsement_change", bool(changes),
            f"{len(changes)} form/endorsement change(s) (edition/added/removed)" if changes
            else "no form/endorsement change", changes, {}, len(changes))
    else:
        not_evaluable.append({"finding": "form_endorsement_change", "why": "no forms listed on either term"})

    # loss_ratio_flag (ESCALATOR) -------------------------------------------------
    if claims and ep is not None and ep > 0:
        window_days = _num(doc.get("review_window_days")) or 365.0
        years = max(cfg["min_years"], round(window_days / 365.0)) or 1
        earned = ep * years
        total_incurred = sum(_num(c.get("incurred")) or 0.0 for c in claims)
        lr = total_incurred / earned if earned else 0.0
        fired = lr >= cfg["loss_ratio_threshold"]
        add("loss_ratio_flag", fired,
            f"incurred {total_incurred:.2f} / (premium {ep:.2f} x {years}y) = loss ratio {lr:.2f} "
            f">= {cfg['loss_ratio_threshold']}" if fired
            else f"loss ratio {lr:.2f} below {cfg['loss_ratio_threshold']}",
            [{"claim_id": c.get("claim_id"), "incurred": _num(c.get("incurred")),
              "status": c.get("status"), "citation": _claim_cite(c)} for c in claims],
            {"loss_ratio": round(lr, 4), "earned_basis": round(earned, 2), "years": years,
             "threshold": cfg["loss_ratio_threshold"]},
            1 if fired else 0)
    else:
        not_evaluable.append({"finding": "loss_ratio_flag", "why": "no claims or no expiring premium"})

    # large_open_claim ------------------------------------------------------------
    if claims:
        big = [c for c in claims if (_num(c.get("incurred")) or 0.0) >= cfg["large_claim_incurred"]
               or str(c.get("status", "")).lower() == "open"]
        add("large_open_claim", bool(big),
            f"{len(big)} large or open claim(s) in the review window" if big
            else "no large or open claim in the review window",
            [{"claim_id": c.get("claim_id"), "incurred": _num(c.get("incurred")),
              "status": c.get("status"), "cause": c.get("cause"), "citation": _claim_cite(c)} for c in big],
            {"large_claim_incurred": cfg["large_claim_incurred"]}, len(big))
    else:
        not_evaluable.append({"finding": "large_open_claim", "why": "no claims provided"})

    # rate_exposure_divergence ----------------------------------------------------
    pb = cfg["primary_exposure_basis"]
    if prem_pct is not None and pb in exp_e and pb in exp_p and exp_e[pb] > 0:
        exp_pct = round((exp_p[pb] - exp_e[pb]) / exp_e[pb] * 100, 2)
        divergence = round(abs(prem_pct - exp_pct), 2)
        fired = divergence >= cfg["rate_exposure_tolerance_pct"]
        add("rate_exposure_divergence", fired,
            f"premium change {prem_pct:+.2f}% vs {pb} exposure change {exp_pct:+.2f}% "
            f"= {divergence:.2f}pt divergence (>= {cfg['rate_exposure_tolerance_pct']}pt)" if fired
            else f"premium/exposure divergence {divergence:.2f}pt within tolerance",
            [{"premium_delta_pct": prem_pct, "exposure_basis": pb, "exposure_delta_pct": exp_pct,
              "divergence_pct": divergence, "citation": _cite(prop, as_of)}],
            {"tolerance_pct": cfg["rate_exposure_tolerance_pct"]}, 1 if fired else 0)
    else:
        not_evaluable.append({"finding": "rate_exposure_divergence",
                              "why": f"premium or primary exposure basis '{pb}' not evaluable on both terms"})

    fired_names = [f["finding"] for f in findings if f["fired"]]

    # deterministic disposition mapping (see references/domain-rules.md)
    if len(fired_names) >= 3 or (ESCALATORS & set(fired_names)):
        disposition = "Escalated"
    elif fired_names:
        disposition = "Review"
    else:
        disposition = "Routine"

    questions = _renewal_questions(findings)
    context = _context_prompts() if fired_names else []

    pid_digits = "".join(ch for ch in str(doc["policy_id"]) if ch.isdigit()) or "policy"
    return {
        "review_id": f"prr-{pid_digits}-{as_of}-0001",
        "policy_id": doc["policy_id"],
        "line_of_business": doc.get("line_of_business"),
        "as_of": as_of,
        "config_version": doc.get("config_version"),
        "terms": {"expiring_effective": exp.get("term_effective"),
                  "proposed_effective": prop.get("term_effective")},
        "findings": findings,
        "fired_findings": fired_names,
        "not_evaluable": not_evaluable,
        "suggested_disposition": disposition,
        "renewal_questions": questions,
        "context_prompts": context,
        "disclaimer": DISCLAIMER,
    }


def _renewal_questions(findings: list) -> list:
    """Deterministic, non-directive question stubs for the human to raise. No decisions."""
    tmpl = {
        "premium_change": "Confirm the drivers behind the premium change (rate action, exposure, loss experience, scheduled filing) for the account file.",
        "exposure_change": "Confirm the exposure basis change reflects real change versus a data correction, and that values are current.",
        "limit_reduced": "Confirm whether the coverage limit reduction is intended and whether it remains adequate to the insured's values.",
        "deductible_increased": "Confirm the deductible increase is agreed and clearly communicated to the insured.",
        "coverage_removed": "Confirm whether removing the coverage is intended and identify any resulting coverage gap to raise with a licensed professional.",
        "coverage_added": "Confirm the added coverage is intended and that terms and pricing are documented.",
        "form_endorsement_change": "Have the changed/added/removed forms reviewed for material wording impact (clause-level comparison).",
        "loss_ratio_flag": "Prepare the loss-ratio discussion (development, large-loss treatment, credibility) for the underwriter's review.",
        "large_open_claim": "Confirm the status and reserve adequacy of the large/open claim(s) with claims before the underwriter's review.",
        "rate_exposure_divergence": "Ask the underwriter to explain the divergence between premium change and exposure change.",
    }
    return [tmpl[f["finding"]] for f in findings if f["fired"] and f["finding"] in tmpl]


def _context_prompts() -> list:
    return [
        "A premium change may reflect exposure growth, inflation guard, a scheduled rate filing, or loss experience rather than a discretionary rate action.",
        "Form/edition changes may be mandatory bureau or state filings rather than carrier-initiated coverage restrictions.",
        "A limit or deductible change may be at the insured's request or reflect updated valuations.",
        "A loss ratio should be read with loss development, large-loss treatment, and credibility in mind.",
        "An exposure basis change may be a data correction rather than real growth or contraction.",
    ]


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "renewal_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
