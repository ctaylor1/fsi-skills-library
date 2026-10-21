#!/usr/bin/env python3
"""Deterministic output validation for portfolio-cashflow-forecaster.

Validates the final liquidity-forecast pack (the calculate_or_transform core + an author
narrative) before it is presented or delivered. Checks, in order of the archetype's validation
focus:

  1. Formula tie-outs (per scenario, re-derived independently, not trusted from the pack):
       - each bucket's inflows == sum(inflow_by_category); outflows == sum(outflow_by_category)
       - net_flow == inflows - outflows
       - closing_balance == opening_balance + net_flow; balance continuity across buckets
       - first bucket opening == opening_cash; cumulative_net is the running sum of net_flow
       - totals.net_over_horizon == sum(bucket net_flow) == sum(totals.by_category)
       - first_shortfall_bucket / min_closing_balance are internally consistent
  2. Reconciliation: any scenario carrying an approved-engine total must tie to it (fail closed).
  3. Scenario coverage: a 'base' scenario is present (the analyst supplies every scenario).
  4. Assumption provenance: every assumptions-log entry carries a non-empty provenance AND citation.
  5. Reproducibility: forecast_id and inputs_hash are present.
  6. Prohibited decision/advice (R2 boundary): no language that chooses/recommends a scenario,
     recommends or executes an asset sale/liquidation, or sets/recommends a liquidity buffer.
  7. Standing disclaimer present.

Usage:
  python validate_output.py forecast_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.01
DISCLAIMER = ("Illustrative liquidity cash-flow forecast for analytical purposes only, computed "
              "from analyst-supplied cash flows and scenarios; it does not choose or recommend a "
              "scenario, recommend or execute the sale or liquidation of any asset, set or "
              "recommend a liquidity buffer, or provide investment advice. A projected shortfall "
              "is a signal for human review, not a decision or instruction; outputs depend "
              "entirely on the stated assumptions, which a qualified human must review.")

# Affirmative decision/advice assertions an R2 forecast must NOT make. Worded to require a
# directed, imperative or recommending form so that factual narrative ("a projected shortfall
# appears under the analyst-supplied severe scenario") and the standing disclaimer (which is
# stripped before scanning) do not self-trip.
DECISION_PATTERNS = [
    r"\byou should\b",
    r"\bwe (recommend|advise|suggest)\b",
    r"\bi (recommend|advise|suggest)\b",
    r"\b(recommend|advise|suggest)(s|ed)? (selling|liquidating|raising cash|gating|suspending|"
    r"holding|choosing|setting the buffer|the (base|severe|adverse|stress|worst|best)[- a-z]*scenario)\b",
    r"\bthe recommended (scenario|buffer|action|liquidation)\b",
    r"\b(set|setting|increase|raise|lower|reduce|maintain|target|hold) (a |an |the |our )?"
    r"(minimum |target |required |additional )?(liquidity )?buffer (of|to|at|=)\b",
    r"\bbuffer should be\b",
    r"\b(the (correct|right|best|most likely) scenario|choose the (base|severe|adverse|stress|worst))\b",
    r"\b(sell|liquidate) (the|our|its|down|off) [a-z]",
    r"\b(gate|suspend) (the fund|redemptions)\b",
    r"\bactivate (a |the )?side pocket\b",
    r"\bguaranteed (liquidity|to cover|that|return)\b",
]


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _check_scenario(s: dict, opening_cash) -> list[str]:
    errors = []
    name = s.get("name", "?")
    rows = s.get("buckets") or []
    if not rows:
        return [f"scenario {name}: no forecast buckets"]

    prev_close = opening_cash
    run = 0.0
    computed_net_sum = 0.0
    for r in rows:
        inflows = _num(r.get("inflows"))
        outflows = _num(r.get("outflows"))
        net = _num(r.get("net_flow"))
        opening = _num(r.get("opening_balance"))
        closing = _num(r.get("closing_balance"))
        cum = _num(r.get("cumulative_net"))
        b = r.get("bucket")
        if None in (inflows, outflows, net, opening, closing, cum):
            errors.append(f"scenario {name} bucket {b}: missing inflows/outflows/net/opening/closing/cumulative")
            continue
        agg_in = round(sum(_num(v, 0.0) for v in (r.get("inflow_by_category") or {}).values()), 4)
        agg_out = round(sum(_num(v, 0.0) for v in (r.get("outflow_by_category") or {}).values()), 4)
        if abs(agg_in - inflows) > TOL:
            errors.append(f"scenario {name} bucket {b}: category-aggregation tie-out fails "
                          f"(sum(inflow_by_category) {agg_in} != inflows {inflows})")
        if abs(agg_out - outflows) > TOL:
            errors.append(f"scenario {name} bucket {b}: category-aggregation tie-out fails "
                          f"(sum(outflow_by_category) {agg_out} != outflows {outflows})")
        if abs(round(inflows - outflows, 4) - net) > TOL:
            errors.append(f"scenario {name} bucket {b}: net-flow tie-out fails "
                          f"(inflows {inflows} - outflows {outflows} != net_flow {net})")
        if abs(opening - prev_close) > TOL:
            errors.append(f"scenario {name} bucket {b}: balance-continuity tie-out fails "
                          f"(opening {opening} != prior closing {prev_close})")
        if abs(round(opening + net, 4) - closing) > TOL:
            errors.append(f"scenario {name} bucket {b}: balance-recursion tie-out fails "
                          f"(opening {opening} + net {net} != closing {closing})")
        run = round(run + net, 4)
        if abs(cum - run) > TOL:
            errors.append(f"scenario {name} bucket {b}: cumulative-net tie-out fails "
                          f"(cumulative_net {cum} != running sum {run})")
        computed_net_sum = round(computed_net_sum + net, 4)
        prev_close = closing

    totals = s.get("totals") or {}
    total_net = _num(totals.get("net_over_horizon"))
    if total_net is None:
        errors.append(f"scenario {name}: missing totals.net_over_horizon")
    else:
        if abs(total_net - computed_net_sum) > TOL:
            errors.append(f"scenario {name}: totals tie-out fails "
                          f"(net_over_horizon {total_net} != sum of bucket net_flow {computed_net_sum})")
        by_cat_sum = round(sum(_num(v, 0.0) for v in (totals.get("by_category") or {}).values()), 4)
        if abs(by_cat_sum - total_net) > TOL:
            errors.append(f"scenario {name}: category-total tie-out fails "
                          f"(sum(by_category) {by_cat_sum} != net_over_horizon {total_net})")

    # first-shortfall / min-closing internal consistency
    closings = [_num(r.get("closing_balance")) for r in rows if _num(r.get("closing_balance")) is not None]
    if closings:
        min_close = _num(s.get("min_closing_balance"))
        if min_close is not None and abs(min_close - round(min(closings), 4)) > TOL:
            errors.append(f"scenario {name}: min_closing_balance {min_close} != actual minimum {round(min(closings), 4)}")
        fs = s.get("first_shortfall_bucket")
        neg = [r.get("bucket") for r in rows if _num(r.get("closing_balance"), 0.0) < 0]
        if fs is None and neg:
            errors.append(f"scenario {name}: first_shortfall_bucket is null but bucket {neg[0]} closes negative")
        if fs is not None and not neg:
            errors.append(f"scenario {name}: first_shortfall_bucket {fs} set but no bucket closes negative")
        if fs is not None and neg and fs != neg[0]:
            errors.append(f"scenario {name}: first_shortfall_bucket {fs} != first negative bucket {neg[0]}")

    # reconciliation to an approved-engine total, if the scenario carries one (fail closed)
    rec = s.get("reconciliation")
    if isinstance(rec, dict):
        approved = _num(rec.get("approved_engine_net"))
        if approved is None:
            errors.append(f"scenario {name}: reconciliation present but approved_engine_net is not numeric")
        elif total_net is not None and abs(total_net - approved) > TOL:
            errors.append(f"scenario {name}: reconciliation does not tie "
                          f"(computed net {total_net} != approved-engine net {approved})")
        elif rec.get("matches") is False:
            errors.append(f"scenario {name}: reconciliation.matches is false")
    return errors


def _validate_legacy(pack: dict) -> list[str]:
    errors: list[str] = []
    scenarios = pack.get("scenarios") or []
    opening_cash = _num(pack.get("opening_cash"))
    if opening_cash is None:
        errors.append("missing opening_cash")
        opening_cash = 0.0

    names = {s.get("name") for s in scenarios}
    if "base" not in names:
        errors.append("missing required scenario 'base'")
    for s in scenarios:
        errors += _check_scenario(s, opening_cash)

    # assumption provenance
    log = pack.get("assumptions_log") or []
    if not log:
        errors.append("assumptions_log missing (provenance must be recorded for every assumption)")
    for a in log:
        if not (a.get("provenance") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing provenance")
        if not (a.get("citation") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing citation")

    # reproducibility
    if not (pack.get("forecast_id") or "").strip():
        errors.append("missing forecast_id (reproducibility)")
    if not (pack.get("inputs_hash") or "").strip():
        errors.append("missing inputs_hash (reproducibility)")

    # prohibited decision/advice scan over author free text — NOT the disclaimer.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("note", "")) for s in scenarios])
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/advice language detected: {m.group(0)!r} "
                          f"(R2 models and calculates; it does not choose scenarios, recommend or "
                          f"execute asset sales, or set liquidity buffers)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def validate(pack: dict, source_doc: dict | None = None) -> list[str]:
    """Require detached original input; do not authenticate it or approve narrative."""
    import runpy
    try:
        errors = _validate_legacy(pack)
    except (TypeError, ValueError, KeyError, AttributeError, OverflowError) as exc:
        return [f"malformed output: {exc}"]
    engine = runpy.run_path(str(Path(__file__).with_name("calculate_or_transform.py")))
    integrity = runpy.run_path(str(Path(__file__).with_name("native_integrity.py")))
    integrity["validate_reconstruction"](pack, engine["compute"], errors, original_input=source_doc)
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "forecast_pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    source_doc = None
    if "--input" in argv:
        source_doc = json.loads(Path(argv[argv.index("--input") + 1]).read_text(encoding="utf-8"))
    errors = validate(pack, source_doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
