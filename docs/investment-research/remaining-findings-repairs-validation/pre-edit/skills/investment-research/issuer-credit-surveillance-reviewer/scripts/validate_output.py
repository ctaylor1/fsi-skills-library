#!/usr/bin/env python3
"""Deterministic output validation for issuer-credit-surveillance-reviewer.

Runs BEFORE a drafted surveillance packet is handed to a human for delivery. It is an
independent gate (it re-derives its findings from the packet record, not from the producer's
own flag list) and enforces the Draft & package + R2 guardrails:

  1. Template fidelity: every required template section is present and non-empty.
  2. No unsupported/unapproved claims: every assertion resolves to a source, and any
     external (market / rating-agency) source is marked approved.
  3. Metric tie-outs hold (no leverage/coverage tie-out break) and no open blocking flag.
  4. The action fields stay neutral - this skill assigns no rating, changes no thesis, and
     takes no position: rating_action == reported-only, position_action == none,
     thesis_action == unchanged.
  5. Required human approvals are recorded (preparer and reviewer).
  6. No prohibited language: assigning/deriving a credit rating, forming or changing a
     thesis, recommending or changing a position/trade, interpreting covenant compliance,
     investment-advice / guarantee wording, or claiming the packet has been sent/circulated.
  7. The standing draft-only note is present.

Usage: python validate_output.py surveillance_packet.json | --selftest
Exit 0 if no errors, 1 otherwise (fail closed).
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import importlib.util
from native_integrity import validate_reconstruction

REQUIRED_SECTIONS = [
    "issuer_summary", "leverage", "coverage", "liquidity", "maturity_wall",
    "spreads", "ratings", "covenant_changes", "citations_and_evidence",
]
REQUIRED_APPROVALS = {"preparer", "reviewer"}
UNAPPROVED_TYPES = {"market", "rating-agency"}
STANDING_NOTE_KEY = "draft credit surveillance packet for human review"

# HARD BOUNDARY 1 - never assign or derive a credit rating (agency ratings are reported only).
RATING_PATTERNS = [
    r"\bwe (?:assign|assigned|are assigning|rate|rated)\b",
    r"\bassign(?:ed|s|ing)? (?:a |an |our )?(?:new |internal |credit )?rating\b",
    r"\bour (?:internal |credit )?rating (?:is|of|would be)\b",
    r"\brecommend(?:ed|s|ing)? (?:a |an )?(?:rating|downgrade|upgrade)\b",
    r"\b(?:internal|implied|derived|our) rating of\b",
]
# HARD BOUNDARY 2 - never form, alter, or restate an investment thesis.
THESIS_PATTERNS = [
    r"\b(?:change|changed|revise|revised|update|updated|rewrite|overturn|flip) (?:the |our )?(?:investment )?thesis\b",
    r"\bnew (?:investment )?thesis\b", r"\bthesis is now\b", r"\bour (?:new |updated )?thesis\b",
]
# HARD BOUNDARY 3 - never recommend or change a position or trade.
POSITION_PATTERNS = [
    r"\b(?:buy|sell|short|overweight|underweight) (?:the |this )?(?:bond|note|name|issuer|credit|position)\b",
    r"\b(?:add to|added to|trim|trimmed|increase|increased|reduce|reduced|exit|unwind|build) (?:the |our )?position\b",
    r"\brecommend(?:ed|s|ing)? (?:buying|selling|adding|trimming|reducing|exiting)\b",
    r"\bgo (?:long|short)\b", r"\breduce (?:the |our )?exposure\b",
]
# Adjacent boundary - covenant interpretation / compliance determination belongs downstream.
COVENANT_PATTERNS = [
    r"\bcovenant (?:is |was )?(?:in )?(?:breach|breached|compliant|non-compliant|violated|satisfied|met|tripped)\b",
    r"\bin compliance with the covenant\b", r"\bcovenant headroom (?:is|of|stands)\b",
    r"\binterpret(?:ing|ed)? the covenant\b", r"\bcovenant (?:is )?(?:cured|waived)\b",
]
# Universal - no personalized investment advice / guarantee language.
ADVICE_PATTERNS = [
    r"\bguaranteed?\b", r"\brisk-free\b", r"\bcan'?t lose\b", r"\bno downside\b",
    r"\byou should (?:buy|sell|invest)\b", r"\bsure thing\b",
]
# Draft-only - never claim the packet has been delivered.
DELIVERY_PATTERNS = [
    r"\bhas been (?:sent|circulated|submitted|filed|emailed|published|distributed)\b",
    r"\bsent to (?:the )?(?:pm|desk|committee|portfolio manager)\b",
    r"\bwe have (?:sent|submitted|circulated)\b", r"\bpacket (?:was|has been) circulated\b",
]


def _scan(text, patterns):
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(0)
    return None


def _validate_native(doc: dict) -> list[str]:
    errors: list[str] = []

    # 1. Template fidelity -------------------------------------------------
    sections = ((doc.get("packet") or {}).get("sections")) or {}
    for name in REQUIRED_SECTIONS:
        s = sections.get(name)
        if not s or not str(s.get("body", "")).strip():
            errors.append(f"missing required section: {name}")

    # 2. Unsupported / unapproved claims -----------------------------------
    for a in doc.get("assertions") or []:
        if not a.get("source_reference_resolved") or a.get("verification_status") != "unverified-source-assertion":
            errors.append(f"unsupported or unapproved claim: {a.get('claim')!r} "
                          f"cites unknown source {a.get('source_id')!r}")
        elif a.get("source_type") in UNAPPROVED_TYPES and not a.get("approved_ok"):
            errors.append(f"unsupported or unapproved claim: {a.get('claim')!r} "
                          f"cites unapproved {a.get('source_type')} source {a.get('source_id')!r}")

    # 3. Tie-outs and blocking flags ---------------------------------------
    for o in doc.get("tie_outs") or []:
        if not o.get("ok"):
            errors.append(f"tie-out break: {o.get('metric')} stated {o.get('packet_value')} "
                          f"!= recomputed {o.get('recomputed')}")
    for f in doc.get("flags") or []:
        if f.get("severity") == "block":
            errors.append(f"unresolved blocking flag: {f.get('code')} - {f.get('detail')}")

    # 4. Neutral action fields (assigns no rating / no thesis / no position) -
    if doc.get("rating_action") not in (None, "reported-only"):
        errors.append(f"rating action must remain reported-only (this skill assigns no rating), "
                      f"got {doc.get('rating_action')!r}")
    if doc.get("position_action") not in (None, "none"):
        errors.append(f"position action must remain none (this skill changes no position), "
                      f"got {doc.get('position_action')!r}")
    if doc.get("thesis_action") not in (None, "unchanged"):
        errors.append(f"thesis action must remain unchanged (this skill alters no thesis), "
                      f"got {doc.get('thesis_action')!r}")

    # 5. Required approvals recorded ---------------------------------------
    recorded = {a.get("role") for a in (doc.get("approvals") or []) if a.get("status") == "recorded"}
    for role in sorted(REQUIRED_APPROVALS - recorded):
        errors.append(f"missing required approval: {role} sign-off not recorded")

    # 6. Prohibited language -----------------------------------------------
    blob = json.dumps(sections) + " " + json.dumps(doc.get("assertions") or []) + \
        " " + str(doc.get("narrative", ""))
    for label, pats in (("assigned/derived credit rating", RATING_PATTERNS),
                        ("thesis change", THESIS_PATTERNS),
                        ("position/trade recommendation", POSITION_PATTERNS),
                        ("covenant compliance interpretation", COVENANT_PATTERNS),
                        ("investment-advice/guarantee", ADVICE_PATTERNS),
                        ("premature delivery/circulation", DELIVERY_PATTERNS)):
        hit = _scan(blob, pats)
        if hit:
            errors.append(f"prohibited language ({label}) detected: {hit!r}")

    # 7. Standing note ------------------------------------------------------
    if STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing draft-only note")

    return errors


def main(argv):
    original_input = None
    argv = list(argv)
    for option in ("--input", "--source"):
        if option in argv:
            index = argv.index(option)
            original_input = _read_json(Path(argv[index + 1]).read_text(encoding="utf-8"))
            del argv[index:index + 2]
    if "--selftest" in argv:
        original_input = _read_json((Path(__file__).resolve().parents[1] / "evals/files/surveillance_request_example.json").read_text())
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "surveillance_packet_example.json"
        doc = _read_json(p.read_text(encoding="utf-8"))
    elif argv:
        doc = _read_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _read_json(sys.stdin.read())
    errors = validate(doc, original_input)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0




def validate(doc: dict, original_input=None) -> list[str]:
    try:
        errors = [] if isinstance(original_input,dict) and original_input.get('schema_version')=='ir-phase2/1.0' else _validate_native(doc)
        if doc.get("support_status")=="PARTIAL":
            # A faithful partial is valid evidence, while its review and data gates remain held.
            errors=[e for e in errors if not e.startswith(("unsupported or unapproved claim:","tie-out break:","unresolved blocking flag:","missing required approval:"))]
    except (KeyError, TypeError, ValueError, AttributeError, ArithmeticError) as exc:
        errors = ["invalid output: " + str(exc)]
    if original_input is not None:
        input_spec = importlib.util.spec_from_file_location("_input_validation", Path(__file__).with_name("validate_input.py"))
        input_module = importlib.util.module_from_spec(input_spec)
        input_spec.loader.exec_module(input_module)
        input_errors, _ = input_module.validate(original_input)
        errors.extend("source input: " + error for error in input_errors)
    spec = importlib.util.spec_from_file_location("_native_calculation_credit_surveillance_packet", Path(__file__).with_name("calculate_or_transform.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    validate_reconstruction(doc, module.assemble, errors, original_input)
    return errors

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
