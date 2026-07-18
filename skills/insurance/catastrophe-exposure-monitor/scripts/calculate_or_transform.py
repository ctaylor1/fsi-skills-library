#!/usr/bin/env python3
"""Deterministic catastrophe-exposure accumulation and threshold-breach engine.

Reads an exposure snapshot (see validate_input.py / references/source-map.md): the in-force
portfolio of insured locations, the current event footprints, modeled-loss data, source
timestamps, versioned thresholds, and the prior run's alert keys. It computes, per event:

  - zone accumulations (aggregate exposed limit and TIV inside each footprint zone/peril),
  - single-location exposure breaches,
  - event modeled-loss ranges (low / mid / high) and appetite breaches (tail estimate),
  - a source-freshness report and confidence flag,
  - data gaps (ungeocoded, stale valuation, unmodeled),
  - deduplication vs the prior run (new / ongoing / cleared),
  - a deterministic severity band and suggested response priority per alert.

IMPORTANT: This is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor. It computes exposure
estimates and packages alerts for a human queue. It NEVER binds/declines coverage, changes
limits or capacity, buys/cedes reinsurance, adjusts reserves, closes an alert, or writes any
system of record. Thresholds are versioned config (references/domain-rules.md); every figure
is an estimate for a human to act on.

Usage:
  python calculate_or_transform.py exposure_snapshot.json | --selftest
Prints the alert-queue package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; exposure and modeled-loss figures are estimates for "
              "human review. No underwriting, reinsurance, capacity, reserving, or "
              "system-of-record action has been taken.")

DEFAULT_CONFIG = {
    "zone_accum_limit": {"default": 20000000},
    "single_location_max": 10000000,
    "modeled_loss_appetite": 50000000,
    "approaching_ratio": 0.9,
    "stale_valuation_years": 3,
    "max_source_staleness_hours": {"default": 24},
}

# Deterministic severity banding by exceedance ratio (metric / threshold).
# Mirrored in validate_output.py — keep the two in lockstep.
PRIORITY = {"Critical": "P1", "Elevated": "P2", "Watch": "P3", "Informational": "P4"}


def band_for_ratio(r: float, approaching: float = 0.9) -> str | None:
    if r >= 1.5:
        return "Critical"
    if r >= 1.25:
        return "Elevated"
    if r >= 1.0:
        return "Watch"
    if r >= approaching:
        return "Informational"
    return None


def _parse_dt(s: str) -> datetime:
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.strptime(s[:10], "%Y-%m-%d")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _zone_limit(cfg: dict, zone: str) -> float:
    zl = cfg.get("zone_accum_limit") or {}
    if isinstance(zl, dict):
        return float(zl.get(zone, zl.get("default", 20000000)))
    return float(zl)


def _freshness(sources: list, run_dt: datetime, cfg: dict) -> tuple[list, bool]:
    limits = cfg.get("max_source_staleness_hours") or {}
    default_h = float(limits.get("default", 24))
    out, degraded = [], False
    for s in sources or []:
        name = s.get("source", "?")
        age_h = None
        if s.get("as_of"):
            age_h = round((run_dt - _parse_dt(s["as_of"])).total_seconds() / 3600.0, 2)
        max_h = float(limits.get(name, default_h))
        stale = age_h is None or age_h > max_h
        if stale:
            degraded = True
        out.append({"source": name, "as_of": s.get("as_of"), "age_hours": age_h,
                    "max_staleness_hours": max_h, "freshness": "stale" if stale else "fresh"})
    return out, degraded


def _data_gaps(locations: list, run_dt: datetime, cfg: dict) -> list:
    gaps = []
    stale_years = float(cfg.get("stale_valuation_years", 3))
    for loc in locations or []:
        lid = loc.get("location_id", "?")
        if not loc.get("geocoded", False):
            gaps.append({"location_id": lid, "gap": "ungeocoded_excluded",
                         "detail": "no geocode; excluded from accumulation"})
        if loc.get("valuation_date"):
            age_y = (run_dt - _parse_dt(loc["valuation_date"])).days / 365.25
            if age_y > stale_years:
                gaps.append({"location_id": lid, "gap": "stale_valuation",
                             "detail": f"valuation {loc['valuation_date']} is {age_y:.1f}y old (> {stale_years}y)"})
        if loc.get("geocoded", False) and not loc.get("modeled_loss"):
            gaps.append({"location_id": lid, "gap": "unmodeled",
                         "detail": "geocoded but no modeled_loss; excluded from modeled-loss range"})
    return gaps


def _exposed(locations: list, event: dict) -> list:
    zones = set(event.get("footprint_zones") or [])
    peril = event.get("peril")
    return [loc for loc in locations
            if loc.get("zone") in zones and peril in (loc.get("peril_exposed") or [])]


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    run_dt = _parse_dt(doc["as_of"])
    approaching = float(cfg.get("approaching_ratio", 0.9))
    locations = doc.get("locations") or []

    sources, degraded = _freshness(doc.get("sources"), run_dt, cfg)
    data_gaps = _data_gaps(locations, run_dt, cfg)

    active = []  # active alerts (new/ongoing) built this run

    def make(alert_key, event, zone, peril, breach_type, metric, threshold, evidence, detail):
        ratio = round(metric / threshold, 4) if threshold else 0.0
        band = band_for_ratio(ratio, approaching)
        if band is None:
            return None
        return {
            "alert_key": alert_key, "event_id": event["event_id"], "event_name": event.get("name"),
            "zone": zone, "peril": peril, "breach_type": breach_type,
            "metric": round(metric, 2), "threshold": round(threshold, 2), "exceedance_ratio": ratio,
            "severity": band, "suggested_response_priority": PRIORITY[band],
            "queue": doc.get("queue", "catastrophe-risk-review"),
            "reason": detail, "evidence": evidence,
        }

    for event in doc.get("events") or []:
        peril = event.get("peril")
        exposed = _exposed(locations, event)
        geo = [l for l in exposed if l.get("geocoded", False)]

        # zone accumulation (aggregate exposed limit), per zone
        by_zone: dict[str, list] = {}
        for loc in geo:
            by_zone.setdefault(loc.get("zone"), []).append(loc)
        for zone, locs in sorted(by_zone.items()):
            agg_limit = sum(_num(l.get("limit")) or 0.0 for l in locs)
            agg_tiv = sum(_num(l.get("tiv")) or 0.0 for l in locs)
            zlimit = _zone_limit(cfg, zone)
            a = make(f"{event['event_id']}:{zone}:{peril}:zone_accumulation", event, zone, peril,
                     "zone_accumulation", agg_limit, zlimit,
                     [{"location_id": l["location_id"], "limit": l.get("limit"),
                       "citation": f"pas:{l.get('source_ref','?')}@{doc['as_of']}"} for l in locs],
                     f"aggregate exposed limit {agg_limit:,.0f} vs zone limit {zlimit:,.0f} "
                     f"(TIV {agg_tiv:,.0f}, {len(locs)} geocoded locations)")
            if a:
                a["aggregate_tiv"] = round(agg_tiv, 2)
                a["location_count"] = len(locs)
                active.append(a)

        # single-location exposure breaches
        smax = float(cfg.get("single_location_max", 10000000))
        for loc in geo:
            lim = _num(loc.get("limit")) or 0.0
            a = make(f"{event['event_id']}:{loc.get('zone')}:{peril}:single_location:{loc['location_id']}",
                     event, loc.get("zone"), peril, "single_location", lim, smax,
                     [{"location_id": loc["location_id"], "limit": loc.get("limit"),
                       "citation": f"pas:{loc.get('source_ref','?')}@{doc['as_of']}"}],
                     f"location {loc['location_id']} limit {lim:,.0f} vs single-location max {smax:,.0f}")
            if a:
                active.append(a)

        # event modeled-loss range and appetite breach (tail / high estimate)
        modeled = [l for l in geo if l.get("modeled_loss")]
        if modeled:
            low = sum(_num(l["modeled_loss"].get("low")) or 0.0 for l in modeled)
            mid = sum(_num(l["modeled_loss"].get("mid")) or 0.0 for l in modeled)
            high = sum(_num(l["modeled_loss"].get("high")) or 0.0 for l in modeled)
            appetite = float(cfg.get("modeled_loss_appetite", 50000000))
            a = make(f"{event['event_id']}:EVENT:{peril}:modeled_loss", event, "EVENT", peril,
                     "modeled_loss", high, appetite,
                     [{"metric": "modeled_high", "value": round(high, 2),
                       "citation": f"model:{event.get('source_ref','?')}@{doc['as_of']}"}],
                     f"event modeled loss range low {low:,.0f} / mid {mid:,.0f} / high {high:,.0f}; "
                     f"tail (high) vs appetite {appetite:,.0f}")
            if a:
                a["modeled_range"] = {"low": round(low, 2), "mid": round(mid, 2), "high": round(high, 2)}
                a["modeled_locations"] = len(modeled)
                active.append(a)

    # deduplication vs prior run
    prior = set(doc.get("prior_alerts") or [])
    active_keys = {a["alert_key"] for a in active}
    for a in active:
        a["status"] = "ongoing" if a["alert_key"] in prior else "new"
    cleared = [{"alert_key": k, "status": "cleared",
                "reason": "no longer breaching this run (metric fell below threshold or exposure removed)"}
               for k in sorted(prior - active_keys)]

    alerts = active + cleared
    dedup = {
        "new": sum(1 for a in active if a["status"] == "new"),
        "ongoing": sum(1 for a in active if a["status"] == "ongoing"),
        "cleared": len(cleared),
    }
    overall = "Informational"
    order = ["Informational", "Watch", "Elevated", "Critical"]
    for a in active:
        if order.index(a["severity"]) > order.index(overall):
            overall = a["severity"]
    if not active:
        overall = "None"

    return {
        "run_id": doc.get("run_id", f"cem-{str(doc['as_of'])[:10]}-0001"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "queue": doc.get("queue", "catastrophe-risk-review"),
        "confidence": "degraded" if degraded else "normal",
        "sources": sources,
        "alerts": alerts,
        "dedup": dedup,
        "data_gaps": data_gaps,
        "overall_severity": overall,
        "disclaimer": DISCLAIMER,
    }


def _selfcheck(pkg: dict) -> list[str]:
    """Internal consistency invariants for the --selftest fixture (deterministic)."""
    errs = []
    active = [a for a in pkg["alerts"] if a.get("status") in ("new", "ongoing")]
    for a in active:
        if band_for_ratio(a["exceedance_ratio"]) != a["severity"]:
            errs.append(f"{a['alert_key']}: severity does not match exceedance_ratio")
        if PRIORITY.get(a["severity"]) != a["suggested_response_priority"]:
            errs.append(f"{a['alert_key']}: priority does not match severity")
        if not a.get("evidence"):
            errs.append(f"{a['alert_key']}: active alert missing evidence")
    dd = pkg["dedup"]
    if dd["new"] != sum(1 for a in active if a["status"] == "new"):
        errs.append("dedup new count does not tie")
    if dd["ongoing"] != sum(1 for a in active if a["status"] == "ongoing"):
        errs.append("dedup ongoing count does not tie")
    if dd["cleared"] != sum(1 for a in pkg["alerts"] if a.get("status") == "cleared"):
        errs.append("dedup cleared count does not tie")
    if not any(s.get("freshness") == "stale" for s in pkg["sources"]) and pkg["confidence"] == "degraded":
        errs.append("confidence degraded but no stale source")
    return errs


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exposure_snapshot.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        pkg = compute(doc)
        print(json.dumps(pkg, indent=2))
        errs = _selfcheck(pkg)
        for e in errs:
            print("ERROR", e)
        print(f"compute self-check: {len(errs)} error(s)")
        return 1 if errs else 0
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
