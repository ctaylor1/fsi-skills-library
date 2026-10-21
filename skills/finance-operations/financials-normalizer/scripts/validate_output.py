#!/usr/bin/env python3
"""Source-bound output validation for financials-normalizer.

Requires separately retained original input (--input ORIGINAL). Reconstructs all fields
and retains bounded domain checks. Fidelity does not establish source truth, economic
validity, institutional approval or independent assurance.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATE_FINDING_COUNT = 4  # matches DEFAULT_CONFIG in calculate_or_transform.py
READY = "Model-ready"
NEEDS = "Needs mapping review"
HOLD = "Hold - tie-out break"
DISCLAIMER = ("Normalization output only; not an accounting, audit, or investment judgment, "
              "and not a system-of-record posting. Source figures are mapped and tied out, "
              "not restated or re-booked; a human reviewer must accept the normalized mapping "
              "before use.")
# Affirmative decision/advice/posting assertions that R2 must not make. The disclaimer's
# negated phrasing ("not an accounting, audit, or investment judgment ...") is intentionally
# NOT matched by any of these.
PROHIBITED_PATTERNS = [
    r"\b(us[- ]?)?(gaap|ifrs)[- ]?compliant\b",
    r"\bcompl(y|ies|iant) with (us[- ]?)?(gaap|ifrs)\b",
    r"\bmaterially (misstated|misstatement|correct|accurate|inaccurate|right)\b",
    r"\b(financials|statements) are (accurate|correct|fairly stated|reliable|right)\b",
    r"\bfairly stated in all material respects\b",
    r"\baudit opinion\b",
    r"\b(is|are) a (strong )?(buy|sell)\b",
    r"\b(buy|sell|hold|overweight|underweight) rating\b",
    r"\bwe recommend (buying|selling|investing|divesting|the investment|this investment)\b",
    r"\binvestment (advice|recommendation)\b",
    r"\b(good|bad|great|poor|strong|weak) investment\b",
    r"\bcreditworthy\b",
    r"\bpost(ed|s)?\b[\w ]*\bto (the )?(general ledger|gl|ledger|books|system of record)\b",
    r"\bre-?book (the|these|those)\b",
    r"\brestate (the|these|those)\b",
]


def _expected_readiness(findings: list[dict], threshold=4, incomplete=False) -> str:
    fired = [f for f in findings if f.get("fired")]
    if any((f.get("severity") == "high") for f in fired) or len(fired) >= threshold:
        return HOLD
    return NEEDS if fired or incomplete else READY


def _validate_rules(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    for f in findings:
        if f.get("fired"):
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"fired finding {f.get('check')} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired finding {f.get('check')} evidence row missing citation")

    exp = _expected_readiness(findings, pack["readiness_config"]["escalate_finding_count"], bool(pack.get("not_evaluable")))
    if pack.get("suggested_readiness") != exp:
        errors.append(f"suggested_readiness {pack.get('suggested_readiness')!r} != deterministic {exp!r}")

    # scan free text (narrative + reasons + notes), NOT the standalone disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/advice language detected: {m.group(0)!r} "
                          f"(R2 normalizes and tie-out-checks; it does not judge, advise, restate, or post)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if any(f.get("fired") for f in findings) and not (pack.get("review_considerations")):
        errors.append("findings raised but no review_considerations included")

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
    calculator = _local_module("calculate_or_transform.py")
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
        output_path, input_path = fixtures / 'normalized_example.json', fixtures / 'financials_example.json'
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
