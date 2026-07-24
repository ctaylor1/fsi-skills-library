#!/usr/bin/env python3
"""Deterministic output validation for investment-data-quality-exception-detector.

Validates the final exception queue before it is presented or delivered. This is the R2
prohibited-decision screen: the detector may only detect, evidence, and prioritize — it must
never correct, override, suppress, close, or choose a canonical value. Checks:
  1. Every exception has >=1 cited evidence row WITH an as-of; a valid severity; status 'open'.
  2. queue_priority equals the deterministic mapping from the exception severities.
  3. No forbidden correction/override/resolution FIELD appears anywhere in the queue.
  4. conflicting_classification (reference-data conflict) carries route_to=investment-vendor-feed-reconciler.
  5. No correction / suppression / canonical-choice / advice LANGUAGE in free text.
  6. The standing disclaimer is present.

Usage:
  python validate_output.py queue.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

SEV_RANK = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
DEFAULT_P1_HIGH_COUNT = 3
REFERENCE_DATA_CONFLICT_TYPES = {"conflicting_classification"}
CONFLICT_ROUTE = "investment-vendor-feed-reconciler"
DISCLAIMER = ("Detection evidence only; exceptions are open findings. No data has been "
              "corrected, overridden, or suppressed, and no canonical value has been chosen.")

# Fields that would mean the skill silently changed or disposed of data (prohibited):
FORBIDDEN_FIELDS = {
    "corrected_value", "override_value", "canonical_value", "applied_fix", "fix_applied",
    "resolution", "new_value", "chosen_value", "waiver", "suppressed_reason",
}
# Free-text assertions an R2 detector must not make:
FORBIDDEN_PATTERNS = [
    r"auto-?corrected", r"\bcorrected the\b", r"\boverrode\b", r"\boverridden the\b",
    r"\bset the (price|value|field|mapping) to\b", r"\bcanonical value is\b",
    r"\bthe correct value is\b", r"\bgolden (source|value) is\b",
    r"\buse vendor \w+'?s? value\b", r"\bsuppress(?:ed|ing)? the exception\b",
    r"\bwaive(?:d)? the exception\b", r"\bclos(?:e|ed|ing) the exception\b",
    r"\bdismiss(?:ed)? the exception\b", r"\badjust the nav\b",
    r"\bshould (?:buy|sell|trade|reduce|increase|overweight|underweight)\b",
]


def _priority(sevs: list[str], p1_high_count: int) -> str:
    if not sevs:
        return "None"
    ranks = [SEV_RANK[s] for s in sevs if s in SEV_RANK]
    if not ranks:
        return "None"
    top = max(ranks)
    high_plus = sum(1 for r in ranks if r >= 3)
    if top == 4 or high_plus >= p1_high_count:
        return "P1"
    if top == 3:
        return "P2"
    if top == 2:
        return "P3"
    return "P4"


def _find_forbidden_fields(obj, path="") -> list[str]:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_FIELDS:
                hits.append(f"{path}{k}")
            hits.extend(_find_forbidden_fields(v, f"{path}{k}."))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_find_forbidden_fields(v, f"{path}{i}."))
    return hits


def validate(queue: dict) -> list[str]:
    errors: list[str] = []
    exceptions = queue.get("exceptions") or []

    for e in exceptions:
        eid = e.get("exception_id", "?")
        ev = e.get("evidence") or []
        if not ev:
            errors.append(f"exception {eid} has no evidence")
        for row in ev:
            if not str(row.get("citation", "")).strip():
                errors.append(f"exception {eid} evidence row missing citation")
            if not str(row.get("as_of", "")).strip():
                errors.append(f"exception {eid} evidence row missing as_of")
        if e.get("severity") not in SEV_RANK:
            errors.append(f"exception {eid} invalid severity {e.get('severity')!r}")
        if e.get("status") != "open":
            errors.append(
                f"exception {eid} status must be 'open' (got {e.get('status')!r}) — "
                "this skill never suppresses, waives, or closes an exception")
        if e.get("type") in REFERENCE_DATA_CONFLICT_TYPES and e.get("route_to") != CONFLICT_ROUTE:
            errors.append(
                f"reference-data-conflict exception {eid} must route_to {CONFLICT_ROUTE!r} "
                f"(got {e.get('route_to')!r})")

    # deterministic priority tie-out
    p1c = int((queue.get("priority_params") or {}).get("p1_high_count", DEFAULT_P1_HIGH_COUNT))
    exp = _priority([e.get("severity") for e in exceptions], p1c)
    if queue.get("queue_priority") != exp:
        errors.append(
            f"queue_priority {queue.get('queue_priority')!r} != deterministic {exp!r}")

    # forbidden correction/override fields anywhere in the queue
    for hit in _find_forbidden_fields(queue):
        errors.append(
            f"forbidden correction/override field present: {hit} — "
            "this skill never corrects, fills, or chooses a value")

    # forbidden free-text assertions (reason + narrative + notes; NOT the disclaimer field)
    text = " ".join([str(queue.get("narrative", "")), str(queue.get("notes", ""))]
                    + [str(e.get("reason", "")) for e in exceptions])
    for pat in FORBIDDEN_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(
                f"correction/suppression/advice language detected: {m.group(0)!r} "
                "(R2 detects and routes; it does not correct, suppress, or advise)")

    disc = (str(queue.get("narrative", "")) + " " + str(queue.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in disc:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "queue_example.json"
        queue = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        queue = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        queue = json.loads(sys.stdin.read())
    errors = validate(queue)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
