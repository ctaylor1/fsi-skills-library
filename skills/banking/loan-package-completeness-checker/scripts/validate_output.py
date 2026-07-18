#!/usr/bin/env python3
"""Deterministic output validation for loan-package-completeness-checker.

Validates the final completeness assessment (the calculate_or_transform core + a narrative)
before it is presented to a human certifier. This is the R3 fail-closed gate. Checks:
  1. Every finding has >= 1 cited evidence reference.
  2. counts equal the recomputed severity tally of findings.
  3. readiness_disposition equals the deterministic mapping from counts.
  4. No lending-decision / closure / filing / condition-waiver language anywhere in the
     narrative, notes, or finding summaries (R3 evidences and recommends; it does not decide).
  5. The standing disclaimer text is present.
  6. certifier_actions are present whenever the package is not Complete (guards false
     negatives — findings must be surfaced for the human).

Usage:
  python validate_output.py assessment.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Completeness findings and cited evidence only; this is not a lending decision "
              "or package certification, and no loan action has been taken. Human review and "
              "certification are required before the package proceeds.")

# Positive decision / closure / filing / waiver assertions an R3 checker must NOT make.
DECISION_PATTERNS = [
    r"\bclear(ed)? to close\b",
    r"\bthe (loan|application) is approved\b", r"\b(loan|application|credit) is approved\b",
    r"\bapprove(d|s)? the (loan|application|credit|package)\b",
    r"\bden(y|ies|ied) the (loan|application|credit)\b",
    r"\b(loan|application) is denied\b",
    r"\badverse action\b",
    r"\bwe (certify|approve|deny|fund|close|book)\b",
    r"\bcertif(y|ies|ied) the (package|loan|file)\b",
    r"\bfund (the|this) loan\b", r"\bclose (the|this) loan\b", r"\bbook (the|this) loan\b",
    r"\bwaive(d|s)? (the|this|these|all) condition", r"\bconditions? (are|is) waived\b",
    r"\bunderwriting decision\b",
    r"\bfile (the |a )?(hmda|report|sar)\b",
]


def _expected_readiness(counts: dict) -> str:
    if counts.get("Blocker", 0) > 0:
        return "Not-ready (blockers present)"
    if counts.get("Exception", 0) > 0:
        return "Conditional (exceptions to adjudicate)"
    return "Complete (ready for human certification)"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    # 1) evidence coverage
    for f in findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('finding_id','?')} ({f.get('category','?')}) has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {f.get('finding_id','?')} evidence row missing citation")

    # 2) counts tie-out
    recomputed = {"Blocker": 0, "Exception": 0, "Advisory": 0}
    for f in findings:
        sev = f.get("severity")
        if sev not in recomputed:
            errors.append(f"finding {f.get('finding_id','?')} has unknown severity {sev!r}")
        else:
            recomputed[sev] += 1
    counts = pack.get("counts") or {}
    for sev, n in recomputed.items():
        if int(counts.get(sev, 0)) != n:
            errors.append(f"counts['{sev}']={counts.get(sev)} != recomputed {n}")

    # 3) deterministic readiness mapping
    exp = _expected_readiness(recomputed)
    if pack.get("readiness_disposition") != exp:
        errors.append(f"readiness_disposition {pack.get('readiness_disposition')!r} != deterministic {exp!r}")

    # 4) prohibited decision/closure/filing/waiver language (scan text fields, NOT disclaimer)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("summary", "")) for f in findings]
                    + [str(a) for a in (pack.get("certifier_actions") or [])])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"decision/closure/filing language detected: {m.group(0)!r} (R3 evidences and recommends; a human decides)")

    # 5) standing disclaimer
    haystack = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in haystack:
        errors.append("missing standing disclaimer text")

    # 6) actions present when not Complete (guards false negatives)
    if recomputed["Blocker"] or recomputed["Exception"]:
        if not (pack.get("certifier_actions") or []):
            errors.append("blockers/exceptions present but no certifier_actions listed")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_example.json"
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
