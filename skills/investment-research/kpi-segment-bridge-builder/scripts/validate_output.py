#!/usr/bin/env python3
"""Source-bound output validation for kpi-segment-bridge-builder.

Requires separately retained original input (--input ORIGINAL). Reconstructs all fields
and retains bounded domain checks. Fidelity does not establish source truth, economic
validity, institutional approval or independent assurance.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.01
VP_CONVENTION = "base_period_weighted_with_joint_mix"
DISCLAIMER = ("Historical, source-linked KPI/segment bridge for analytical purposes only; a "
              "decomposition of disclosed, reported results. It is not a forecast, not "
              "normalized accounting, not investment advice, and not a recommendation. Every "
              "figure ties to a disclosed source, and a qualified human must review it before "
              "any use.")

FORBIDDEN_SOURCE_TYPES = {"forecast", "projection", "guidance", "estimate",
                          "consensus", "target", "budget", "plan", "model-output"}

# Forward-looking assertions this skill must never make (it decomposes disclosed history).
# Worded affirmatively so the disclaimer's negated phrases ("not a forecast") do not self-trip.
FORECAST_PATTERNS = [
    r"\bwe (forecast|project|expect|anticipate|estimate)\b[^.]{0,60}\b(fy?20\d\d|next (year|quarter|period)|20\d\d|coming|future)\b",
    r"\b(projected|forecast|forecasted|expected)\s+(fy?20\d\d\s+)?(revenue|sales|margin|ebit|ebitda|growth|volume|arpu)\s+(of|will|to reach|to grow|to be)\b",
    r"\bnext[- ](year|quarter|period)('?s)?\s+(revenue|sales|margin|ebit|growth|volume)\b",
    r"\bguidance implies\b",
    r"\bwe (forecast|project) that\b",
    r"\bwill (grow|reach|rise to|climb to|decline to|fall to)\s+\$?\d",
]
# Investment advice / recommendation an R2 bridge must NOT make.
ADVICE_PATTERNS = [
    r"\byou should (buy|sell|short|hold|acquire|divest|invest in|avoid)\b",
    r"\bwe recommend (buying|selling|shorting|holding|a buy|a sell|the stock|the shares|investors)\b",
    r"\b(our|the) (buy|sell|hold|overweight|underweight|outperform|underperform) rating\b",
    r"\bprice target (of|is|:)\b",
    r"\b(this is|represents|constitutes) a (buy|sell|strong buy|strong sell)\b",
    r"\bguaranteed (return|upside|to)\b",
]


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _check_walk(b) -> list[str]:
    errors = []
    bid = b.get("id", "?")
    beginning = _num(b.get("beginning"))
    ending = _num(b.get("ending"))
    comps = b.get("components") or []
    if beginning is None or ending is None:
        return [f"bridge {bid}: missing beginning/ending"]
    csum = 0.0
    for c in comps:
        amt = _num(c.get("amount"))
        if amt is None:
            errors.append(f"bridge {bid} component {c.get('id')!r}: amount is not numeric")
        else:
            csum += amt
    csum = round(csum, 4)
    if abs(beginning + csum - ending) > TOL:
        errors.append(f"bridge {bid}: walk tie-out fails "
                      f"(beginning {beginning} + sum(components) {csum} != ending {ending})")
    total_change = round(ending - beginning, 4)
    if total_change != 0:
        cs = sum(_num(c.get("contribution"), 0.0) for c in comps)
        if abs(cs - 1.0) > 1e-3:
            errors.append(f"bridge {bid}: contribution shares do not sum to 1 (got {round(cs, 6)})")
    return errors


def _check_volume_price(b) -> list[str]:
    errors = []
    bid = b.get("id", "?")
    f = b.get("factors") or {}
    u0, p0 = _num(f.get("prior_units")), _num(f.get("prior_price"))
    ut, pt = _num(f.get("current_units")), _num(f.get("current_price"))
    if None in (u0, p0, ut, pt):
        return [f"bridge {bid}: volume_price missing/invalid factors"]
    if b.get("convention") != VP_CONVENTION:
        errors.append(f"bridge {bid}: volume_price convention {b.get('convention')!r} != "
                      f"expected {VP_CONVENTION!r}")
    beginning = _num(b.get("beginning"))
    ending = _num(b.get("ending"))
    if beginning is None or abs(u0 * p0 - beginning) > TOL:
        errors.append(f"bridge {bid}: beginning does not equal prior_units*prior_price")
    if ending is None or abs(ut * pt - ending) > TOL:
        errors.append(f"bridge {bid}: ending does not equal current_units*current_price")
    expect = {"volume": round((ut - u0) * p0, 4), "price": round((pt - p0) * u0, 4),
              "mix": round((ut - u0) * (pt - p0), 4)}
    got = {c.get("id"): _num(c.get("amount")) for c in (b.get("components") or [])}
    for k, want in expect.items():
        if k not in got:
            errors.append(f"bridge {bid}: missing computed component {k!r}")
        elif got[k] is None or abs(got[k] - want) > TOL:
            errors.append(f"bridge {bid} component {k!r}: recomputed {want} != pack {got.get(k)}")
    total_change = round((ending or 0) - (beginning or 0), 4)
    if total_change != 0 and abs(sum(expect.values()) - total_change) > TOL:
        errors.append(f"bridge {bid}: volume+price+mix does not equal the revenue delta")
    return errors


def _validate_rules(pack: dict) -> list[str]:
    errors: list[str] = []
    bridges = pack.get("bridges") or []
    if not bridges:
        errors.append("pack has no bridges")
    reported = pack.get("reported_totals") or {}

    for b in bridges:
        btype = b.get("type")
        if btype == "walk":
            errors += _check_walk(b)
        elif btype == "volume_price":
            errors += _check_volume_price(b)
        else:
            errors.append(f"bridge {b.get('id')!r}: unknown type {btype!r}")

        # reconciliation to the stated authoritative (disclosed) totals
        rec = b.get("reconcile_to") or {}
        for side, val in (("beginning", b.get("beginning")), ("ending", b.get("ending"))):
            key = rec.get(f"{side}_key")
            if key and key in reported:
                if abs(_num(val, 0.0) - _num(reported[key], 0.0)) > TOL:
                    errors.append(f"bridge {b.get('id')!r}: reconciliation to disclosed totals fails "
                                  f"({side} {val} != reported_totals.{key})")
            elif rec.get(f"{side}_ok") is False:
                errors.append(f"bridge {b.get('id')!r}: reconciliation to disclosed totals fails ({side})")

    # HARD BOUNDARY 1  - no forward-looking source types on any bridge input
    for b in bridges:
        for c in b.get("components", []):
            st = (c.get("source_type") or "").strip().lower()
            if st in FORBIDDEN_SOURCE_TYPES:
                errors.append(f"bridge {b.get('id')!r} component {c.get('id')!r}: source_type "
                              f"{st!r} is forward-looking  - this skill never forecasts")

    # HARD BOUNDARY 2  - mapping discipline: mapping components must reference an approved mapping
    mreg = {m.get("mapping_id"): (m.get("status") or "").strip().lower()
            for m in (pack.get("mapping_register") or [])}
    for mid, status in mreg.items():
        if status != "approved":
            errors.append(f"mapping {mid!r} in the register is not approved (status {status or 'missing'!r})  - "
                          f"normalization beyond approved mappings is prohibited")
    for b in bridges:
        for c in b.get("components", []):
            if (c.get("derivation") or "").strip().lower() == "mapping":
                mid = (c.get("mapping_id") or "").strip()
                if not mid:
                    errors.append(f"bridge {b.get('id')!r} component {c.get('id')!r}: mapping derivation "
                                  f"without a mapping_id")
                elif mreg.get(mid) != "approved":
                    errors.append(f"bridge {b.get('id')!r} component {c.get('id')!r}: mapping_id {mid!r} "
                                  f"is not an approved mapping (normalization beyond approved mappings is prohibited)")

    # assumption provenance & source-type discipline over the register
    register = pack.get("assumptions_register") or []
    if not register:
        errors.append("assumptions_register missing (provenance must be recorded for every input)")
    for a in register:
        if not (a.get("provenance") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing provenance")
        if not (a.get("citation") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing citation")
        st = (a.get("source_type") or "").strip().lower()
        if st in FORBIDDEN_SOURCE_TYPES:
            errors.append(f"assumption {a.get('id')!r}: source_type {st!r} is forward-looking "
                          f" - this skill never forecasts")

    # versioning + reproducibility
    if not (pack.get("config_version") or "").strip():
        errors.append("missing config_version (versioned convention/tolerance provenance)")
    if not (pack.get("mapping_version") or "").strip():
        errors.append("missing mapping_version (approved-mapping provenance)")
    if not (pack.get("pack_id") or "").strip():
        errors.append("missing pack_id (reproducibility)")
    if not (pack.get("inputs_hash") or "").strip():
        errors.append("missing inputs_hash (reproducibility)")

    # narrative screen  - strip the disclaimer first so its negated phrases cannot self-trip
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(b.get("note", "")) for b in bridges])
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in FORECAST_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited forecast/projection language detected: {m.group(0)!r} "
                          f"(this skill decomposes disclosed history; it never forecasts)")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited investment-advice/recommendation language detected: {m.group(0)!r} "
                          f"(R2 builds a bridge; it does not advise, recommend, or set a target)")

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
        output_path, input_path = fixtures / 'kpi_bridge_pack_example.json', fixtures / 'kpi_bridge_input.json'
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
