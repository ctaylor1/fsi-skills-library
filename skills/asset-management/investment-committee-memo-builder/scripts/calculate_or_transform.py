#!/usr/bin/env python3
"""Deterministic IC-memo assembly engine for investment-committee-memo-builder.

Takes a validated IC build request (diligence index, model outputs, scenarios, valuation,
risks, sizing, thesis, decision questions, and recorded approvals) and assembles a DRAFT
investment-committee memorandum record. It:

  1. Ties memo figures back to the model source (entry multiple, equity check, leverage).
  2. Checks scenario consistency (a downside case exists; MOIC/IRR are ordered
     downside <= base <= upside; the base case ties to the model returns).
  3. Computes position sizing and checks single-name / sector concentration limits.
  4. Maps every material claim to a source and flags any unsupported or unapproved claim.
  5. Populates the required template sections from the approved inputs only.

It NEVER makes or records the committee's investment decision, never sends/circulates the
memo, and never fabricates a figure or claim that is not present in the inputs. The
committee decision is always left `pending`.

Usage: python calculate_or_transform.py ic_request.json | --selftest
Prints the draft memo JSON to stdout and a self-check summary (ending "N error(s)") to
stderr. Exit 0 if the draft assembles with no blocking flag, 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Canonical template sections (must match assets/output-template.md and validate_output.py).
REQUIRED_SECTIONS = [
    "executive_summary",
    "investment_thesis",
    "transaction_structure",
    "valuation",
    "returns_analysis",
    "scenario_analysis",
    "key_risks_and_mitigants",
    "position_sizing_and_portfolio_fit",
    "recommendation_and_decision_questions",
]
UNAPPROVED_TYPES = {"market", "research"}  # external inputs that must be marked approved
TOL = 0.05  # tie-out tolerance for computed multiples/ratios
STANDING_NOTE = (
    "Draft investment-committee memorandum for human review. It is not investment advice, "
    "records no committee decision, and has not been circulated, sent, or submitted."
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
        "supported": supported,
        "approved_ok": approved_ok,
    }


def _find(scenarios, name):
    for s in scenarios:
        if str(s.get("name", "")).strip().lower() == name:
            return s
    return None


def _tie_outs(model):
    entry = model.get("entry") or {}
    lev = model.get("leverage") or {}
    outs = []

    def add(metric, stated, recomputed):
        ok = stated is not None and recomputed is not None and abs(float(stated) - float(recomputed)) <= TOL
        outs.append({"metric": metric, "memo_value": stated,
                     "recomputed": round(recomputed, 4) if recomputed is not None else None, "ok": ok})

    mv = entry.get("metric_value")
    outs_ev = entry.get("ev")
    add("entry_multiple", entry.get("entry_multiple"),
        (outs_ev / mv) if (mv not in (None, 0) and outs_ev is not None) else None)
    add("equity_check", entry.get("equity_check"),
        (outs_ev - entry.get("net_debt")) if (outs_ev is not None and entry.get("net_debt") is not None) else None)
    ebitda = lev.get("ebitda")
    add("leverage_x", lev.get("leverage_x"),
        (lev.get("total_debt") / ebitda) if (ebitda not in (None, 0) and lev.get("total_debt") is not None) else None)
    return outs


def _scenario_check(scenarios, model_returns):
    base, up, down = _find(scenarios, "base"), _find(scenarios, "upside"), _find(scenarios, "downside")
    chk = {"has_base": base is not None, "has_upside": up is not None, "has_downside": down is not None,
           "moic_ordered": None, "irr_ordered": None, "base_ties_model": None}
    if base and up and down:
        chk["moic_ordered"] = down.get("moic", 0) <= base.get("moic", 0) <= up.get("moic", 0)
        chk["irr_ordered"] = down.get("irr", 0) <= base.get("irr", 0) <= up.get("irr", 0)
    if base and model_returns:
        chk["base_ties_model"] = (
            abs(float(base.get("moic", 0)) - float(model_returns.get("moic", -1))) <= TOL
            and abs(float(base.get("irr", 0)) - float(model_returns.get("irr", -1))) <= 0.5
        )
    return chk


def _sizing_check(sizing):
    nav = sizing.get("fund_nav")
    commit = sizing.get("proposed_commitment")
    pos = round(commit / nav * 100, 2) if (nav not in (None, 0) and commit is not None) else None
    single = sizing.get("single_name_limit_pct")
    sector_post = None
    if sizing.get("sector_current_pct") is not None and pos is not None:
        sector_post = round(sizing.get("sector_current_pct") + pos, 2)
    return {
        "computed_position_pct": pos,
        "stated_position_pct": sizing.get("position_pct"),
        "position_ties": pos is not None and sizing.get("position_pct") is not None
        and abs(pos - sizing.get("position_pct")) <= 0.1,
        "single_name_limit_pct": single,
        "within_single_name": pos is not None and single is not None and pos <= single,
        "sector_post_pct": sector_post,
        "sector_limit_pct": sizing.get("sector_limit_pct"),
        "within_sector": sector_post is not None and sizing.get("sector_limit_pct") is not None
        and sector_post <= sizing.get("sector_limit_pct"),
    }


def _sections(doc, sizing_chk):
    deal = doc.get("deal") or {}
    model = doc.get("model") or {}
    entry = model.get("entry") or {}
    lev = model.get("leverage") or {}
    ret = model.get("returns") or {}
    val = doc.get("valuation") or {}
    sc = doc.get("scenarios") or []
    risks = doc.get("risks") or []
    thesis = doc.get("thesis_points") or []
    dq = doc.get("decision_questions") or []

    def sec(body, source_ids):
        return {"body": body.strip(), "source_ids": [s for s in source_ids if s]}

    scen_lines = "; ".join(f"{s.get('name')} MOIC {s.get('moic')}x / IRR {s.get('irr')}%" for s in sc)
    risk_lines = " ".join(f"[{r.get('severity','?')}] {r.get('risk')} -> Mitigant: {r.get('mitigant')}." for r in risks)
    thesis_lines = " ".join(f"{t.get('claim')}." for t in thesis)

    return {
        "executive_summary": sec(
            f"{deal.get('name')} ({deal.get('strategy')}, {deal.get('sector')}/{deal.get('geography')}). "
            f"Deal-team recommendation: {deal.get('recommended_action')}. Entry {entry.get('entry_multiple')}x "
            f"{entry.get('metric')} on EV {entry.get('ev')}; base case {ret.get('moic')}x / {ret.get('irr')}% IRR "
            f"over {ret.get('hold_years')} years. This is a draft for committee decision.",
            [model.get("source_id")]),
        "investment_thesis": sec(thesis_lines or "No thesis points supplied.",
                                 [t.get("source_id") for t in thesis]),
        "transaction_structure": sec(
            f"EV {entry.get('ev')} at {entry.get('entry_multiple')}x {entry.get('metric')} "
            f"({entry.get('metric_value')}). Net debt {entry.get('net_debt')}; equity check "
            f"{entry.get('equity_check')}. Total debt {lev.get('total_debt')} = {lev.get('leverage_x')}x EBITDA.",
            [model.get("source_id")]),
        "valuation": sec(
            f"{val.get('method')}: entry {val.get('entry_multiple')}x vs. peer range "
            f"{val.get('peer_range_low')}x-{val.get('peer_range_high')}x.",
            [val.get("source_id")]),
        "returns_analysis": sec(
            f"Base case {ret.get('moic')}x MOIC / {ret.get('irr')}% IRR over {ret.get('hold_years')} years.",
            [model.get("source_id")]),
        "scenario_analysis": sec(scen_lines or "No scenarios supplied.",
                                 [s.get("source_id") for s in sc]),
        "key_risks_and_mitigants": sec(risk_lines or "No risks supplied.",
                                       [r.get("source_id") for r in risks]),
        "position_sizing_and_portfolio_fit": sec(
            f"Proposed commitment {doc.get('sizing',{}).get('proposed_commitment')} on fund NAV "
            f"{doc.get('sizing',{}).get('fund_nav')} = {sizing_chk['computed_position_pct']}% "
            f"(single-name limit {sizing_chk['single_name_limit_pct']}%). Sector exposure post-deal "
            f"{sizing_chk['sector_post_pct']}% vs. limit {sizing_chk['sector_limit_pct']}%.",
            [doc.get("sizing", {}).get("source_id")]),
        "recommendation_and_decision_questions": sec(
            f"Deal-team recommendation: {deal.get('recommended_action')} (committee decision pending). "
            f"Decision questions: " + " ".join(f"({i+1}) {q}" for i, q in enumerate(dq)),
            [model.get("source_id")]),
    }


def assemble(doc: dict) -> dict:
    idx = _src_index(doc)
    model = doc.get("model") or {}
    sizing = doc.get("sizing") or {}
    val = doc.get("valuation") or {}

    # Traceability: one assertion per material claim.
    assertions = []
    for t in doc.get("thesis_points") or []:
        assertions.append(_assert(t.get("claim"), t.get("source_id"), idx))
    for r in doc.get("risks") or []:
        assertions.append(_assert(r.get("risk"), r.get("source_id"), idx))
    for s in doc.get("scenarios") or []:
        assertions.append(_assert(f"scenario {s.get('name')}", s.get("source_id"), idx))
    assertions.append(_assert("valuation basis", val.get("source_id"), idx))
    assertions.append(_assert("position sizing", sizing.get("source_id"), idx))

    tie_outs = _tie_outs(model)
    scen = _scenario_check(doc.get("scenarios") or [], model.get("returns") or {})
    size = _sizing_check(sizing)
    sizing_chk_public = {k: size[k] for k in
                         ("computed_position_pct", "single_name_limit_pct", "sector_post_pct", "sector_limit_pct")}
    sections = _sections(doc, size)

    flags = []
    for a in assertions:
        if not a["supported"]:
            flags.append({"code": "unsupported-claim", "severity": "block",
                          "detail": f"claim {a['claim']!r} cites unknown source {a['source_id']!r}"})
        elif not a["approved_ok"]:
            flags.append({"code": "unapproved-source", "severity": "block",
                          "detail": f"claim {a['claim']!r} cites unapproved {a['source_type']} source {a['source_id']!r}"})
    for o in tie_outs:
        if not o["ok"]:
            flags.append({"code": "tie-out-break", "severity": "block",
                          "detail": f"{o['metric']} stated {o['memo_value']} != recomputed {o['recomputed']}"})
    if not scen["has_downside"]:
        flags.append({"code": "missing-downside", "severity": "block", "detail": "no downside scenario supplied"})
    if scen["moic_ordered"] is False or scen["irr_ordered"] is False:
        flags.append({"code": "scenario-ordering", "severity": "block",
                      "detail": "scenarios not ordered downside <= base <= upside"})
    if scen["base_ties_model"] is False:
        flags.append({"code": "base-scenario-mismatch", "severity": "block",
                      "detail": "base scenario does not tie to model returns"})
    if size["position_ties"] is False:
        flags.append({"code": "sizing-mismatch", "severity": "block",
                      "detail": f"stated position {size['stated_position_pct']}% != computed {size['computed_position_pct']}%"})
    if size["within_single_name"] is False:
        flags.append({"code": "single-name-breach", "severity": "block",
                      "detail": f"position {size['computed_position_pct']}% exceeds single-name limit {size['single_name_limit_pct']}%"})
    if size["within_sector"] is False:
        flags.append({"code": "sector-limit-breach", "severity": "warn",
                      "detail": f"sector exposure post-deal {size['sector_post_pct']}% exceeds limit {size['sector_limit_pct']}% - disclose to committee"})
    if val.get("entry_multiple") is not None and val.get("peer_range_high") is not None \
            and val.get("entry_multiple") > val.get("peer_range_high"):
        flags.append({"code": "valuation-above-peers", "severity": "warn",
                      "detail": "entry multiple is above the peer range - disclose to committee"})

    unresolved = [f["detail"] for f in flags if f["severity"] == "block"]

    return {
        "template_version": doc.get("template_version"),
        "deal_id": (doc.get("deal") or {}).get("deal_id"),
        "deal_name": (doc.get("deal") or {}).get("name"),
        "memo": {"required_sections": REQUIRED_SECTIONS, "sections": sections},
        "assertions": assertions,
        "tie_outs": tie_outs,
        "scenario_check": scen,
        "sizing_check": sizing_chk_public,
        "flags": flags,
        "approvals": doc.get("approvals") or [],
        "committee_decision": "pending",
        "decision_questions": doc.get("decision_questions") or [],
        "unresolved": unresolved,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ic_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    memo = assemble(doc)
    print(json.dumps(memo, indent=2))
    n = len(memo["unresolved"])
    print(f"assembly self-check: {n} error(s)", file=sys.stderr)
    return 1 if n else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
