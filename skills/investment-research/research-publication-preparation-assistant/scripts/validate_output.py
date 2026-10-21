#!/usr/bin/env python3
"""Deterministic output validation for research-publication-preparation-assistant.

Enforces the R3 guardrails before the pre-publication packet is presented:
  1. Every gap and flag carries a citation.
  2. suggested_disposition is review-only (ready-for-compliance-review | gaps-for-review).
  3. A restricted-list flag must NOT coexist with ready-for-compliance-review.
  4. No publish / approval / rating-determination language.
  5. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"ready-for-compliance-review", "gaps-for-review"}
DISCLAIMER_RE = re.compile(r"not a publication", re.I)
PROHIBITED = [
    r"\bwe publish\b", r"\bpublish the note\b", r"\bnote is approved\b", r"\bcleared for publication\b",
    r"\bwe rate it\b", r"\bthe rating is set\b", r"\bapproved for distribution\b", r"\bdistribute the note\b",
]


def _validate_native(p: dict) -> list[str]:
    errors = []
    for g in p.get("gaps") or []:
        if not (g.get("citation") or "").strip():
            errors.append(f"gap {g.get('check','?')}: missing citation")
    restricted = False
    for f in p.get("flags") or []:
        if not (f.get("citation") or "").strip():
            errors.append(f"flag {f.get('check','?')}: missing citation")
        if f.get("check") == "restricted_list":
            restricted = True
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    if restricted and p.get("suggested_disposition") == "ready-for-compliance-review":
        errors.append("restricted-list flag present but disposition is ready-for-compliance-review (restricted is a hard stop)")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"publish/approval/rating language detected: {m.group(0)!r} (R3 checks, human publishes/approves/rates)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (pre-publication prep only / nothing published)")
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
        source=_read_json((base/'note_example.json').read_text())
        output=_read_json((base/'packet_example.json').read_text())
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
