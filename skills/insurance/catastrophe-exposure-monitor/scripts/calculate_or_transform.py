#!/usr/bin/env python3
"""Read-only event-bound CAT exposure monitor; missing evidence never clears an alert."""
from __future__ import annotations
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
from insurance_contract import amount, build_artifact, iso_date, stable_hash, timestamp
from validate_input import validate

DISCLAIMER = ("Monitoring alert only; exposure and modeled-loss figures are estimates for "
              "human review. No underwriting, reinsurance, capacity, reserving, or "
              "system-of-record action has been taken.")
DEFAULT_CONFIG = {"zone_accum_limit": {"default": 20000000}, "single_location_max": 10000000,
                  "modeled_loss_appetite": 50000000, "approaching_ratio": 0.9,
                  "stale_valuation_years": 3, "max_source_staleness_hours": {"default": 24}}
PRIORITY = {"Critical": "P1", "Elevated": "P2", "Watch": "P3", "Informational": "P4"}


def band_for_ratio(r, approaching=0.9):
    r, approaching = amount(r), amount(approaching)
    for boundary, label in (("1.5", "Critical"), ("1.25", "Elevated"), ("1", "Watch")):
        if r >= amount(boundary):
            return label
    return "Informational" if r >= approaching else None


def compute(doc):
    errors, warnings = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    cfg = {**DEFAULT_CONFIG, **doc.get("config", {})}
    run_dt = timestamp(doc["as_of"])
    approaching = amount(cfg["approaching_ratio"])
    locations = doc.get("locations", [])
    issues, gaps, sources, metrics, active = list(warnings), [], [], {}, []
    source_rows = {s["source"]: s for s in doc.get("sources", [])}
    metadata = build_artifact(doc, {}, producer="catastrophe-exposure-monitor", artifact_type="metadata-check")
    issues.extend(metadata["unresolved_issues"])
    if doc.get("exposure_snapshot_id") != source_rows.get("policy_admin", {}).get("version"):
        issues.append("exposure_snapshot_id does not match policy_admin source version")
    limits = cfg["max_source_staleness_hours"]
    for role in ("policy_admin", "event_feed", "cat_model"):
        source = source_rows.get(role, {})
        age = None
        state = "unknown"
        max_h = amount(limits.get(role, limits.get("default", 24)))
        try:
            age = (run_dt - timestamp(source.get("as_of"))).total_seconds() / 3600
            state = "future" if age < 0 else "stale" if amount(age) > max_h else "fresh"
        except (TypeError, ValueError):
            pass
        if state != "fresh" or not source.get("source_ref") or not source.get("version"):
            issues.append(f"{role}: freshness/provenance unavailable or {state}")
        sources.append({"source": role, "as_of": source.get("as_of"), "source_ref": source.get("source_ref"),
                        "version": source.get("version"), "age_hours": age, "max_staleness_hours": float(max_h), "freshness": state})
    finance = doc.get("financial_context")
    if not isinstance(finance, dict):
        finance = {}
    basis_fields = ("currency", "unit", "financial_basis", "limit_grain")
    financial_ok = (isinstance(finance.get("currency"), str) and len(finance["currency"]) == 3 and finance["currency"].isupper()
                    and finance.get("unit") == "currency" and finance.get("financial_basis") in {"gross", "net", "ceded"}
                    and finance.get("limit_grain") == "location")
    if not financial_ok:
        issues.append("financial_context requires currency, currency unit, gross/net/ceded basis and allocated location limit grain")
    limit_ids = Counter(l.get("limit_id") for l in locations)

    def gap(location, kind, detail):
        gaps.append({"location_id": location.get("location_id"), "gap": kind, "detail": detail})

    usable = []
    for loc in locations:
        if loc.get("geocoded") is not True:
            gap(loc, "ungeocoded_excluded", "not included in geocoded metrics; no all-clear")
        if not loc.get("limit_id") or limit_ids[loc.get("limit_id")] > 1:
            gap(loc, "limit_grain_ambiguous", "unique allocated location limit_id required; shared policy limits must not be double-counted")
            continue
        if any(loc.get(k, finance.get(k)) != finance.get(k) for k in basis_fields):
            gap(loc, "incompatible_financial_basis", "location basis differs from run thresholds; no currency/basis conversion")
            continue
        if not loc.get("source_ref"):
            gap(loc, "missing_source", "source reference required")
            continue
        try:
            valuation = iso_date(loc.get("valuation_date"))
            age = (run_dt.date() - valuation).days / 365.25
            if age < 0 or amount(age) > amount(cfg["stale_valuation_years"]):
                gap(loc, "stale_valuation", "valuation date is stale or future")
        except ValueError:
            gap(loc, "unknown_valuation", "valuation date unavailable")
        if financial_ok and loc.get("geocoded") is True:
            usable.append(loc)

    policy_source = source_rows.get("policy_admin", {})
    exposure_complete = (bool(locations) and financial_ok and not gaps
                         and doc.get("data_coverage", {}).get("exposures") == "complete"
                         and policy_source.get("version") == doc.get("exposure_snapshot_id")
                         and bool(policy_source.get("source_ref"))
                         and next(s["freshness"] for s in sources if s["source"] == "policy_admin") == "fresh")

    def metric(key, event, zone, kind, value, threshold, evidence, extra=None):
        threshold = amount(threshold)
        ratio = value / threshold
        band = band_for_ratio(ratio, approaching)
        row = {"alert_key": key, "event_id": event["event_id"], "event_name": event.get("name"), "zone": zone,
               "peril": event["peril"], "breach_type": kind, "metric": str(value), "threshold": str(threshold),
               "exceedance_ratio": str(ratio), "financial_context": finance, "evidence": evidence,
               "footprint_version": event.get("footprint_version"), "exposure_snapshot_id": doc.get("exposure_snapshot_id")}
        if extra:
            row.update(extra)
        metrics[key] = row
        if band:
            active.append({**row, "severity": band, "suggested_response_priority": PRIORITY[band],
                           "queue": doc.get("queue", "catastrophe-risk-review"), "reason": f"{kind} {value} compared with {threshold}"})

    for event in doc.get("events", []):
        if not event.get("footprint_version") or not event.get("source_ref") or not event.get("footprint_zones"):
            issues.append(f"event {event['event_id']} lacks a versioned footprint; not evaluable")
            continue
        if (event.get("source_ref") != source_rows.get("event_feed", {}).get("source_ref")
                or event.get("footprint_version") != source_rows.get("event_feed", {}).get("version")):
            issues.append(f"event {event['event_id']} is not bound to the supplied event feed")
            continue
        exposed = [l for l in usable if l.get("zone") in event["footprint_zones"] and event["peril"] in l["peril_exposed"]]
        all_exposed = [l for l in locations if l.get("zone") in event["footprint_zones"] and event["peril"] in l["peril_exposed"]]
        for zone in sorted(set(event["footprint_zones"])):
            locs = [l for l in exposed if l["zone"] == zone]
            if not financial_ok:
                continue
            if not locs and not exposure_complete:
                issues.append(f"event {event['event_id']} zone {zone}: zero exposure not evaluable from incomplete/unavailable exposure evidence")
                continue
            limit = cfg["zone_accum_limit"].get(zone, cfg["zone_accum_limit"].get("default", 20000000))
            metric(f"{event['event_id']}:{zone}:{event['peril']}:zone_accumulation", event, zone, "zone_accumulation",
                   sum((amount(l["limit"]) for l in locs), Decimal(0)), limit,
                   [{"citation": l["source_ref"], "location_id": l["location_id"], "limit_id": l["limit_id"]} for l in locs]
                   or [{"citation": source_rows.get("policy_admin", {}).get("source_ref", "unknown"), "zero_observed_locations": True}],
                   {"aggregate_tiv": str(sum((amount(l["tiv"]) for l in locs), Decimal(0))), "location_count": len(locs)})
        for loc in exposed:
            metric(f"{event['event_id']}:{loc['zone']}:{event['peril']}:single_location:{loc['location_id']}", event, loc["zone"], "single_location",
                   amount(loc["limit"]), cfg["single_location_max"], [{"citation": loc["source_ref"], "location_id": loc["location_id"]}])
        models = []
        for loc in exposed:
            candidates = [m for m in loc.get("modeled_losses", []) if m.get("event_id") == event["event_id"]]
            if len(candidates) != 1:
                gap(loc, "unmodeled_or_ambiguous", f"event {event['event_id']} needs one bound model result")
                continue
            model = candidates[0]
            bindings = {"peril": event["peril"], "footprint_version": event["footprint_version"],
                        "exposure_snapshot_id": doc.get("exposure_snapshot_id"), "model_version": source_rows.get("cat_model", {}).get("version"),
                        "model_run_id": source_rows.get("cat_model", {}).get("source_ref"), "currency": finance.get("currency"),
                        "financial_basis": finance.get("financial_basis"), "unit": "currency", "statistic": "scenario_range"}
            scenario_ids = model.get("scenario_ids")
            if (any(not expected or model.get(k) != expected for k, expected in bindings.items()) or not model.get("scenario_set_id")
                    or not isinstance(scenario_ids, dict) or not all(isinstance(scenario_ids.get(k), str) and scenario_ids[k] for k in ("low", "mid", "high"))
                    or len(set(scenario_ids.values())) != 3):
                gap(loc, "model_binding_mismatch", f"event {event['event_id']} model/footprint/exposure/financial/statistic binding incompatible")
                continue
            models.append((loc, model))
        scenario_sets = {(m["scenario_set_id"], tuple(m["scenario_ids"][k] for k in ("low", "mid", "high"))) for _, m in models}
        if models and len(models) == len(all_exposed) and len(scenario_sets) == 1:
            values = {name: sum((amount(m[name]) for _, m in models), Decimal(0)) for name in ("low", "mid", "high")}
            metric(f"{event['event_id']}:EVENT:{event['peril']}:modeled_loss", event, "EVENT", "modeled_loss", values["high"], cfg["modeled_loss_appetite"],
                   [{"citation": m["model_run_id"], "location_id": l["location_id"], "model_version": m["model_version"]} for l, m in models],
                   {"modeled_range": {k: str(v) for k, v in values.items()}, "modeled_locations": len(models),
                    "statistic": "scenario_range", "scenario_set_id": models[0][1]["scenario_set_id"], "scenario_ids": models[0][1]["scenario_ids"]})
        elif models:
            issues.append(f"event {event['event_id']} model total withheld: incomplete/incompatible location scenarios")
    issues.extend(f"{g['location_id']}: {g['gap']} ({g['detail']})" for g in gaps)
    complete = not issues and bool(doc.get("events")) and bool(locations)
    current_evidence = {"completeness": "complete" if complete else "partial",
                        "unresolved_issues": list(dict.fromkeys(issues))}
    prior = set(doc.get("prior_alerts", []))
    for alert in active:
        alert["status"] = "ongoing" if alert["alert_key"] in prior else "new"
    active_keys = {a["alert_key"] for a in active}
    inactive = []
    for key in sorted(prior - active_keys):
        observed = metrics.get(key)
        can_clear = complete and observed is not None
        inactive.append({"alert_key": key, "status": "cleared" if can_clear else "unknown",
                         "reason": "observed below configured threshold in complete current evidence" if can_clear else "not evaluable on complete current evidence; prior alert retained",
                         "evaluation": observed})
    alerts = active + inactive
    dedup = {state: sum(a["status"] == state for a in alerts) for state in ("new", "ongoing", "cleared", "unknown")}
    issues.extend(f"prior alert {alert['alert_key']} remains unknown" for alert in inactive if alert["status"] == "unknown")
    complete = complete and not dedup["unknown"]
    order = ["Informational", "Watch", "Elevated", "Critical"]
    overall = max((a["severity"] for a in active), key=order.index) if active else "None" if complete else "Unknown"
    result = {"run_id": doc.get("run_id", "cem-" + stable_hash(doc)[:16]), "as_of": doc["as_of"], "config_version": doc.get("config_version"),
              "exposure_snapshot_id": doc.get("exposure_snapshot_id"), "financial_context": finance, "queue": doc.get("queue", "catastrophe-risk-review"),
              "approaching_ratio": str(approaching), "confidence": "normal" if complete else "degraded", "sources": sources,
              "alerts": alerts, "dedup": dedup, "data_gaps": gaps, "evaluated_metrics": list(metrics.values()), "overall_severity": overall,
              "current_evidence": current_evidence,
              "completeness": "complete" if complete else "partial", "evaluability": "evaluable" if complete else "partial" if metrics else "not_evaluable",
              "unresolved_issues": list(dict.fromkeys(issues)), "disclaimer": DISCLAIMER}
    result["artifact"] = build_artifact(doc, result, producer="catastrophe-exposure-monitor", artifact_type="catastrophe-exposure-alerts")
    return result


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/exposure_snapshot.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    try:
        package = compute(json.loads(path.read_text() if path else sys.stdin.read()))
        print(json.dumps(package, indent=2, allow_nan=False))
        if "--selftest" in argv:
            from validate_output import validate as validate_output
            errors = validate_output(package)
            for error in errors:
                print("ERROR", error)
            print(f"compute self-check: {len(errors)} error(s)")
            return bool(errors)
        return 0
    except (TypeError, ValueError) as exc:
        print(f"ERROR {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
