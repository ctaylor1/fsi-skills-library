#!/usr/bin/env python3
"""Deterministic output validation for scenario-sensitivity-generator.

Validates the final analysis pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. It INDEPENDENTLY re-derives every number from the stated drivers
and formulas, so a pack only passes if it ties out and reproduces. Checks:

  1. Assumption provenance — every driver has a base + non-empty source_ref; every output
     has a formula; every override/analysis references a declared driver/output.
  2. Formula tie-out — reported base_case equals an independent recomputation from
     drivers + formulas (formula correctness).
  3. Scenario behaviour — each scenario's reported outputs and deltas_vs_base recompute
     from base + overrides.
  4. Sensitivity / two-way / breakeven / threshold — every reported cell/solution
     recomputes; a converged breakeven/threshold plugged back in hits its target.
  5. Reproducibility — model_id + config_version present so a re-run is identified.
  6. No investment advice — narrative/labels contain no buy/sell/hold recommendation,
     price-target-as-advice, or personalized advice; the standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import ast, json, operator, re, sys
from pathlib import Path

TOL = 1e-6
DISCLAIMER_KEY = "not investment advice"
ADVICE_PATTERNS = [
    r"\bwe recommend (?:buy|sell|invest|purchas|acquir|divest)",
    r"\b(?:strong|conviction)\s+buy\b",
    r"\bbuy[\s-]?rating\b", r"\bsell[\s-]?rating\b", r"\bhold[\s-]?rating\b",
    r"\byou should (?:buy|sell|invest|acquire|divest)\b",
    r"\binvestors? should (?:buy|sell|invest|acquire|divest)\b",
    r"\brecommend(?:ed|ation)?\b.{0,20}\b(?:buy|sell|invest)\b",
    r"\bprice target\b", r"\boverweight\b", r"\bunderweight\b",
    r"\bour recommendation\b", r"\bwe advise\b", r"\bguaranteed returns?\b",
    r"\bshould (?:buy|sell|acquire|divest) (?:the )?(?:stock|shares|company)\b",
]

# ---- independent safe evaluator (duplicated so this script is self-contained) --------
_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
_UN = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCS = {"min": min, "max": max, "abs": abs}


def _seval(expr, env):
    return float(_ev(ast.parse(str(expr), mode="eval").body, env))


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
        raise ValueError(f"unknown variable {n.id!r}")
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUNCS:
        return float(_FUNCS[n.func.id](*[_ev(a, env) for a in n.args]))
    raise ValueError("unsupported expression element")


def _model(driver_values, outputs):
    env = {k: float(v) for k, v in driver_values.items()}
    for o in outputs:
        env[o["name"]] = _seval(o["formula"], env)
    return env


def _close(a, b):
    try:
        return abs(float(a) - float(b)) <= TOL + TOL * abs(float(b))
    except (TypeError, ValueError):
        return False


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    drivers = pack.get("drivers") or []
    outputs = pack.get("outputs_def") or []
    if not drivers or not outputs:
        return ["pack missing 'drivers' or 'outputs_def' — cannot tie out"]

    # 1. provenance --------------------------------------------------------------------
    base_drivers, driver_names = {}, set()
    for d in drivers:
        nm = d.get("name")
        if not nm:
            errors.append("driver missing 'name'")
            continue
        driver_names.add(nm)
        try:
            base_drivers[nm] = float(d["base"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"driver {nm!r} missing numeric 'base'")
        if not str(d.get("source_ref", "")).strip():
            errors.append(f"driver {nm!r} missing source_ref (assumption provenance)")
    out_names = []
    for o in outputs:
        if not str(o.get("formula", "")).strip():
            errors.append(f"output {o.get('name')!r} missing formula")
        out_names.append(o.get("name"))
    if errors:
        return errors  # cannot safely recompute without clean definitions

    # 2. base-case tie-out -------------------------------------------------------------
    try:
        recomputed = _model(base_drivers, outputs)
    except Exception as e:  # noqa: BLE001 - surface any formula error as a validation failure
        return [f"base-case recomputation failed: {e}"]
    base_case = pack.get("base_case") or {}
    if set(base_case) != set(out_names):
        errors.append(f"base_case keys {sorted(base_case)} != outputs {sorted(out_names)}")
    for n in out_names:
        if n in base_case and not _close(base_case[n], recomputed[n]):
            errors.append(f"base-case tie-out mismatch for {n}: reported {base_case[n]} vs recomputed {recomputed[n]}")

    # 3. scenarios ---------------------------------------------------------------------
    for sc in pack.get("scenarios", []):
        overrides = sc.get("overrides") or {}
        for k in overrides:
            if k not in driver_names:
                errors.append(f"scenario {sc.get('name')!r} overrides unknown driver {k!r}")
        dv = dict(base_drivers)
        dv.update({k: float(v) for k, v in overrides.items() if k in driver_names})
        env = _model(dv, outputs)
        for n in out_names:
            rep = (sc.get("outputs") or {}).get(n)
            if rep is not None and not _close(rep, env[n]):
                errors.append(f"scenario {sc.get('name')!r} tie-out mismatch for {n}: {rep} vs {env[n]}")
            dlt = (sc.get("deltas_vs_base") or {}).get(n)
            if dlt is not None and not _close(dlt, env[n] - recomputed[n]):
                errors.append(f"scenario {sc.get('name')!r} delta mismatch for {n}")

    # 4a. one-way sensitivities --------------------------------------------------------
    for s in pack.get("sensitivities", []):
        drv, out = s.get("driver"), s.get("output")
        for p in s.get("points", []):
            dv = dict(base_drivers)
            dv[drv] = float(p["driver_value"])
            if not _close(p["output_value"], _model(dv, outputs)[out]):
                errors.append(f"sensitivity {drv}->{out} tie-out mismatch at {p['driver_value']}")

    # 4b. two-way tables ---------------------------------------------------------------
    for t in pack.get("two_way_tables", []):
        rd, cd, out = t.get("row_driver"), t.get("col_driver"), t.get("output")
        for ri, rv in enumerate(t.get("row_points", [])):
            for ci, cv in enumerate(t.get("col_points", [])):
                dv = dict(base_drivers)
                dv[rd] = float(rv)
                dv[cd] = float(cv)
                if not _close(t["grid"][ri][ci], _model(dv, outputs)[out]):
                    errors.append(f"two-way {rd}x{cd}->{out} tie-out mismatch at [{rv},{cv}]")

    # 4c. breakevens / thresholds recompute to target ----------------------------------
    for b in pack.get("breakevens", []):
        if b.get("converged") and b.get("solution") is not None:
            dv = dict(base_drivers)
            dv[b["driver"]] = float(b["solution"])
            got = _model(dv, outputs)[b["output"]]
            if not _close(got, b["target"]):
                errors.append(f"breakeven {b['driver']}->{b['output']} solution does not hit target "
                              f"({got} vs {b['target']})")
    for th in pack.get("decision_thresholds", []):
        if th.get("converged") and th.get("threshold_value") is not None:
            dv = dict(base_drivers)
            dv[th["driver"]] = float(th["threshold_value"])
            got = _model(dv, outputs)[th["output"]]
            if not _close(got, th["target"]):
                errors.append(f"threshold {th['driver']}->{th['output']} value does not hit target "
                              f"({got} vs {th['target']})")

    # 5. reproducibility ---------------------------------------------------------------
    if not str(pack.get("model_id", "")).strip():
        errors.append("missing model_id (reproducibility)")
    if not str(pack.get("config_version", "")).strip():
        errors.append("missing config_version (reproducibility)")

    # 6. no investment advice + disclaimer ---------------------------------------------
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(s.get("name", "")) for s in pack.get("scenarios", [])]
    text_parts += [str(th.get("label", "")) for th in pack.get("decision_thresholds", [])]
    text = " ".join(text_parts)
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"investment-advice language detected: {m.group(0)!r} "
                          f"(R2 computes mechanics; it does not advise)")
    disclaimer_text = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER_KEY not in disclaimer_text:
        errors.append("missing standing disclaimer text (must state output is not investment advice)")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "analysis_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
