#!/usr/bin/env python3
"""Deterministic output validation for account-anomaly-screener.

Validates the final screening pack (the calculate_or_transform core + a narrative) before
it is presented or delivered. Checks:
  1. Every fired signal has >= 1 cited evidence row.
  2. suggested_priority equals the deterministic mapping from fired_signals.
  3. No fraud/AML determination or account-action language (narrative + signal reasons).
  4. The standing disclaimer is present.
  5. benign_prompts are included when any signal fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"rapid_in_out", "round_amount_clustering"}
DISCLAIMER = "Screening evidence only; not a fraud determination. No account action has been taken."
# Positive determination / action assertions that R2 must not make:
DETERMINATION_PATTERNS = [
    r"\bis fraud\b", r"\bfraudulent\b", r"\bconfirmed fraud\b", r"\bmoney laundering\b",
    r"structuring to evade", r"\bblock (the )?account\b", r"\bfreeze (the )?account\b",
    r"\bfile (a )?sar\b", r"\bclose (the )?account\b", r"\breverse (the )?transaction\b",
    r"\bplace a hold\b", r"\bthe customer is (a )?(criminal|launder)", r"\bguilty\b",
]


def _expected_priority(fired: list[str]) -> str:
    if len(fired) >= 3 or (ESCALATORS & set(fired)):
        return "Elevated"
    return "Review" if fired else "Informational"


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

    exp = _expected_priority(fired)
    if pack.get("suggested_priority") != exp:
        errors.append(f"suggested_priority {pack.get('suggested_priority')!r} != deterministic {exp!r} for fired={fired}")

    # scan free text (narrative + reasons + notes), but NOT the disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("reason", "")) for s in signals])
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action language detected: {m.group(0)!r} (R2 evidences, does not decide/act)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

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
