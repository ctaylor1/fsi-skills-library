#!/usr/bin/env python3
"""Deterministic input validation for market-risk-limit-monitor.

Validates a monitoring-run file before the limit engine evaluates it. Fails closed on
structural problems; warns on data-quality gaps that limit which limits are evaluable or
that disable freshness / deduplication for this run.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  run_id, as_of (YYYY-MM-DD or ISO datetime), config_version, max_staleness_hours,
  open_alerts[{fingerprint}],                       # previously-open breaches, for dedup
  limits[{limit_id, metric, scope, scope_value, direction, limit_value, warn_buffer_pct,
          unit, horizon, confidence, sensitivity, scenario_id, sub_scope}],
  books[{unit_id, unit_type, desk, measured_as_of,
         measures[{metric, value, unit, horizon, confidence, sensitivity, scenario_id,
                   sub_scope, projected_value}]}]

metric is one of: var, es, sensitivity, stress_loss, notional, concentration.

Usage:
  python validate_input.py run.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("run_id", "as_of", "config_version", "books", "limits")
REQUIRED_UNIT = ("unit_id", "unit_type", "measures")
REQUIRED_MEASURE = ("metric", "value")
REQUIRED_LIMIT = ("limit_id", "metric", "scope", "scope_value", "limit_value")
METRIC_TYPES = {"var", "es", "sensitivity", "stress_loss", "notional", "concentration"}
DIRECTIONS = {"max", "min"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _measure_key(m: dict) -> str:
    """Identity of a measure used to match a limit (metric + its discriminators)."""
    metric = m.get("metric")
    if metric in ("var", "es"):
        return f"{metric}:{m.get('horizon')}:{m.get('confidence')}"
    if metric == "sensitivity":
        return f"sensitivity:{m.get('sensitivity')}"
    if metric == "stress_loss":
        return f"stress_loss:{m.get('scenario_id')}"
    if metric == "concentration":
        return f"concentration:{m.get('sub_scope')}"
    return str(metric)


def _limit_key(r: dict) -> str:
    metric = r.get("metric")
    if metric in ("var", "es"):
        return f"{metric}:{r.get('horizon')}:{r.get('confidence')}"
    if metric == "sensitivity":
        return f"sensitivity:{r.get('sensitivity')}"
    if metric == "stress_loss":
        return f"stress_loss:{r.get('scenario_id')}"
    if metric == "concentration":
        return f"concentration:{r.get('sub_scope')}"
    return str(metric)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if "max_staleness_hours" not in doc:
        warnings.append("no 'max_staleness_hours' — freshness is not evaluable this run; alerts may be based on stale risk measures")
    if "open_alerts" not in doc:
        warnings.append("no 'open_alerts' baseline — deduplication is disabled; every breach will be reported as new")

    books = doc.get("books") or []
    if not isinstance(books, list) or not books:
        errors.append("books must be a non-empty list")
        return errors, warnings

    # index of (unit_type, unit_id) -> set of measure keys, for limit-evaluability checks
    unit_index: dict[tuple, set] = {}
    uids = set()
    for i, b in enumerate(books):
        tag = f"books[{i}] ({b.get('unit_id','?')})"
        for k in REQUIRED_UNIT:
            if k not in b or b[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        uid = b.get("unit_id")
        if uid in uids:
            errors.append(f"{tag}: duplicate unit_id")
        uids.add(uid)
        measures = b.get("measures") or []
        if not isinstance(measures, list) or not measures:
            errors.append(f"{tag}: measures must be a non-empty list")
            continue
        if not b.get("measured_as_of"):
            warnings.append(f"{tag}: no measured_as_of — freshness not evaluable for this unit")
        keys = set()
        for j, m in enumerate(measures):
            mtag = f"{tag}.measures[{j}] ({m.get('metric','?')})"
            for k in REQUIRED_MEASURE:
                if k not in m or m[k] in (None, ""):
                    errors.append(f"{mtag}: missing '{k}'")
            if m.get("metric") not in METRIC_TYPES:
                errors.append(f"{mtag}: metric must be one of {sorted(METRIC_TYPES)}, got {m.get('metric')!r}")
            if _num(m.get("value")) is None:
                errors.append(f"{mtag}: value not numeric")
            if m.get("projected_value") is not None and _num(m.get("projected_value")) is None:
                errors.append(f"{mtag}: projected_value present but not numeric")
            if m.get("metric") in ("var", "es") and (m.get("horizon") is None or m.get("confidence") is None):
                warnings.append(f"{mtag}: var/es measure missing horizon/confidence — limit matching may be ambiguous")
            if m.get("metric") == "sensitivity" and not m.get("sensitivity"):
                warnings.append(f"{mtag}: sensitivity measure missing 'sensitivity' (e.g. dv01/cs01/vega)")
            if m.get("metric") == "stress_loss" and not m.get("scenario_id"):
                warnings.append(f"{mtag}: stress_loss measure missing 'scenario_id'")
            key = _measure_key(m)
            if key in keys:
                warnings.append(f"{mtag}: repeated measure key {key!r} — later value will be used")
            keys.add(key)
        unit_index[(b.get("unit_type"), uid)] = keys

    limits = doc.get("limits") or []
    if not isinstance(limits, list) or not limits:
        errors.append("limits must be a non-empty list")
        return errors, warnings
    lids = set()
    for i, r in enumerate(limits):
        tag = f"limits[{i}] ({r.get('limit_id','?')})"
        for k in REQUIRED_LIMIT:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if r.get("limit_id") in lids:
            errors.append(f"{tag}: duplicate limit_id")
        lids.add(r.get("limit_id"))
        if r.get("metric") not in METRIC_TYPES:
            errors.append(f"{tag}: metric must be one of {sorted(METRIC_TYPES)}, got {r.get('metric')!r}")
            continue
        if _num(r.get("limit_value")) is None:
            errors.append(f"{tag}: limit_value not numeric")
        direction = r.get("direction", "max")
        if direction not in DIRECTIONS:
            errors.append(f"{tag}: direction must be one of {sorted(DIRECTIONS)}, got {direction!r}")
        if r.get("warn_buffer_pct") is not None and _num(r.get("warn_buffer_pct")) is None:
            errors.append(f"{tag}: warn_buffer_pct present but not numeric")
        # evaluability: is there a measured unit + matching measure for this limit?
        unit_key = (r.get("scope"), r.get("scope_value"))
        if unit_key not in unit_index:
            warnings.append(f"{tag}: no measured unit for scope {r.get('scope')}={r.get('scope_value')!r} — limit not evaluable this run")
        elif _limit_key(r) not in unit_index[unit_key]:
            warnings.append(f"{tag}: unit has no matching {_limit_key(r)!r} measure — limit not evaluable this run")

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
