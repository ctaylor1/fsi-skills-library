#!/usr/bin/env python3
"""Deterministic scenario / sensitivity / breakeven / decision-threshold engine.

Reads a model file (see validate_input.py), evaluates the base case and every requested
analysis DETERMINISTICALLY from explicit driver assumptions and whitelisted arithmetic
formulas, and emits a machine-readable analysis pack the SKILL wraps in a narrative.

Model contract (JSON): see references/source-map.md and references/domain-rules.md. Outputs
are computed from drivers (and earlier outputs) via safe arithmetic only — no black-box or
learned function, no I/O, no advice. The same inputs + config always reproduce the same
numbers (reproducibility), and every number ties out to a stated formula and driver value.

IMPORTANT: This produces analytical *mechanics* only — scenarios, sensitivity tables,
breakevens, and decision thresholds. It never produces a buy/sell/hold recommendation, a
price target presented as advice, or any personalized investment advice.

Usage:
  python calculate_or_transform.py model.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import ast, json, operator, sys, math
from pathlib import Path

DISCLAIMER = (
    "Analytical scenario and sensitivity output only; not investment advice, a "
    "recommendation, or a price target. Assumptions are user/model-supplied and must be "
    "reviewed by a qualified professional before any decision or external delivery."
)

# ---- safe arithmetic evaluator (deterministic, no eval/exec) -------------------------
_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
_UN = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCS = {"min": min, "max": max, "abs": abs}


def safe_eval(expr: str, env: dict) -> float:
    """Evaluate a whitelisted arithmetic expression over the variable namespace `env`."""
    node = ast.parse(str(expr), mode="eval").body
    value = float(_ev(node, env))
    if not math.isfinite(value):
        raise ValueError("formula produced a non-finite result")
    return value


def _ev(n, env):
    if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
        return _BIN[type(n.op)](_ev(n.left, env), _ev(n.right, env))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _UN:
        return _UN[type(n.op)](_ev(n.operand, env))
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
        return float(n.value)
    if isinstance(n, ast.Name):
        if n.id in env:
            return float(env[n.id])
        raise ValueError(f"unknown variable {n.id!r} in formula")
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUNCS:
        return float(_FUNCS[n.func.id](*[_ev(a, env) for a in n.args]))
    raise ValueError("unsupported expression element in formula")


def evaluate_model(driver_values: dict, outputs: list) -> dict:
    """Compute every output in declared order; outputs may reference drivers + earlier outputs."""
    env = {k: float(v) for k, v in driver_values.items()}
    for o in outputs:
        env[o["name"]] = safe_eval(o["formula"], env)
    return env


def _bisect(f, lo: float, hi: float, iters: int = 200, tol: float = 1e-12):
    """Deterministic bisection for a single sign change in [lo, hi]. Returns (root|None, n, ok)."""
    flo, fhi = f(lo), f(hi)
    if flo == 0.0:
        return lo, 0, True
    if fhi == 0.0:
        return hi, 0, True
    if flo * fhi > 0:
        return None, 0, False  # Same-sign endpoints do not rule out interior roots.
    a, b = lo, hi
    for i in range(1, iters + 1):
        m = 0.5 * (a + b)
        fm = f(m)
        if abs(fm) <= tol or (b - a) <= tol:
            return m, i, True
        if flo * fm < 0:
            b, fhi = m, fm
        else:
            a, flo = m, fm
    return 0.5 * (a + b), iters, True


# ---- analysis builders ---------------------------------------------------------------

def _calculate_native(doc: dict) -> dict:
    outputs_def = doc["outputs"]
    out_names = [o["name"] for o in outputs_def]
    base_drivers = {d["name"]: float(d["base"]) for d in doc["drivers"]}

    base_env = evaluate_model(base_drivers, outputs_def)
    base_case = {n: base_env[n] for n in out_names}

    # Scenarios ------------------------------------------------------------------------
    scenarios = []
    for sc in doc.get("scenarios", []):
        overrides = sc.get("overrides", {}) or {}
        dv = dict(base_drivers)
        dv.update({k: float(v) for k, v in overrides.items()})
        env = evaluate_model(dv, outputs_def)
        outs = {n: env[n] for n in out_names}
        deltas = {n: outs[n] - base_case[n] for n in out_names}
        pct = {n: ((outs[n] - base_case[n]) / base_case[n]) if base_case[n] != 0 else None
               for n in out_names}
        scenarios.append({"name": sc["name"], "overrides": overrides,
                          "outputs": outs, "deltas_vs_base": deltas, "pct_vs_base": pct})

    # One-way sensitivities ------------------------------------------------------------
    sensitivities = []
    for s in doc.get("sensitivities", []):
        drv, out = s["driver"], s["output"]
        base_val = base_case[out]
        pts = []
        for x in s["points"]:
            dv = dict(base_drivers)
            dv[drv] = float(x)
            env = evaluate_model(dv, outputs_def)
            val = env[out]
            pts.append({"driver_value": float(x), "output_value": val,
                        "pct_change_vs_base": ((val - base_val) / base_val) if base_val != 0 else None})
        sensitivities.append({"driver": drv, "output": out, "base_value": base_val, "points": pts})

    # Two-way data tables --------------------------------------------------------------
    two_way = []
    for t in doc.get("two_way", []):
        rd, cd, out = t["row_driver"], t["col_driver"], t["output"]
        grid = []
        for rv in t["row_points"]:
            row = []
            for cv in t["col_points"]:
                dv = dict(base_drivers)
                dv[rd] = float(rv)
                dv[cd] = float(cv)
                env = evaluate_model(dv, outputs_def)
                row.append(env[out])
            grid.append(row)
        two_way.append({"row_driver": rd, "col_driver": cd, "output": out,
                        "row_points": [float(x) for x in t["row_points"]],
                        "col_points": [float(x) for x in t["col_points"]], "grid": grid})

    # Breakevens (solve driver value where output == target) ---------------------------
    breakevens = []
    for b in doc.get("breakevens", []):
        drv, out, target = b["driver"], b["output"], float(b["target"])
        lo, hi = float(b.get("lo", 0.0)), float(b.get("hi", base_drivers[drv] * 4 + 1.0))

        def f(x, drv=drv, out=out, target=target):
            dv = dict(base_drivers)
            dv[drv] = x
            return evaluate_model(dv, outputs_def)[out] - target
        root, n, ok = _bisect(f, lo, hi)
        breakevens.append({"driver": drv, "output": out, "target": target,
                           "bracket": [lo, hi], "method": "bisection", "iterations": n,
                           "converged": ok, "solution": root,
                           "search_status": "root-found" if ok else "not-bracketed",
                           "note": None if ok else "No sign-change bracket; existence of interior roots is unknown."})

    # Decision thresholds (driver level at which output crosses a reference target) -----
    thresholds = []
    for th in doc.get("decision_thresholds", []):
        drv, out, target = th["driver"], th["output"], float(th["target"])
        lo, hi = float(th.get("lo", 0.0)), float(th.get("hi", base_drivers[drv] * 4 + 1.0))
        base_out = base_case[out]

        def g(x, drv=drv, out=out, target=target):
            dv = dict(base_drivers)
            dv[drv] = x
            return evaluate_model(dv, outputs_def)[out] - target
        root, n, ok = _bisect(g, lo, hi)
        thresholds.append({
            "driver": drv, "output": out, "target": target, "label": th.get("label"),
            "bracket": [lo, hi], "iterations": n, "converged": ok,
            "threshold_value": root, "base_driver_value": base_drivers[drv],
            "base_output_value": base_out, "base_meets_target": base_out >= target,
            "search_status": "root-found" if ok else "not-bracketed",
            "note": None if ok else "No sign-change bracket; existence of interior roots is unknown."})

    return {
        "analysis_id": f"ssg-{doc['model_id']}-{doc['as_of']}-0001",
        "model_id": doc["model_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "currency": doc.get("currency"),
        "unit": doc.get("unit"),
        "drivers": doc["drivers"],
        "outputs_def": outputs_def,
        "base_case": base_case,
        "integration_status": "supplied-formula-graph-only",
        "limitations": ["No native three-statement/DCF/credit runner adapter; formulas are supplied independently.", "No economic coherence, financing feasibility, calibrated probabilities or full instrument repricing is established."],
        "scenarios": scenarios,
        "sensitivities": sensitivities,
        "two_way_tables": two_way,
        "breakevens": breakevens,
        "decision_thresholds": thresholds,
        "disclaimer": DISCLAIMER,
    }


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

def compute(doc):
    errors, warnings = _local_module("validate_input.py").validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    result = _calculate_native(doc)
    result["validation_warnings"] = warnings
    result["method_id"] = 'scenario-sensitivity-generator'
    result["method_version"] = "0.3.0"
    result["result_origin"] = "local-analysis"
    result["review_status"] = "not-requested"
    result["execution_status"] = "not-performed"
    result["method_scope"] = 'scenario-sensitivity-generator: bounded supplied-input local analysis; no source authentication, approval or execution'
    return _local_module("native_integrity.py").attach_source(result, doc)

def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_example.json"
        doc = _strict_json(p.read_text(encoding="utf-8"))
    elif argv:
        doc = _strict_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _strict_json(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


_main_checked = main

def main(argv):
    try:
        return _main_checked(argv)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR", str(exc), file=sys.stderr)
        return 1

_compute_phase1 = compute

def compute(doc):
    if isinstance(doc, dict) and doc.get('schema_version') == 'ir-phase2/1.0':
        return _local_module('phase2_domain.py').compute(doc)
    return _compute_phase1(doc)

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
