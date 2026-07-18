#!/usr/bin/env python3
"""Deterministic merchant-fee decomposition and savings-opportunity estimation.

Reads a merchant processing statement (see validate_input.py), decomposes fees into
interchange / network assessments / processor markup, and estimates transparent, evidenced
savings opportunities:
  - pricing_model_switch   (markup above an interchange-plus benchmark)
  - downgrade_recovery     (interchange downgrades vs the qualified category)
  - level_2_3_enablement   (commercial/corporate cards submitted at Level 1 only)

IMPORTANT: This produces *estimates and options with stated assumptions* only. It never
guarantees savings and never recommends a binding decision to sign, terminate, or change a
processor or contract. Every estimate is a RANGE with a conservative low band. All benchmarks
are versioned configuration (see references/domain-rules.md), not hard-coded judgments.

Usage:
  python calculate_or_transform.py statement.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "interchange_plus_markup_bps": 25.0,   # competitive interchange-plus markup benchmark
    "target_effective_rate_bps": 250.0,    # informational effective-rate benchmark
    "level23_eligible_card_types": ["visa_commercial", "visa_corporate", "mc_commercial",
                                    "mc_corporate", "amex_corporate"],
    "level23_savings_bps": 80.0,           # est. interchange reduction when L2/L3 supplied
    "downgrade_recoverable_share": 0.7,    # est. share of downgrade cost that is fixable
    "savings_low_band": 0.6,               # conservative floor applied to each estimate
    "savings_high_band": 1.0,              # ceiling = the point estimate (do not overpromise)
    "min_txn_count": 5,
}
DISCLAIMER = (
    "Estimated savings and analysis only, based on the stated assumptions and the statement "
    "period reviewed. This is not a guarantee of savings and not a recommendation to sign, "
    "terminate, or change any processor or contract; it is not legal, tax, or accounting "
    "advice. Interchange and network fees change frequently; validate against current "
    "published schedules and obtain human review before acting."
)


def _bps(part: float, whole: float) -> float:
    return round(part / whole * 10000, 2) if whole else 0.0


def _cite(t: dict, period: str) -> str:
    return f"stmt:{t.get('source_ref', '?')}@{period}"


def _band(cfg: dict, point: float) -> tuple[float, float, float]:
    return (round(point, 2),
            round(point * cfg["savings_low_band"], 2),
            round(point * cfg["savings_high_band"], 2))


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    period = str(doc["statement_period"])
    txns = doc["transactions"]
    eligible = {str(c).lower() for c in cfg["level23_eligible_card_types"]}

    volume = round(sum(float(t["amount"]) for t in txns), 2)
    interchange = round(sum(float(t["interchange_fee"]) for t in txns), 2)
    assessments = round(sum(float(t["assessment_fee"]) for t in txns), 2)
    markup = round(sum(float(t["processor_fee"]) for t in txns), 2)
    monthly_fixed = round(sum(float(f["amount"]) for f in (doc.get("processor") or {}).get("monthly_fees", [])), 2)
    total_fees = round(interchange + assessments + markup + monthly_fixed, 2)
    eff_bps = _bps(total_fees, volume)
    markup_bps = _bps(markup, volume)

    opportunities, not_evaluable = [], []

    def add(name, fired, description, point, assumptions, evidence, basis):
        mon, low, high = _band(cfg, point) if fired else (0.0, 0.0, 0.0)
        opportunities.append({
            "opportunity": name, "fired": bool(fired), "description": description,
            "est_savings_monthly": mon, "est_savings_low": low, "est_savings_high": high,
            "assumptions": assumptions if fired else [], "evidence": evidence if fired else [],
            "basis": basis,
        })

    # --- Opportunity A: pricing model / markup vs interchange-plus benchmark ---
    if doc["pricing_model"] in ("tiered", "blended", "flat"):
        bench = cfg["interchange_plus_markup_bps"]
        excess_bps = markup_bps - bench
        point = round(max(0.0, excess_bps) / 10000 * volume, 2)
        fired = point > 0
        add("pricing_model_switch", fired,
            "An interchange-plus structure prices interchange and assessments at pass-through "
            "with a fixed, transparent markup; the current implied markup exceeds the benchmark, "
            "so this pricing option could reduce processor markup on the same volume.",
            point,
            [f"Interchange-plus markup benchmark of {bench:.0f} bps is attainable for this merchant profile",
             "Interchange and network assessments pass through unchanged",
             "Excludes fixed monthly fees and any early-termination costs"],
            [{"line": "processor_markup", "markup_bps": markup_bps, "benchmark_bps": bench,
              "amount": markup, "citation": f"stmt:mid={doc['merchant_id']};line=processor_markup@{period}"}],
            {"implied_markup_bps": markup_bps, "benchmark_bps": bench, "volume": volume})
    else:
        not_evaluable.append({"opportunity": "pricing_model_switch",
                              "why": f"pricing_model '{doc['pricing_model']}' already pass-through/transparent"})

    # --- Opportunity B: interchange downgrade recovery ---
    downgraded = [t for t in txns if t.get("downgraded")]
    evaluable = [t for t in downgraded if t.get("qualified_interchange_fee") not in (None, "")]
    skipped = [t for t in downgraded if t.get("qualified_interchange_fee") in (None, "")]
    dg_cost = round(sum(max(0.0, float(t["interchange_fee"]) - float(t["qualified_interchange_fee"]))
                        for t in evaluable), 2)
    point_b = round(cfg["downgrade_recoverable_share"] * dg_cost, 2)
    ev_b = [{"txn_id": t["txn_id"], "interchange_category": t.get("interchange_category", "?"),
             "downgrade_cost": round(float(t["interchange_fee"]) - float(t["qualified_interchange_fee"]), 2),
             "citation": _cite(t, period)} for t in evaluable]
    add("downgrade_recovery", bool(evaluable) and point_b > 0,
        "Transactions cleared at a downgraded (non-qualified) interchange category cost more than "
        "the qualified category; correcting the data/process that caused the downgrade could recover "
        "part of that incremental cost.",
        point_b,
        [f"{cfg['downgrade_recoverable_share'] * 100:.0f}% of observed downgrade cost is recoverable via correct data and timely settlement",
         "Requires process or gateway/integration changes at the merchant",
         "Based on the reviewed statement period only"],
        ev_b, {"observed_downgrade_cost": dg_cost, "recoverable_share": cfg["downgrade_recoverable_share"]})
    if skipped:
        not_evaluable.append({"opportunity": "downgrade_recovery",
                              "why": f"{len(skipped)} downgraded txn(s) missing qualified_interchange_fee"})

    # --- Opportunity C: Level 2/3 enablement on commercial/corporate cards ---
    l23 = [t for t in txns if str(t.get("card_type", "")).lower() in eligible
           and str(t.get("level", "1")) == "1"]
    l23_volume = round(sum(float(t["amount"]) for t in l23), 2)
    point_c = round(cfg["level23_savings_bps"] / 10000 * l23_volume, 2)
    ev_c = [{"txn_id": t["txn_id"], "card_type": t["card_type"], "amount": float(t["amount"]),
             "level": str(t.get("level", "1")), "citation": _cite(t, period)} for t in l23]
    add("level_2_3_enablement", bool(l23) and point_c > 0,
        "Commercial/corporate-card transactions submitted with only Level 1 data may qualify for "
        "lower interchange when Level 2/Level 3 line-item data is supplied; enabling that data could "
        "reduce interchange on these transactions.",
        point_c,
        ["Level 2/Level 3 data can be captured and transmitted for these commercial-card transactions",
         f"Estimated interchange reduction of {cfg['level23_savings_bps']:.0f} bps per network schedules (validate against current tables)",
         "Merchant meets the qualification requirements for commercial-card programs"],
        ev_c, {"eligible_volume": l23_volume, "savings_bps": cfg["level23_savings_bps"]})

    fired_opps = [o for o in opportunities if o["fired"]]
    monthly_low = round(sum(o["est_savings_low"] for o in fired_opps), 2)
    monthly_high = round(sum(o["est_savings_high"] for o in fired_opps), 2)
    total = {"monthly_low": monthly_low, "monthly_high": monthly_high,
             "annual_low": round(monthly_low * 12, 2), "annual_high": round(monthly_high * 12, 2)}

    observations = [
        {"observation": "effective_rate", "value_bps": eff_bps, "benchmark_bps": cfg["target_effective_rate_bps"],
         "note": "Effective rate = total fees / volume. Benchmark comparison is informational only; "
                 "a higher effective rate can reflect card mix, ticket size, or channel, not just pricing."},
        {"observation": "fee_mix", "interchange_pct": _bps(interchange, total_fees) / 100 if total_fees else 0.0,
         "assessments_pct": _bps(assessments, total_fees) / 100 if total_fees else 0.0,
         "markup_pct": _bps(markup, total_fees) / 100 if total_fees else 0.0,
         "monthly_fixed_pct": _bps(monthly_fixed, total_fees) / 100 if total_fees else 0.0,
         "note": "Share of total fees. Interchange and assessments are largely non-negotiable pass-through."},
    ]

    contract = doc.get("contract") or {}
    contract_flags = []
    if contract.get("early_termination_fee"):
        contract_flags.append(f"Early-termination fee of {contract['early_termination_fee']} is on file; "
                              f"factor this into any evaluation (informational, not legal advice).")
    if contract.get("auto_renew"):
        contract_flags.append(f"Contract auto-renews with a {contract.get('notice_days', '?')}-day notice window; "
                              f"note the window when planning any evaluation (informational, not legal advice).")

    return {
        "analysis_id": f"mfo-{str(doc['merchant_id']).replace('*', '')}-{period}-0001",
        "merchant_id": doc["merchant_id"],
        "statement_period": period,
        "config_version": doc.get("config_version"),
        "currency": doc.get("currency", "USD"),
        "pricing_model": doc["pricing_model"],
        "totals": {"volume": volume, "txn_count": len(txns), "interchange": interchange,
                   "assessments": assessments, "processor_markup": markup,
                   "monthly_fixed": monthly_fixed, "total_fees": total_fees},
        "effective_rate_bps": eff_bps,
        "implied_markup_bps": markup_bps,
        "opportunities": opportunities,
        "total_estimated_savings": total,
        "observations": observations,
        "contract_flags": contract_flags,
        "not_evaluable": not_evaluable,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "statement_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
