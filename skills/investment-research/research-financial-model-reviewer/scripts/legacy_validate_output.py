#!/usr/bin/env python3
"""Source-bound output validation for model-roll-forward-auditor.

Requires separately retained original input (--input ORIGINAL). Reconstructs all fields
and retains bounded domain checks. Fidelity does not establish source truth, economic
validity, institutional approval or independent assurance.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"tied", "breaks-for-review"}
DISCLAIMER_RE = re.compile(r"not a model approval", re.I)
PROHIBITED = [
    r"\bmodel is approved\b", r"\bwe approve the model\b", r"\bfair value is\b", r"\bvaluation is\b",
    r"\bthe model is correct\b", r"\bsign off on the model\b", r"\bmodel is validated\b",
    r"\bwe validate the model\b",
]
EPS = 1e-6


def _validate_rules(p: dict) -> list[str]:
    errors = []
    for it in p.get("line_items") or []:
        pe, co, res = it.get("prior_ending"), it.get("current_opening"), it.get("residual")
        if None in (pe, co, res):
            continue
        if abs((co - pe) - res) > EPS:
            errors.append(f"{it.get('line_item')}: residual {res} != current_opening {co} - prior_ending {pe}")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"valuation/model-approval language detected: {m.group(0)!r} (R2 checks continuity, deal team approves/values)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (continuity check only / no model approved or valued)")
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
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)

def _local_module(filename):
    import importlib.util
    spec = importlib.util.spec_from_file_location("_local_" + filename.replace(".", "_"), Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def validate(output, original_input=None):
    errors = []
    integrity = _local_module("native_integrity.py")
    calculator = _local_module("legacy_calculate.py")
    integrity.validate_reconstruction(output, calculator.compute, errors, original_input)
    # Existing domain checks operate only on a complete, source-bound reconstruction.
    if not errors:
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
        output_path, input_path = fixtures / 'audit_example.json', fixtures / 'model_example.json'
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

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
