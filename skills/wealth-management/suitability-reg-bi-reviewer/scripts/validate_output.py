#!/usr/bin/env python3
"""Deterministic output validation + prohibited-decision screen for suitability-reg-bi-reviewer.

Validates the final review pack (the calculate_or_transform core + a narrative) before it is
presented to a human. This is the R3 fail-closed gate: a pack that decides, approves, clears,
closes, or files must NOT pass. Checks:
  1. Every SATISFIED check has >= 1 cited evidence row (evidence traceability).
  2. disposition equals the deterministic mapping from the checks (tie-out).
  3. No best-interest/suitability DETERMINATION, approval, trade-clearance, closure, or filing
     language in the narrative / notes / check reasons (prohibited-decision screen).
  4. The standing disclaimer is present.
  5. When disposition != "Evidence-complete", open_items (remediation prompts) are included.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_KEY = "not a best-interest determination"  # stable substring of the standing disclaimer

# Affirmative decision / approval / action / closure / filing assertions an R3 reviewer must
# NOT make. Written to match directive/conclusive phrasing, not negated descriptions of scope.
PROHIBITED_PATTERNS = [
    r"\bapprove(s|d)? (the |this )?recommendation\b",
    r"\brecommendation (is|was) approved\b",
    r"\bsuitability (is |was )?approved\b",
    r"\b(is|are|was|deemed) suitable\b",
    r"\bnot suitable\b",
    r"\bunsuitable\b",
    r"\bmeets the best[ -]interest standard\b",
    r"\bsatisfies the best[ -]interest standard\b",
    r"\bcleared (for|to) (execution|execute|trade|proceed|placement|place)\b",
    r"\bexecute the (order|trade|recommendation)\b",
    r"\bplace the (order|trade)\b",
    r"\breject(s|ed)? (the |this )?recommendation\b",
    r"\bden(y|ies|ied) (the |this )?recommendation\b",
    r"\bcase (is |was )?closed\b",
    r"\bclose (the |this )?case\b",
    r"\bsigns? off\b",
    r"\bsigned off\b",
    r"\bprincipal (review|approval) (granted|complete|approved)\b",
    r"\b(file|submit)(s|ted)? (the |a )?(sar|form|report|filing)\b",
]


def _disposition(checks: list) -> str:
    """Recompute disposition from the emitted checks — must match calculate_or_transform.py."""
    if any(c.get("blocking") and c.get("status") == "not_evaluable" for c in checks):
        return "Insufficient-evidence"
    if any(c.get("status") == "gap" for c in checks):
        return "Gaps-identified"
    return "Evidence-complete"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    checks = pack.get("checks") or []

    # 1. evidence traceability for satisfied checks
    for c in checks:
        if c.get("status") == "satisfied":
            ev = c.get("evidence") or []
            if not ev:
                errors.append(f"satisfied check {c.get('check')} has no evidence")
            for row in ev:
                if not str(row.get("citation", "")).strip():
                    errors.append(f"satisfied check {c.get('check')} evidence row missing citation")

    # 2. deterministic disposition tie-out
    exp = _disposition(checks)
    if pack.get("disposition") != exp:
        errors.append(f"disposition {pack.get('disposition')!r} != deterministic {exp!r} from checks")

    # 3. prohibited-decision screen (narrative + notes + check reasons; NOT the disclaimer field)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(c.get("reason", "")) for c in checks])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/approval language detected: {m.group(0)!r} "
                          f"(R3 reports evidence; a human adjudicates the best-interest determination)")

    # 4. standing disclaimer present
    hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER_KEY not in hay:
        errors.append("missing standing disclaimer")

    # 5. remediation prompts when not evidence-complete
    if pack.get("disposition") != "Evidence-complete" and not pack.get("open_items"):
        errors.append("disposition is not Evidence-complete but no open_items (remediation prompts) included")

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
