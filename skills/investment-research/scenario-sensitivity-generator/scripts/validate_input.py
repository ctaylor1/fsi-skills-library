#!/usr/bin/env python3
"""Bounded input validation for scenario-sensitivity-generator.

Finite JSON numbers, typed shapes, dates, identifiers and method domains are checked.
Malformed inputs return validation errors. See references/domain-rules.md for supported scope.
"""
from __future__ import annotations
import ast, json, re, sys, math
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("model_id", "as_of", "config_version", "drivers", "outputs")
_ALLOWED_FUNCS = {"min", "max", "abs"}


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


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


def _validate_native(doc: dict) -> tuple[list[str], list[str]]:
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
        if t.get("row_driver") == t.get("col_driver"):
            errors.append(f"two_way[{i}]: row_driver and col_driver must be distinct")
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


def _number(value):
    if isinstance(value, dict):
        value = value.get("value")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def _base_domains(doc):
    from datetime import date
    errors = []
    for key in ("as_of", "as_of_date", "valuation_date"):
        if key in doc:
            try:
                date.fromisoformat(doc[key])
            except (TypeError, ValueError):
                errors.append(key + " must be an exact valid YYYY-MM-DD date")
    for key in ("company", "company_id", "entity_id", "config_version", "analysis_id", "model_id", "currency", "units"):
        if key in doc and (not isinstance(doc[key], str) or not doc[key].strip()):
            errors.append(key + " must be a nonempty string")
    return errors


def _unique(rows, field, label, errors):
    seen = set()
    for row in rows:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(label + ": " + field + " must be a nonempty string")
        elif value in seen:
            errors.append(label + ": duplicate " + field + " " + value)
        else:
            seen.add(value)

def _phase1_shapes(doc):
    errors = []
    for key in []:
        if key in doc and not isinstance(doc[key], dict):
            errors.append(key + " must be an object")
    for key in ['drivers', 'outputs', 'scenarios', 'sensitivities', 'two_way', 'breakevens', 'decision_thresholds']:
        if key in doc and (not isinstance(doc[key], list) or any(not isinstance(row, dict) for row in doc[key])):
            errors.append(key + " must be a list of objects")
    if errors:
        return errors
    return errors

def _phase1_domains(doc):
    errors = _base_domains(doc)
    _unique(doc["drivers"], "name", "drivers", errors)
    _unique(doc["outputs"], "name", "outputs", errors)
    _unique(doc.get("scenarios", []), "name", "scenarios", errors)
    for row in doc["drivers"]:
        if not isinstance(row["name"], str) or not row["name"].isidentifier() or row["name"] in _ALLOWED_FUNCS:
            errors.append("driver names must be identifiers distinct from function names")
    for output in doc["outputs"]:
        if not output["name"].isidentifier() or output["name"] in _ALLOWED_FUNCS:
            errors.append("output names must be identifiers distinct from functions")
        expr = output["formula"]
        if not isinstance(expr, str) or len(expr) > 4096:
            errors.append("formula must be a string of at most 4096 characters")
            continue
        tree = ast.parse(expr, mode="eval")
        allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Load, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.UAdd, ast.USub)
        if len(list(ast.walk(tree))) > 512:
            errors.append("formula exceeds supported expression size")
        for node in ast.walk(tree):
            if not isinstance(node, allowed):
                errors.append("unsupported expression element")
            if isinstance(node, ast.Constant) and _number(node.value) is None:
                errors.append("formula constants must be finite numbers, not booleans/strings")
            if isinstance(node, ast.Call) and (node.keywords or not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS or (node.func.id == "abs" and len(node.args) != 1) or (node.func.id in ("min","max") and len(node.args) < 2)):
                errors.append("unsupported function call arguments")
    for scenario in doc.get("scenarios", []):
        if not isinstance(scenario.get("overrides", {}), dict) or any(_number(v) is None for v in scenario.get("overrides", {}).values()):
            errors.append("scenario overrides must be numeric objects")
    for group in ("sensitivities", "two_way"):
        for row in doc.get(group, []):
            keys = ("points",) if group == "sensitivities" else ("row_points", "col_points")
            for key in keys:
                values = row.get(key)
                if not isinstance(values, list) or not values or len(values) > 1000 or any(_number(v) is None for v in values):
                    errors.append(group + ": " + key + " requires 1–1000 numeric points")
            if group == "two_way" and isinstance(row.get("row_points"), list) and isinstance(row.get("col_points"), list) and len(row["row_points"]) * len(row["col_points"]) > 10000:
                errors.append("two-way grid exceeds 10000 cells")
    for group in ("breakevens", "decision_thresholds"):
        for row in doc.get(group, []):
            for key in ("lo", "hi", "target"):
                if key in row and _number(row[key]) is None:
                    errors.append(group + ": " + key + " must be numeric")
            if "lo" in row and "hi" in row and _number(row["lo"]) is not None and _number(row["hi"]) is not None and row["lo"] >= row["hi"]:
                errors.append(group + ": lower bracket must be below upper bracket")
    return errors

def _strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON object key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError("non-finite JSON constant: " + value)
    return _read_json(text, object_pairs_hook=pairs, parse_constant=constant)

def _local_module(filename):
    import importlib.util
    spec = importlib.util.spec_from_file_location("_local_" + filename.replace(".", "_"), Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def validate(doc):
    """Reject invalid JSON/shapes without treating an exception as a passing validation."""
    if not isinstance(doc, dict):
        return ["input must be an object"], []
    try:
        _local_module("native_integrity.py").canonical_hash(doc)
        shape_errors = _phase1_shapes(doc)
        if shape_errors:
            return shape_errors, []
        errors, warnings = _validate_native(doc)
        if not errors:
            errors.extend(_phase1_domains(doc))
        return errors, warnings
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
        return ["invalid input: " + str(exc)], []

def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_example.json"
        doc = _strict_json(p.read_text(encoding="utf-8"))
    elif argv:
        doc = _strict_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _strict_json(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


_main_checked = main

def main(argv):
    try:
        return _main_checked(argv)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR", str(exc), file=sys.stderr)
        return 1

_validate_phase1 = validate

def validate(doc):
    if isinstance(doc, dict) and doc.get('schema_version') == 'ir-phase2/1.0':
        try:
            _local_module('phase2_domain.py').validate_document(doc)
            return [], []
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
            return ['invalid Phase2 input: ' + str(exc)], []
    return _validate_phase1(doc)

def _read_json(raw, **options):
    """Reject duplicate object keys and nonfinite constants before binding."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON object key: '+key)
            result[key]=value
        return result
    def constant(value): raise ValueError('non-finite JSON constant: '+value)
    options.setdefault('object_pairs_hook',pairs)
    options.setdefault('parse_constant',constant)
    return json.loads(raw,**options)


_phase2_json_main = main

def main(*args, **kwargs):
    try: return _phase2_json_main(*args, **kwargs)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print('ERROR:', str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
