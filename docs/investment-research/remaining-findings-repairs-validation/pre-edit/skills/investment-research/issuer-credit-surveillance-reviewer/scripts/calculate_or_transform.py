#!/usr/bin/env python3
"""Deterministic credit-surveillance assembly engine for issuer-credit-surveillance-reviewer.

Takes a validated surveillance build request (issuer, financials, prior-period financials,
maturities, spreads, reported agency ratings, and covenant-change flags) and assembles a
DRAFT credit surveillance packet record. It:

  1. Computes credit metrics deterministically from the supplied financials:
     gross and net leverage (x EBITDA), interest coverage, a fixed-charge coverage proxy,
     total liquidity, and near-term maturity coverage.
  2. Ties computed metrics back to any analyst/vendor-stated values (leverage, coverage);
     a mismatch beyond tolerance is a BLOCK (the packet never restates an unsupported figure).
  3. Tracks period-over-period change vs the prior financials (leverage, coverage deltas),
     spread widening/tightening, reported rating/outlook changes, and covenant-change flags.
  4. Maps every metric and claim to a source_id and flags any unsupported claim, or any
     external (market / rating-agency) source not marked approved.
  5. Populates the required template sections from the approved inputs only.

It NEVER assigns or derives a credit rating (agency ratings are reported only), NEVER forms,
alters, or restates an investment thesis, NEVER recommends or changes a position or trade,
and NEVER interprets covenant terms or determines covenant compliance (a changed covenant is
flagged for handoff to credit-document-terms-reviewer). The action fields stay neutral:
rating_action=reported-only, position_action=none, thesis_action=unchanged.

Usage: python calculate_or_transform.py surveillance_request.json | --selftest
Prints the draft packet JSON to stdout and a self-check summary (ending "N error(s)") to
stderr. Exit 0 if the packet assembles with no blocking flag, 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
import calendar
from pathlib import Path
from native_integrity import attach_source, canonical_hash

# Canonical template sections (must match assets/output-template.md and validate_output.py).
REQUIRED_SECTIONS = [
    "issuer_summary",
    "leverage",
    "coverage",
    "liquidity",
    "maturity_wall",
    "spreads",
    "ratings",
    "covenant_changes",
    "citations_and_evidence",
]
UNAPPROVED_TYPES = {"market", "rating-agency"}  # external inputs that must be marked approved
TOL = 0.05  # tie-out tolerance for computed leverage/coverage ratios

DEFAULT_CONFIG = {
    "near_term_years": 2,            # maturities within (as_of_year + N) count as near-term
    "spread_widening_alert_bps": 50,  # disclose (warn) when spread widens by >= this
    "leverage_increase_alert_x": 0.25,  # disclose (warn) when net leverage rises by >= this
    "coverage_decline_alert_x": 0.25,   # disclose (warn) when interest coverage falls by >= this
}
STANDING_NOTE = (
    "Draft credit surveillance packet for human review. It reports agency ratings but assigns "
    "none, forms or changes no investment thesis, recommends no position or trade, and has not "
    "been circulated, sent, or submitted."
)


def _src_index(doc):
    return {s.get("source_id"): s for s in (doc.get("sources") or []) if s.get("source_id")}


def _assert(claim, source_id, idx):
    s = idx.get(source_id)
    supported = s is not None
    stype = (s or {}).get("type", "unknown")
    approved = bool((s or {}).get("approved")) if supported else False
    approved_ok = supported and (stype not in UNAPPROVED_TYPES or approved)
    return {
        "claim": claim,
        "source_id": source_id,
        "source_type": stype,
        "source_ref": (s or {}).get("ref"),
        "source_reference_resolved": supported,
        "verification_status": "unverified-source-assertion",
        "approved_ok": approved_ok,
    }


def _ratios(fin):
    ebitda = fin.get("ebitda")
    gross_debt = fin.get("gross_debt")
    cash = fin.get("cash")
    interest = fin.get("interest_expense")
    capex = fin.get("capex")
    out = {"gross_leverage_x":None,"net_leverage_x":None,"interest_coverage_x":None,"fccr_x":None}
    if ebitda is not None and ebitda>0:
        out["gross_leverage_x"] = round(gross_debt / ebitda, 4) if gross_debt is not None else None
        out["net_leverage_x"] = round((gross_debt - cash) / ebitda, 4) \
            if (gross_debt is not None and cash is not None) else None
    if interest is not None and interest>0:
        out["interest_coverage_x"] = round(ebitda / interest, 4) if ebitda is not None else None
        out["fccr_x"] = round((ebitda - capex) / interest, 4) \
            if (ebitda is not None and capex is not None) else None
    return out


def _tie_outs(fin, ratios):
    outs = []

    def add(metric, stated, recomputed):
        ok = stated is not None and recomputed is not None and abs(float(stated) - float(recomputed)) <= TOL
        outs.append({"metric": metric, "packet_value": stated, "recomputed": recomputed, "ok": ok})

    if fin.get("stated_gross_leverage_x") is not None:
        add("gross_leverage_x", fin.get("stated_gross_leverage_x"), ratios.get("gross_leverage_x"))
    if fin.get("stated_net_leverage_x") is not None:
        add("net_leverage_x", fin.get("stated_net_leverage_x"), ratios.get("net_leverage_x"))
    if fin.get("stated_interest_coverage_x") is not None:
        add("interest_coverage_x", fin.get("stated_interest_coverage_x"), ratios.get("interest_coverage_x"))
    return outs


def _liquidity(fin, maturities, as_of, cfg, basis):
    cutoff = date.fromisoformat(as_of)
    year = cutoff.year + int(cfg["near_term_years"])
    horizon = cutoff.replace(year=year, day=min(cutoff.day, calendar.monthrange(year, cutoff.month)[1]))
    dated, gaps = [], []
    for m in maturities:
        try:
            due = date.fromisoformat(m["maturity_date"])
            dated.append((due, m))
        except (KeyError, TypeError, ValueError):
            gaps.append(m.get("source_id"))
    cash, revolver = fin.get("cash"), fin.get("undrawn_revolver")
    eligible_cash=cash if basis.get("cash_accessibility")=="confirmed" else None
    eligible_revolver=revolver if basis.get("revolver_availability")=="confirmed" else None
    total = eligible_cash+eligible_revolver if eligible_cash is not None and eligible_revolver is not None else None
    known_near=sum(m["amount"] for due,m in dated if cutoff<=due<=horizon)
    complete=basis.get("maturity_schedule_complete") is True and not gaps
    near=known_near if complete else None
    future = [(due, m) for due, m in dated if due >= cutoff]
    nearest = min(future, key=lambda x: x[0]) if future else None
    return {"available_cash":eligible_cash,"available_revolver":eligible_revolver,"liquidity_basis":basis,
            "comparison_scope":"scheduled maturities only; operating uses, contingent liabilities and refinancing feasibility not assessed",
            "maturity_schedule_complete":complete,"known_near_term_maturities":known_near,
            "maturity_funding_comparison":total>=near if total is not None and near is not None and not any(due<cutoff for due,_ in dated) else None,
            "cash": cash, "undrawn_revolver": revolver, "total_liquidity": total,
            "near_term_horizon_year": horizon.year, "near_term_horizon_date": horizon.isoformat(),
            "near_term_maturities": near, "maturity_date_gaps": gaps,
            "past_due_maturities": [m for due, m in dated if due < cutoff],
            "liquidity_covers_near_term": None,
            "nearest_maturity": {"year": nearest[0].year, "maturity_date": nearest[0].isoformat(), "amount": nearest[1]["amount"]} if nearest else None}


def _changes(ratios, prior_ratios, spreads, ratings, cfg):
    ch = {}
    if prior_ratios:
        for k in ("net_leverage_x", "gross_leverage_x", "interest_coverage_x"):
            cur, prev = ratios.get(k), prior_ratios.get(k)
            ch[k + "_delta"] = round(cur - prev, 4) if (cur is not None and prev is not None) else None
    cur_bps, prior_bps = spreads.get("current_bps"), spreads.get("prior_bps")
    ch["spread_delta_bps"] = (cur_bps - prior_bps) if (cur_bps is not None and prior_bps is not None) else None
    ch["spread_widening"] = (ch["spread_delta_bps"] is not None and ch["spread_delta_bps"] > 0)
    rating_changes = []
    for r in ratings:
        changed = (r.get("rating") != r.get("prior_rating")) or (r.get("outlook") != r.get("prior_outlook"))
        rating_changes.append({
            "agency": r.get("agency"), "rating": r.get("rating"), "outlook": r.get("outlook"),
            "prior_rating": r.get("prior_rating"), "prior_outlook": r.get("prior_outlook"),
            "rated_object_type":r.get("rated_object_type"),"rated_object_id":r.get("rated_object_id"),
            "changed": changed, "source_id": r.get("source_id"),
        })
    ch["rating_changes"] = rating_changes
    return ch


def _sections(doc, ratios, prior_ratios, liq, changes, cov_changes):
    issuer = doc.get("issuer") or {}
    spreads = doc.get("spreads") or {}
    maturities = doc.get("maturities") or []

    def sec(body, source_ids):
        return {"body": body.strip(), "source_ids": [s for s in source_ids if s]}

    fin_src = (doc.get("financials") or {}).get("source_id")
    prior_note = ""
    if prior_ratios:
        d = changes.get("net_leverage_x_delta")
        if d is not None:
            prior_note = f" Net leverage change vs prior {issuer.get('prior_as_of')}: {d:+.2f}x."

    mat_lines = "; ".join(f"{m.get('year')}: {m.get('amount')}" for m in maturities) or "none supplied"
    nearest = liq.get("nearest_maturity")
    nearest_txt = f"{nearest['year']} ({nearest['amount']})" if nearest else "none"

    rc = changes.get("rating_changes") or []
    rating_lines = "; ".join(
        f"{r['agency']} {r['rating']} (outlook {r['outlook']}; prior {r['prior_rating']}/{r['prior_outlook']}"
        f"{', changed' if r['changed'] else ''})" for r in rc) or "none supplied"

    changed_cov = [c for c in cov_changes if c.get("changed")]
    cov_line = ("Covenant items changed vs prior: "
                + "; ".join(f"{c['covenant_id']} ({c['name']})" for c in changed_cov)
                + ". Term-level detail and interpretation are handed off, not performed here."
                ) if changed_cov else "No covenant items flagged as changed this period."

    return {
        "issuer_summary": sec(
            f"{issuer.get('name')} ({issuer.get('sector')}). Surveillance as of {issuer.get('as_of')} "
            f"(prior {issuer.get('prior_as_of')}). Reported net leverage {ratios.get('net_leverage_x')}x, "
            f"interest coverage {ratios.get('interest_coverage_x')}x, total liquidity {liq.get('total_liquidity')}."
            f"{prior_note} Surveillance packet only; no rating is set and no position view is expressed.",
            [fin_src]),
        "leverage": sec(
            f"Gross leverage {ratios.get('gross_leverage_x')}x EBITDA; net leverage {ratios.get('net_leverage_x')}x. "
            f"Computed from EBITDA {(doc.get('financials') or {}).get('ebitda')}, gross debt "
            f"{(doc.get('financials') or {}).get('gross_debt')}, cash {(doc.get('financials') or {}).get('cash')}.",
            [fin_src]),
        "coverage": sec(
            f"Interest coverage {ratios.get('interest_coverage_x')}x (EBITDA / interest expense). "
            f"Fixed-charge coverage proxy {ratios.get('fccr_x')}x ((EBITDA - capex) / interest expense); not contractual FCCR or DSCR.",
            [fin_src]),
        "liquidity": sec(
            f"Available supplied funding {liq.get('total_liquidity')}; nominal cash {liq.get('cash')} and undrawn revolver "
            f"{liq.get('undrawn_revolver')}. Near-term maturities through {liq.get('near_term_horizon_year')}: "
            f"{liq.get('near_term_maturities')} ("
            f"{'not evaluable' if liq.get('liquidity_covers_near_term') is None else ('covered by liquidity' if liq.get('liquidity_covers_near_term') else 'NOT fully covered by liquidity')}).",
            [fin_src, (maturities[0].get("source_id") if maturities else None)]),
        "maturity_wall": sec(
            f"Scheduled maturities by year: {mat_lines}. Nearest maturity: {nearest_txt}.",
            [(maturities[0].get("source_id") if maturities else None)]),
        "spreads": sec(
            f"Credit spread ({spreads.get('instrument', 'issuer spread')}): current {spreads.get('current_bps')} bps "
            f"vs prior {spreads.get('prior_bps')} bps (delta {changes.get('spread_delta_bps')} bps, "
            f"{'widening' if changes.get('spread_widening') else 'tightening/flat'}).",
            [spreads.get("source_id")]),
        "ratings": sec(
            f"Reported agency ratings: {rating_lines}. Ratings are reported from the agency source; this "
            f"packet does not set an internal rating or opine on the level.",
            [r.get("source_id") for r in rc]),
        "covenant_changes": sec(
            cov_line, [c.get("source_id") for c in cov_changes]),
        "citations_and_evidence": sec(
            "Claims reference supplied source records and eligibility assertions; authenticity and entitlements remain unverified. This is a draft for human review.",
            [fin_src]),
    }


def _native_assemble(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("thresholds") or {})}
    idx = _src_index(doc)
    issuer = doc.get("issuer") or {}
    fin = doc.get("financials") or {}
    prior = doc.get("prior_financials")
    spreads = doc.get("spreads") or {}
    ratings = doc.get("ratings") or []
    maturities = doc.get("maturities") or []

    try:
        as_of_year = int(str(issuer.get("as_of"))[:4])
    except (TypeError, ValueError):
        as_of_year = None

    ratios = _ratios(fin)
    prior_ratios = _ratios(prior) if prior else None
    tie_outs = _tie_outs(fin, ratios)
    liq = _liquidity(fin, maturities, issuer.get("as_of"), cfg, doc.get("liquidity_basis") or {})
    changes = _changes(ratios, prior_ratios, spreads, ratings, cfg)

    cov_changes = [{"covenant_id": c.get("covenant_id"), "name": c.get("name"),
                    "changed": bool(c.get("changed")), "source_id": c.get("source_id"),
                    "instrument_id":c.get("instrument_id"),"doc_id":c.get("doc_id"),"doc_version":c.get("doc_version"),
                    "handoff": "credit-document-terms-reviewer" if c.get("changed") else None}
                   for c in (doc.get("covenants") or [])]

    # Traceability: one assertion per material claim.
    assertions = [_assert("core credit metrics (leverage/coverage/liquidity)", fin.get("source_id"), idx)]
    if prior:
        assertions.append(_assert("prior financial metrics", prior.get("source_id"), idx))
    assertions.append(_assert("credit spreads", spreads.get("source_id"), idx))
    for r in ratings:
        assertions.append(_assert(f"reported rating {r.get('agency')}", r.get("source_id"), idx))
    for sid in dict.fromkeys(m.get("source_id") for m in maturities):
        assertions.append(_assert("maturity schedule", sid, idx))
    for c in (doc.get("covenants") or []):
        assertions.append(_assert(f"covenant-change flag {c.get('covenant_id')}", c.get("source_id"), idx))

    sections = _sections(doc, ratios, prior_ratios, liq, changes, cov_changes)

    flags = []
    if liq["maturity_date_gaps"]:
        flags.append({"code": "missing-maturity-date", "severity": "block", "detail": "exact maturity dates required; year-only coverage is not evaluable"})
    for a in assertions:
        if not a["source_reference_resolved"]:
            flags.append({"code": "unsupported-claim", "severity": "block",
                          "detail": f"claim {a['claim']!r} cites unknown source {a['source_id']!r}"})
        elif not a["approved_ok"]:
            flags.append({"code": "unapproved-source", "severity": "block",
                          "detail": f"claim {a['claim']!r} cites unapproved {a['source_type']} source {a['source_id']!r}"})
    for o in tie_outs:
        if not o["ok"]:
            flags.append({"code": "tie-out-break", "severity": "block",
                          "detail": f"{o['metric']} stated {o['packet_value']} != recomputed {o['recomputed']}"})

    # Disclosure (warn) flags: surveillance surfaces deterioration; it never judges or acts on it.
    d = changes.get("net_leverage_x_delta")
    if d is not None and d >= cfg["leverage_increase_alert_x"]:
        flags.append({"code": "leverage-increase", "severity": "warn",
                      "detail": f"net leverage rose {d:+.2f}x vs prior - disclose"})
    cd = changes.get("interest_coverage_x_delta")
    if cd is not None and cd <= -cfg["coverage_decline_alert_x"]:
        flags.append({"code": "coverage-decline", "severity": "warn",
                      "detail": f"interest coverage fell {cd:+.2f}x vs prior - disclose"})
    sd = changes.get("spread_delta_bps")
    if sd is not None and sd >= cfg["spread_widening_alert_bps"]:
        flags.append({"code": "spread-widening", "severity": "warn",
                      "detail": f"spread widened {sd} bps vs prior - disclose"})
    if liq.get("maturity_funding_comparison") is False:
        flags.append({"code": "near-term-maturity-liquidity-gap", "severity": "warn",
                      "detail": "supplied available funding is below supplied scheduled maturities; full liquidity sufficiency remains unassessed"})
    for rc in changes.get("rating_changes") or []:
        if rc.get("changed"):
            flags.append({"code": "rating-change-reported", "severity": "warn",
                          "detail": f"{rc['agency']} rating/outlook changed vs prior (reported, not assigned) - disclose"})
    if any(c.get("changed") for c in cov_changes):
        flags.append({"code": "covenant-change-handoff", "severity": "warn",
                      "detail": "covenant item(s) changed - route detail to credit-document-terms-reviewer"})

    unresolved = [f["detail"] for f in flags if f["severity"] == "block"]

    return {
        "packet_version": doc.get("packet_version"),
        "config_version": doc.get("config_version"),
        "issuer_id": issuer.get("issuer_id"),
        "issuer_name": issuer.get("name"),
        "as_of": issuer.get("as_of"),
        "prior_as_of": issuer.get("prior_as_of"),
        "packet": {"required_sections": REQUIRED_SECTIONS, "sections": sections},
        "metrics": {**ratios, **liq,"fccr_method":"(EBITDA - capex) / interest expense proxy; not contractual FCCR or DSCR"},
        "changes": changes,
        "assertions": assertions,
        "tie_outs": tie_outs,
        "covenant_changes": cov_changes,
        "flags": flags,
        "approvals": doc.get("approvals") or [],
        "rating_action": "reported-only",
        "position_action": "none",
        "thesis_action": "unchanged",
        "unresolved": unresolved,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "surveillance_request_example.json"
        doc = _read_json(p.read_text(encoding="utf-8"))
    elif argv:
        doc = _read_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _read_json(sys.stdin.read())
    packet = assemble(doc)
    print(json.dumps(packet, indent=2))
    if isinstance(doc,dict) and doc.get('schema_version')=='ir-phase2/1.0': return 0
    n = len(packet["unresolved"])
    print(f"assembly self-check: {n} error(s)", file=sys.stderr)
    return 1 if n else 0




def _validated_input(doc):
    import importlib.util
    p=Path(__file__).with_name("validate_input.py")
    spec=importlib.util.spec_from_file_location("_native_input_"+p.parent.parent.name.replace("-","_"),p)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    errors,_=module.validate(doc)
    if errors: raise ValueError("; ".join(errors))

def assemble(doc: dict) -> dict:
    if isinstance(doc,dict) and doc.get('schema_version')=='ir-phase2/1.0':
        from phase2_domain import compute as phase2_compute
        return phase2_compute(doc)
    # Reject non-JSON and non-finite input before any calculations.
    _validated_input(doc)
    result=_native_assemble(doc)
    result.update({"knowledge_cutoff":doc["knowledge_cutoff"],"financial_basis":{k:doc["financials"][k] for k in ("currency","units","period","accounting_basis")},
                   "spreads":doc["spreads"],"maturities":doc["maturities"],
                   "authority":"source eligibility, identity and role records are supplied assertions, not authentication or authorization",
                   "scope_limit":"supplied corporate credit surveillance only; no complete issuer credit conclusion, issue relative value, legal opinion or liquidity sufficiency assessment"})
    if result["metrics"]["total_liquidity"] is None or not result["metrics"]["maturity_schedule_complete"]:
        result["unresolved"].append("available funding or maturity inventory incomplete; liquidity assessment withheld")
    recorded={a.get("role") for a in doc["approvals"] if a.get("status")=="recorded"}
    if not {"preparer","reviewer"}.issubset(recorded): result["unresolved"].append("required review-role assertions missing; handoff held")
    result["support_status"]="PARTIAL" if result["unresolved"] else "SUPPLIED_INPUT_REVIEW"
    canonical_hash(result)
    return attach_source(result, doc)

def _read_json(raw, **options):
    """Reject duplicate object keys and nonfinite constants before binding."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON object key: '+key)
            result[key]=value
        return result
    def constant(value): raise ValueError('non-finite JSON constant: '+value)
    options.setdefault('object_pairs_hook',pairs)
    options.setdefault('parse_constant',constant)
    return json.loads(raw,**options)


_phase2_json_main = main

def main(*args, **kwargs):
    try: return _phase2_json_main(*args, **kwargs)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print('ERROR:', str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
