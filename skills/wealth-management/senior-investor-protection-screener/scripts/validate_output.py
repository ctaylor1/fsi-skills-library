#!/usr/bin/env python3
"""Deterministic output validation for senior-investor-protection-screener.

Validates the final screening pack (the calculate_or_transform core + a narrative) before
it is presented to a trained reviewer. This is the R3 prohibited-decision screen: it fails
CLOSED if the pack asserts a regulated decision the human must own. Checks:
  1. Every fired signal has >= 1 cited evidence row.
  2. suggested_disposition equals the deterministic mapping from fired_signals.
  3. No exploitation/capacity DETERMINATION, hold/freeze/reject DECISION, filing/reporting
     or trusted-contact ACTION, or case-CLOSURE language (narrative + notes + signal reasons).
  4. The standing disclaimer is present.
  5. benign_prompts are included when any signal fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

HIGH_SEVERITY = {"rapid_liquidation", "third_party_influence", "communication_red_flags"}
DISCLAIMER = ("Screening evidence only; not a determination of financial exploitation or "
              "capacity, and no hold, report, or account action has been taken.")

# Assertive determinations / regulated decisions / actions / closures an R3 screen must NOT make.
# Safe, recommendation-framed language ("recommend supervisory review", "consider whether a
# Rule 2165 temporary hold is warranted") is intentionally NOT matched.
PROHIBITED_PATTERNS = [
    r"\bis being (financially )?exploited\b",
    r"\b(confirmed|clear|obvious) (financial )?exploitation\b",
    r"\bexploitation (is|has been) confirmed\b",
    r"\bvictim of (financial )?(exploitation|abuse|fraud)\b",
    r"\blacks (mental )?capacity\b",
    r"\bis incapacitated\b",
    r"\b(diminished capacity|incapacity) (is )?confirmed\b",
    r"\bdiagnos(e|ed|is|ing)\b",
    r"\bplace(d)? a (temporary )?hold\b",
    r"\bhold (the )?(disbursement|transaction|account)\b",
    r"\bfreeze (the )?account\b",
    r"\bblock (the )?(account|disbursement|transaction)\b",
    r"\breject (the )?(disbursement|transaction)\b",
    r"\bfile (a )?sar\b",
    r"\bwe (have )?(filed|reported)\b",
    r"\breport(ed)? to (adult protective services|aps|the state)\b",
    r"\bnotif(y|ied) (the )?(trusted contact|aps|adult protective services)\b",
    r"\b(we|i) (have )?(contacted|notified) the trusted contact\b",
    r"\bclose (the )?case\b", r"\bcase closed\b",
    r"\bno further action (is )?(required|needed|necessary)\b",
    r"\bcleared for (release|disbursement)\b",
]


def expected_disposition(fired: list[str]) -> str:
    if len(fired) >= 3 or (HIGH_SEVERITY & set(fired)):
        return "Escalate"
    return "Review" if fired else "Monitor"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    signals = pack.get("signals") or []
    fired = [s["signal"] for s in signals if s.get("fired")]

    for s in signals:
        if s.get("fired"):
            ev = s.get("evidence") or []
            if not ev:
                errors.append(f"fired signal {s['signal']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired signal {s['signal']} evidence row missing citation")

    exp = expected_disposition(fired)
    if pack.get("suggested_disposition") != exp:
        errors.append(f"suggested_disposition {pack.get('suggested_disposition')!r} != deterministic {exp!r} for fired={fired}")

    # Scan free text (narrative + notes + signal reasons), NOT the disclaimer field.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("reason", "")) for s in signals])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/decision language detected: {m.group(0)!r} (R3 evidences + recommends; it does not decide/act/close)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer")

    if fired and not (pack.get("benign_prompts")):
        errors.append("signals fired but no benign_prompts included")

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
