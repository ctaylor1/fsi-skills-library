#!/usr/bin/env python3
"""Deterministic input validation for market-sizing-builder.

Validates a market-sizing input file before the model runs. Fails closed on structural
problems (missing methods, missing scenario values, non-numeric or out-of-range drivers);
warns on data-quality gaps that weaken provenance or scenario behavior (missing source tier,
non-monotonic driver values, thin segment coverage).

Input schema (JSON): see references/source-map.md. Key fields:
  market_id, market_name, as_of (YYYY-MM-DD), currency, config_version,
  config{scenarios[],primary_method,triangulation_tolerance_pct,tolerance},
  top_down{total_market, sam_ratio, som_ratio},
  bottom_up{segments[{id,label,units,arpu,attach_rate,capture_rate}]}
Every driver is {id,label,provenance,source_tier,values{<scenario>:number}}. Ratios
(sam_ratio, som_ratio, attach_rate, capture_rate) must be fractions in [0,1]; magnitudes
(total_market, units, arpu) must be positive.

Usage:
  python validate_input.py market_sizing_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("market_id", "as_of", "config_version", "top_down", "bottom_up")
RATIO_KINDS = {"sam_ratio", "som_ratio", "attach_rate", "capture_rate"}
MAGNITUDE_KINDS = {"total_market", "units", "arpu"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _check_driver(driver, kind, scope, scenarios, errors, warnings):
    tag = f"{scope}.{kind} ({(driver or {}).get('id', '?')})"
    if not isinstance(driver, dict):
        errors.append(f"{tag}: driver must be an object")
        return
    if not driver.get("id"):
        errors.append(f"{tag}: missing 'id'")
    if not (driver.get("provenance") or "").strip():
        errors.append(f"{tag}: missing 'provenance' (every assumption must cite a source)")
    if not (driver.get("source_tier") or "").strip():
        warnings.append(f"{tag}: no 'source_tier' — source hierarchy cannot rank this assumption")
    vals = driver.get("values")
    if not isinstance(vals, dict):
        errors.append(f"{tag}: missing 'values' map for scenarios")
        return
    series = []
    for sc in scenarios:
        if sc not in vals:
            errors.append(f"{tag}: missing value for scenario '{sc}'")
            series.append(None)
            continue
        n = _num(vals[sc])
        if n is None:
            errors.append(f"{tag}: value for '{sc}' not numeric")
            series.append(None)
            continue
        if kind in RATIO_KINDS and not (0.0 <= n <= 1.0):
            errors.append(f"{tag}: ratio for '{sc}' must be in [0,1], got {n}")
        if kind in MAGNITUDE_KINDS and n <= 0:
            errors.append(f"{tag}: magnitude for '{sc}' must be positive, got {n}")
        series.append(n)
    clean = [s for s in series if s is not None]
    if len(clean) == len(series) and clean != sorted(clean):
        warnings.append(f"{tag}: values not monotonic across {scenarios} "
                        f"({clean}) — scenario ordering may fail in the model")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    cfg = doc.get("config") or {}
    scenarios = list(cfg.get("scenarios") or ["low", "base", "high"])
    if len(scenarios) < 2:
        errors.append("config.scenarios must list at least two scenarios (e.g. low, base, high)")
    primary = cfg.get("primary_method", "top_down")
    if primary not in ("top_down", "bottom_up"):
        errors.append(f"config.primary_method must be 'top_down' or 'bottom_up', got {primary!r}")

    td = doc.get("top_down") or {}
    for kind in ("total_market", "sam_ratio", "som_ratio"):
        if kind not in td:
            errors.append(f"top_down: missing '{kind}'")
        else:
            _check_driver(td[kind], kind, "top_down", scenarios, errors, warnings)

    bu = doc.get("bottom_up") or {}
    segs = bu.get("segments")
    if not isinstance(segs, list) or not segs:
        errors.append("bottom_up.segments must be a non-empty list")
    else:
        seen = set()
        for i, seg in enumerate(segs):
            sid = seg.get("id", f"[{i}]")
            if sid in seen:
                errors.append(f"bottom_up.segments: duplicate segment id {sid!r}")
            seen.add(sid)
            for kind in ("units", "arpu", "attach_rate", "capture_rate"):
                if kind not in seg:
                    errors.append(f"bottom_up.segment {sid}: missing '{kind}'")
                else:
                    _check_driver(seg[kind], kind, f"bottom_up:{sid}", scenarios, errors, warnings)
        if len(segs) < 2:
            warnings.append(f"only {len(segs)} bottom-up segment(s) — coverage may be thin; "
                            f"confirm the segmentation spans the market")

    if not doc.get("config"):
        warnings.append("no 'config' block — default scenarios/tolerances used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "market_sizing_input_example.json"
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
