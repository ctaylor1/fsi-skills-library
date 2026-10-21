#!/usr/bin/env python3
"""Deterministic output validation for earnings-results-analyzer.

Validates the final earnings-analysis pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks:
  1. Every evaluable metric finding has cited 'actual' AND 'estimate' evidence.
  2. Every evaluable guidance finding has >= 1 cited evidence row.
  3. overall_result equals the deterministic mapping from the findings.
  4. No prohibited investment-decision language (rating / price target / buy-sell-hold
     recommendation / personalized advice) in the narrative, notes, or finding reasons.
  5. The standing disclaimer is present.
  6. thesis_considerations are included when any finding is evaluable.

This is the R2 prohibited-decision screen: the skill evidences and classifies the print; it
never issues a call. Fails closed on any miss.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Factual earnings analysis and cited evidence only; not investment advice, a "
              "rating, or a price target. No recommendation to buy, sell, or hold has been made.")

# Prohibited investment-decision / advice language an R2 analyzer must never emit.
# Tight patterns so factual earnings prose ("revenue outperformed consensus") is not flagged.
DECISION_PATTERNS = [
    r"\bprice target\b", r"\btarget price\b",
    r"\b(buy|sell|hold)\s+rating\b", r"\brat(?:e|ed|ing)\s+(?:it\s+)?(?:a\s+)?(?:buy|sell|hold)\b",
    r"\bstrong\s+(?:buy|sell)\b", r"\bconviction\s+(?:buy|list)\b",
    r"\boverweight\b", r"\bunderweight\b", r"\bequal[\s-]?weight\b", r"\bmarket\s+perform\b",
    r"\bwe\s+recommend\s+(?:buy|sell|buying|selling)", r"\bwe\s+advise\s+(?:buying|selling)",
    r"\byou\s+should\s+(?:buy|sell|invest)\b",
    r"\binitiat(?:e|es|ing|ed)\s+coverage\b",
    r"\bupgrade\s+to\s+(?:buy|outperform)\b", r"\bdowngrade\s+to\s+(?:sell|underperform)\b",
    r"\breiterate\s+(?:our\s+)?(?:buy|sell)\b", r"\bset\s+(?:a\s+)?price target\b",
]


def _expected_overall(metric_findings, guidance_findings) -> str:
    headline = [f for f in metric_findings if f.get("headline") and f.get("evaluable")]
    hb = sum(1 for f in headline if f.get("classification") == "Beat")
    hm = sum(1 for f in headline if f.get("classification") == "Miss")
    guidance_negative = any(
        g.get("headline") and g.get("classification") in ("Lowered", "Withdrawn")
        for g in guidance_findings
    )
    if not headline:
        return "Undetermined"
    if hm >= 1 and hb >= 1:
        return "Mixed"
    if hm >= 1:
        return "Miss"
    if hb >= 1:
        return "Mixed" if guidance_negative else "Beat"
    return "Mixed" if guidance_negative else "In-line"


def _validate_native(pack: dict) -> list[str]:
    errors: list[str] = []
    metric_findings = pack.get("metric_findings") or []
    guidance_findings = pack.get("guidance_findings") or []

    for f in metric_findings:
        if f.get("evaluable"):
            roles = {e.get("role") for e in (f.get("evidence") or []) if (e.get("citation") or "").strip()}
            if "actual" not in roles:
                errors.append(f"metric finding {f.get('metric')!r} missing cited 'actual' evidence")
            if "estimate" not in roles:
                errors.append(f"metric finding {f.get('metric')!r} missing cited 'estimate' evidence")

    for g in guidance_findings:
        cited = [e for e in (g.get("evidence") or []) if (e.get("citation") or "").strip()]
        if not cited:
            errors.append(f"guidance finding {g.get('metric')!r} has no cited evidence")

    exp = _expected_overall(metric_findings, guidance_findings)
    if pack.get("overall_result") != exp:
        errors.append(
            f"overall_result {pack.get('overall_result')!r} != deterministic {exp!r} for findings")

    # scan free text, but NOT the disclaimer (the standing disclaimer legitimately names the
    # very terms we prohibit — "rating", "price target", "buy, sell, or hold" — so strip it
    # before scanning, in the narrative or the disclaimer field).
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(f.get("reason", "")) for f in metric_findings]
    text_parts += [str(g.get("reason", "")) for g in guidance_findings]
    text_parts += [str(o.get("note", "")) + " " + str(o.get("current_language", ""))
                   for o in (pack.get("transcript_observations") or [])]
    text = " ".join(text_parts)
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(
                f"investment-decision language detected: {m.group(0)!r} "
                f"(R2 evidences/classifies the print, it does not issue a rating/target/recommendation)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if any(f.get("evaluable") for f in metric_findings) and not pack.get("thesis_considerations"):
        errors.append("evaluable findings present but no thesis_considerations included")

    return errors


from native_integrity import canonical_hash,validate_reconstruction

def validate(output,original_input=None):
    errors=[]
    try:
        canonical_hash(output)
        if not isinstance(output,dict): raise ValueError("output must be an object")
        native_errors=[] if isinstance(original_input,dict) and original_input.get('schema_version')=='ir-phase2/1.0' else _validate_native(output)
        errors.extend(native_errors)
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError) as exc:
        errors.append("invalid native output: "+str(exc))
    try:
        import importlib.util
        p=Path(__file__).with_name("calculate_or_transform.py")
        spec=importlib.util.spec_from_file_location("_output_calc_"+p.parent.parent.name.replace("-","_"),p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        validate_reconstruction(output,module.compute,errors,original_input=original_input)
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError) as exc:
        errors.append("cannot reconstruct output: "+str(exc))
    return errors

def main(argv):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",nargs="?");parser.add_argument("--input",dest="original_input");parser.add_argument("--selftest",action="store_true")
    args=parser.parse_args(argv)
    if args.selftest:
        base=Path(__file__).resolve().parents[1]/"evals/files"
        source=_read_json((base/'earnings_example.json').read_text())
        output=_read_json((base/'pack_example.json').read_text())
    else:
        source=_read_json(Path(args.original_input).read_text()) if args.original_input else None
        output=_read_json(Path(args.output).read_text()) if args.output else _read_json(sys.stdin.read())
    errors=validate(output,original_input=source)
    for e in errors: print("ERROR",e)
    print(f"output validation: {len(errors)} error(s)")
    return bool(errors)

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


if __name__=="__main__":raise SystemExit(main(sys.argv[1:]))
