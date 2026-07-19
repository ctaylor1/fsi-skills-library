#!/usr/bin/env python3
"""Deterministic input validation for stress-test-scenario-designer.

Validates a scenario-design file before the engine runs. Fails closed on structural
problems; warns on design-quality gaps that weaken severe-but-plausible calibration or
reviewer acceptance.

Input schema (JSON): see references/source-map.md. Key fields:
  as_of (YYYY-MM-DD), config_version, horizon_quarters,
  binding_constraints[{metric,direction(min|max),limit,starting_value,unit}],
  risk_factors[{factor,unit,baseline,plausible_max_shock,severe_min_shock}],
  impact_model{metric:{factor:beta}}, reverse_stress{scenario,constraint},
  scenarios[{name,severity(baseline|adverse|severely_adverse),variables[{factor,value}],
             transmission_channels[],assumptions[],management_actions[]}]

Usage:
  python validate_input.py design.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("as_of", "config_version", "binding_constraints", "risk_factors", "scenarios")
SEVERITIES = {"baseline", "adverse", "severely_adverse"}


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

    factors = {}
    for i, f in enumerate(doc.get("risk_factors") or []):
        if not f.get("factor"):
            errors.append(f"risk_factors[{i}]: missing 'factor'")
            continue
        factors[f["factor"]] = f
        if _num(f.get("baseline")) is None:
            errors.append(f"risk_factor '{f['factor']}': baseline not numeric")
        if _num(f.get("plausible_max_shock")) is None:
            warnings.append(f"risk_factor '{f['factor']}': no plausible_max_shock — implausibly-severe shocks not screened")
        if _num(f.get("severe_min_shock")) is None:
            warnings.append(f"risk_factor '{f['factor']}': no severe_min_shock — insufficient-severity not screened")

    constraints = doc.get("binding_constraints") or []
    if not isinstance(constraints, list) or not constraints:
        errors.append("binding_constraints must be a non-empty list")
    cmetrics = set()
    for i, c in enumerate(constraints):
        tag = f"binding_constraints[{i}] ({c.get('metric','?')})"
        if not c.get("metric"):
            errors.append(f"{tag}: missing 'metric'")
        else:
            cmetrics.add(c["metric"])
        if c.get("direction") not in ("min", "max"):
            errors.append(f"{tag}: direction must be 'min' or 'max'")
        if _num(c.get("limit")) is None:
            errors.append(f"{tag}: limit not numeric")
        if _num(c.get("starting_value")) is None:
            errors.append(f"{tag}: starting_value not numeric")

    impact_model = doc.get("impact_model") or {}
    for metric in cmetrics:
        if metric not in impact_model:
            warnings.append(f"binding constraint '{metric}' has no impact_model betas — it will not be projected")

    scenarios = doc.get("scenarios") or []
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenarios must be a non-empty list")
        return errors, warnings
    if len(scenarios) < 2:
        warnings.append("only one scenario — a severity ladder needs at least baseline + one stress scenario")

    names, severities = set(), set()
    for i, s in enumerate(scenarios):
        tag = f"scenarios[{i}] ({s.get('name','?')})"
        if not s.get("name"):
            errors.append(f"{tag}: missing 'name'")
        elif s["name"] in names:
            errors.append(f"{tag}: duplicate scenario name")
        names.add(s.get("name"))
        sev = s.get("severity")
        if sev not in SEVERITIES:
            errors.append(f"{tag}: severity must be one of {sorted(SEVERITIES)}, got {sev!r}")
        severities.add(sev)
        vars_ = s.get("variables") or []
        if not vars_:
            errors.append(f"{tag}: no variables")
        for v in vars_:
            if v.get("factor") not in factors:
                errors.append(f"{tag}: variable references unknown factor {v.get('factor')!r}")
            if _num(v.get("value")) is None:
                errors.append(f"{tag}: variable '{v.get('factor')}' value not numeric")
        if not s.get("transmission_channels"):
            warnings.append(f"{tag}: no transmission_channels — evidence quality and coverage will be weak")
        if not s.get("assumptions"):
            warnings.append(f"{tag}: no assumptions documented")
        if sev != "baseline" and not s.get("management_actions"):
            warnings.append(f"{tag}: stress scenario has no management_actions")

    if "baseline" not in severities:
        warnings.append("no baseline scenario — shocks are computed against each scenario's own values (zero shock)")

    rs = doc.get("reverse_stress") or {}
    if rs:
        if rs.get("scenario") not in names:
            errors.append(f"reverse_stress.scenario {rs.get('scenario')!r} is not a defined scenario")
        if rs.get("constraint") not in cmetrics:
            errors.append(f"reverse_stress.constraint {rs.get('constraint')!r} is not a binding constraint")
    else:
        warnings.append("no reverse_stress block — reverse-stress threshold will not be derived")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "scenario_design_example.json"
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
