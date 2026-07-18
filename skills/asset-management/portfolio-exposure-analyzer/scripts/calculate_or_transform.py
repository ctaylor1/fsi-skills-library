#!/usr/bin/env python3
"""Deterministic, source-linked exposure computation for portfolio-exposure-analyzer.

Reads a portfolio holdings file (see validate_input.py), aggregates exposures across issuer,
sector, country, currency, asset-class, duration, liquidity, and look-through holdings, then
screens each exposure against documented concentration limits. Emits a machine-readable core
the SKILL wraps in a plain-language, cited pack.

IMPORTANT: This produces explainable *exposure findings and a triage suggestion* only. It
never produces a mandate-compliance determination, an investment recommendation, or a trade
or portfolio action. The priority mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py portfolio.json | --selftest
Prints the exposure JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_LIMITS = {
    "single_issuer_max_pct": 5.0, "single_issuer_hard_pct": 10.0,
    "sector_max_pct": 25.0, "country_max_pct": 40.0,
    "non_base_currency_max_pct": 30.0,
    "illiquid_max_pct": 20.0, "illiquid_horizon_days": 7,
    "duration_target": 6.5, "duration_tolerance": 1.5,
    "home_country": "US",
    "issuer_sector_exempt_asset_classes": ["govt_bond", "cash"],
}
DISCLAIMER = ("Exposure analysis and evidence only; not a mandate-compliance determination or "
              "investment advice. No trade or portfolio action has been taken or recommended.")


def expected_priority(findings: list[dict]) -> str:
    """Deterministic mapping from the finding set to a review-priority band.

    Escalator = any over-hard issuer finding OR any liquidity finding. See domain-rules.md.
    """
    escalator = any(f.get("band") == "over_hard" for f in findings) or \
        any(f.get("dimension") == "liquidity" for f in findings)
    n = len(findings)
    if escalator or n >= 3:
        return "Elevated"
    if n >= 1:
        return "Review"
    return "Informational"


def _cite(p: dict, as_of: str) -> str:
    return f"pms:{p.get('source_ref','?')}@{as_of}"


def _cite_lt(p: dict, c: dict, as_of: str) -> str:
    return f"pms:{p.get('source_ref','?')}#lt={c.get('issuer','?')}@{as_of}"


def _attributions(positions: list[dict], as_of: str) -> list[dict]:
    """Flatten positions into attribution rows, applying look-through where present."""
    rows = []
    for p in positions:
        lt = p.get("look_through")
        mv = float(p["market_value"])
        if lt:
            for c in lt:
                rows.append({
                    "issuer": c.get("issuer"), "sector": c.get("sector"),
                    "country": c.get("country"), "currency": c.get("currency"),
                    "asset_class": p.get("asset_class"),
                    "market_value": mv * float(c["weight"]),
                    "position_id": p.get("position_id"),
                    "cite": _cite_lt(p, c, as_of), "look_through": True,
                })
        else:
            rows.append({
                "issuer": p.get("issuer"), "sector": p.get("sector"),
                "country": p.get("country"), "currency": p.get("currency"),
                "asset_class": p.get("asset_class"),
                "market_value": mv, "position_id": p.get("position_id"),
                "cite": _cite(p, as_of), "look_through": False,
            })
    return rows


def _agg(rows, dim, nav, exempt_ac=(), exempt_values=()):
    buckets = {}
    for r in rows:
        if r["asset_class"] in exempt_ac:
            continue
        v = r.get(dim)
        if not v or v in exempt_values:
            continue
        b = buckets.setdefault(v, {"bucket": v, "market_value": 0.0, "evidence": []})
        b["market_value"] += r["market_value"]
        b["evidence"].append({"position_id": r["position_id"],
                              "market_value": round(r["market_value"], 2),
                              "citation": r["cite"]})
    out = []
    for b in buckets.values():
        b["pct"] = round(b["market_value"] / nav * 100, 2)
        b["market_value"] = round(b["market_value"], 2)
        out.append(b)
    out.sort(key=lambda x: -x["pct"])
    return out


def compute(doc: dict) -> dict:
    lim = {**DEFAULT_LIMITS, **(doc.get("limits") or {})}
    positions = doc["positions"]
    as_of = doc["as_of"]
    nav = round(sum(float(p["market_value"]) for p in positions), 2)
    exempt_ac = tuple(lim["issuer_sector_exempt_asset_classes"])
    home = lim.get("home_country")

    rows = _attributions(positions, as_of)

    issuer_exp = _agg(rows, "issuer", nav, exempt_ac=exempt_ac)
    sector_exp = _agg(rows, "sector", nav, exempt_ac=exempt_ac)
    country_exp = _agg(rows, "country", nav, exempt_values=(home,) if home else ())
    currency_exp = _agg(rows, "currency", nav)
    asset_class_exp = _agg(rows, "asset_class", nav)

    # non-base currency aggregate
    base = doc["base_currency"]
    non_base_mv = sum(b["market_value"] for b in currency_exp if b["bucket"] != base)
    non_base_pct = round(non_base_mv / nav * 100, 2)

    # liquidity (position-level, not look-through split)
    horizon = lim["illiquid_horizon_days"]
    liq_buckets = {"<=1d": 0.0, "<=7d": 0.0, "<=30d": 0.0, ">30d": 0.0}
    illiquid_mv, illiquid_ev = 0.0, []
    liq_evaluable = True
    for p in positions:
        d = p.get("liquidity_days")
        mv = float(p["market_value"])
        if d is None:
            liq_evaluable = False
            continue
        d = float(d)
        if d <= 1:
            liq_buckets["<=1d"] += mv
        elif d <= 7:
            liq_buckets["<=7d"] += mv
        elif d <= 30:
            liq_buckets["<=30d"] += mv
        else:
            liq_buckets[">30d"] += mv
        if d > horizon:
            illiquid_mv += mv
            illiquid_ev.append({"position_id": p.get("position_id"), "liquidity_days": d,
                                "market_value": round(mv, 2), "citation": _cite(p, as_of)})
    illiquid_pct = round(illiquid_mv / nav * 100, 2)

    # duration (FI sleeve)
    fi = [p for p in positions if p.get("asset_class") in ("corp_bond", "govt_bond")
          and p.get("modified_duration") is not None]
    duration = None
    if fi:
        sleeve_mv = sum(float(p["market_value"]) for p in fi)
        wdur = sum(float(p["market_value"]) * float(p["modified_duration"]) for p in fi)
        sleeve_dur = round(wdur / sleeve_mv, 3) if sleeve_mv else 0.0
        duration = {
            "fi_sleeve_market_value": round(sleeve_mv, 2),
            "fi_sleeve_modified_duration": sleeve_dur,
            "portfolio_duration_contribution": round(wdur / nav, 3),
            "target": lim["duration_target"], "tolerance": lim["duration_tolerance"],
            "evidence": [{"position_id": p.get("position_id"),
                          "modified_duration": p.get("modified_duration"),
                          "citation": _cite(p, as_of)} for p in fi],
        }

    # factor exposure (only if loadings present)
    fac_positions = [p for p in positions if p.get("factors")]
    if fac_positions:
        factors = {}
        for p in fac_positions:
            w = float(p["market_value"]) / nav
            for name, load in p["factors"].items():
                factors[name] = round(factors.get(name, 0.0) + w * float(load), 4)
        coverage = round(sum(float(p["market_value"]) for p in fac_positions) / nav * 100, 2)
        factor_exp = {"net_exposure": factors, "coverage_pct": coverage}
        not_evaluable = []
    else:
        factor_exp = None
        not_evaluable = [{"dimension": "factor",
                          "why": "no factor loadings on any position (requires factor-model service)"}]

    # ---- concentration screen -> findings ----
    findings = []

    for b in issuer_exp:
        if b["pct"] > lim["single_issuer_hard_pct"]:
            band, limit = "over_hard", lim["single_issuer_hard_pct"]
        elif b["pct"] > lim["single_issuer_max_pct"]:
            band, limit = "over_soft", lim["single_issuer_max_pct"]
        else:
            continue
        findings.append({"dimension": "issuer", "bucket": b["bucket"], "pct": b["pct"],
                         "limit_pct": limit, "band": band,
                         "excess_pct": round(b["pct"] - limit, 2),
                         "reason": f"issuer exposure {b['pct']}% exceeds the documented limit of {limit}% (look-through applied)",
                         "evidence": b["evidence"]})

    for b in sector_exp:
        if b["pct"] > lim["sector_max_pct"]:
            findings.append({"dimension": "sector", "bucket": b["bucket"], "pct": b["pct"],
                             "limit_pct": lim["sector_max_pct"], "band": "over_soft",
                             "excess_pct": round(b["pct"] - lim["sector_max_pct"], 2),
                             "reason": f"sector exposure {b['pct']}% exceeds the documented limit of {lim['sector_max_pct']}%",
                             "evidence": b["evidence"]})

    for b in country_exp:
        if b["pct"] > lim["country_max_pct"]:
            findings.append({"dimension": "country", "bucket": b["bucket"], "pct": b["pct"],
                             "limit_pct": lim["country_max_pct"], "band": "over_soft",
                             "excess_pct": round(b["pct"] - lim["country_max_pct"], 2),
                             "reason": f"country exposure {b['pct']}% exceeds the documented limit of {lim['country_max_pct']}% (home country {home} exempt)",
                             "evidence": b["evidence"]})

    if non_base_pct > lim["non_base_currency_max_pct"]:
        cur_ev = []
        for b in currency_exp:
            if b["bucket"] != base:
                cur_ev.extend(b["evidence"])
        findings.append({"dimension": "currency", "bucket": f"non-base (vs {base})",
                         "pct": non_base_pct, "limit_pct": lim["non_base_currency_max_pct"],
                         "band": "over_soft",
                         "excess_pct": round(non_base_pct - lim["non_base_currency_max_pct"], 2),
                         "reason": f"non-base-currency exposure {non_base_pct}% exceeds the documented limit of {lim['non_base_currency_max_pct']}%",
                         "evidence": cur_ev})

    if liq_evaluable and illiquid_pct > lim["illiquid_max_pct"]:
        findings.append({"dimension": "liquidity", "bucket": f">{horizon}d horizon",
                         "pct": illiquid_pct, "limit_pct": lim["illiquid_max_pct"],
                         "band": "over_limit",
                         "excess_pct": round(illiquid_pct - lim["illiquid_max_pct"], 2),
                         "reason": f"{illiquid_pct}% of NAV liquidatable only beyond the {horizon}-day horizon, exceeding the documented limit of {lim['illiquid_max_pct']}%",
                         "evidence": illiquid_ev})

    if duration is not None:
        lo = lim["duration_target"] - lim["duration_tolerance"]
        hi = lim["duration_target"] + lim["duration_tolerance"]
        sd = duration["fi_sleeve_modified_duration"]
        if sd < lo or sd > hi:
            side = "below" if sd < lo else "above"
            findings.append({"dimension": "duration", "bucket": "fi_sleeve",
                             "pct": sd, "limit_pct": lim["duration_target"], "band": "over_soft",
                             "excess_pct": round(sd - lim["duration_target"], 2),
                             "reason": f"fixed-income sleeve modified duration {sd} is {side} the documented tolerance band [{round(lo,2)}, {round(hi,2)}]",
                             "evidence": duration["evidence"]})

    if not liq_evaluable:
        not_evaluable.append({"dimension": "liquidity",
                              "why": "one or more positions missing liquidity_days"})

    priority = expected_priority(findings)
    fired = [f"{f['dimension']}:{f['bucket']}" for f in findings]

    considerations = []
    if findings:
        considerations = [
            "Concentration may reflect the benchmark's own weights (active vs absolute exposure differ).",
            "An intended, mandate-permitted tilt or thematic sleeve.",
            "Look-through of a pooled vehicle can shift issuer/sector attribution — verify the constituent data date.",
            "FX or duration exposure may be offset by overlays not present in the holdings file.",
            "An illiquid sleeve may sit within a documented private-assets bucket allowance.",
            "Sovereign and cash positions are exempt from issuer/sector limits by config.",
        ]

    return {
        "exposure_id": f"pea-{doc['portfolio_id']}-{as_of}-0001",
        "portfolio_id": doc["portfolio_id"],
        "as_of": as_of,
        "base_currency": base,
        "config_version": doc.get("config_version"),
        "benchmark_id": doc.get("benchmark_id"),
        "nav": nav,
        "limits": lim,
        "exposures": {
            "issuer": issuer_exp,
            "sector": sector_exp,
            "country": country_exp,
            "currency": currency_exp,
            "asset_class": asset_class_exp,
            "non_base_currency_pct": non_base_pct,
            "liquidity": {"horizon_days": horizon, "buckets": {k: round(v, 2) for k, v in liq_buckets.items()},
                          "illiquid_pct": illiquid_pct},
            "duration": duration,
            "factor": factor_exp,
        },
        "findings": findings,
        "fired_findings": fired,
        "not_evaluable": not_evaluable,
        "suggested_priority": priority,
        "considerations": considerations,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "portfolio_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
