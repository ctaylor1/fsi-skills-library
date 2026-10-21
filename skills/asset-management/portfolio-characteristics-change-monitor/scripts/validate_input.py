#!/usr/bin/env python3
"""Deterministic input validation for portfolio-characteristics-change-monitor.

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
        import math
        if isinstance(v, bool): return None
        number = float(v)
        return number if math.isfinite(number) else None
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


def _validate_legacy(doc: dict) -> tuple[list[str], list[str]]:
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
                        "investment-mandate-reviewer is disabled for this run")
    if not doc.get("config"):
        warnings.append("no 'config' block — default attention bands used; record the config_version")
    buffers = (doc.get("config") or {}).get("route_buffers")
    if not isinstance(buffers, dict) or any(_num(buffers.get(k)) is None or _num(buffers[k]) < 0 for k in ("tracking_error", "duration", "active_weights")):
        errors.append("nonnegative metric-specific route_buffers required in snapshot units")
    current_basis = (doc.get("current") or {}).get("basis")
    prior_basis = (doc.get("prior") or {}).get("basis")
    for label, basis in (("current", current_basis), ("prior", prior_basis)):
        if not isinstance(basis, dict) or any(not basis.get(k) for k in ("benchmark_id", "model_version", "units")):
            errors.append(f"{label}: basis benchmark_id/model_version/units required")
    if current_basis != prior_basis: errors.append("snapshot bases differ; changes are not comparable")
    if current_basis and current_basis.get("benchmark_id") != doc.get("benchmark_id"):
        errors.append("snapshot benchmark differs from run benchmark")
    warnings.append("approval metadata is supplied, not authenticated; changes do not explain causes")
    return errors, warnings


def validate(doc: dict):
    """Validate finite source data and real ISO dates before package-specific checks."""
    import math
    from datetime import datetime
    errors = []
    def walk(value, path="input", key=""):
        if isinstance(value, str) and value.strip().lower() in {"nan", "inf", "infinity", "-inf", "+inf", "-infinity", "+infinity"}:
            errors.append(f"{path}: non-finite numeric string")
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f"{path}: non-finite number")
        if isinstance(value, dict):
            for k, v in value.items(): walk(v, f"{path}.{k}", k)
        elif isinstance(value, list):
            for i, v in enumerate(value): walk(v, f"{path}[{i}]", key)
        elif value not in (None, "") and (key in {"as_of", "prior_as_of", "date", "valuation_date", "run_date", "forecast_start", "effective_date", "holdings_as_of", "prices_as_of", "bucket_dates", "effective_from", "effective_to"}):
            try: datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError: errors.append(f"{path}: invalid ISO date/timestamp")
    if not isinstance(doc, dict): return ["input must be an object"], []
    walk(doc)
    if errors: return errors, []
    try:
        native_errors, warnings = _validate_legacy(doc)
        return native_errors, warnings
    except (TypeError, ValueError, KeyError, AttributeError, OverflowError) as exc:
        return [f"malformed input: {exc}"], []


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
