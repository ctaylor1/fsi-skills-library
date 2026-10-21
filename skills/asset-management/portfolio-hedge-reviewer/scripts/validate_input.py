#!/usr/bin/env python3
"""Deterministic input validation for portfolio-hedge-reviewer.

Validates a hedge-analysis input file before exposures/sensitivities are computed. Fails
closed on structural problems (missing model/version, undefined risk factors, non-numeric
sensitivities or shocks, no candidate hedges, duplicate hedge ids); warns on data-quality
gaps that weaken the packet (missing provenance/citation, a hedge that touches a factor the
portfolio has no exposure to, approved-engine totals that reference an unknown scenario).

Input schema (JSON): see references/source-map.md. Key fields:
  case_id, as_of (YYYY-MM-DD), valuation_date (YYYY-MM-DD), config_version, base_currency,
  units, model{id,version,effective_date,provenance,citation},
  risk_factors{FACTOR -> {unit, provenance, citation}},
  portfolio{id, sensitivities{FACTOR -> {value,provenance,citation}},
            approved_engine_totals{gross_sensitivity, scenarios{scenario_id -> value}}},
  candidate_hedges[ {id, label, sensitivities{FACTOR -> {value,...}}, cost{value,...}} ],
  scenarios[ {id, label, shocks{FACTOR -> value}, provenance, citation} ]

Usage:
  python validate_input.py hedge_input.json | --selftest
Prints a line ending "N error(s)"; exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("case_id", "as_of", "valuation_date", "config_version", "model",
                "risk_factors", "portfolio", "candidate_hedges", "scenarios")


def _v(node):
    try:
        import math
        value = node.get("value") if isinstance(node, dict) else node
        if isinstance(value, bool): return None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, AttributeError):
        return None


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
    if not DATE_RE.match(str(doc["valuation_date"])):
        errors.append(f"valuation_date must start YYYY-MM-DD, got {doc['valuation_date']!r}")

    # model (approved-model provenance is mandatory for reproducibility)
    model = doc.get("model") or {}
    for k in ("id", "version", "effective_date"):
        if not str(model.get(k, "")).strip():
            errors.append(f"model.{k} is required (approved-model version/effective-date provenance)")
    if model.get("effective_date") and not DATE_RE.match(str(model["effective_date"])):
        errors.append(f"model.effective_date must start YYYY-MM-DD, got {model['effective_date']!r}")
    mprov, mcite = _prov_cite(model)
    if not mprov or not mcite:
        warnings.append("model has no provenance/citation — validate_output will reject the packet")

    # risk factors
    factors = doc.get("risk_factors") or {}
    if not factors:
        errors.append("risk_factors is empty — at least one factor is required")
    for f, node in factors.items():
        if not (isinstance(node, dict) and str(node.get("unit", "")).strip()):
            errors.append(f"risk_factors.{f}.unit is required (standardized shock unit, e.g. +1bp)")
        prov, cite = _prov_cite(node)
        if not prov or not cite:
            warnings.append(f"risk_factors.{f} has no provenance/citation — validate_output will reject the packet")

    # portfolio
    port = doc.get("portfolio") or {}
    if not str(port.get("id", "")).strip():
        errors.append("portfolio.id is required")
    p_sens = port.get("sensitivities") or {}
    if not p_sens:
        errors.append("portfolio.sensitivities is empty — the base exposure set is required")
    for f, node in p_sens.items():
        if f not in factors:
            errors.append(f"portfolio.sensitivities references undefined risk factor '{f}'")
        if _v(node) is None:
            errors.append(f"portfolio.sensitivities.{f} value is not numeric")
        prov, cite = _prov_cite(node)
        if not prov or not cite:
            warnings.append(f"portfolio.sensitivities.{f} has no provenance/citation — validate_output will reject the packet")

    # candidate hedges
    hedges = doc.get("candidate_hedges") or []
    if not hedges:
        errors.append("candidate_hedges is empty — a human-defined hedge set is required (this skill does not invent hedges)")
    seen = set()
    for i, h in enumerate(hedges):
        hid = h.get("id")
        if not str(hid or "").strip():
            errors.append(f"candidate_hedges[{i}].id is required")
        elif hid in seen:
            errors.append(f"duplicate candidate hedge id '{hid}'")
        else:
            seen.add(hid)
        hs = h.get("sensitivities") or {}
        if not hs:
            errors.append(f"candidate hedge '{hid}' has no sensitivities")
        for f, node in hs.items():
            if f not in factors:
                errors.append(f"hedge '{hid}' references undefined risk factor '{f}'")
            if _v(node) is None:
                errors.append(f"hedge '{hid}' sensitivity {f} is not numeric")
            prov, cite = _prov_cite(node)
            if not prov or not cite:
                warnings.append(f"hedge '{hid}' sensitivity {f} has no provenance/citation — validate_output will reject the packet")
            if f in factors and f not in p_sens:
                warnings.append(f"hedge '{hid}' hedges factor '{f}' the portfolio has no exposure to — it will add exposure, not offset it")
        cost = h.get("cost")
        if cost is not None and _v(cost) is None:
            errors.append(f"hedge '{hid}' cost value is not numeric")
        if isinstance(cost, dict):
            prov, cite = _prov_cite(cost)
            if not prov or not cite:
                warnings.append(f"hedge '{hid}' cost has no provenance/citation — validate_output will reject the packet")

    # scenarios
    scen_ids = set()
    for i, s in enumerate(doc.get("scenarios") or []):
        sid = s.get("id")
        if not str(sid or "").strip():
            errors.append(f"scenarios[{i}].id is required")
        else:
            scen_ids.add(sid)
        shocks = s.get("shocks") or {}
        if not shocks:
            errors.append(f"scenario '{sid}' has no shocks")
        for f, val in shocks.items():
            if f not in factors:
                errors.append(f"scenario '{sid}' shocks undefined risk factor '{f}'")
            if _v(val) is None:
                errors.append(f"scenario '{sid}' shock {f} is not numeric")
        prov, cite = _prov_cite(s)
        if not prov or not cite:
            warnings.append(f"scenario '{sid}' has no provenance/citation — validate_output will reject the packet")

    # approved-engine totals (optional; reconciled downstream)
    approved = (port.get("approved_engine_totals") or {})
    for sid in (approved.get("scenarios") or {}):
        if sid not in scen_ids:
            warnings.append(f"approved_engine_totals references scenario '{sid}' not in scenarios — it cannot be reconciled")
    if not approved:
        warnings.append("no portfolio.approved_engine_totals supplied — the packet will not reconcile to an approved risk engine")

    for factor, definition in (doc.get("risk_factors") or {}).items():
        if not definition.get("unit"): errors.append(f"{factor}: explicit shock unit required")
    for hedge in doc.get("candidate_hedges", []):
        cost = hedge.get("cost")
        if not isinstance(cost, dict) or not cost.get("type") or not cost.get("provenance") or not cost.get("citation"):
            errors.append("each supplied hedge cost needs type, provenance and citation")
        elif not cost.get("horizon"): warnings.append(f"{hedge.get('id')}: cost horizon unavailable; no cross-candidate cost ranking")
    warnings.append("aggregate coverage depends on factor shock normalization; it does not measure total portfolio risk reduction")
    return errors, warnings


def validate(doc: dict):
    """Validate finite source data and real ISO dates before package-specific checks."""
    if isinstance(doc, dict) and 'extension' in doc:
        from advanced_derivatives import validate as specialist_validate
        return specialist_validate(doc), []
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
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "hedge_input_example.json"
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
