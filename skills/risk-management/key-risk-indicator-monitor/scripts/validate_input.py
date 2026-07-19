#!/usr/bin/env python3
"""Deterministic input validation for key-risk-indicator-monitor.

Validates a KRI monitoring-run file before the rule engine evaluates it. Fails closed on
structural problems; warns on data-quality gaps that limit which lenses are evaluable or
that disable freshness / deduplication for this run.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  run_id, as_of (YYYY-MM-DD), config_version, max_staleness_days,
  open_alerts[{fingerprint}],                      # previously-open alerts, for dedup
  kris[{kri_id, name, category, owner, unit, direction, critical, amber, red,
        observation_as_of, observations[{period, value}],
        seasonal_baseline{period: expected}, seasonal_tolerance_pct, trend_min_moves,
        plausible_range[min, max], linked_incidents[]}]

Thresholds (amber/red), directions, and seasonal baselines are VERSIONED configuration owned
by the risk-appetite function (config_version); this validator never invents or tunes them.

Usage:
  python validate_input.py run.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("run_id", "as_of", "config_version", "kris")
REQUIRED_KRI = ("kri_id",)
DIRECTIONS = {"higher_is_worse", "lower_is_worse"}


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

    if "max_staleness_days" not in doc:
        warnings.append("no 'max_staleness_days' — freshness is not evaluable this run; alerts may be based on stale observations")
    if "open_alerts" not in doc:
        warnings.append("no 'open_alerts' baseline — deduplication is disabled; every breach will be reported as new")

    kris = doc.get("kris") or []
    if not isinstance(kris, list) or not kris:
        errors.append("kris must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, k in enumerate(kris):
        tag = f"kris[{i}] ({k.get('kri_id','?')})"
        for f in REQUIRED_KRI:
            if not k.get(f):
                errors.append(f"{tag}: missing '{f}'")
        kid = k.get("kri_id")
        if kid in ids:
            errors.append(f"{tag}: duplicate kri_id")
        ids.add(kid)

        direction = k.get("direction", "higher_is_worse")
        if direction not in DIRECTIONS:
            errors.append(f"{tag}: direction must be one of {sorted(DIRECTIONS)}, got {direction!r}")

        amber, red = k.get("amber"), k.get("red")
        if amber is None and red is None:
            warnings.append(f"{tag}: no amber/red thresholds — threshold lens not evaluable for this KRI")
        else:
            if amber is not None and _num(amber) is None:
                errors.append(f"{tag}: amber threshold not numeric")
            if red is not None and _num(red) is None:
                errors.append(f"{tag}: red threshold not numeric")
            a, r = _num(amber), _num(red)
            if a is not None and r is not None and direction in DIRECTIONS:
                if direction == "higher_is_worse" and not (a <= r):
                    warnings.append(f"{tag}: higher_is_worse expects amber <= red; got amber={a}, red={r} — check config")
                if direction == "lower_is_worse" and not (a >= r):
                    warnings.append(f"{tag}: lower_is_worse expects amber >= red; got amber={a}, red={r} — check config")

        obs = k.get("observations")
        if not isinstance(obs, list) or not obs:
            warnings.append(f"{tag}: no observations — KRI not measurable this run (data-quality alert will fire)")
        else:
            latest = obs[-1]
            if not isinstance(latest, dict) or "value" not in latest:
                errors.append(f"{tag}: latest observation must be an object with a 'value'")
            elif latest.get("value") is None:
                warnings.append(f"{tag}: latest observation value is null — data-quality alert will fire; thresholds not evaluable")

        if not k.get("observation_as_of"):
            warnings.append(f"{tag}: no observation_as_of — freshness not evaluable for this KRI")

        sb = k.get("seasonal_baseline")
        if sb is not None and not isinstance(sb, dict):
            errors.append(f"{tag}: seasonal_baseline must be an object {{period: expected}}")
        if k.get("seasonal_tolerance_pct") is not None and _num(k.get("seasonal_tolerance_pct")) is None:
            errors.append(f"{tag}: seasonal_tolerance_pct not numeric")
        if k.get("trend_min_moves") is not None and _num(k.get("trend_min_moves")) is None:
            errors.append(f"{tag}: trend_min_moves not numeric")
        if k.get("critical") is not None and not isinstance(k.get("critical"), bool):
            warnings.append(f"{tag}: 'critical' should be a boolean; treated as truthy/falsey")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
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
