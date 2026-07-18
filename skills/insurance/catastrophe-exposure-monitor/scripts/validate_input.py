#!/usr/bin/env python3
"""Deterministic input validation for catastrophe-exposure-monitor.

Validates an exposure snapshot before accumulation/threshold computation. Fails closed on
structural problems; warns on data-quality gaps that limit which locations or signals are
evaluable (these are surfaced, not silently dropped).

Input schema (JSON): see references/source-map.md. Key fields:
  as_of (YYYY-MM-DD[THH:MM:SS]), config_version, sources[{source,as_of}],
  events[{event_id,peril,footprint_zones[]}],
  locations[{location_id,policy_id,zone,peril_exposed[],tiv,limit,geocoded,valuation_date,
             modeled_loss{low,mid,high},source_ref}],
  prior_alerts[], config{...thresholds...}

Usage:
  python validate_input.py exposure_snapshot.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("as_of", "config_version", "sources", "events", "locations")
REQUIRED_EVENT = ("event_id", "peril", "footprint_zones")
REQUIRED_LOC = ("location_id", "zone", "peril_exposed", "limit", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    sources = doc.get("sources") or []
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list (freshness cannot be evaluated)")
    else:
        for i, s in enumerate(sources):
            if not s.get("source"):
                errors.append(f"sources[{i}] missing 'source'")
            if not s.get("as_of"):
                warnings.append(f"sources[{i}] ({s.get('source','?')}) has no as_of — will be treated as stale")

    events = doc.get("events") or []
    if not isinstance(events, list) or not events:
        errors.append("events must be a non-empty list")
        return errors, warnings
    footprint_zones = set()
    for i, e in enumerate(events):
        tag = f"events[{i}] ({e.get('event_id','?')})"
        for k in REQUIRED_EVENT:
            if k not in e or e[k] in (None, "", []):
                errors.append(f"{tag}: missing '{k}'")
        fz = e.get("footprint_zones") or []
        if not isinstance(fz, list) or not fz:
            errors.append(f"{tag}: footprint_zones must be a non-empty list")
        else:
            footprint_zones.update(fz)

    locs = doc.get("locations") or []
    if not isinstance(locs, list) or not locs:
        errors.append("locations must be a non-empty list")
        return errors, warnings

    ids = set()
    n_exposed = 0
    for i, loc in enumerate(locs):
        tag = f"locations[{i}] ({loc.get('location_id','?')})"
        for k in REQUIRED_LOC:
            if k not in loc or loc[k] in (None, "", []):
                errors.append(f"{tag}: missing '{k}'")
        if _num(loc.get("limit")) is None:
            errors.append(f"{tag}: limit not numeric")
        if loc.get("tiv") is not None and _num(loc.get("tiv")) is None:
            errors.append(f"{tag}: tiv not numeric")
        lid = loc.get("location_id")
        if lid in ids:
            errors.append(f"{tag}: duplicate location_id")
        ids.add(lid)
        if loc.get("zone") in footprint_zones:
            n_exposed += 1
            if not loc.get("geocoded", False):
                warnings.append(f"{tag}: in-footprint but ungeocoded — excluded from accumulation")
            if not loc.get("modeled_loss"):
                warnings.append(f"{tag}: in-footprint but no modeled_loss — excluded from modeled-loss range")

    if n_exposed == 0:
        warnings.append("no location falls inside any event footprint zone — run will produce no exposure alerts")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    if "prior_alerts" not in doc:
        warnings.append("no 'prior_alerts' — every breach will be reported as new (no deduplication baseline)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exposure_snapshot.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
