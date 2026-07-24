#!/usr/bin/env python3
"""Deterministic portfolio-characteristic drift computation for portfolio-drift-monitor.

Reads a drift-input file (two APPROVED characteristic snapshots — current and prior — see
validate_input.py), computes the prior->current change for every comparable characteristic
(active weights, tracking error, duration, beta, factor exposures), flags changes whose
magnitude exceeds the configured attention band ("material drift"), flags characteristics
whose current value is at or near a supplied mandate reference ("limit proximity"), attaches
cited evidence to each, and maps the flagged set to a review-priority band. Emits a
machine-readable change-and-exception packet the SKILL wraps in a plain-language pack.

IMPORTANT: This produces explainable *changes, exceptions, and a triage suggestion* only. It
NEVER directs, recommends, or executes rebalancing or any trade; NEVER sets, modifies, or
overrides a mandate limit or band; and NEVER adjudicates a mandate breach. A characteristic
at/near a supplied mandate reference is ROUTED to mandate-compliance-monitor for the
authoritative limit test. The band/priority mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py drift_input.json | --selftest
Prints the change-and-exception JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "tracking_error_band": 0.50,   # abs change in ex-ante TE (%) that warrants review
    "duration_band": 0.50,         # abs change in effective duration (years)
    "beta_band": 0.10,             # abs change in beta vs benchmark
    "active_weight_band": 2.00,    # abs change in a bucket active weight (pct pts)
    "factor_band": 0.25,           # abs change in a factor exposure (std)
    "route_buffer": 0.25,          # proximity buffer to a supplied mandate reference
}
# Escalation is a fixed, documented constant (not tuned per portfolio); see domain-rules.md.
ESCALATE_EXCEPTION_COUNT = 4

# Scalar characteristics: name -> config band key.
SCALAR_BANDS = {
    "tracking_error": "tracking_error_band",
    "duration": "duration_band",
    "beta": "beta_band",
}
# Vector characteristic families: family -> (per-entry value field, config band key).
VECTOR_SPECS = {
    "active_weights": ("active_weight", "active_weight_band"),
    "factors": ("exposure", "factor_band"),
}
DISCLAIMER = ("Change and exception evidence only; not a rebalancing instruction or a "
              "compliance determination. No trade, rebalancing, or limit change has been "
              "made or directed.")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _cite(snap: dict, label: str) -> str:
    ref = ((snap.get("approval") or {}).get("source_ref")) or "risksys:?"
    return f"{ref}#{label}"


def _mandate(doc: dict) -> dict:
    return doc.get("mandate_reference") or {}


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    buf = float(cfg["route_buffer"])
    cur, pri = doc["current"], doc["prior"]
    mref = _mandate(doc)
    changes, not_evaluable = [], []

    def evidence():
        return [{"snapshot": "current", "citation": _cite(cur, "current")},
                {"snapshot": "prior", "citation": _cite(pri, "prior")}]

    def route_note(kind: str, reference) -> str:
        return (f"current {kind} is at or near the supplied mandate reference {reference}; "
                "route to mandate-compliance-monitor for the authoritative limit test")

    # ---- scalar characteristics -------------------------------------------------------
    for name, band_key in SCALAR_BANDS.items():
        cv, pv = _num(cur.get(name)), _num(pri.get(name))
        if cv is None or pv is None:
            not_evaluable.append({"characteristic": name, "family": "scalar",
                                  "why": "value absent in current and/or prior snapshot"})
            continue
        band = float(cfg[band_key])
        delta = round(cv - pv, 4)
        material = abs(delta) > band
        route, reference = False, None
        if name == "tracking_error" and _num(mref.get("tracking_error_max")) is not None:
            reference = _num(mref["tracking_error_max"])
            route = cv >= reference - buf
        elif name == "duration" and isinstance(mref.get("duration_band"), list) and len(mref["duration_band"]) == 2:
            lo, hi = _num(mref["duration_band"][0]), _num(mref["duration_band"][1])
            reference = [lo, hi]
            route = (lo is not None and cv <= lo + buf) or (hi is not None and cv >= hi - buf)
        changes.append({
            "characteristic": name, "family": "scalar", "key": name,
            "prior": pv, "current": cv, "delta": delta, "band": band,
            "material": material, "route_to_compliance": bool(route),
            "reference": reference,
            "reason": (f"{name} moved {delta:+.4f} vs prior (band {band})"
                       + ("; " + route_note(name, reference) if route else "")),
            "evidence": evidence(),
        })

    # ---- vector characteristic families ----------------------------------------------
    max_aw = _num(mref.get("max_active_weight"))
    for family, (value_field, band_key) in VECTOR_SPECS.items():
        band = float(cfg[band_key])
        cur_map = {e["key"]: _num(e.get(value_field)) for e in (cur.get(family) or []) if e.get("key") is not None}
        pri_map = {e["key"]: _num(e.get(value_field)) for e in (pri.get(family) or []) if e.get("key") is not None}
        for key in sorted(set(cur_map) | set(pri_map)):
            cv, pv = cur_map.get(key), pri_map.get(key)
            if cv is None or pv is None:
                not_evaluable.append({"characteristic": f"{family}:{key}", "family": family,
                                      "why": "bucket present in only one snapshot"})
                continue
            delta = round(cv - pv, 4)
            material = abs(delta) > band
            route, reference = False, None
            if family == "active_weights" and max_aw is not None:
                reference = max_aw
                route = abs(cv) >= max_aw - buf
            changes.append({
                "characteristic": f"{family}:{key}", "family": family, "key": key,
                "prior": pv, "current": cv, "delta": delta, "band": band,
                "material": material, "route_to_compliance": bool(route),
                "reference": reference,
                "reason": (f"active weight for {key} moved {delta:+.4f} vs prior (band {band})"
                           if family == "active_weights"
                           else f"factor exposure for {key} moved {delta:+.4f} vs prior (band {band})")
                          + ("; " + route_note(f"{family} {key}", reference) if route else ""),
                "evidence": evidence(),
            })

    # ---- exceptions, routing, priority ------------------------------------------------
    exceptions = []
    for c in changes:
        if c["material"] or c["route_to_compliance"]:
            types = []
            if c["material"]:
                types.append("material_drift")
            if c["route_to_compliance"]:
                types.append("limit_proximity")
            exceptions.append({
                "characteristic": c["characteristic"], "family": c["family"], "key": c["key"],
                "delta": c["delta"], "band": c["band"], "type": types,
                "reason": c["reason"], "evidence": c["evidence"],
            })

    route_items = [{"characteristic": c["characteristic"], "family": c["family"], "key": c["key"],
                    "current": c["current"], "reference": c["reference"]}
                   for c in changes if c["route_to_compliance"]]

    route_present = bool(route_items)
    if route_present or len(exceptions) >= ESCALATE_EXCEPTION_COUNT:
        priority = "Elevated"
    elif exceptions:
        priority = "Review"
    else:
        priority = "Informational"

    packet = {
        "packet_id": f"pdm-{doc['portfolio_id']}-{doc['as_of']}-0001",
        "portfolio_id": doc["portfolio_id"],
        "benchmark_id": doc.get("benchmark_id"),
        "as_of": doc["as_of"],
        "prior_as_of": doc["prior_as_of"],
        "config_version": doc.get("config_version"),
        "window": {"prior_as_of": doc["prior_as_of"], "as_of": doc["as_of"],
                   "label": doc.get("lookback_label")},
        "changes": changes,
        "exceptions": exceptions,
        "fired_exceptions": [f"{e['family']}:{e['key']}" for e in exceptions],
        "route_to_compliance": route_items,
        "not_evaluable": not_evaluable,
        "suggested_priority": priority,
        "disclaimer": DISCLAIMER,
    }
    if route_present:
        packet["handoff"] = {
            "skill": "mandate-compliance-monitor",
            "reason": ("One or more characteristics are at or near a supplied mandate "
                       "reference; mandate-compliance-monitor is the authoritative limit "
                       "test. This packet does not adjudicate the limit."),
            "items": route_items,
        }
    return packet


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "drift_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
