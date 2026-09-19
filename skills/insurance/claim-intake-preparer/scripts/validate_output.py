#!/usr/bin/env python3
"""Deterministic output validation for claim-intake-preparer.

Enforces the R3 guardrails before the normalized record is presented:
  1. Every exception carries a non-empty citation.
  2. suggested_disposition is review-only (normalized | exceptions-for-review).
  3. No coverage / liability / reserve / claim-adjudication language.
  4. Standing disclaimer present.

Usage: python validate_output.py record.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from insurance_contract import validate_artifact

ALLOWED = {"prepared-for-review", "exceptions-for-review"}
DISCLAIMER_RE = re.compile(r"not a coverage, liability, or reserve determination", re.I)
PROHIBITED = [
    r"\bcoverage (is|applies|does not apply)\b",
    r"\bcovered under\b",
    r"\bdeny coverage\b",
    r"\bassign(ed)? liability\b",
    r"\bat fault\b",
    r"\bset the reserve\b",
    r"\breserve is\b",
    r"\bopen(ed)? the claim\b",
    r"\brout(e|ed) the claim\b",
]


def _validate(p: dict) -> list[str]:
    errors = []
    states = p.get("intake_states") or {}
    if set(states) != {"receipt", "normalization", "completeness", "timeliness"}:
        errors.append("missing separate intake states")
    if p.get("notice_receipt_blocked") is not False:
        errors.append("completeness must never block notice receipt")
    ready = all(
        states.get(k) == v
        for k, v in (
            ("receipt", "recorded"),
            ("normalization", "complete"),
            ("completeness", "complete"),
            ("timeliness", "checked"),
        )
    )
    if (p.get("suggested_disposition") == "prepared-for-review") != ready:
        errors.append("prepared status does not match evaluated intake states")
    if states.get("receipt") == "recorded" and not all(
        (p.get("receipt_evidence") or {}).get(k) for k in ("source_ref", "received_at")
    ):
        errors.append("receipt recorded without source evidence")
    assessment = p.get("submission_assessment")
    if assessment and assessment.get("not_evaluable") and assessment.get("readiness_status", "").startswith("Ready"):
        errors.append("unknown submission checks cannot be Ready")
    if assessment and assessment.get("not_evaluable") and ready:
        errors.append("unknown submission checks cannot produce prepared status")
    if states.get("receipt") == "recorded":
        from insurance_contract import timestamp

        try:
            timestamp(p.get("receipt_evidence", {}).get("received_at"))
        except ValueError:
            errors.append("recorded receipt requires valid timezone-aware timestamp")
    for e in p.get("exceptions") or []:
        if not (e.get("citation") or "").strip():
            errors.append(f"exception {e.get('field', '?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = " ".join(str(p.get(k, "")) for k in ("narrative", "notes", "conclusion", "decision", "action"))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(
                f"coverage/liability/reserve language detected: {m.group(0)!r} (R3 normalizes, human adjudicates)"
            )
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (normalization only / no claim opened or adjudicated)")
    return errors


def validate(doc: dict, *args, **kwargs) -> list[str]:
    if not isinstance(doc, dict):
        return ["output must be an object"]
    try:
        errors = _validate(doc, *args, **kwargs)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        errors = ["malformed output: " + str(exc)]
    return errors + validate_artifact(doc.get("artifact"), output=doc)


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "record_example.json"
        p = json.loads(pth.read_text(encoding="utf-8"))
    elif argv:
        p = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        p = json.loads(sys.stdin.read())
    errors = validate(p)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
