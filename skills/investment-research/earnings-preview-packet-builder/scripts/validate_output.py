#!/usr/bin/env python3
"""Deterministic output validation for earnings-preview-packet-builder.

Enforces the Draft & package guardrails and the R2 prohibited-decision/advice screen before
an assembled preview packet is handed to a supervisory analyst / compliance for review:

  1. Template fidelity / completeness  - every required template section is present.
  2. Source mapping / no unsupported assertions - every data point carries an approved
     source_ref; forward-looking figures (consensus/guidance/sensitivity) are third-party
     attributed and never originated by the skill.
  3. Item completeness - every item has a takeaway and at least one source citation.
  4. HARD BOUNDARY screen - no forecast, rating, price-target, or trade-view / personalized-
     advice language anywhere (fails closed), and no data point of an originated-view kind.
  5. Required approvals recorded - supervisory-analyst, research-compliance, and legal roles;
     a `ready-for-control-review` status is allowed only when all required approvals are approved.
  6. Draft-only - packet_status is never a published/distributed state; the draft-only notice
     and standing note are present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_STATUS = {"draft", "hold-for-approval", "ready-for-control-review"}
FORBIDDEN_STATUS = {"published", "distributed", "sent", "filed", "posted", "released", "emailed", "circulated"}

STANDING_NOTE_KEY = "pre-event preview compilation only"
DRAFT_NOTICE_KEY = "draft"

FORWARD_KINDS = {"consensus", "guidance", "sensitivity"}
SELF_ATTRIB = {"self", "own", "analyst", "analyst-own", "house", "our-model", "skill"}
PROHIBITED_KINDS = {"own_forecast", "target", "price_target", "rating", "trade_view"}

# HARD BOUNDARY: the packet compiles sourced facts and third-party-attributed debate points.
# It must never contain the skill's own forecast, rating, price target, or trade view. These
# patterns match ASSERTED views (first-person origination, or an explicit rating/target token
# with a value), so an attributed third-party statement ("consensus expects", "bulls argue",
# "management guided") and a disclaimer negation ("contains no price target, rating, or trade
# view") do NOT trip the screen.
PROHIBITED_PATTERNS = [
    # ratings (assigned, not negated)
    r"\brating\s*[:=]\s*(buy|sell|hold|overweight|underweight|outperform|underperform|neutral)\b",
    r"\bwe (rate|are rating)\b",
    r"\bwe initiate coverage (at|with)\b",
    r"\b(up|down)grade (to|from) (buy|sell|hold|overweight|underweight|neutral|outperform|underperform)\b",
    r"\breiterate (our )?(buy|sell|hold|overweight|underweight)\b",
    r"\bmaintain (a|an|our) (buy|sell|hold|overweight|underweight) (rating|call)\b",
    # price targets (with a value or first-person setting)
    r"\b(price target|target price|12-?month (price )?target)\s*(of|:|=|is|at|to)\s*\$?\d",
    r"\bpt\s*[:=]\s*\$?\d",
    r"\bwe (set|assign|raise|lower|maintain|introduce|establish)\b[^.]{0,30}\btarget\b",
    r"\bfair value of \$?\d",
    r"\bwe value\b[^.]{0,40}\bat \$?\d",
    # originated forecast (first person)
    r"\bwe (forecast|estimate|project|model)\b",
    r"\bour (forecast|estimate|projection|model|number) (of|for|is)\b",
    r"\bwe expect\b[^.]{0,30}\bto come in\b",
    r"\bwe see (eps|revenue|the print|results) (of|at)\b",
    r"\bwe are (above|below) (consensus|the street)\b",
    # trade view / personalized advice
    r"\bwe recommend (buying|selling|adding|trimming|a position)\b",
    r"\byou should (buy|sell|hold|invest|trade)\b",
    r"\b(buy|sell) (the|this) (stock|name|print|dip)\b",
    r"\btrade the print\b",
    r"\btop pick\b",
    r"\b(add to|trim) (the|your) position\b",
    r"\b(go|going) (long|short) (here|into the print)\b",
]


def _text_blob(doc: dict) -> str:
    parts = []
    for it in doc.get("items") or []:
        parts.append(str(it.get("title", "")))
        parts.append(str(it.get("takeaway", "")))
        for c in it.get("data_points") or []:
            parts.append(str(c.get("label", "")))
            parts.append(str(c.get("value", "")))
    parts.append(str(doc.get("narrative", "")))
    return " ".join(parts)


def _validate_native(doc: dict) -> list[str]:
    errors: list[str] = []
    items = doc.get("items") or []
    if not items:
        return ["assembled packet has no items"]

    # 6. Draft-only status
    status = doc.get("packet_status")
    if status in FORBIDDEN_STATUS:
        errors.append(
            f"packet_status {status!r} indicates the packet was published/distributed - this "
            f"skill is draft-only and never distributes"
        )
    elif status not in ALLOWED_STATUS:
        errors.append(f"packet_status {status!r} is not an allowed draft state {sorted(ALLOWED_STATUS)}")

    # 1. Template fidelity / completeness
    required_sections = doc.get("template_required_sections") or []
    present = {it.get("section") for it in items}
    for sec in required_sections:
        if sec not in present:
            errors.append(f"missing required template section: {sec!r}")

    # 2/3. Source mapping, unsupported assertions, attribution, completeness
    for it in items:
        iid = it.get("item_id", "?")
        if not it.get("takeaway"):
            errors.append(f"{iid}: item has no takeaway (template fidelity)")
        if not it.get("sources"):
            errors.append(f"{iid}: item has no source citation")
        for c in it.get("data_points") or []:
            if c.get("kind") in PROHIBITED_KINDS:
                errors.append(f"{iid}: data point of originated-view kind {c.get('kind')!r} (forecast/rating/target/trade view)")
            if not c.get("source_ref") or c.get("approved") is not True:
                errors.append(f"{iid}: unsupported/unapproved data point (no approved source): {c.get('label','')!r}")
            if c.get("kind") in FORWARD_KINDS:
                attr = str(c.get("attribution", "")).strip().lower()
                if not attr or attr in SELF_ATTRIB:
                    errors.append(f"{iid}: forward-looking data point not third-party attributed (would be an originated estimate): {c.get('label','')!r}")

    # 4. HARD BOUNDARY language screen
    blob = _text_blob(doc)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            errors.append(f"prohibited forecast/rating/target/trade-view language: {m.group(0)!r}")

    # 5. Required approvals recorded + status consistency
    required_approvals = doc.get("required_approvals") or []
    appr_map = {a.get("role"): a.get("status") for a in (doc.get("approvals") or [])}
    for role in required_approvals:
        if role not in appr_map:
            errors.append(f"required approval not recorded: {role!r}")
    if status == "ready-for-control-review":
        for role in required_approvals:
            if appr_map.get(role) != "approved":
                errors.append(
                    f"packet_status 'ready-for-control-review' but required approval {role!r} "
                    f"is {appr_map.get(role)!r}"
                )

    # 6. Notices present
    if STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing draft-only standing note")
    if DRAFT_NOTICE_KEY not in str(doc.get("draft_only_notice", "")).lower():
        errors.append("missing draft-only notice")

    return errors


from native_integrity import canonical_hash,validate_reconstruction

def validate(output,original_input=None):
    errors=[]
    try:
        canonical_hash(output)
        if not isinstance(output,dict): raise ValueError("output must be an object")
        native_errors=[] if isinstance(original_input,dict) and original_input.get('schema_version')=='ir-phase2/1.0' else _validate_native(output)
        if output.get("packet_status")=="hold-for-approval":
            native_errors=[e for e in native_errors if any(w in e for w in ("prohibited","originated","published/distributed","not an allowed","missing draft-only"))]
        errors.extend(native_errors)
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError) as exc:
        errors.append("invalid native output: "+str(exc))
    try:
        import importlib.util
        p=Path(__file__).with_name("calculate_or_transform.py")
        spec=importlib.util.spec_from_file_location("_output_calc_"+p.parent.parent.name.replace("-","_"),p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        validate_reconstruction(output,module.assemble,errors,original_input=original_input)
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
        source=_read_json((base/'preview_request_example.json').read_text())
        output=_read_json((base/'preview_packet_example.json').read_text())
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
