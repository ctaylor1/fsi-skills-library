#!/usr/bin/env python3
"""Deterministic output validation for fixed-income-pricing-reviewer.

Validates the final pricing-review pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks, and fails closed on any miss:
  1. Every flagged check (in every focal instrument) has >= 1 cited evidence row.
  2. Each instrument's suggested_priority equals the deterministic band mapping from its
     flagged_checks; overall_suggested_priority equals the highest instrument band.
  3. No valuation-determination / price-approval / mark-action language anywhere in the
     narrative, notes, or any check reason (an R2 skill evidences, it does not decide/act).
  4. The standing disclaimer is present.
  5. benign_prompts are included when any check flagged.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"stale_price", "fair_value_level_inconsistent"}
BAND_RANK = {"Informational": 0, "Review": 1, "Elevated": 2}
DISCLAIMER = ("Pricing-review evidence only; not a valuation determination or price "
              "approval. No mark has been changed, approved, or booked.")

# Positive valuation-determination / approval / mark-action assertions an R2 must not make:
DETERMINATION_PATTERNS = [
    r"\bapprove(d|s)? the (mark|price|valuation)\b",
    r"\bapprove the override\b",
    r"\boverride approved\b",
    r"\bbook (this|the) (mark|price)\b",
    r"\b(the )?(mark|price) is (correct|accurate|fair value)\b",
    r"\bis fair value\b",
    r"\bapproved as fair value\b",
    r"\bvaluation is (correct|confirmed|approved)\b",
    r"\bipv (sign-?off|signed off|approved|complete)\b",
    r"\bsign off (the )?(price|mark|valuation|ipv)\b",
    r"\b(waive|waived|clear|cleared|dismiss|dismissed) the (pricing )?exception\b",
    r"\bforce the (price|mark)\b",
    r"\brestate the (mark|price)\b",
    r"\bchange the mark to\b",
    r"\bconfirmed (mismark|mispricing)\b",
    r"\bthis is (a )?mismark\b",
    r"\bpass(ed)? the security\b",
    r"\bfail(ed)? the security\b",
]


def _band(flagged: list[str]) -> str:
    if len(flagged) >= 3 or (ESCALATORS & set(flagged)):
        return "Elevated"
    return "Review" if flagged else "Informational"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    instruments = pack.get("instruments") or []
    if not instruments:
        errors.append("pack has no instruments")

    reasons_text: list[str] = []
    overall_rank = 0
    for inst in instruments:
        iid = inst.get("instrument_id", "?")
        checks = inst.get("checks") or []
        flagged = [c["check"] for c in checks if c.get("flagged")]
        for c in checks:
            reasons_text.append(str(c.get("reason", "")))
            if c.get("flagged"):
                ev = c.get("evidence") or []
                if not ev:
                    errors.append(f"instrument {iid} flagged check {c['check']} has no evidence")
                for row in ev:
                    if not (row.get("citation") or "").strip():
                        errors.append(f"instrument {iid} flagged check {c['check']} evidence row missing citation")
        # tie flagged_checks list (if present) to computed flagged set
        declared = inst.get("flagged_checks")
        if declared is not None and sorted(declared) != sorted(flagged):
            errors.append(f"instrument {iid} flagged_checks {declared} != checks with flagged=true {flagged}")
        exp = _band(flagged)
        if inst.get("suggested_priority") != exp:
            errors.append(f"instrument {iid} suggested_priority {inst.get('suggested_priority')!r} "
                          f"!= deterministic {exp!r} for flagged={flagged}")
        overall_rank = max(overall_rank, BAND_RANK.get(exp, 0))

    exp_overall = {v: k for k, v in BAND_RANK.items()}[overall_rank] if instruments else "Informational"
    if pack.get("overall_suggested_priority") != exp_overall:
        errors.append(f"overall_suggested_priority {pack.get('overall_suggested_priority')!r} "
                      f"!= deterministic {exp_overall!r}")

    # scan free text: narrative + notes + every check reason (NOT the disclaimer field)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))] + reasons_text)
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action language detected: {m.group(0)!r} "
                          f"(R2 evidences pricing exceptions, it does not approve, override, or book marks)")

    combined = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in combined:
        errors.append("missing standing disclaimer text")

    any_flagged = any(c.get("flagged") for inst in instruments for c in (inst.get("checks") or []))
    if any_flagged and not pack.get("benign_prompts"):
        errors.append("checks flagged but no benign_prompts included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
