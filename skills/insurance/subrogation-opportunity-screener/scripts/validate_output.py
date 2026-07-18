#!/usr/bin/env python3
"""Deterministic output validation for subrogation-opportunity-screener.

Validates the final screening/referral pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Fails closed on any miss. Checks:
  1. Every fired signal has >= 1 cited evidence row.
  2. screening_band equals the deterministic mapping from fired_signals (+ time_critical).
  3. No subrogation/liability/limitation *determination* or recovery-*action* language
     (narrative + signal reasons + notes).
  4. The standing disclaimer is present.
  5. consider_prompts are included whenever the band is not No-Action.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Screening evidence only; not a subrogation, liability, or limitation "
              "determination. No demand, filing, waiver, or recovery action has been taken.")
CORE = {"third_party_liability_indicated", "recovery_above_floor", "positive_expected_recovery"}

# Positive determination / action assertions an R2 screener must NOT make:
DETERMINATION_PATTERNS = [
    r"\bthird part(y|ies) (is|are) liable\b", r"\bis (definitely |clearly |fully )?liable\b",
    r"\bis time[- ]barred\b", r"\bclaim is barred\b", r"\bstatute has run\b",
    r"\bfile (a )?(suit|lawsuit|claim in court)\b", r"\bissue (a |the )?demand\b",
    r"\bsend (a |the )?demand (letter|package)\b", r"\bplace a lien\b",
    r"\bwaive (the )?(subrogation|recovery)\b", r"\brelease (the )?(claim|third party)\b",
    r"\bclose the recovery\b", r"\bdeny (the )?claim\b",
    r"\b(guaranteed|certain) recovery\b", r"\bwe will recover\b",
]


def expected_band(fired: set, time_critical: bool) -> str:
    if "recovery_not_waived" not in fired:
        return "No-Action"
    if CORE <= fired and "supporting_evidence_present" in fired and "limitation_window_open" in fired:
        band = "Refer"
    elif CORE <= fired:
        band = "Review"
    elif {"third_party_liability_indicated", "recovery_above_floor"} & fired:
        band = "Review"
    else:
        band = "No-Action"
    if band == "No-Action" and time_critical and "third_party_liability_indicated" in fired:
        band = "Review"
    return band


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    signals = pack.get("signals") or []
    fired = {s["signal"] for s in signals if s.get("fired")}

    for s in signals:
        if s.get("fired"):
            ev = s.get("evidence") or []
            if not ev:
                errors.append(f"fired signal {s['signal']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired signal {s['signal']} evidence row missing citation")

    exp = expected_band(fired, bool(pack.get("time_critical")))
    if pack.get("screening_band") != exp:
        errors.append(f"screening_band {pack.get('screening_band')!r} != deterministic {exp!r} "
                      f"for fired={sorted(fired)} time_critical={bool(pack.get('time_critical'))}")

    # scan free text (narrative + notes + reasons) but NOT the disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("reason", "")) for s in signals])
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action language detected: {m.group(0)!r} "
                          f"(R2 screens and evidences; it does not decide/act)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if pack.get("screening_band") != "No-Action" and not pack.get("consider_prompts"):
        errors.append("band is not No-Action but no consider_prompts (counter-considerations) included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "screening_example.json"
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
