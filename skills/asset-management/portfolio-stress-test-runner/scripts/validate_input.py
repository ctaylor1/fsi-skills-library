#!/usr/bin/env python3
"""Deterministic input validation for portfolio-stress-test-runner.

Validates a stress-run input file before scenarios are executed. Fails closed on
structural problems (missing portfolio/positions/scenarios, non-numeric sensitivities or
shocks, exposures or shocks that reference an unknown risk factor) and on the skill's HARD
BOUNDARY: it will not run a scenario the firm has not approved. A scenario that is not
marked `approved: true`, carries no `scenario_set_id`, or comes from a source that is not an
approved scenario library (e.g. `stress-test-scenario-designer`) is rejected here - the
runner executes approved scenarios; it never invents them. Data-quality gaps that weaken a
run but do not break it (missing provenance/citation, positions that do not reconcile to the
stated base value, shocks with no exposed position) are warnings.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  portfolio_id, as_of (YYYY-MM-DD), run_date (YYYY-MM-DD), config_version, model_version,
  portfolio_base_value (> 0), reconciliation_tolerance (optional),
  risk_factors{factor_id -> {label,unit,provenance,citation}},
  positions[ {position_id, market_value, provenance, citation,
              factor_exposures{factor_id -> {sensitivity, convexity?, provenance, citation}}} ],
  scenarios[ {scenario_id, type('historical'|'hypothetical'), approved(bool),
              scenario_set_id, scenario_set_version, source, approval_ref, citation,
              shocks{factor_id -> number}} ],
  approved_engine_totals{scenario_id -> number}   (optional)

Usage:
  python validate_input.py stress_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("portfolio_id", "as_of", "run_date", "config_version", "model_version",
                "portfolio_base_value", "risk_factors", "positions", "scenarios")
# HARD BOUNDARY: scenarios may only originate from an approved scenario library. The runner
# consumes definitions from stress-test-scenario-designer (or a firm approved-scenario
# library); it never authors or improvises a scenario.
APPROVED_SOURCES = {"stress-test-scenario-designer", "approved-scenario-library"}
SCENARIO_TYPES = {"historical", "hypothetical"}


def _num(node, default=None):
    try:
        import math
        value = node.get("value") if isinstance(node, dict) else node
        if isinstance(value, bool): return None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, AttributeError):
        return default


def _prov_cite(node):
    if isinstance(node, dict):
        return (node.get("provenance") or "").strip(), (node.get("citation") or "").strip()
    return "", ""


def _validate_legacy(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if not DATE_RE.match(str(doc["run_date"])):
        errors.append(f"run_date must start YYYY-MM-DD, got {doc['run_date']!r}")

    base_value = _num(doc["portfolio_base_value"])
    if base_value is None or base_value <= 0:
        errors.append(f"portfolio_base_value must be a positive number, got {doc['portfolio_base_value']!r}")

    factors = doc.get("risk_factors") or {}
    if not isinstance(factors, dict) or not factors:
        errors.append("risk_factors must be a non-empty mapping of factor_id -> definition")
        factors = {}

    # positions
    positions = doc.get("positions") or []
    if not positions:
        errors.append("positions must be a non-empty list")
    mv_sum = 0.0
    seen_pos = set()
    for i, p in enumerate(positions):
        pid = p.get("position_id")
        if not pid:
            errors.append(f"positions[{i}] missing position_id")
            pid = f"#{i}"
        if pid in seen_pos:
            errors.append(f"duplicate position_id {pid!r}")
        seen_pos.add(pid)
        mv = _num(p.get("market_value"))
        if mv is None:
            errors.append(f"position {pid}: market_value is not numeric")
        else:
            mv_sum += mv
        prov, cite = _prov_cite(p)
        if not prov or not cite:
            warnings.append(f"position {pid}: missing provenance/citation - validate_output will reject an unsourced position")
        exps = p.get("factor_exposures") or {}
        if not isinstance(exps, dict) or not exps:
            errors.append(f"position {pid}: factor_exposures must be a non-empty mapping")
            continue
        for fid, node in exps.items():
            if fid not in factors:
                errors.append(f"position {pid}: exposure references unknown risk factor {fid!r}")
            if _num(node.get("sensitivity") if isinstance(node, dict) else node) is None:
                errors.append(f"position {pid}: exposure {fid} sensitivity is not numeric")
            if isinstance(node, dict) and "convexity" in node and _num(node.get("convexity")) is None:
                errors.append(f"position {pid}: exposure {fid} convexity is present but not numeric")
            eprov, ecite = _prov_cite(node)
            if not eprov or not ecite:
                warnings.append(f"position {pid} exposure {fid}: missing provenance/citation on the factor sensitivity")

    if base_value and positions and errors == []:
        tol = _num(doc.get("reconciliation_tolerance"), 0.01) or 0.01
        if abs(mv_sum - base_value) > max(tol, abs(base_value) * 1e-6):
            warnings.append(f"positions market_value sum ({round(mv_sum, 4)}) does not reconcile to "
                            f"portfolio_base_value ({base_value}); check the holdings feed")

    # scenarios (HARD BOUNDARY enforcement)
    scenarios = doc.get("scenarios") or []
    if not scenarios:
        errors.append("scenarios must be a non-empty list")
    seen_scen = set()
    for i, s in enumerate(scenarios):
        sid = s.get("scenario_id")
        if not sid:
            errors.append(f"scenarios[{i}] missing scenario_id")
            sid = f"#{i}"
        if sid in seen_scen:
            errors.append(f"duplicate scenario_id {sid!r}")
        seen_scen.add(sid)
        if s.get("type") not in SCENARIO_TYPES:
            errors.append(f"scenario {sid}: type must be one of {sorted(SCENARIO_TYPES)}, got {s.get('type')!r}")
        if s.get("approved") is not True:
            errors.append(f"scenario {sid}: 'approved' must be true - the runner never executes an "
                          f"un-approved or invented scenario (HARD BOUNDARY)")
        if not (s.get("scenario_set_id") or "").strip():
            errors.append(f"scenario {sid}: missing scenario_set_id - a scenario must come from an "
                          f"approved scenario set, not be improvised")
        src = (s.get("source") or "").strip()
        if src not in APPROVED_SOURCES:
            errors.append(f"scenario {sid}: source {src!r} is not an approved scenario source "
                          f"{sorted(APPROVED_SOURCES)} - consume definitions from stress-test-scenario-designer")
        if not (s.get("citation") or "").strip():
            warnings.append(f"scenario {sid}: missing citation - validate_output will reject an uncited scenario")
        if not (s.get("approval_ref") or "").strip():
            warnings.append(f"scenario {sid}: missing approval_ref - record who approved the scenario set")
        shocks = s.get("shocks") or {}
        if not isinstance(shocks, dict) or not shocks:
            errors.append(f"scenario {sid}: shocks must be a non-empty mapping of factor_id -> number")
            continue
        for fid, val in shocks.items():
            if fid not in factors:
                errors.append(f"scenario {sid}: shock references unknown risk factor {fid!r}")
            if _num(val) is None:
                errors.append(f"scenario {sid}: shock {fid} is not numeric")
        exposed = {fid for p in positions for fid in (p.get("factor_exposures") or {})}
        for fid in shocks:
            if fid in factors and fid not in exposed:
                warnings.append(f"scenario {sid}: shocks factor {fid} that no position is exposed to - no P&L effect")

    # optional approved-engine totals
    aet = doc.get("approved_engine_totals") or {}
    if aet:
        if not isinstance(aet, dict):
            errors.append("approved_engine_totals must be a mapping of scenario_id -> number")
        else:
            for k, v in aet.items():
                if k not in seen_scen:
                    warnings.append(f"approved_engine_totals references unknown scenario_id {k!r}")
                if _num(v) is None:
                    errors.append(f"approved_engine_totals[{k}] is not numeric")

    if "reconciliation_tolerance" in doc and (_num(doc["reconciliation_tolerance"]) is None or _num(doc["reconciliation_tolerance"]) < 0):
        errors.append("reconciliation_tolerance must be nonnegative")
    for scenario in doc.get("scenarios", []):
        for key in ("scenario_set_version", "approval_ref", "citation"):
            if not scenario.get(key): errors.append(f"scenario {scenario.get('scenario_id')}: {key} required")
    for factor, definition in (doc.get("risk_factors") or {}).items():
        if not definition.get("unit"): errors.append(f"{factor}: shock unit required")
    if str(doc.get("run_date", "")) < str(doc.get("as_of", "")): errors.append("run_date precedes portfolio as_of")
    warnings.append("supplied approval metadata is unverified; delta/diagonal-gamma approximation is not historical calibration or full repricing")
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
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "stress_input_example.json"
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
