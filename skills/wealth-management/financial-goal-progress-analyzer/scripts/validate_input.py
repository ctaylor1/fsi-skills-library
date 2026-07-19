#!/usr/bin/env python3
"""Deterministic input validation for financial-goal-progress-analyzer.

Validates a goals file before progress computation. Fails closed on structural problems;
warns on data-quality gaps that limit which goals are evaluable or lower confidence.

Input schema (JSON): see references/source-map.md. Key fields:
  client_id, as_of (YYYY-MM-DD), assumptions_version,
  goals[{goal_id, name, target_amount, target_date, current_balance, monthly_contribution?,
         target_terms? ("nominal"|"real"), priority?, source_ref, balance_ref?, contribution_ref?}],
  assumptions{expected_return_annual, inflation_annual, on_track_min, at_risk_min, ...}

Usage:
  python validate_input.py goals.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("client_id", "as_of", "assumptions_version", "goals")
REQUIRED_GOAL = ("goal_id", "name", "target_amount", "target_date", "current_balance", "source_ref")
VALID_TERMS = ("nominal", "real")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _date(v):
    if not DATE_RE.match(str(v)):
        return None
    try:
        return datetime.strptime(str(v), "%Y-%m-%d")
    except ValueError:
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    as_of = _date(doc["as_of"])
    if as_of is None:
        errors.append(f"as_of must be YYYY-MM-DD, got {doc['as_of']!r}")

    goals = doc.get("goals") or []
    if not isinstance(goals, list) or not goals:
        errors.append("goals must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, g in enumerate(goals):
        tag = f"goals[{i}] ({g.get('goal_id', '?')})"
        for k in REQUIRED_GOAL:
            if k not in g or g[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        gid = g.get("goal_id")
        if gid in ids:
            errors.append(f"{tag}: duplicate goal_id")
        ids.add(gid)

        ta = _num(g.get("target_amount"))
        if ta is None:
            errors.append(f"{tag}: target_amount not numeric")
        elif ta <= 0:
            errors.append(f"{tag}: target_amount must be > 0")

        if _num(g.get("current_balance")) is None:
            errors.append(f"{tag}: current_balance not numeric")

        terms = g.get("target_terms", "nominal")
        if terms not in VALID_TERMS:
            errors.append(f"{tag}: target_terms must be one of {VALID_TERMS}, got {terms!r}")

        td = _date(g.get("target_date"))
        if g.get("target_date") is not None and td is None:
            errors.append(f"{tag}: target_date must be YYYY-MM-DD, got {g.get('target_date')!r}")
        elif td is not None and as_of is not None and td <= as_of:
            warnings.append(f"{tag}: target_date {g.get('target_date')} not after as_of — "
                            f"goal will be reported not_evaluable (no forward projection)")

        if "monthly_contribution" not in g:
            warnings.append(f"{tag}: no monthly_contribution — treated as 0 for the projection")
        elif _num(g.get("monthly_contribution")) is None:
            errors.append(f"{tag}: monthly_contribution not numeric")

    asmp = doc.get("assumptions")
    if not asmp:
        warnings.append("no 'assumptions' block — approved defaults will be used; record the "
                        "assumptions_version so the analysis is reproducible")
    else:
        for k in ("expected_return_annual", "inflation_annual"):
            if k in asmp and _num(asmp[k]) is None:
                errors.append(f"assumptions.{k} not numeric")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "goals_example.json"
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
