#!/usr/bin/env python3
"""Deterministic input validation for earnings-results-analyzer.

Validates an earnings file before analysis. Fails closed on structural problems; warns on
data-quality gaps that limit which metrics/guidance items are evaluable (so the analysis does
not overstate a beat/miss it cannot support).

Input schema (JSON): see references/source-map.md. Key fields:
  ticker, company, period, as_of (YYYY-MM-DD), config_version, estimate_source,
  metrics[{metric, actual, estimate, unit, direction, headline, actual_ref, estimate_ref}],
  guidance[{metric, period, direction_sense, prior_low, prior_high, new_low, new_high,
            withdrawn, headline, source_ref}],
  transcript_changes[{topic, prior_language, current_language, source_ref}],
  config{beat_tol, miss_tol, guidance_tol}

Usage:
  python validate_input.py earnings.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("ticker", "period", "as_of", "config_version", "estimate_source", "metrics")
REQUIRED_METRIC = ("metric", "actual", "direction", "actual_ref")
DIRECTIONS = ("higher_is_better", "lower_is_better")


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

    metrics = doc.get("metrics") or []
    if not isinstance(metrics, list) or not metrics:
        errors.append("metrics must be a non-empty list")
        return errors, warnings

    names, headline_n, evaluable_n = set(), 0, 0
    for i, m in enumerate(metrics):
        tag = f"metrics[{i}] ({m.get('metric', '?')})"
        for k in REQUIRED_METRIC:
            if k not in m or m[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(m.get("actual")) is None:
            errors.append(f"{tag}: actual not numeric")
        if m.get("direction") not in DIRECTIONS:
            errors.append(f"{tag}: direction must be one of {DIRECTIONS}")
        nm = m.get("metric")
        if nm in names:
            errors.append(f"{tag}: duplicate metric name")
        names.add(nm)
        if m.get("headline"):
            headline_n += 1
        est = m.get("estimate")
        if est is None:
            warnings.append(f"{tag}: no estimate — surprise not evaluable; reported as not_evaluable")
        elif _num(est) is None:
            errors.append(f"{tag}: estimate present but not numeric")
        elif _num(est) == 0:
            warnings.append(f"{tag}: zero estimate — relative surprise not evaluable")
        else:
            evaluable_n += 1
            if not m.get("estimate_ref"):
                warnings.append(f"{tag}: estimate present but no estimate_ref — citation gap")
        if not m.get("unit"):
            warnings.append(f"{tag}: no unit — label the figure to avoid misreads")

    if headline_n == 0:
        warnings.append("no headline metric flagged — overall_result will be 'Undetermined'")
    if evaluable_n == 0:
        warnings.append("no metric has an estimate — nothing is evaluable as beat/miss")

    for i, g in enumerate(doc.get("guidance", []) or []):
        gtag = f"guidance[{i}] ({g.get('metric', '?')})"
        sense = g.get("direction_sense", "higher_is_better")
        if sense not in DIRECTIONS:
            errors.append(f"{gtag}: direction_sense must be one of {DIRECTIONS}")
        if not g.get("source_ref"):
            warnings.append(f"{gtag}: no source_ref — guidance evidence will be uncitable")
        has_new = g.get("new_low") is not None or g.get("new_high") is not None
        if not g.get("withdrawn") and not has_new:
            warnings.append(f"{gtag}: no new range and not marked withdrawn — direction not evaluable")

    for i, t in enumerate(doc.get("transcript_changes", []) or []):
        ttag = f"transcript_changes[{i}] ({t.get('topic', '?')})"
        if not t.get("source_ref"):
            warnings.append(f"{ttag}: no source_ref — transcript observation will be uncitable")
        if not t.get("prior_language"):
            warnings.append(f"{ttag}: no prior_language — surfaced as new disclosure, not a change")

    if not doc.get("config"):
        warnings.append("no 'config' block — default tolerances will be used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "earnings_example.json"
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
