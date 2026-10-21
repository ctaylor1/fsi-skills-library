#!/usr/bin/env python3
"""Source-bound output validation for comps-analysis-builder.

Requires separately retained original input (--input ORIGINAL). Reconstructs all fields
and retains bounded domain checks. Fidelity does not establish source truth, economic
validity, institutional approval or independent assurance.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "analysis_summary", "subject_company", "peer_set", "ev_bridges", "trading_multiples",
    "summary_statistics", "implied_valuation", "qa_checks", "open_items", "approvals",
    "source_index",
]
STANDING_NOTE = (
    "Draft comparable-company analysis for human review only. It is not investment advice, "
    "not a research rating or price-target, and not a valuation or fairness view; the multiples "
    "and any implied ranges are an analytical cross-check, and this draft has not been reviewed, "
    "approved, or delivered."
)
TOL = 1  # rounding tolerance in currency units for tie-out reconciliation

# Claims a comps builder must NEVER make.
RECOMMENDATION_PATTERNS = [
    r"\bstrong buy\b", r"\bbuy rating\b", r"\bsell rating\b", r"\brating:\s*(buy|sell|hold)\b",
    r"\boverweight\b", r"\bunderweight\b", r"\bwe recommend\b", r"\bour recommendation\b",
    r"\brecommend (buying|selling)\b", r"\bprice target\b", r"\btarget price\b",
]
OPINION_PATTERNS = [
    r"\bfairness opinion\b", r"\bwe opine\b", r"\bfair value is\b", r"\bintrinsic value is\b",
    r"\bthe company is worth\b", r"\bworth exactly\b", r"\bguaranteed return\b",
    r"\bis fairly valued at\b",
]
DELIVERY_PATTERNS = [
    r"\bsent to the client\b", r"\bsubmitted to\b", r"\bdelivered to\b", r"\bdistributed to\b",
    r"\bwe have sent\b", r"\bemailed to the (client|investor)\b",
]
MNPI_PATTERNS = [
    r"\bmaterial non-?public information\b", r"\bbased on mnpi\b", r"\binsider information\b",
]


def _has_citation(entry):
    c = entry.get("citation") if isinstance(entry, dict) else None
    cs = entry.get("citations") if isinstance(entry, dict) else None
    return bool(c) or bool(cs)


def _validate_rules(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections")
    if not isinstance(sections, dict):
        return ["comps output has no 'sections' object"]

    # 1. required sections present
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required section '{sec}'")

    # 2/3. EV bridges cited + reconcile
    for b in sections.get("ev_bridges") or []:
        tk = b.get("ticker", "?")
        if not _has_citation(b):
            errors.append(f"unsupported claim: EV bridge {tk} has no citation")
        try:
            mc = round(float(b["share_price"]) * float(b["diluted_shares"]))
            if abs(mc - float(b["market_cap"])) > TOL:
                errors.append(f"tie-out failed: {tk} market_cap {b['market_cap']} != price*shares {mc}")
            recomputed = (float(b["market_cap"]) + float(b["plus_total_debt"]) + float(b["plus_preferred"])
                          + float(b["plus_minority_interest"]) + float(b["less_cash"]))
            if abs(recomputed - float(b["enterprise_value"])) > TOL:
                errors.append(f"tie-out failed: {tk} enterprise_value {b['enterprise_value']} != bridge sum {recomputed}")
        except (KeyError, TypeError, ValueError):
            errors.append(f"EV bridge {tk} is missing numeric components required for the tie-out")

    # 2. multiples rows carry a citation (no uncited multiples)
    for tm in sections.get("trading_multiples") or []:
        if not _has_citation(tm):
            errors.append(f"unsupported claim: trading_multiples row {tm.get('ticker','?')} has no citation")

    # 2. implied-value rows must cite an existing statistic basis
    stats = sections.get("summary_statistics") or {}
    for iv in sections.get("implied_valuation") or []:
        if iv.get("status") == "not-derivable":
            continue
        label, basis = iv.get("multiple"), iv.get("basis")
        if basis is None or label not in stats:
            errors.append(f"unsupported claim: implied value for {label!r} without a valid statistic basis")
        elif stats.get(label, {}).get(basis) is None:
            errors.append(f"unsupported claim: implied value cites {label} {basis!r} which is not present in summary_statistics")

    # 4. approvals recorded well-formed; delivery approval flagged
    approvals = sections.get("approvals")
    if not isinstance(approvals, dict) or "recorded" not in approvals:
        errors.append("approvals section missing or lacks a 'recorded' list")
    else:
        for rec in approvals.get("recorded") or []:
            for field in ("type", "approver_role", "date", "citation"):
                if not rec.get(field):
                    errors.append(f"recorded approval {rec.get('type','?')!r} missing '{field}'")
    if doc.get("human_approval_required_before_delivery") is not True:
        errors.append("human_approval_required_before_delivery must be true (external-delivery posture)")

    # 5. forbidden language (scan everything except the disclaimer standing note)
    scan = json.dumps({k: v for k, v in doc.items() if k != "standing_note"})
    for label, patterns in (("investment-recommendation", RECOMMENDATION_PATTERNS),
                            ("valuation/fairness-opinion", OPINION_PATTERNS),
                            ("delivery/submission", DELIVERY_PATTERNS),
                            ("MNPI/selective-disclosure", MNPI_PATTERNS)):
        for pat in patterns:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {label} language detected: {m.group(0)!r} "
                              f"(comps builder only assembles a draft cross-check)")

    # 6. build status must be draft
    if doc.get("build_status") != "draft-comps":
        errors.append(f"build_status must be 'draft-comps', got {doc.get('build_status')!r}")

    # 7. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
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
    integrity.validate_reconstruction(output, calculator.build, errors, original_input)
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
        output_path, input_path = fixtures / 'comps_example.json', fixtures / 'comps_intake_example.json'
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
