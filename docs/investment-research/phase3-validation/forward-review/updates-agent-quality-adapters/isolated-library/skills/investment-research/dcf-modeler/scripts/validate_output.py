#!/usr/bin/env python3
"""Source-bound output validation for dcf-modeler.

Requires separately retained original input (--input ORIGINAL). Reconstructs all fields
and retains bounded domain checks. Fidelity does not establish source truth, economic
validity, institutional approval or independent assurance.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.01
DISCLAIMER = ("Illustrative valuation model for analytical purposes only; not investment "
              "advice, not a recommendation to buy, sell, or hold any security, not a price "
              "target, and not a fairness opinion. Outputs depend entirely on the stated "
              "assumptions, which a qualified human must review.")

# Affirmative advice / recommendation / target / opinion assertions an R2 model must NOT make.
# Worded so the standing disclaimer above (which says "not a recommendation to buy, sell...",
# "not a price target", "not a fairness opinion") does not self-trip: the patterns require an
# affirmative directed form, not the negated disclaimer form.
ADVICE_PATTERNS = [
    r"\byou should (buy|sell|short|hold|acquire|divest|invest in|avoid)\b",
    r"\bwe recommend (buying|selling|shorting|holding|acquiring|a buy|a sell|the stock|the shares|investors)\b",
    r"\bi recommend (buying|selling|shorting|holding|the stock|the shares)\b",
    r"\b(our|the) (buy|sell|hold|overweight|underweight|outperform|underperform) rating\b",
    r"\brated (a )?(buy|sell|hold|overweight|underweight)\b",
    r"\bprice target (of|is|:)\b",
    r"\bfair value (is|of|:)\s*\$?\d",
    r"\b(this is|represents|constitutes) a (buy|sell|strong buy|strong sell)\b",
    r"\bfairness opinion\b(?!\.?\s*$)",
    r"\b(undervalued|overvalued),? (so|therefore) (buy|sell|investors should)\b",
    r"\bguaranteed (return|upside|to)\b",
    r"\brisk-free (return|investment)\b",
]


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _check_scenario(s: dict, shares: float) -> list[str]:
    errors = []
    name = s.get("name", "?")
    rows = s.get("years") or []
    if not rows:
        return [f"scenario {name}: no forecast years"]

    # PV recompute + discount-factor monotonicity
    sum_pv = 0.0
    prev_df = None
    for r in rows:
        ufcf = _num(r.get("ufcf")); df = _num(r.get("discount_factor")); pv = _num(r.get("pv_ufcf"))
        if None in (ufcf, df, pv):
            errors.append(f"scenario {name} year {r.get('year')}: missing ufcf/discount_factor/pv_ufcf")
            continue
        if abs(round(ufcf * df, 4) - pv) > TOL:
            errors.append(f"scenario {name} year {r.get('year')}: pv tie-out fails "
                          f"(ufcf {ufcf} * df {df} != pv {pv})")
        if prev_df is not None and df > prev_df + 1e-9:
            errors.append(f"scenario {name}: discount factors not non-increasing at year {r.get('year')}")
        prev_df = df
        sum_pv += pv
    sum_pv = round(sum_pv, 4)

    pv_tv = _num(s.get("pv_terminal_value"))
    ev = _num(s.get("enterprise_value"))
    if pv_tv is None or ev is None:
        errors.append(f"scenario {name}: missing pv_terminal_value or enterprise_value")
        return errors
    if abs(sum_pv + pv_tv - ev) > TOL:
        errors.append(f"scenario {name}: enterprise-value tie-out fails "
                      f"(sum_pv {sum_pv} + pv_tv {pv_tv} != ev {ev})")

    # equity bridge tie-out
    bridge = s.get("equity_bridge") or []
    adj = round(sum(_num(i.get("amount"), 0.0) for i in bridge
                    if i.get("item") != "enterprise value"), 4)
    equity = _num(s.get("equity_value"))
    if equity is None:
        errors.append(f"scenario {name}: missing equity_value")
    elif abs(ev + adj - equity) > TOL:
        errors.append(f"scenario {name}: equity-bridge tie-out fails "
                      f"(ev {ev} + bridge_adj {adj} != equity {equity})")

    # per-share tie-out
    vps = _num(s.get("value_per_share"))
    if equity is not None and shares:
        if vps is None:
            errors.append(f"scenario {name}: missing value_per_share")
        elif abs(vps * shares - equity) > TOL:
            errors.append(f"scenario {name}: per-share tie-out fails "
                          f"(vps {vps} * shares {shares} != equity {equity})")
    return errors


def _validate_rules(pack: dict) -> list[str]:
    errors: list[str] = []
    scenarios = pack.get("scenarios") or []
    by = {s.get("name"): s for s in scenarios}
    shares = _num(pack.get("shares_outstanding"), 0.0)

    for req in ("base", "upside", "downside"):
        if req not in by:
            errors.append(f"missing required scenario '{req}'")

    for s in scenarios:
        errors += _check_scenario(s, shares)

    # scenario behaviour: monotonic across enterprise, equity, and per-share values
    if all(n in by for n in ("base", "upside", "downside")):
        for field in ("enterprise_value", "equity_value", "value_per_share"):
            d = _num(by["downside"].get(field)); b = _num(by["base"].get(field)); u = _num(by["upside"].get(field))
            if None in (d, b, u):
                continue
            if not (d <= b + TOL and b <= u + TOL):
                errors.append(f"scenario {field}s not monotonic (expected downside <= base <= upside): "
                              f"downside={d}, base={b}, upside={u}")

    # terminal-value sanity (Gordon guard)
    term = pack.get("terminal") or {}
    if term.get("method") == "gordon":
        wacc = _num(pack.get("wacc")); g = _num(term.get("growth"))
        if wacc is not None and g is not None and wacc - g <= 1e-9:
            errors.append(f"gordon terminal value requires WACC ({wacc}) > terminal growth ({g})")
        if term.get("gordon_guard_ok") is False:
            errors.append("terminal.gordon_guard_ok is false (WACC not greater than terminal growth)")

    # assumption provenance
    register = pack.get("assumptions_register") or []
    if not register:
        errors.append("assumptions_register missing (provenance must be recorded for every assumption)")
    for a in register:
        if not (a.get("provenance") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing provenance")
        if not (a.get("citation") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing citation")

    # reproducibility
    if not (pack.get("model_id") or "").strip():
        errors.append("missing model_id (reproducibility)")
    if not (pack.get("inputs_hash") or "").strip():
        errors.append("missing inputs_hash (reproducibility)")

    # advice/recommendation/target scan over author free text — NOT the disclaimer.
    # The standing disclaimer itself contains negated phrases ("not a fairness opinion",
    # "not a price target"); strip it first so it cannot self-trip, even when an author
    # embeds it inside the narrative.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("note", "")) for s in scenarios])
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited investment-advice/recommendation language detected: {m.group(0)!r} "
                          f"(R2 models and explains; it does not advise, recommend, or set a target)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

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

def validate(output, original_input=None):
    errors = []
    integrity = _local_module("native_integrity.py")
    calculator = _local_module("calculate_or_transform.py")
    integrity.validate_reconstruction(output, calculator.compute, errors, original_input)
    # Existing domain checks operate only on a complete, source-bound reconstruction.
    if not errors and not (isinstance(original_input, dict) and original_input.get("schema_version") == "ir-phase2/1.0"):
        try:
            errors.extend(_validate_rules(output))
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
            errors.append("invalid output: " + str(exc))
    return errors

def main(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Validate against separately retained original input; source truth remains unverified.")
    parser.add_argument("output", nargs="?")
    parser.add_argument("--input", dest="original")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    fixtures = Path(__file__).resolve().parents[1] / "evals" / "files"
    if args.selftest:
        output_path, input_path = fixtures / 'dcf_pack_example.json', fixtures / 'dcf_input_example.json'
    elif args.output and args.original:
        output_path, input_path = Path(args.output), Path(args.original)
    else:
        parser.error("output and --input ORIGINAL are required (or --selftest)")
    output = _strict_json(output_path.read_text(encoding="utf-8"))
    original = _strict_json(input_path.read_text(encoding="utf-8"))
    errors = validate(output, original)
    for error in errors:
        print("ERROR", error)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0

_main_checked = main

def main(argv):
    try:
        return _main_checked(argv)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR", str(exc), file=sys.stderr)
        return 1

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
