#!/usr/bin/env python3
"""Deterministic input validation for portfolio-drift-monitor.

Validates a drift-input file before change computation. Fails closed on structural problems
and on the core contract that BOTH snapshots must be APPROVED characteristics (the skill
compares only approved current and prior characteristics). Warns on data-quality gaps that
limit which characteristics are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  portfolio_id, benchmark_id, as_of (YYYY-MM-DD), prior_as_of (YYYY-MM-DD), config_version,
  lookback_label, config{...bands...}, mandate_reference{...optional limit references...},
  current{approval{approved,source_ref,...}, tracking_error, duration, beta,
          active_weights[{key,active_weight}], factors[{key,exposure}]},
  prior{ ...same shape... }

Usage:
  python validate_input.py drift_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("portfolio_id", "as_of", "prior_as_of", "config_version", "current", "prior")
SCALARS = ("tracking_error", "duration", "beta")
VECTORS = {"active_weights": "active_weight", "factors": "exposure"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _check_snapshot(errors, warnings, snap, label):
    if not isinstance(snap, dict):
        errors.append(f"{label} snapshot must be an object")
        return
    approval = snap.get("approval") or {}
    if approval.get("approved") is not True:
        errors.append(f"{label} snapshot not approved (approval.approved must be true) — "
                      "only approved characteristics may be compared")
    if not str(approval.get("source_ref") or "").strip():
        errors.append(f"{label} snapshot missing approval.source_ref (needed to cite evidence)")
    for name in SCALARS:
        if name in snap and _num(snap.get(name)) is None:
            errors.append(f"{label}.{name} present but not numeric")
    for family, value_field in VECTORS.items():
        rows = snap.get(family)
        if rows is None:
            continue
        if not isinstance(rows, list):
            errors.append(f"{label}.{family} must be a list")
            continue
        seen = set()
        for i, e in enumerate(rows):
            tag = f"{label}.{family}[{i}]"
            if not isinstance(e, dict) or e.get("key") in (None, ""):
                errors.append(f"{tag}: missing 'key'")
                continue
            if _num(e.get(value_field)) is None:
                errors.append(f"{tag} ({e.get('key')}): '{value_field}' not numeric")
            if e["key"] in seen:
                errors.append(f"{tag}: duplicate key {e['key']!r}")
            seen.add(e["key"])


def _comparable(cur, pri):
    """Return the set of characteristics evaluable in BOTH snapshots."""
    out = set()
    if isinstance(cur, dict) and isinstance(pri, dict):
        for name in SCALARS:
            if _num(cur.get(name)) is not None and _num(pri.get(name)) is not None:
                out.add(name)
        for family, value_field in VECTORS.items():
            ck = {e.get("key") for e in (cur.get(family) or []) if isinstance(e, dict)}
            pk = {e.get("key") for e in (pri.get(family) or []) if isinstance(e, dict)}
            if ck & pk:
                out.add(family)
    return out


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    for field in ("as_of", "prior_as_of"):
        if not DATE_RE.match(str(doc[field])):
            errors.append(f"{field} must be YYYY-MM-DD, got {doc[field]!r}")
    if DATE_RE.match(str(doc["as_of"])) and DATE_RE.match(str(doc["prior_as_of"])):
        if str(doc["prior_as_of"]) >= str(doc["as_of"]):
            errors.append(f"prior_as_of ({doc['prior_as_of']}) must be strictly before as_of ({doc['as_of']})")

    if not str(doc.get("config_version") or "").strip():
        errors.append("config_version must be a non-empty versioned identifier")

    cur, pri = doc.get("current"), doc.get("prior")
    _check_snapshot(errors, warnings, cur, "current")
    _check_snapshot(errors, warnings, pri, "prior")

    comparable = _comparable(cur, pri)
    if not comparable:
        errors.append("no characteristic is evaluable in both snapshots — nothing to compare")

    # data-quality warnings (do not fail): characteristics present in only one snapshot
    if isinstance(cur, dict) and isinstance(pri, dict):
        for name in SCALARS:
            in_cur, in_pri = _num(cur.get(name)) is not None, _num(pri.get(name)) is not None
            if in_cur != in_pri:
                warnings.append(f"{name} present in only one snapshot — not evaluable")
        for family in VECTORS:
            ck = {e.get("key") for e in (cur.get(family) or []) if isinstance(e, dict)}
            pk = {e.get("key") for e in (pri.get(family) or []) if isinstance(e, dict)}
            for key in ck ^ pk:
                warnings.append(f"{family} bucket {key!r} present in only one snapshot — not evaluable")

    if not doc.get("mandate_reference"):
        warnings.append("no 'mandate_reference' block — limit-proximity routing to "
                        "mandate-compliance-monitor is disabled for this run")
    if not doc.get("config"):
        warnings.append("no 'config' block — default attention bands used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "drift_input_example.json"
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
