#!/usr/bin/env python3
"""Deterministic, explainable credit-portfolio analytics for credit-risk-portfolio-analyzer.

Reads a portfolio file (see validate_input.py), computes transparent portfolio metrics
(quality, expected loss, delinquency, concentration, collateral, migration, vintage, and a
stress-scenario impact), and derives limit/threshold **exceptions** with row-level evidence.
Each exception cites the specific exposure rows behind it. A deterministic disposition band
(Stable / Watch / Elevated) is mapped from the exception severities.

IMPORTANT: This produces decision-support *findings, evidence, and a triage disposition*
only. It is R3 decision-support: it NEVER makes a credit decision (approval/adverse action),
sets a reserve/allowance, disposes of a limit breach, files, closes a case, or writes a
system of record. A human credit-risk officer / credit risk committee adjudicates every
exception. The disposition mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py portfolio.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "single_name_max_pct": 0.05,
    "sector_max_pct": 0.25,
    "geography_max_pct": 0.35,
    "delinquency_90plus_max_pct": 0.03,
    "max_ltv": 0.80,
    "el_budget_pct": 0.015,
    "downgrade_rate_max": 0.15,
    "scenario_el_max_pct": 0.025,
    "min_exposures": 10,
}
# Ordinal credit-grade scale (index increases as quality worsens). Used only for migration.
RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"]
DPD_BUCKETS = [("current", 0, 1), ("dpd_1_29", 1, 30), ("dpd_30_59", 30, 60),
               ("dpd_60_89", 60, 90), ("dpd_90plus", 90, 10 ** 9)]
DISCLAIMER = ("Decision-support analysis only; findings and evidence require human "
              "credit-risk adjudication. No credit decision, reserve or allowance "
              "determination, limit action, filing, or system-of-record change has been made.")
ADJUDICATION = ("This analysis is decision-support only. A human credit-risk officer / "
                "credit risk committee must adjudicate each exception before any credit "
                "decision, reserve or allowance determination, limit action, filing, case "
                "closure, or system-of-record change.")
# Exception codes that are always critical (drive an Elevated disposition).
CRITICAL_CODES = {"single_name_concentration", "sector_concentration", "delinquency_90plus"}


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _cite(e: dict, as_of: str) -> str:
    return f"loan_tape:{e.get('source_ref', 'exp=' + str(e.get('exposure_id', '?')))}@{as_of}"


def _bucket(dpd: float) -> str:
    for name, lo, hi in DPD_BUCKETS:
        if lo <= dpd < hi:
            return name
    return "current"


def _share_map(exposures, key, total):
    agg = {}
    for e in exposures:
        k = e.get(key)
        if k in (None, ""):
            continue
        agg[k] = agg.get(k, 0.0) + _num(e.get("ead"))
    return {k: (v / total if total else 0.0) for k, v in agg.items()}


def _hhi(shares) -> float:
    return round(sum(s * s for s in shares.values()), 6)


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("limits") or {})}
    as_of = doc["as_of"]
    exposures = doc["exposures"]
    total_ead = sum(_num(e.get("ead")) for e in exposures)
    exceptions, not_evaluable = [], []

    def add_exc(code, severity, finding, metric, threshold, observed, evidence, review):
        exceptions.append({
            "code": code, "severity": severity, "finding": finding,
            "metric": metric, "threshold": round(threshold, 6), "observed": round(observed, 6),
            "evidence": evidence, "recommended_review": review,
        })

    # ---- portfolio quality ----
    wavg_pd = (sum(_num(e.get("pd")) * _num(e.get("ead")) for e in exposures) / total_ead) if total_ead else 0.0
    wavg_lgd = (sum(_num(e.get("lgd")) * _num(e.get("ead")) for e in exposures) / total_ead) if total_ead else 0.0
    rating_dist = {}
    for e in exposures:
        r = e.get("rating") or "UNRATED"
        rating_dist[r] = rating_dist.get(r, 0.0) + _num(e.get("ead"))
    rating_dist = {k: round(v / total_ead, 4) if total_ead else 0.0 for k, v in rating_dist.items()}

    # ---- expected loss (EL = PD * LGD * EAD) ----
    for e in exposures:
        e["_el"] = _num(e.get("pd")) * _num(e.get("lgd")) * _num(e.get("ead"))
    expected_loss = sum(e["_el"] for e in exposures)
    el_pct = expected_loss / total_ead if total_ead else 0.0

    def top_el_evidence(pool, n=3):
        rows = sorted(pool, key=lambda x: x["_el"], reverse=True)[:n]
        return [{"exposure_id": e.get("exposure_id"), "el": round(e["_el"], 2),
                 "citation": _cite(e, as_of)} for e in rows]

    # ---- delinquency ----
    delinquency = {name: 0.0 for name, _, _ in DPD_BUCKETS}
    for e in exposures:
        delinquency[_bucket(_num(e.get("days_past_due")))] += _num(e.get("ead"))
    delinquency = {k: {"ead": round(v, 2), "pct": round(v / total_ead, 4) if total_ead else 0.0}
                   for k, v in delinquency.items()}
    dpd90_pct = delinquency["dpd_90plus"]["pct"]

    # ---- concentration ----
    obligor_shares = _share_map(exposures, "obligor_id", total_ead)
    sector_shares = _share_map(exposures, "sector", total_ead)
    geo_shares = _share_map(exposures, "geography", total_ead)

    def _top(shares):
        if not shares:
            return {"key": None, "pct": 0.0}
        k = max(shares, key=shares.get)
        return {"key": k, "pct": round(shares[k], 4)}

    # ---- collateral ----
    secured_ead = sum(_num(e.get("ead")) for e in exposures if _num(e.get("collateral_value")) > 0)
    unsecured_ead = total_ead - secured_ead
    ltv_num = sum(_num(e.get("ead")) for e in exposures if _num(e.get("collateral_value")) > 0)
    ltv_den = sum(_num(e.get("collateral_value")) for e in exposures if _num(e.get("collateral_value")) > 0)
    wavg_ltv = (ltv_num / ltv_den) if ltv_den else None

    # ---- migration (optional) ----
    pairs = [(e, e.get("prior_rating"), e.get("rating")) for e in exposures
             if e.get("prior_rating") in RATING_ORDER and e.get("rating") in RATING_ORDER]
    migration = None
    if pairs:
        downgraded, notches = [], 0
        for e, pr, cur in pairs:
            d = RATING_ORDER.index(cur) - RATING_ORDER.index(pr)
            notches += d
            if d > 0:
                downgraded.append(e)
        migration = {
            "rated_pairs": len(pairs),
            "downgrade_rate": round(len(downgraded) / len(pairs), 4),
            "net_notch_per_pair": round(notches / len(pairs), 4),
        }
    else:
        not_evaluable.append({"metric": "migration", "why": "no exposure has both prior_rating and rating on the graded scale"})

    # ---- vintage ----
    vint = {}
    for e in exposures:
        v = e.get("vintage") or "UNKNOWN"
        b = vint.setdefault(v, {"ead": 0.0, "dpd90": 0.0, "el": 0.0})
        b["ead"] += _num(e.get("ead"))
        b["el"] += e["_el"]
        if _num(e.get("days_past_due")) >= 90:
            b["dpd90"] += _num(e.get("ead"))
    vintage = [{"vintage": k, "ead": round(b["ead"], 2),
                "dpd_90plus_pct": round(b["dpd90"] / b["ead"], 4) if b["ead"] else 0.0,
                "el_pct": round(b["el"] / b["ead"], 4) if b["ead"] else 0.0}
               for k, b in sorted(vint.items())]

    # ---- scenario impact (optional) ----
    scenario = doc.get("scenario") or None
    scen_out = None
    if scenario:
        pm = _num(scenario.get("pd_multiplier"), 1.0)
        lm = _num(scenario.get("lgd_multiplier"), 1.0)
        stressed_el = sum(min(1.0, _num(e.get("pd")) * pm) * min(1.0, _num(e.get("lgd")) * lm) * _num(e.get("ead"))
                          for e in exposures)
        scen_out = {
            "name": scenario.get("name"), "pd_multiplier": pm, "lgd_multiplier": lm,
            "stressed_el": round(stressed_el, 2),
            "stressed_el_pct_ead": round(stressed_el / total_ead, 4) if total_ead else 0.0,
            "el_delta": round(stressed_el - expected_loss, 2),
        }
    else:
        not_evaluable.append({"metric": "scenario_impact", "why": "no scenario block supplied"})

    # ============================ exceptions ============================
    # single-name concentration
    over_obl = {k: v for k, v in obligor_shares.items() if v > cfg["single_name_max_pct"]}
    for obl, share in sorted(over_obl.items(), key=lambda kv: kv[1], reverse=True):
        rows = [e for e in exposures if e.get("obligor_id") == obl]
        add_exc("single_name_concentration", "critical",
                f"Obligor {obl} share {share*100:.2f}% exceeds single-name limit {cfg['single_name_max_pct']*100:.2f}%.",
                "single_name_pct", cfg["single_name_max_pct"], share,
                [{"exposure_id": e.get("exposure_id"), "obligor_id": obl, "ead": _num(e.get("ead")),
                  "citation": _cite(e, as_of)} for e in rows],
                "Route the single-name concentration exception to the credit risk committee for adjudication.")

    # sector concentration
    over_sec = {k: v for k, v in sector_shares.items() if v > cfg["sector_max_pct"]}
    for sec, share in sorted(over_sec.items(), key=lambda kv: kv[1], reverse=True):
        rows = [e for e in exposures if e.get("sector") == sec]
        add_exc("sector_concentration", "critical",
                f"Sector '{sec}' share {share*100:.2f}% exceeds sector limit {cfg['sector_max_pct']*100:.2f}%.",
                "sector_pct", cfg["sector_max_pct"], share,
                [{"exposure_id": e.get("exposure_id"), "sector": sec, "ead": _num(e.get("ead")),
                  "citation": _cite(e, as_of)} for e in rows[:8]],
                "Escalate the sector concentration to the credit risk committee for adjudication.")

    # geography concentration
    over_geo = {k: v for k, v in geo_shares.items() if v > cfg["geography_max_pct"]}
    for geo, share in sorted(over_geo.items(), key=lambda kv: kv[1], reverse=True):
        rows = [e for e in exposures if e.get("geography") == geo]
        add_exc("geography_concentration", "high",
                f"Geography '{geo}' share {share*100:.2f}% exceeds geography limit {cfg['geography_max_pct']*100:.2f}%.",
                "geography_pct", cfg["geography_max_pct"], share,
                [{"exposure_id": e.get("exposure_id"), "geography": geo, "ead": _num(e.get("ead")),
                  "citation": _cite(e, as_of)} for e in rows[:8]],
                "Refer the geographic concentration to portfolio management for review.")

    # 90+ delinquency
    if dpd90_pct > cfg["delinquency_90plus_max_pct"]:
        rows = [e for e in exposures if _num(e.get("days_past_due")) >= 90]
        add_exc("delinquency_90plus", "critical",
                f"90+ day delinquent balance {dpd90_pct*100:.2f}% of EAD exceeds threshold {cfg['delinquency_90plus_max_pct']*100:.2f}%.",
                "dpd_90plus_pct", cfg["delinquency_90plus_max_pct"], dpd90_pct,
                [{"exposure_id": e.get("exposure_id"), "days_past_due": _num(e.get("days_past_due")),
                  "ead": _num(e.get("ead")), "citation": _cite(e, as_of)} for e in rows],
                "Route delinquent exposures to workout / servicing review for human adjudication.")

    # collateral LTV
    over_ltv = [e for e in exposures if _num(e.get("collateral_value")) > 0
                and _num(e.get("ead")) / _num(e.get("collateral_value")) > cfg["max_ltv"]]
    if over_ltv:
        add_exc("collateral_ltv", "high",
                f"{len(over_ltv)} secured exposure(s) breach the maximum LTV limit {cfg['max_ltv']*100:.2f}%.",
                "max_ltv", cfg["max_ltv"],
                max(_num(e.get("ead")) / _num(e.get("collateral_value")) for e in over_ltv),
                [{"exposure_id": e.get("exposure_id"),
                  "ltv": round(_num(e.get("ead")) / _num(e.get("collateral_value")), 4),
                  "citation": _cite(e, as_of)} for e in over_ltv[:8]],
                "Refer over-LTV exposures for collateral revaluation and human review.")

    # EL vs budget
    if el_pct > cfg["el_budget_pct"]:
        add_exc("el_budget", "high",
                f"Portfolio expected loss {el_pct*100:.2f}% of EAD exceeds EL budget {cfg['el_budget_pct']*100:.2f}%.",
                "el_pct_ead", cfg["el_budget_pct"], el_pct,
                top_el_evidence(exposures),
                "Provide the EL breakdown to risk management; reserve/allowance decisions remain human.")

    # migration downgrade
    if migration and migration["downgrade_rate"] > cfg["downgrade_rate_max"]:
        rows = [e for e, pr, cur in pairs if RATING_ORDER.index(cur) > RATING_ORDER.index(pr)]
        add_exc("migration_downgrade", "medium",
                f"Downgrade rate {migration['downgrade_rate']*100:.2f}% exceeds threshold {cfg['downgrade_rate_max']*100:.2f}%.",
                "downgrade_rate", cfg["downgrade_rate_max"], migration["downgrade_rate"],
                [{"exposure_id": e.get("exposure_id"), "prior_rating": e.get("prior_rating"),
                  "rating": e.get("rating"), "citation": _cite(e, as_of)} for e in rows[:8]],
                "Summarize downgrade drift for the portfolio review meeting.")

    # scenario EL breach
    if scen_out and scen_out["stressed_el_pct_ead"] > cfg["scenario_el_max_pct"]:
        add_exc("scenario_el", "high",
                f"Stressed expected loss {scen_out['stressed_el_pct_ead']*100:.2f}% of EAD under '{scen_out['name']}' "
                f"exceeds stress threshold {cfg['scenario_el_max_pct']*100:.2f}%.",
                "scenario_el_pct_ead", cfg["scenario_el_max_pct"], scen_out["stressed_el_pct_ead"],
                top_el_evidence(exposures),
                "Provide the stressed-loss evidence to the stress-testing program; capital actions remain human.")

    # ---- deterministic disposition (see references/domain-rules.md) ----
    sev = {x["severity"] for x in exceptions}
    if "critical" in sev:
        disposition = "Elevated"
    elif exceptions:
        disposition = "Watch"
    else:
        disposition = "Stable"

    routing = []
    if exceptions:
        routing = [
            "Escalate every exception to a human credit-risk officer / credit risk committee for adjudication; this analysis decides nothing.",
            "For ongoing tracking of a flagged concentration, a human may engage the concentration-risk-monitor or key-risk-indicator-monitor skills.",
            "To document findings for committee, a human may route to the credit-memo-drafter (draft-only) skill.",
        ]

    pid = str(doc["portfolio_id"]).replace(" ", "")
    return {
        "analysis_id": f"crpa-{pid}-{as_of}-0001",
        "portfolio_id": doc["portfolio_id"],
        "as_of": as_of,
        "config_version": doc.get("config_version"),
        "currency": doc.get("currency"),
        "metrics": {
            "total_ead": round(total_ead, 2),
            "exposure_count": len(exposures),
            "obligor_count": len({e.get("obligor_id") for e in exposures if e.get("obligor_id")}),
            "weighted_avg_pd": round(wavg_pd, 6),
            "weighted_avg_lgd": round(wavg_lgd, 6),
            "expected_loss": round(expected_loss, 2),
            "el_pct_ead": round(el_pct, 6),
            "rating_distribution": rating_dist,
            "delinquency": delinquency,
            "dpd_90plus_pct": dpd90_pct,
            "concentration": {
                "single_name_hhi": _hhi(obligor_shares),
                "sector_hhi": _hhi(sector_shares),
                "geography_hhi": _hhi(geo_shares),
                "top_obligor": _top(obligor_shares),
                "top_sector": _top(sector_shares),
                "top_geography": _top(geo_shares),
            },
            "collateral": {
                "secured_pct": round(secured_ead / total_ead, 4) if total_ead else 0.0,
                "unsecured_pct": round(unsecured_ead / total_ead, 4) if total_ead else 0.0,
                "weighted_ltv_secured": round(wavg_ltv, 4) if wavg_ltv is not None else None,
            },
            "migration": migration,
            "vintage": vintage,
            "scenario": scen_out,
        },
        "exceptions": exceptions,
        "not_evaluable": not_evaluable,
        "suggested_disposition": disposition,
        "adjudication": ADJUDICATION,
        "recommended_routing": routing,
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
