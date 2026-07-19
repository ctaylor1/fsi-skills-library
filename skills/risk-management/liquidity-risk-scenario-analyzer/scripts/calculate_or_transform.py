#!/usr/bin/env python3
"""Deterministic liquidity stress computation for liquidity-risk-scenario-analyzer.

Reads a liquidity position file (see validate_input.py), and for each configured stress
scenario projects stressed inflows/outflows by time bucket, the running cumulative cash-flow
gap, the counterbalancing capacity (CBC) after stressed haircuts, the survival horizon, and a
coverage ratio. It then raises source-linked FINDINGS against the configured limits and maps
the finding set to an overall assessment band.

IMPORTANT: This produces explainable liquidity *findings, evidence, and proposed contingency
options* for human (Treasury / ALCO) adjudication only. It never makes a regulated liquidity
determination, approves a funding action, clears a limit breach, files a regulatory return, or
writes any system of record. The band mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py position.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = (
    "Liquidity stress analysis and evidence only; not a regulatory determination, funding "
    "decision, or limit action. All contingency measures are proposals requiring "
    "Treasury/ALCO adjudication. No funding action has been taken and no system of record "
    "has been updated."
)

# Severity ranking used to map the finding set to an overall assessment band.
SEVERITY_RANK = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}
BAND_BY_SEVERITY = {3: "Breach", 2: "Elevated", 1: "Watch", 0: "Within appetite"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _bucket_order(doc: dict) -> list[dict]:
    """Return buckets sorted by end_day ascending."""
    return sorted(doc["buckets"], key=lambda b: float(b["end_day"]))


def _cite(ref: str, as_of: str) -> str:
    return f"liq:{ref}@{as_of}"


def _rate(scenario: dict, key: str, category: str, default_key: str) -> float:
    rates = scenario.get(key) or {}
    if category in rates:
        return float(rates[category])
    return float(scenario.get(default_key, 1.0))


def _cbc(doc: dict, scenario: dict) -> tuple[float, list[dict]]:
    """Counterbalancing capacity after base + scenario stress haircuts, with per-asset detail."""
    addon = scenario.get("cb_haircut_addon") or {}
    total = 0.0
    detail = []
    for a in doc["counterbalancing"]:
        cls = a.get("asset_class", "")
        base = float(a.get("base_haircut", 0.0))
        extra = float(addon.get(cls, 0.0))
        eff = min(1.0, base + extra)
        avail = float(a["market_value"]) * (1.0 - eff)
        total += avail
        detail.append({
            "asset_id": a["asset_id"], "asset_class": cls,
            "market_value": float(a["market_value"]), "effective_haircut": round(eff, 4),
            "available": round(avail, 2),
            "citation": _cite(a.get("source_ref", a["asset_id"]), doc["as_of"]),
        })
    return round(total, 2), detail


def _run_scenario(doc: dict, scenario: dict, buckets: list[dict], limits: dict) -> dict:
    as_of = doc["as_of"]
    horizon = float(doc["reporting_horizon_days"])
    items = doc["positions"]
    cbc, cbc_detail = _cbc(doc, scenario)

    rows, cumulative = [], 0.0
    survival_days = None
    prev_end = 0.0
    for b in buckets:
        name = b["bucket"]
        end_day = float(b["end_day"])
        in_items = [it for it in items if it["bucket"] == name and it["direction"] == "inflow"]
        out_items = [it for it in items if it["bucket"] == name and it["direction"] == "outflow"]
        s_in = sum(float(it["amount"]) * _rate(scenario, "inflow_rates", it["category"], "default_inflow_rate")
                   for it in in_items)
        s_out = sum(float(it["amount"]) * _rate(scenario, "outflow_rates", it["category"], "default_outflow_rate")
                    for it in out_items)
        net = s_in - s_out
        cumulative += net
        position = cbc + cumulative
        rows.append({
            "bucket": name, "end_day": end_day,
            "stressed_inflow": round(s_in, 2), "stressed_outflow": round(s_out, 2),
            "net": round(net, 2), "cumulative_net": round(cumulative, 2),
            "liquidity_position": round(position, 2),
        })
        # survival horizon: last bucket end_day at which position stayed >= 0
        if position < 0 and survival_days is None:
            survival_days = prev_end
        prev_end = end_day
    if survival_days is None:
        survival_days = float(buckets[-1]["end_day"])

    net_cum_outflow = max(0.0, -cumulative)
    coverage = None if net_cum_outflow == 0 else round(cbc / net_cum_outflow, 4)
    peak_gap = round(min([r["cumulative_net"] for r in rows]), 2)

    findings = []
    min_surv = float(limits["min_survival_days"])
    if survival_days < min_surv:
        breach_row = next((r for r in rows if r["liquidity_position"] < 0), rows[-1])
        findings.append({
            "finding": "survival_horizon_breach", "severity": "CRITICAL",
            "detail": (f"survival horizon {survival_days:g}d < minimum {min_surv:g}d under "
                       f"scenario {scenario['scenario_id']}; net position turns negative in bucket "
                       f"'{breach_row['bucket']}'"),
            "evidence": [{
                "bucket": breach_row["bucket"], "liquidity_position": breach_row["liquidity_position"],
                "cumulative_net": breach_row["cumulative_net"], "counterbalancing_capacity": cbc,
                "citation": _cite(f"{doc['entity_id']};scenario={scenario['scenario_id']};bucket={breach_row['bucket']}", as_of),
            }],
        })
    min_cov = float(limits["min_coverage_ratio"])
    if coverage is not None and coverage < min_cov:
        findings.append({
            "finding": "coverage_ratio_breach", "severity": "HIGH",
            "detail": (f"stressed coverage ratio {coverage:.3f} < minimum {min_cov:g} over the "
                       f"{horizon:g}-day horizon under scenario {scenario['scenario_id']} "
                       f"(CBC {cbc:.2f} / net cumulative outflow {net_cum_outflow:.2f})"),
            "evidence": [{
                "counterbalancing_capacity": cbc, "net_cumulative_outflow": round(net_cum_outflow, 2),
                "coverage_ratio": coverage,
                "citation": _cite(f"{doc['entity_id']};scenario={scenario['scenario_id']};horizon={horizon:g}d", as_of),
            }],
        })

    return {
        "scenario_id": scenario["scenario_id"], "name": scenario.get("name", scenario["scenario_id"]),
        "counterbalancing_capacity": cbc, "cbc_detail": cbc_detail,
        "buckets": rows, "survival_horizon_days": survival_days,
        "coverage_ratio": coverage, "peak_cumulative_gap": peak_gap,
        "findings": findings,
    }


def _structural_findings(doc: dict, limits: dict) -> list[dict]:
    """Position-level findings independent of any single scenario (e.g. funding concentration)."""
    findings = []
    conc_limit = limits.get("concentration_limit_pct")
    if conc_limit is not None:
        outs = [it for it in doc["positions"] if it["direction"] == "outflow"]
        total = sum(float(it["amount"]) for it in outs) or 1.0
        by_cat: dict[str, float] = {}
        for it in outs:
            by_cat[it["category"]] = by_cat.get(it["category"], 0.0) + float(it["amount"])
        for cat, amt in sorted(by_cat.items(), key=lambda kv: -kv[1]):
            share = amt / total
            if share > float(conc_limit):
                ev_items = [it for it in outs if it["category"] == cat]
                findings.append({
                    "finding": "funding_concentration", "severity": "MEDIUM",
                    "detail": (f"funding category '{cat}' is {share:.1%} of maturing/contractual "
                               f"outflow notional, above the {float(conc_limit):.0%} concentration limit"),
                    "evidence": [{
                        "category": cat, "share": round(share, 4), "notional": round(amt, 2),
                        "item_ids": [it["item_id"] for it in ev_items],
                        "citation": _cite(f"{doc['entity_id']};category={cat}", doc["as_of"]),
                    }],
                })
                break  # report the single largest concentration only
    return findings


def _band(all_findings: list[dict]) -> str:
    top = 0
    for f in all_findings:
        top = max(top, SEVERITY_RANK.get(f.get("severity", ""), 0))
    return BAND_BY_SEVERITY[top]


def _proposed_actions(band: str) -> list[str]:
    if band == "Within appetite":
        return []
    return [
        "PROPOSAL (Treasury/ALCO adjudication required): monetize Level 1 HQLA via repo to cover the "
        "near-term cumulative gap; size against the survival-horizon bucket.",
        "PROPOSAL (Treasury/ALCO adjudication required): pre-position additional eligible collateral at "
        "the central-bank standing facility to extend counterbalancing capacity.",
        "PROPOSAL (Treasury/ALCO adjudication required): term out maturing wholesale unsecured funding to "
        "lengthen the maturity profile and reduce short-bucket rollover risk.",
        "PROPOSAL (Treasury/ALCO adjudication required): slow discretionary asset growth / new lending "
        "during the stress window to preserve liquidity.",
        "These are options for the Contingency Funding Plan owner to evaluate; none has been executed.",
    ]


def compute(doc: dict) -> dict:
    buckets = _bucket_order(doc)
    limits = doc["limits"]
    scen_results = [_run_scenario(doc, s, buckets, limits) for s in doc["scenarios"]]
    structural = _structural_findings(doc, limits)

    all_findings = structural + [f for sr in scen_results for f in sr["findings"]]
    band = _band(all_findings)

    # worst scenario = lowest survival horizon, then lowest coverage
    def _key(sr):
        cov = sr["coverage_ratio"] if sr["coverage_ratio"] is not None else float("inf")
        return (sr["survival_horizon_days"], cov)
    worst = min(scen_results, key=_key)["scenario_id"] if scen_results else None

    return {
        "analysis_id": f"lrsa-{str(doc['entity_id']).replace(' ', '')}-{doc['as_of']}-0001",
        "entity_id": doc["entity_id"],
        "as_of": doc["as_of"],
        "currency": doc.get("currency"),
        "config_version": doc.get("config_version"),
        "reporting_horizon_days": doc["reporting_horizon_days"],
        "limits": limits,
        "scenarios": scen_results,
        "structural_findings": structural,
        "worst_scenario": worst,
        "overall_assessment": band,
        "proposed_contingency_actions": _proposed_actions(band),
        "disclaimer": DISCLAIMER,
    }


def _selfcheck(doc: dict) -> tuple[dict, list[str]]:
    """Internal consistency + determinism checks used by --selftest."""
    errors = []
    a1 = compute(doc)
    a2 = compute(doc)
    if json.dumps(a1, sort_keys=True) != json.dumps(a2, sort_keys=True):
        errors.append("computation is not deterministic (two runs differ)")
    all_findings = a1["structural_findings"] + [f for sr in a1["scenarios"] for f in sr["findings"]]
    if a1["overall_assessment"] != _band(all_findings):
        errors.append("overall_assessment does not equal the deterministic band mapping")
    for f in all_findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f['finding']} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {f['finding']} evidence row missing citation")
    if a1["overall_assessment"] != "Within appetite" and not a1["proposed_contingency_actions"]:
        errors.append("findings present but no proposed contingency options supplied")
    return a1, errors


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "position_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        analysis, errors = _selfcheck(doc)
        print(json.dumps(analysis, indent=2))
        print(f"compute self-check: {len(errors)} error(s)")
        for e in errors:
            print("ERROR", e)
        return 1 if errors else 0
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
