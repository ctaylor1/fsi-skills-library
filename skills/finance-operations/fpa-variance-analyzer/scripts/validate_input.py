#!/usr/bin/env python3
"""Deterministic input validation for fpa-variance-analyzer.

Validates a variance dataset before analysis. Fails closed on structural problems; warns on
data-quality gaps that limit which comparisons or attributions are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  entity, period, as_of (YYYY-MM-DD), config_version, basis ("budget"|"forecast"|"prior"),
  config{abs_threshold,pct_threshold,min_base,run_rate_escalation,attribution_tolerance,periods_remaining},
  lines[{line_id, account, account_type ("revenue"|"expense"), actual, budget,
          forecast?, prior?, persistence?, drivers?[{name, amount, source_ref}], source_ref}]

Usage:
  python validate_input.py variance.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("entity", "period", "as_of", "config_version", "lines")
REQUIRED_LINE = ("line_id", "account", "account_type", "actual", "budget", "source_ref")
ACCOUNT_TYPES = {"revenue", "expense"}
PERSISTENCE = {"recurring", "one_time", "timing", None}
BASES = {"budget", "forecast", "prior"}


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
    basis = doc.get("basis", "budget")
    if basis not in BASES:
        errors.append(f"basis must be one of {sorted(BASES)}, got {basis!r}")

    lines = doc.get("lines") or []
    if not isinstance(lines, list) or not lines:
        errors.append("lines must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, ln in enumerate(lines):
        tag = f"lines[{i}] ({ln.get('line_id','?')})"
        for k in REQUIRED_LINE:
            if k not in ln or ln[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(ln.get("actual")) is None:
            errors.append(f"{tag}: actual not numeric")
        if _num(ln.get("budget")) is None:
            errors.append(f"{tag}: budget not numeric")
        if ln.get("account_type") not in ACCOUNT_TYPES:
            errors.append(f"{tag}: account_type must be 'revenue' or 'expense'")
        if ln.get("persistence") not in PERSISTENCE:
            errors.append(f"{tag}: persistence must be one of recurring|one_time|timing")
        lid = ln.get("line_id")
        if lid in ids:
            errors.append(f"{tag}: duplicate line_id")
        ids.add(lid)

        # driver structure (attribution tie-out depends on it)
        drivers = ln.get("drivers")
        if drivers is not None:
            if not isinstance(drivers, list):
                errors.append(f"{tag}: drivers must be a list")
            else:
                for j, d in enumerate(drivers):
                    if _num(d.get("amount")) is None:
                        errors.append(f"{tag}: drivers[{j}] amount not numeric")
                    if not d.get("source_ref"):
                        warnings.append(f"{tag}: drivers[{j}] has no source_ref - driver evidence will fall back to the line source")
        else:
            warnings.append(f"{tag}: no drivers - a material variance here will be reported 'unattributed'")

        if _num(ln.get("forecast")) is None and "forecast" not in ln:
            warnings.append(f"{tag}: no forecast - vs_forecast not evaluable for this line")
        if _num(ln.get("prior")) is None and "prior" not in ln:
            warnings.append(f"{tag}: no prior - vs_prior not evaluable for this line")

    cfg = doc.get("config") or {}
    if not cfg:
        warnings.append("no 'config' block - default materiality thresholds will be used; record the config_version")
    elif cfg.get("periods_remaining") in (None, 0):
        warnings.append("periods_remaining is 0/absent - run-rate impact will be 0 for all recurring lines")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "variance_example.json"
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
