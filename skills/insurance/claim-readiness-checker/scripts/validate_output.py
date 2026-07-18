#!/usr/bin/env python3
"""Deterministic output validation for claim-readiness-checker.

Validates the final readiness assessment (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks:
  1. Every check that carries evidence rows cites each row (present items are traceable).
  2. Every gap names an 'item' and a 'category'.
  3. readiness_status equals the deterministic mapping from gaps.
  4. No coverage / eligibility / claim-decision / fraud language (R2 evidences, does not
     decide, adjudicate, approve, deny, price, or pay).
  5. The standing disclaimer is present.
  6. considerations are included when any gap exists.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Readiness and completeness check only; not a coverage, eligibility, or "
              "claim decision. No claim has been adjudicated, approved, denied, or paid.")

# Coverage / eligibility / claim-decision / settlement / fraud assertions an R2 readiness
# check must never make. The claim decision belongs to a human adjuster / insurer.
PROHIBITED_PATTERNS = [
    r"\bis covered\b", r"\bnot covered\b", r"\bis not covered\b",
    r"\bcoverage (is )?(confirmed|denied|granted|approved)\b", r"\bcoverage determination\b",
    r"\bclaim (is )?approved\b", r"\bclaim (is )?denied\b",
    r"\bapprove the claim\b", r"\bdeny the claim\b", r"\bdenied the claim\b",
    r"\bis eligible\b", r"\bnot eligible\b", r"\bineligible\b",
    r"\bexcluded under the policy\b", r"\bthe exclusion applies\b", r"\bfalls under an exclusion\b",
    r"\bsettlement amount\b", r"\bwe will pay\b", r"\bpayout of\b", r"\bpay the claim\b",
    r"\bissue payment\b", r"\bis fraud\b", r"\bfraudulent\b", r"\bconfirmed fraud\b",
]


def _expected_status(gaps: list[dict]) -> str:
    if any(g.get("blocking") for g in gaps):
        return "Not ready"
    return "Ready with minor gaps" if gaps else "Ready"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    # 1. evidence rows must be cited
    for c in pack.get("checks") or []:
        for row in c.get("evidence") or []:
            if not (row.get("citation") or "").strip():
                errors.append(f"check {c.get('check')} evidence row missing citation")

    # 2. every gap is traceable
    gaps = pack.get("gaps") or []
    for g in gaps:
        if not g.get("item"):
            errors.append("gap missing 'item'")
        if not g.get("category"):
            errors.append(f"gap {g.get('item')!r} missing 'category'")

    # 3. deterministic status mapping
    exp = _expected_status(gaps)
    if pack.get("readiness_status") != exp:
        errors.append(f"readiness_status {pack.get('readiness_status')!r} != deterministic {exp!r} for gaps")

    # 4. no coverage/eligibility/claim-decision language (scan free text, not the disclaimer field)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(c.get("detail", "")) for c in pack.get("checks") or []]
                    + [str(g.get("detail", "")) for g in gaps])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"coverage/eligibility/claim-decision language detected: {m.group(0)!r} "
                          "(R2 checks readiness, it does not decide/adjudicate/approve/deny/pay)")

    # 5. standing disclaimer present
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    # 6. considerations required when gaps exist
    if gaps and not pack.get("considerations"):
        errors.append("gaps present but no considerations included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "readiness_example.json"
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
