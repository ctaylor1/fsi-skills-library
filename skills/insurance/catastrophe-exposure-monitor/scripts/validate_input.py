#!/usr/bin/env python3
"""CAT snapshot validation. Missing feeds are explicit unknowns, never an all-clear."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from insurance_contract import amount, timestamp, iso_date


def validate(doc):
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["input must be an object"], []
    try:
        timestamp(doc.get("as_of"))
    except (TypeError, ValueError):
        errors.append("as_of requires a valid timezone-aware timestamp")
    for field in ("config_version", "exposure_snapshot_id"):
        if not isinstance(doc.get(field), str) or not doc[field].strip():
            warnings.append(f"{field} unavailable")
    for field in ("events", "locations", "sources", "prior_alerts"):
        if not isinstance(doc.get(field, []), list):
            errors.append(f"{field} must be a list")
    if errors:
        return errors, warnings
    for field in ("events", "locations", "sources"):
        if not doc.get(field):
            warnings.append(f"{field} unavailable or empty; no absence-based clearing")
    if not all(isinstance(v, str) and v for v in doc.get("prior_alerts", [])):
        errors.append("prior_alerts must contain nonempty keys")
    coverage = doc.get("data_coverage", {})
    if not isinstance(coverage, dict):
        errors.append("data_coverage must be an object")
    else:
        for key in ("events", "exposures", "models"):
            if coverage.get(key) != "complete":
                warnings.append(f"data_coverage.{key} not complete")
    seen_sources = set()
    for i, source in enumerate(doc.get("sources", [])):
        if not isinstance(source, dict):
            errors.append(f"sources[{i}] must be an object")
            continue
        role = source.get("source")
        if not isinstance(role, str) or not role:
            errors.append(f"sources[{i}].source required")
        elif role in seen_sources:
            errors.append(f"duplicate source role {role}")
        else:
            seen_sources.add(role)
    for role in ("policy_admin", "event_feed", "cat_model"):
        if role not in seen_sources:
            warnings.append(f"missing required source {role}")
    for field, id_field in (("events", "event_id"), ("locations", "location_id")):
        seen = set()
        for i, row in enumerate(doc.get(field, [])):
            if not isinstance(row, dict):
                errors.append(f"{field}[{i}] must be an object")
                continue
            ident = row.get(id_field)
            if not isinstance(ident, str) or not ident:
                errors.append(f"{field}[{i}].{id_field} required")
            elif ident in seen:
                errors.append(f"duplicate {id_field} {ident}")
            else:
                seen.add(ident)
            if field == "events":
                if not isinstance(row.get("peril"), str) or not isinstance(row.get("footprint_zones"), list) or not all(isinstance(z, str) and z for z in row.get("footprint_zones", [])):
                    errors.append(f"events[{i}] requires peril and footprint_zones list")
                if not row.get("footprint_version") or not row.get("source_ref"):
                    warnings.append(f"event {ident} footprint provenance missing")
                try:
                    if timestamp(row.get("footprint_as_of")) > timestamp(doc["as_of"]):
                        raise ValueError()
                except (TypeError, ValueError):
                    warnings.append(f"event {ident} footprint timestamp missing/invalid/future")
            else:
                if not isinstance(row.get("peril_exposed"), list) or not all(isinstance(v, str) for v in row.get("peril_exposed", [])):
                    errors.append(f"locations[{i}].peril_exposed must be a list")
                if not isinstance(row.get("zone"), str) or not row.get("zone"):
                    warnings.append(f"location {ident} zone unavailable")
                for monetary in ("limit", "tiv"):
                    try:
                        if amount(row.get(monetary)) < 0:
                            raise ValueError()
                    except ValueError:
                        errors.append(f"location {ident} {monetary} must be finite nonnegative numeric")
                if not isinstance(row.get("geocoded"), bool):
                    warnings.append(f"location {ident} geocoded must be boolean")
                try:
                    iso_date(row.get("valuation_date"))
                except ValueError:
                    warnings.append(f"location {ident} valuation date unavailable/invalid")
                models = row.get("modeled_losses", [])
                if not isinstance(models, list) or not all(isinstance(m, dict) for m in models):
                    errors.append(f"location {ident} modeled_losses must be a list of objects")
                else:
                    for model in models:
                        try:
                            low, mid, high = [amount(model.get(k)) for k in ("low", "mid", "high")]
                            if not 0 <= low <= mid <= high:
                                raise ValueError()
                        except ValueError:
                            errors.append(f"location {ident} model requires finite 0 <= low <= mid <= high")
    cfg = doc.get("config", {})
    if not isinstance(cfg, dict):
        errors.append("config must be an object")
        return errors, warnings
    for key in ("single_location_max", "modeled_loss_appetite", "stale_valuation_years"):
        if key in cfg:
            try:
                if amount(cfg[key]) <= 0:
                    raise ValueError()
            except ValueError:
                errors.append(f"config.{key} must be finite and positive")
    for key in ("zone_accum_limit", "max_source_staleness_hours"):
        if key in cfg:
            values = cfg[key]
            if not isinstance(values, dict):
                errors.append(f"config.{key} must be an object")
            else:
                for value in values.values():
                    try:
                        if amount(value) <= 0:
                            raise ValueError()
                    except ValueError:
                        errors.append(f"config.{key} values must be finite and positive")
    try:
        if not 0 < amount(cfg.get("approaching_ratio", 0.9)) <= 1:
            raise ValueError()
    except ValueError:
        errors.append("approaching_ratio must be finite, > 0 and <= 1")
    return errors, warnings


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/exposure_snapshot.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    errors, warnings = validate(json.loads(path.read_text() if path else sys.stdin.read()))
    for message in warnings:
        print("WARN", message)
    for message in errors:
        print("ERROR", message)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
