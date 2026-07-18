#!/usr/bin/env python3
"""Deterministic single-period performance-attribution builder for performance-attribution-builder.

Implements arithmetic Brinson-Fachler attribution by segment and decomposes the portfolio's
single-period active return (portfolio return minus benchmark return) into ALLOCATION,
SELECTION, INTERACTION, and CURRENCY effects, rolls the effects up by currency, reconciles the
bottom-up return to an official book-of-record return when supplied, and lists open items. Every
segment carries its citation. It never states an investment recommendation or advice, never makes
a forward-looking or guaranteed-performance claim, never asserts GIPS compliance, never fabricates
a return or weight, and never sends or delivers. Output is a DRAFT manifest
(`build_status: draft-attribution`) for human review.

Method (arithmetic, single period; all returns are additive):
  base return per segment  R_i      = local_return_i + currency_return_i
  benchmark local total    Rb_local = sum(wb_i * local_return_bench_i)
  allocation_i = (wp_i - wb_i) * (local_return_bench_i - Rb_local)
  selection_i  =  wb_i         * (local_return_port_i  - local_return_bench_i)
  interaction_i= (wp_i - wb_i) * (local_return_port_i  - local_return_bench_i)
  currency_i   = (wp_i - wb_i) *  currency_return_i
  Then sum(allocation + selection + interaction + currency) == Rp - Rb  (exact, arithmetic).

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the attribution manifest JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

STANDING_NOTE = (
    "Draft performance-attribution analysis for human review only. It is not investment advice "
    "and not a recommendation; it makes no forward-looking or guaranteed-performance claim and "
    "asserts no GIPS compliance; the effects are an ex-post decomposition of realized return, and "
    "this draft has not been reviewed, approved, or delivered."
)
SUPPORTED_MODELS = {"brinson-fachler-arithmetic", "brinson-fachler", "arithmetic"}
RETURN_FIELDS = ("local_return_port", "local_return_bench", "currency_return")
RND = 10  # internal rounding to tame floating-point noise while preserving tie-outs


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _r(x):
    v = round(float(x), RND)
    return 0.0 if v == 0 else v  # normalize -0.0 -> 0.0


def _mask(s):
    if not s:
        return s
    s = str(s)
    return s if len(s) <= 3 else f"{s[:2]}**{s[-2:]}"


def _complete(seg):
    return all(_num(seg.get(k)) for k in RETURN_FIELDS)


def build(doc: dict) -> dict:
    cfg = doc.get("config") or {}
    recon_tol = cfg.get("reconciliation_tolerance", 1e-6)
    weight_tol = cfg.get("weight_tolerance", 0.005)
    official_tol = cfg.get("official_tolerance", 5e-4)
    base = doc.get("base_currency")
    segments = doc.get("segments") or []

    complete = [s for s in segments if _complete(s)]
    incomplete = [s for s in segments if not _complete(s)]

    # bottom-up totals over the segments that carry returns
    rb_local = _r(sum(float(s["weight_bench"]) * float(s["local_return_bench"]) for s in complete))
    rp_local = _r(sum(float(s["weight_port"]) * float(s["local_return_port"]) for s in complete))
    port_ccy = _r(sum(float(s["weight_port"]) * float(s["currency_return"]) for s in complete))
    bench_ccy = _r(sum(float(s["weight_bench"]) * float(s["currency_return"]) for s in complete))
    rp = _r(rp_local + port_ccy)
    rb = _r(rb_local + bench_ccy)
    active = _r(rp - rb)

    sum_wp = _r(sum(float(s.get("weight_port") or 0) for s in segments))
    sum_wb = _r(sum(float(s.get("weight_bench") or 0) for s in segments))

    segment_attribution = []
    open_items = []
    citations = []
    tot_alloc = tot_sel = tot_inter = tot_ccy = 0.0
    by_currency = {}

    for s in segments:
        cite = s.get("source_ref")
        if cite:
            citations.append(cite)
        wp = float(s.get("weight_port") or 0)
        wb = float(s.get("weight_bench") or 0)
        ccy = s.get("currency")
        if not _complete(s):
            missing = [k for k in RETURN_FIELDS if not _num(s.get(k))]
            segment_attribution.append({
                "segment": s.get("segment"), "currency": ccy,
                "weight_port": wp, "weight_bench": wb, "active_weight": _r(wp - wb),
                "local_return_port": s.get("local_return_port"),
                "local_return_bench": s.get("local_return_bench"),
                "currency_return": s.get("currency_return"),
                "allocation": None, "selection": None, "interaction": None,
                "currency_effect": None, "total": None,
                "status": "needs-data", "missing": missing, "citation": cite,
            })
            open_items.append({"item": s.get("segment"), "type": "missing-return",
                               "citation": cite,
                               "action": f"obtain {', '.join(missing)} or exclude the segment; "
                                         "its weight is unattributed until resolved"})
            continue

        rlp = float(s["local_return_port"])
        rlb = float(s["local_return_bench"])
        f = float(s["currency_return"])
        alloc = _r((wp - wb) * (rlb - rb_local))
        sel = _r(wb * (rlp - rlb))
        inter = _r((wp - wb) * (rlp - rlb))
        ccy_eff = _r((wp - wb) * f)
        total = _r(alloc + sel + inter + ccy_eff)
        tot_alloc += alloc; tot_sel += sel; tot_inter += inter; tot_ccy += ccy_eff
        by_currency[ccy] = _r(by_currency.get(ccy, 0.0) + total)
        segment_attribution.append({
            "segment": s.get("segment"), "currency": ccy,
            "weight_port": wp, "weight_bench": wb, "active_weight": _r(wp - wb),
            "local_return_port": rlp, "local_return_bench": rlb, "currency_return": f,
            "allocation": alloc, "selection": sel, "interaction": inter,
            "currency_effect": ccy_eff, "total": total,
            "status": "attributed", "citation": cite,
        })
        if base and ccy and ccy != base and f == 0:
            open_items.append({"item": s.get("segment"), "type": "currency-return-zero",
                               "citation": cite,
                               "action": f"confirm the {ccy}/{base} return is truly zero (hedged) "
                                         "or supply the period currency return"})

    tot_alloc, tot_sel, tot_inter, tot_ccy = _r(tot_alloc), _r(tot_sel), _r(tot_inter), _r(tot_ccy)
    total_attributed = _r(tot_alloc + tot_sel + tot_inter + tot_ccy)
    residual = _r(active - total_attributed)

    effect_totals = {
        "allocation": tot_alloc, "selection": tot_sel, "interaction": tot_inter,
        "currency": tot_ccy, "total_attributed": total_attributed,
    }
    currency_attribution = [{"currency": c, "total": v} for c, v in sorted(by_currency.items())]

    # reconciliation: internal (effects tie to active) + external (bottom-up vs official book of record)
    reconciliation = {
        "active_return": active,
        "attributed_active_return": total_attributed,
        "residual": residual,
        "status": "reconciled" if abs(residual) <= recon_tol else "residual-exceeds-tolerance",
        "reconciliation_tolerance": recon_tol,
    }
    if abs(residual) > recon_tol:
        open_items.append({"item": "attribution residual", "type": "unreconciled-effects",
                           "action": f"investigate residual {residual}; effects do not sum to active return"})

    official = doc.get("official_returns") or {}
    if official:
        op = official.get("portfolio")
        ob = official.get("benchmark")
        rec_off = {"provided": True, "official_tolerance": official_tol}
        if _num(op):
            rp_res = _r(op - rp)
            rec_off["portfolio"] = {"official": op, "bottom_up": rp, "residual": rp_res,
                                    "status": "reconciled" if abs(rp_res) <= official_tol else "break"}
            if abs(rp_res) > official_tol:
                open_items.append({"item": "portfolio return vs book of record", "type": "official-return-break",
                                   "action": f"portfolio bottom-up {rp} != official {op} (residual {rp_res}); "
                                             "reconcile before use"})
        if _num(ob):
            rb_res = _r(ob - rb)
            rec_off["benchmark"] = {"official": ob, "bottom_up": rb, "residual": rb_res,
                                    "status": "reconciled" if abs(rb_res) <= official_tol else "break"}
            if abs(rb_res) > official_tol:
                open_items.append({"item": "benchmark return vs official index", "type": "official-return-break",
                                   "action": f"benchmark bottom-up {rb} != official {ob} (residual {rb_res}); "
                                             "reconcile before use"})
        reconciliation["official"] = rec_off
    else:
        reconciliation["official"] = {"provided": False}
        open_items.append({"item": "official returns", "type": "no-official-return",
                           "action": "supply the official portfolio and benchmark returns to reconcile "
                                     "the attribution to the book of record"})

    # weight coverage
    unattributed_wp = _r(sum(float(s.get("weight_port") or 0) for s in incomplete))
    weight_coverage = {"sum_weight_port": sum_wp, "sum_weight_bench": sum_wb,
                       "unattributed_weight_port": unattributed_wp}
    if abs(sum_wp - 1.0) > weight_tol:
        open_items.append({"item": "portfolio weights", "type": "weight-sum",
                           "action": f"portfolio weights sum to {sum_wp} (expected ~1.0); "
                                     "confirm cash/residual treatment"})
    if abs(sum_wb - 1.0) > weight_tol:
        open_items.append({"item": "benchmark weights", "type": "weight-sum",
                           "action": f"benchmark weights sum to {sum_wb} (expected ~1.0); confirm coverage"})

    # QA checks (deterministic; each PASS is reproducible from the cited inputs)
    qa_checks = [
        {"check": "effects_tie_to_active",
         "status": "pass" if abs(residual) <= recon_tol else "flag",
         "detail": f"allocation+selection+interaction+currency = {total_attributed} vs active {active} "
                   f"(residual {residual})"},
        {"check": "portfolio_weight_sum",
         "status": "pass" if abs(sum_wp - 1.0) <= weight_tol else "flag",
         "detail": f"sum(weight_port) = {sum_wp}"},
        {"check": "benchmark_weight_sum",
         "status": "pass" if abs(sum_wb - 1.0) <= weight_tol else "flag",
         "detail": f"sum(weight_bench) = {sum_wb}"},
        {"check": "return_coverage",
         "status": "pass" if not incomplete else "flag",
         "detail": "all segments carry returns" if not incomplete
                   else f"{len(incomplete)} segment(s) missing returns (unattributed weight {unattributed_wp})"},
    ]
    off = reconciliation.get("official") or {}
    if off.get("provided"):
        for side in ("portfolio", "benchmark"):
            if side in off:
                qa_checks.append({"check": f"official_{side}_reconciliation",
                                  "status": "pass" if off[side]["status"] == "reconciled" else "flag",
                                  "detail": f"bottom-up {off[side]['bottom_up']} vs official {off[side]['official']} "
                                            f"(residual {off[side]['residual']})"})

    # approvals: capture recorded; mark required-but-missing as outstanding open items
    approvals = {"recorded": [], "outstanding": []}
    recorded_types = set()
    for a in doc.get("approvals") or []:
        if a.get("status") == "recorded":
            rec = {"type": a.get("type"), "approver_role": a.get("approver_role"),
                   "approver": _mask(a.get("approver")), "date": a.get("date"),
                   "citation": a.get("source_ref")}
            approvals["recorded"].append(rec)
            recorded_types.add(a.get("type"))
            if rec["citation"]:
                citations.append(rec["citation"])
        else:
            approvals["outstanding"].append({"type": a.get("type"), "status": a.get("status") or "outstanding"})
    for req in doc.get("required_approvals") or []:
        if req not in recorded_types:
            if not any(o.get("type") == req for o in approvals["outstanding"]):
                approvals["outstanding"].append({"type": req, "status": "outstanding"})
            open_items.append({"item": req, "type": "outstanding-approval",
                               "action": "obtain the required approval before external or marketing use"})

    # dedup source index preserving order
    seen, source_index = set(), []
    for c in citations:
        if c and c not in seen:
            seen.add(c)
            source_index.append(c)

    methodology = {
        "model": doc.get("model"),
        "model_family": "Brinson-Fachler (arithmetic, single-period)",
        "return_basis": "arithmetic (additive); base return = local return + currency return",
        "interaction": "reported as a separate effect",
        "currency": "arithmetic currency effect = active weight x period currency return",
        "linking": "none (single period); multi-period geometric linking is out of scope",
        "factor_attribution": "out of scope for this deterministic engine (route to the quant/risk team)",
        "benchmark_id": doc.get("benchmark_id"),
        "config_version": doc.get("config_version"),
        "template_version": doc.get("template_version", "attribution-template@0.1.0"),
    }

    attribution_summary = {
        "attribution_id": doc.get("attribution_id"),
        "portfolio_id": doc.get("portfolio_id"),
        "benchmark_id": doc.get("benchmark_id"),
        "period": doc.get("period"),
        "base_currency": base,
        "config_version": doc.get("config_version"),
        "template_version": methodology["template_version"],
        "counts": {
            "segments": len(segments),
            "segments_attributed": len(complete),
            "segments_needs_data": len(incomplete),
            "open_items": len(open_items),
            "approvals_recorded": len(approvals["recorded"]),
            "approvals_outstanding": len(approvals["outstanding"]),
        },
    }

    portfolio_benchmark = {
        "portfolio_return": rp, "benchmark_return": rb, "active_return": active,
        "portfolio_return_local": rp_local, "benchmark_return_local": rb_local,
        "portfolio_currency_return": port_ccy, "benchmark_currency_return": bench_ccy,
        "citations": source_index[:] or None,
    }

    return {
        "config_version": doc.get("config_version"),
        "attribution_id": doc.get("attribution_id"),
        "period": doc.get("period"),
        "base_currency": base,
        "template_version": methodology["template_version"],
        "build_status": "draft-attribution",
        "human_approval_required_before_delivery": True,
        "sections": {
            "attribution_summary": attribution_summary,
            "portfolio_benchmark": portfolio_benchmark,
            "segment_attribution": segment_attribution,
            "effect_totals": effect_totals,
            "currency_attribution": currency_attribution,
            "reconciliation": reconciliation,
            "methodology": methodology,
            "qa_checks": qa_checks,
            "open_items": open_items,
            "approvals": approvals,
            "weight_coverage": weight_coverage,
            "source_index": source_index,
        },
        "open_items": open_items,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "attribution_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
