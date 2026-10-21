#!/usr/bin/env python3
"""Deterministic input validation for counterparty-exposure-monitor.

Validates an exposures file before aggregation and alerting. Fails closed on structural
problems; warns on data-quality gaps that limit which checks are evaluable or that reduce
alert confidence (stale feeds, missing limits, missing collateral/PFE, missing credit
fields). A stale feed is a WARNING here (the monitor still runs and flags dependent alerts
stale) — it is never a reason to silently drop an exposure.

Input schema (JSON): see references/source-map.md. Key fields:
  as_of (YYYY-MM-DD[THH:MM[:SS]]), config_version,
  feeds[{feed, as_of, max_age_hours}],
  counterparties[{counterparty_id, rating, rating_floor, cds_bps, cds_baseline_bps, watch, source_ref}],
  limits[{counterparty_id?, limit_type, limit}],
  exposures[{counterparty_id, exposure_type, current_exposure, collateral, pfe_addon, feed, source_ref}],
  open_alerts[], config{...thresholds...}

Usage:
  python validate_input.py exposures.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("as_of", "config_version", "counterparties", "limits", "exposures")
REQUIRED_EXP = ("counterparty_id", "exposure_type", "current_exposure", "feed", "source_ref")


def _num(v):
    try:
        import math
        if isinstance(v, bool): return None
        number = float(v)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _parse_dt(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _validate_legacy(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    run_dt = _parse_dt(doc["as_of"])
    if not DATE_RE.match(str(doc["as_of"])) or run_dt is None:
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    # feeds + freshness (warn only)
    feed_names = set()
    feed_ages = {}
    for i, f in enumerate(doc.get("feeds", []) or []):
        if not f.get("feed") or not f.get("as_of"):
            errors.append(f"feeds[{i}]: missing 'feed' or 'as_of'")
            continue
        feed_names.add(f["feed"])
        fdt = _parse_dt(f["as_of"])
        if fdt is None:
            errors.append(f"feeds[{i}] ({f['feed']}): unparseable as_of {f['as_of']!r}")
        elif run_dt is not None:
            age = (run_dt - fdt).total_seconds() / 3600.0
            feed_ages[f["feed"]] = age
            max_age = _num(f.get("max_age_hours"))
            if max_age is not None and age > max_age:
                warnings.append(f"feed '{f['feed']}' is stale ({age:.1f}h > {max_age:.0f}h) — "
                                f"dependent alerts will be flagged stale, not suppressed")

    # counterparties
    cp_ids = set()
    for i, c in enumerate(doc.get("counterparties", []) or []):
        cid = c.get("counterparty_id")
        if not cid:
            errors.append(f"counterparties[{i}]: missing 'counterparty_id'")
            continue
        if cid in cp_ids:
            errors.append(f"counterparties[{i}]: duplicate counterparty_id {cid!r}")
        cp_ids.add(cid)
        if not c.get("rating") or not c.get("rating_floor"):
            warnings.append(f"counterparty {cid}: no rating/rating_floor — rating-floor check not evaluable")
        if c.get("cds_bps") is None or c.get("cds_baseline_bps") is None:
            warnings.append(f"counterparty {cid}: no CDS baseline — spread-widening check not evaluable")

    # exposures
    exps = doc.get("exposures") or []
    if not isinstance(exps, list) or not exps:
        errors.append("exposures must be a non-empty list")
        return errors, warnings
    exp_cps = set()
    for i, e in enumerate(exps):
        tag = f"exposures[{i}] ({e.get('counterparty_id', '?')}/{e.get('exposure_type', '?')})"
        for k in REQUIRED_EXP:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(e.get("current_exposure")) is None:
            errors.append(f"{tag}: current_exposure not numeric")
        if e.get("collateral") is not None and _num(e.get("collateral")) is None:
            errors.append(f"{tag}: collateral not numeric")
        if e.get("counterparty_id") and e["counterparty_id"] not in cp_ids:
            errors.append(f"{tag}: references counterparty not in counterparties list")
        if feed_names and e.get("feed") and e["feed"] not in feed_names:
            warnings.append(f"{tag}: feed '{e.get('feed')}' has no freshness record — calculation will reject incomplete freshness coverage")
        if e.get("collateral") is None:
            warnings.append(f"{tag}: no collateral field — treated as uncollateralized")
        exp_cps.add(e.get("counterparty_id"))

    # limits
    cp_limited = set()
    has_conc = False
    for i, lim in enumerate(doc.get("limits", []) or []):
        lt = lim.get("limit_type")
        if lt == "total_current_exposure":
            if not lim.get("counterparty_id"):
                errors.append(f"limits[{i}]: total_current_exposure limit needs a counterparty_id")
            else:
                cp_limited.add(lim["counterparty_id"])
            if _num(lim.get("limit")) is None:
                errors.append(f"limits[{i}]: limit not numeric")
        elif lt == "single_name_concentration_pct":
            has_conc = True
            if _num(lim.get("limit")) is None:
                errors.append(f"limits[{i}]: concentration limit not numeric")
        else:
            warnings.append(f"limits[{i}]: unrecognized limit_type {lt!r}")

    for cp in sorted(exp_cps):
        if cp and cp not in cp_limited:
            warnings.append(f"counterparty {cp}: no total_current_exposure limit — utilization not evaluable")
    if not has_conc:
        warnings.append("no single_name_concentration_pct limit — concentration not evaluable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")

    feed_map = {f["feed"]: f for f in doc.get("feeds", [])}
    if doc.get("counterparties") and "credit" not in feed_map: errors.append("credit assessment requires credit feed freshness")
    for row in doc.get("exposures", []):
        if row.get("feed") not in feed_map: errors.append("every exposure requires a feed freshness record")
        for key in ("current_exposure", "collateral", "pfe_addon"):
            if row.get(key) is None or _num(row.get(key)) is None: errors.append(f"exposure requires explicit numeric {key}")
        for key in ("collateral", "pfe_addon"):
            if _num(row.get(key)) is not None and _num(row[key]) < 0: errors.append(f"negative {key} unsupported")
    from datetime import datetime
    for f in doc.get("feeds", []):
        try:
            age = (datetime.fromisoformat(str(doc["as_of"]).replace("Z", "+00:00")) - datetime.fromisoformat(str(f["as_of"]).replace("Z", "+00:00"))).total_seconds()
            if age < 0: errors.append("feed timestamp cannot be after run timestamp")
        except (ValueError, TypeError): errors.append("feed and run timestamps require compatible timezone conventions")
        if float(f.get("max_age_hours", 24)) < 0: errors.append("negative feed freshness threshold")
    cfg = doc.get("config") or {}
    if not 0 <= float(cfg.get("warn_pct", .8)) <= float(cfg.get("breach_pct", 1)) <= float(cfg.get("critical_pct", 1.1)):
        errors.append("counterparty utilization thresholds must be ordered and nonnegative")
    if any(float(l.get("limit", 0)) <= 0 for l in doc.get("limits", [])): errors.append("limits must be positive")
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
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exposures_example.json"
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
