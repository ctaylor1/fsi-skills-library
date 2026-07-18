#!/usr/bin/env python3
"""Deterministic credit-memo drafting engine for credit-memo-drafter.

Consumes a validated credit-memo request bundle and produces a DRAFT memorandum object:
computes repayment/credit metrics (DSCR, leverage, LTV), ties the recomputed ratios back to
the approved financial spread, checks policy-requirement coverage and covenant headroom,
records exceptions with their mitigants, assembles the required template sections with
source citations, and records the REQUIRED (still pending) human approvals.

It never approves, declines, books, funds, files, waives an exception, or writes any system
of record. Every figure is derived from a cited input; anything unsupported is surfaced in
`unsupported_assertions` rather than asserted. Output is decision-support for a human
underwriter.

Usage: python calculate_or_transform.py request.json | --selftest
Prints the draft-memo JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_POLICY = {
    "dscr_floor": 1.20,
    "leverage_cap": 4.00,
    "tie_out_tolerance": 0.01,          # absolute tolerance on recomputed ratios
    "large_credit_threshold": 5_000_000,  # adds Credit Committee to approvals
    "base_approvers": ["Underwriter", "Credit Officer"],
}

REQUIRED_SECTIONS = [
    "borrower_overview", "facility_summary", "financial_analysis", "repayment_analysis",
    "collateral_analysis", "risk_rating", "covenants", "policy_exceptions", "recommendation",
]

DISPOSITION = "draft-for-underwriter-review"
STANDING_NOTE = (
    "Draft credit memorandum for human underwriting adjudication only. No credit decision "
    "has been made; no facility has been approved, declined, booked, funded, or disbursed; "
    "and nothing has been filed or written to a system of record."
)


def _r(x, n=2):
    return round(float(x), n)


def _section(content, citations):
    return {"content": content, "citations": list(citations)}


def compute_metrics(doc, pol):
    spread = doc.get("financial_spread") or {}
    cfads = float(spread.get("cfads") or 0)
    tds = float(spread.get("total_debt_service") or 0)
    total_debt = float(spread.get("total_debt") or 0)
    ebitda = float(spread.get("ebitda") or 0)

    dscr = _r(cfads / tds) if tds > 0 else None
    leverage = _r(total_debt / ebitda) if ebitda > 0 else None

    exposure = sum(float(f.get("amount") or 0) for f in (doc.get("facilities") or []))
    collateral = doc.get("collateral") or []
    appraised = sum(float(c.get("appraised_value") or 0) for c in collateral)
    lendable = sum(float(c.get("appraised_value") or 0) * float(c.get("advance_rate") or 0)
                   for c in collateral)
    ltv = _r(exposure / appraised, 4) if appraised > 0 else None
    advance_coverage = _r(lendable / exposure, 4) if exposure > 0 else None
    collateral_shortfall = bool(collateral) and lendable < exposure

    return {
        "dscr": dscr, "dscr_floor": pol["dscr_floor"],
        "dscr_below_floor": (dscr is not None and dscr < pol["dscr_floor"]),
        "leverage": leverage, "leverage_cap": pol["leverage_cap"],
        "leverage_above_cap": (leverage is not None and leverage > pol["leverage_cap"]),
        "total_exposure": _r(exposure, 2),
        "collateral_appraised": _r(appraised, 2),
        "collateral_lendable": _r(lendable, 2),
        "ltv": ltv, "advance_coverage": advance_coverage,
        "collateral_shortfall": collateral_shortfall,
    }


def tie_out(doc, metrics, pol):
    """Recompute DSCR/leverage from spread primitives and compare to the ratios the approved
    spread reported. Out-of-tolerance => tie-out break (financial section not fully supported)."""
    reported = ((doc.get("financial_spread") or {}).get("ratios") or {})
    tol = pol["tie_out_tolerance"]
    diffs, broken = [], False
    for name, computed in (("dscr", metrics["dscr"]), ("leverage", metrics["leverage"])):
        rep = reported.get(name)
        if rep is None or computed is None:
            continue
        d = abs(float(rep) - float(computed))
        if d > tol:
            broken = True
            diffs.append({"ratio": name, "spread_reported": float(rep),
                          "recomputed": computed, "abs_diff": _r(d, 4), "tolerance": tol})
    return {"status": "break" if broken else "tie", "diffs": diffs}


def covenant_table(doc):
    rows = []
    for c in (doc.get("covenants") or []):
        thr = float(c.get("threshold"))
        met = float(c.get("tested_metric"))
        headroom = _r(met - thr, 4) if c.get("type") == "min" else _r(thr - met, 4)
        rows.append({
            "covenant_id": c.get("covenant_id"), "type": c.get("type"),
            "threshold": thr, "tested_metric": met, "headroom": headroom,
            "breach_at_inception": headroom < 0, "citation": c.get("source_ref"),
        })
    return rows


def exceptions_with_mitigants(doc):
    out, missing = [], []
    for e in (doc.get("exceptions") or []):
        rec = {"exception_id": e.get("exception_id"), "policy_ref": e.get("policy_ref"),
               "description": e.get("description"), "mitigant": e.get("mitigant")}
        out.append(rec)
        if not e.get("mitigant"):
            missing.append(e.get("exception_id"))
    return out, missing


def policy_coverage(doc):
    reqs = doc.get("policy_requirements") or []
    ex_ids = {e.get("exception_id") for e in (doc.get("exceptions") or [])
              if e.get("mitigant")}
    gaps, addressed = [], 0
    for p in reqs:
        if not p.get("applies"):
            continue
        ok = bool(p.get("addressed_section")) or (p.get("exception_ref") in ex_ids)
        if ok:
            addressed += 1
        else:
            gaps.append(p.get("requirement_id"))
    applicable = sum(1 for p in reqs if p.get("applies"))
    return {"applicable": applicable, "addressed": addressed, "gaps": gaps}


def build_draft(doc, pol):
    metrics = compute_metrics(doc, pol)
    tie = tie_out(doc, metrics, pol)
    cov_rows = covenant_table(doc)
    exc, exc_missing_mit = exceptions_with_mitigants(doc)
    coverage = policy_coverage(doc)

    borrower = doc.get("borrower") or {}
    spread = doc.get("financial_spread") or {}
    rr = doc.get("risk_rating") or {}
    unsupported = []

    def cite(*refs):
        return [r for r in refs if r]

    # --- sections -----------------------------------------------------------------------
    sections = {}
    sections["borrower_overview"] = _section(
        f"Obligor {borrower.get('obligor_id')} ({borrower.get('name_masked','[masked]')}), "
        f"{borrower.get('entity_type','?')} in {borrower.get('industry','?')}.",
        cite((doc.get("evidence") or [{}])[0].get("ref") if doc.get("evidence") else None,
             spread.get("source_ref")))
    fac_lines = "; ".join(
        f"{f.get('facility_id')} {f.get('type')} {f.get('amount')} ({f.get('purpose','')})"
        for f in (doc.get("facilities") or []))
    sections["facility_summary"] = _section(
        f"Requested facilities: {fac_lines}. Total exposure {metrics['total_exposure']}.",
        cite(*[f.get("source_ref") for f in (doc.get("facilities") or [])]))
    sections["financial_analysis"] = _section(
        f"Spread {spread.get('source_ref')} (provider {spread.get('spread_provider','?')}): "
        f"EBITDA {spread.get('ebitda')}, total debt {spread.get('total_debt')}, "
        f"leverage {metrics['leverage']} (cap {metrics['leverage_cap']}). "
        f"Tie-out {tie['status']}.",
        cite(spread.get("source_ref")))
    sections["repayment_analysis"] = _section(
        f"CFADS {spread.get('cfads')} against total debt service {spread.get('total_debt_service')} "
        f"=> DSCR {metrics['dscr']} (policy floor {metrics['dscr_floor']}).",
        cite(spread.get("source_ref")))
    coll_lines = "; ".join(
        f"{c.get('collateral_id')} {c.get('type')} appraised {c.get('appraised_value')} "
        f"@ advance {c.get('advance_rate')}" for c in (doc.get("collateral") or []))
    sections["collateral_analysis"] = _section(
        (f"Collateral: {coll_lines}. Appraised {metrics['collateral_appraised']}, "
         f"lendable {metrics['collateral_lendable']}, LTV {metrics['ltv']}, "
         f"advance-coverage {metrics['advance_coverage']}.") if doc.get("collateral")
        else "No collateral provided; facility treated as unsecured for coverage purposes.",
        cite(*[c.get("source_ref") for c in (doc.get("collateral") or [])]) or ["computed:collateral"])
    if rr.get("grade"):
        sections["risk_rating"] = _section(
            f"Risk rating {rr.get('grade')} (model {rr.get('model','?')}).",
            cite(rr.get("source_ref")))
    else:
        sections["risk_rating"] = _section("Risk rating not provided (needs-data).",
                                            ["needs-data:risk_rating"])
        unsupported.append("risk_rating: grade not provided by an approved source")
    cov_txt = "; ".join(
        f"{r['covenant_id']} {r['type']} thr {r['threshold']} tested {r['tested_metric']} "
        f"headroom {r['headroom']}{' BREACH' if r['breach_at_inception'] else ''}"
        for r in cov_rows) or "No covenants supplied."
    sections["covenants"] = _section(
        cov_txt, cite(*[r["citation"] for r in cov_rows]) or ["computed:covenants"])
    exc_txt = "; ".join(
        f"{e['exception_id']} ({e['policy_ref']}): {e['description']} -> mitigant: "
        f"{e['mitigant'] or 'MISSING'}" for e in exc) or "No policy exceptions recorded."
    sections["policy_exceptions"] = _section(
        exc_txt, cite(*[e.get("policy_ref") for e in exc]) or ["computed:exceptions"])

    obs = []
    if metrics["dscr_below_floor"]:
        obs.append(f"DSCR {metrics['dscr']} below floor {metrics['dscr_floor']}")
    if metrics["leverage_above_cap"]:
        obs.append(f"leverage {metrics['leverage']} above cap {metrics['leverage_cap']}")
    if metrics["collateral_shortfall"]:
        obs.append("collateral lendable value below exposure")
    breaches = [r["covenant_id"] for r in cov_rows if r["breach_at_inception"]]
    if breaches:
        obs.append(f"covenant breach-at-inception: {', '.join(breaches)}")
    obs_txt = ("Observations for the underwriter: " + "; ".join(obs) + ". ") if obs else \
        "No policy-floor or covenant observations at inception. "
    sections["recommendation"] = _section(
        obs_txt + "Recommended for underwriter adjudication and credit-officer review; this "
        "memorandum presents evidence and analysis only. Any exception disposition, the credit "
        "decision, and booking remain with the human approvers.",
        ["computed:dscr,leverage,ltv,coverage"])

    # --- unsupported / coverage integrity -----------------------------------------------
    for name in REQUIRED_SECTIONS:
        s = sections.get(name) or {}
        if not s.get("content") or not s.get("citations"):
            unsupported.append(f"{name}: section incomplete or missing citation")
    if tie["status"] == "break":
        unsupported.append("financial_analysis: spread tie-out break (recomputed ratios differ)")
    for eid in exc_missing_mit:
        unsupported.append(f"exception {eid}: recorded without a mitigant")
    for g in coverage["gaps"]:
        unsupported.append(f"policy requirement {g}: applicable but not addressed")

    # --- required (still pending) approvals ---------------------------------------------
    approvers = list(pol["base_approvers"])
    if metrics["total_exposure"] >= pol["large_credit_threshold"]:
        approvers.append("Credit Committee")
    approvals = [{"role": r, "status": "pending"} for r in approvers]

    return {
        "memo_id": doc.get("memo_id"),
        "policy_version": doc.get("policy_version"),
        "template_version": doc.get("template_version"),
        "disposition": DISPOSITION,
        "computed_metrics": metrics,
        "spread_tie_out": tie,
        "covenant_table": cov_rows,
        "policy_coverage": coverage,
        "exceptions_with_mitigants": exc,
        "sections": sections,
        "unsupported_assertions": unsupported,
        "approvals": approvals,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "memo_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    pol = {**DEFAULT_POLICY, **(doc.get("policy_config") or {})}
    print(json.dumps(build_draft(doc, pol), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
