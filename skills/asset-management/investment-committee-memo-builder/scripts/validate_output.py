#!/usr/bin/env python3
"""Deterministic output validation for investment-committee-memo-builder.

Runs BEFORE a drafted IC memo is handed to a human for committee circulation. It is an
independent gate (it re-derives its findings from the memo record, not from the producer's
own flag list). It enforces the Draft & package guardrails:

  1. Template fidelity: every required template section is present and non-empty.
  2. No unsupported/unapproved claims: every assertion resolves to a source, and any
     external (market/research) source is marked approved.
  3. Model/scenario/sizing tie-outs hold (no tie-out break, ordered scenarios, downside
     present, base ties to the model, sizing within the single-name concentration limit).
  4. Required human approvals are recorded (preparer and reviewer).
  5. The committee decision remains `pending` - this skill never records the IC's decision.
  6. No prohibited language: investment-advice / guarantee wording, or any claim that the
     memo has been sent/circulated/submitted or that the committee has decided.
  7. The standing draft-only note is present.

Usage: python validate_output.py ic_memo.json | --selftest
Exit 0 if no errors, 1 otherwise (fail closed).
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "executive_summary", "investment_thesis", "transaction_structure", "valuation",
    "returns_analysis", "scenario_analysis", "key_risks_and_mitigants",
    "position_sizing_and_portfolio_fit", "recommendation_and_decision_questions",
]
REQUIRED_APPROVALS = {"preparer", "reviewer"}
UNAPPROVED_TYPES = {"market", "research"}
STANDING_NOTE_KEY = "draft investment-committee memorandum for human review"

ADVICE_PATTERNS = [
    r"\bguaranteed?\b", r"\brisk-free\b", r"\bcan'?t lose\b", r"\bno downside\b",
    r"\byou should invest\b", r"\bwill (?:definitely|certainly) (?:return|deliver|outperform)\b",
    r"\bsure thing\b",
]
DELIVERY_PATTERNS = [
    r"\bhas been (?:sent|circulated|submitted|filed|emailed)\b",
    r"\bsent to (?:the )?(?:committee|lps|investors|limited partners)\b",
    r"\bwe have submitted\b", r"\bmemo (?:was|has been) circulated\b",
]
DECISION_PATTERNS = [
    r"\b(?:committee|ic) (?:approved|declined|rejected|voted)\b",
    r"\bapproved by the (?:committee|ic)\b", r"\bthe committee has decided\b",
]


def _scan(text, patterns):
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(0)
    return None


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    # 1. Template fidelity -------------------------------------------------
    sections = ((doc.get("memo") or {}).get("sections")) or {}
    for name in REQUIRED_SECTIONS:
        s = sections.get(name)
        if not s or not str(s.get("body", "")).strip():
            errors.append(f"missing required section: {name}")

    # 2. Unsupported / unapproved claims -----------------------------------
    for a in doc.get("assertions") or []:
        if not a.get("supported"):
            errors.append(f"unsupported or unapproved claim: {a.get('claim')!r} "
                          f"cites unknown source {a.get('source_id')!r}")
        elif a.get("source_type") in UNAPPROVED_TYPES and not a.get("approved_ok"):
            errors.append(f"unsupported or unapproved claim: {a.get('claim')!r} "
                          f"cites unapproved {a.get('source_type')} source {a.get('source_id')!r}")

    # 3. Tie-outs, scenarios, sizing ---------------------------------------
    for o in doc.get("tie_outs") or []:
        if not o.get("ok"):
            errors.append(f"tie-out break: {o.get('metric')} stated {o.get('memo_value')} "
                          f"!= recomputed {o.get('recomputed')}")
    scen = doc.get("scenario_check") or {}
    if scen.get("has_downside") is not True:
        errors.append("scenario check failed: no downside scenario present")
    if scen.get("moic_ordered") is False or scen.get("irr_ordered") is False:
        errors.append("scenario check failed: scenarios not ordered downside <= base <= upside")
    if scen.get("base_ties_model") is False:
        errors.append("scenario check failed: base case does not tie to the model returns")
    size = doc.get("sizing_check") or {}
    pos, limit = size.get("computed_position_pct"), size.get("single_name_limit_pct")
    if pos is not None and limit is not None and pos > limit:
        errors.append(f"single-name concentration limit breach: {pos}% exceeds {limit}%")

    # honor any producer block-severity flags too
    for f in doc.get("flags") or []:
        if f.get("severity") == "block":
            errors.append(f"unresolved blocking flag: {f.get('code')} - {f.get('detail')}")

    # 4. Required approvals recorded ---------------------------------------
    recorded = {a.get("role") for a in (doc.get("approvals") or []) if a.get("status") == "recorded"}
    for role in sorted(REQUIRED_APPROVALS - recorded):
        errors.append(f"missing required approval: {role} sign-off not recorded")

    # 5. Committee decision must remain pending ----------------------------
    cd = doc.get("committee_decision")
    if cd not in (None, "pending"):
        errors.append(f"committee decision must remain pending (draft-only), got {cd!r}")

    # 6. Prohibited language -----------------------------------------------
    blob = json.dumps(sections) + " " + json.dumps(doc.get("assertions") or []) + \
        " " + str(doc.get("narrative", ""))
    for label, pats in (("investment-advice/guarantee", ADVICE_PATTERNS),
                        ("premature delivery/circulation", DELIVERY_PATTERNS),
                        ("recorded committee decision", DECISION_PATTERNS)):
        hit = _scan(blob, pats)
        if hit:
            errors.append(f"prohibited language ({label}) detected: {hit!r}")

    # 7. Standing note ------------------------------------------------------
    if STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing draft-only note")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ic_memo_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
