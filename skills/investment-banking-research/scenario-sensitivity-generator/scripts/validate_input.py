#!/usr/bin/env python3
"""Deterministic input validation for scenario-sensitivity-generator.

Validates a model file before the engine runs. Fails closed on structural problems (missing
drivers, unparsable/undefined formulas, analyses that reference unknown drivers/outputs) and
warns on provenance gaps that weaken assumption traceability.

Input schema (JSON): see references/source-map.md. Key fields:
  model_id, as_of (YYYY-MM-DD), config_version, currency, unit,
  drivers[{name, base, unit, source_ref, provenance}],
  outputs[{name, formula, unit}],                       # formula = whitelisted arithmetic
  scenarios[{name, overrides{driver:value}}],
  sensitivities[{driver, output, points[]}],
  two_way[{row_driver, col_driver, output, row_points[], col_points[]}],
  breakevens[{driver, output, target, lo?, hi?}],
  decision_thresholds[{driver, output, target, label, lo?, hi?}]

Usage:
  python validate_input.py model.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import ast, json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("model_id", "as_of", "config_version", "drivers", "outputs")
_ALLOWED_FUNCS = {"min", "max", "abs"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _formula_names(expr: str):
    """Return the set of variable names referenced by a whitelisted arithmetic formula.

    Raises ValueError if the formula uses an unsupported construct (calls to unknown
    functions, attribute access, subscripting, comprehensions, etc.).
    """
    tree = ast.parse(str(expr), mode="eval")
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Call):
            if not (isinstance(node.func, ast.Name) and node.func.id in _ALLOWED_FUNCS):
                raise ValueError("only min/max/abs calls are allowed")
        elif isinstance(node, (ast.Attribute, ast.Subscript, ast.Lambda, ast.comprehension,
                               ast.BoolOp, ast.Compare, ast.IfExp)):
            raise ValueError("unsupported expression construct")
    # function names appear as ast.Name too; drop the whitelisted ones
    return names - _ALLOWED_FUNCS


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    drivers = doc.get("drivers") or []
    outputs = doc.get("outputs") or []
    if not isinstance(drivers, list) or not drivers:
        errors.append("drivers must be a non-empty list")
    if not isinstance(outputs, list) or not outputs:
        errors.append("outputs must be a non-empty list")
    if errors:
        return errors, warnings

    # drivers -------------------------------------------------------------------------
    driver_names, seen = set(), set()
    for i, d in enumerate(drivers):
        tag = f"drivers[{i}] ({d.get('name','?')})"
        nm = d.get("name")
        if not nm:
            errors.append(f"{tag}: missing 'name'")
            continue
        if nm in seen:
            errors.append(f"{tag}: duplicate driver name")
        seen.add(nm)
        driver_names.add(nm)
        if _num(d.get("base")) is None:
            errors.append(f"{tag}: 'base' not numeric")
        if not str(d.get("source_ref", "")).strip():
            errors.append(f"{tag}: missing 'source_ref' (assumption provenance is required)")
        if not str(d.get("provenance", "")).strip():
            warnings.append(f"{tag}: no 'provenance' (upstream model/source) recorded")

    # outputs -------------------------------------------------------------------------
    output_names, defined = set(), set(driver_names)
    for i, o in enumerate(outputs):
        tag = f"outputs[{i}] ({o.get('name','?')})"
        nm = o.get("name")
        if not nm:
            errors.append(f"{tag}: missing 'name'")
            continue
        if nm in driver_names:
            errors.append(f"{tag}: output name collides with a driver name")
        if nm in output_names:
            errors.append(f"{tag}: duplicate output name")
        output_names.add(nm)
        formula = o.get("formula")
        if not str(formula or "").strip():
            errors.append(f"{tag}: missing 'formula'")
            continue
        try:
            refs = _formula_names(formula)
        except (SyntaxError, ValueError) as e:
            errors.append(f"{tag}: invalid formula ({e})")
            continue
        unknown = refs - defined
        if unknown:
            errors.append(f"{tag}: formula references undefined name(s) {sorted(unknown)} "
                          f"(declare as a driver or an earlier output)")
        defined.add(nm)  # later outputs may reference this one

    driver_names | output_names

    # analyses reference declared drivers / outputs -----------------------------------
    def _check_driver(name, where):
        if name not in driver_names:
            errors.append(f"{where}: unknown driver {name!r}")

    def _check_output(name, where):
        if name not in output_names:
            errors.append(f"{where}: unknown output {name!r}")

    for i, sc in enumerate(doc.get("scenarios", [])):
        for k in (sc.get("overrides") or {}):
            _check_driver(k, f"scenarios[{i}] ({sc.get('name','?')}) override")
    for i, s in enumerate(doc.get("sensitivities", [])):
        _check_driver(s.get("driver"), f"sensitivities[{i}]")
        _check_output(s.get("output"), f"sensitivities[{i}]")
        if not s.get("points"):
            errors.append(f"sensitivities[{i}]: 'points' must be a non-empty list")
    for i, t in enumerate(doc.get("two_way", [])):
        _check_driver(t.get("row_driver"), f"two_way[{i}] row")
        _check_driver(t.get("col_driver"), f"two_way[{i}] col")
        _check_output(t.get("output"), f"two_way[{i}]")
    for i, b in enumerate(doc.get("breakevens", [])):
        _check_driver(b.get("driver"), f"breakevens[{i}]")
        _check_output(b.get("output"), f"breakevens[{i}]")
        if _num(b.get("target")) is None:
            errors.append(f"breakevens[{i}]: 'target' not numeric")
    for i, th in enumerate(doc.get("decision_thresholds", [])):
        _check_driver(th.get("driver"), f"decision_thresholds[{i}]")
        _check_output(th.get("output"), f"decision_thresholds[{i}]")
        if _num(th.get("target")) is None:
            errors.append(f"decision_thresholds[{i}]: 'target' not numeric")

    # data-quality warnings ------------------------------------------------------------
    if not doc.get("scenarios"):
        warnings.append("no 'scenarios' defined — only a base case will be produced")
    if not any(doc.get(k) for k in ("sensitivities", "two_way", "breakevens", "decision_thresholds")):
        warnings.append("no sensitivity/breakeven/threshold analysis requested — base case + scenarios only")
    if not str(doc.get("config_version", "")).strip():
        warnings.append("empty config_version — record the versioned assumption set for reproducibility")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_example.json"
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
