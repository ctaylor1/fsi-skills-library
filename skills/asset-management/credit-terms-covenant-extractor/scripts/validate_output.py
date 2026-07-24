#!/usr/bin/env python3
"""Deterministic output validation for credit-terms-covenant-extractor.

Validates the final extraction package (the calculate_or_transform core + a narrative)
before it is presented or delivered. Fails closed on any miss. Checks:
  1. Every extracted/needs_review field carries a page-level citation (positive int page).
  2. No compliance-determination or investment-advice language in generated prose
     (narrative + notes + per-field reason). Verbatim source text (raw_value / value.raw)
     is NOT screened — the skill quotes source; it must never ADD a determination.
  3. No silently-resolved ambiguity: a field whose source text contains an ambiguity
     marker must be status `needs_review`, never `extracted` (the HARD BOUNDARY).
  4. The standing disclaimer is present.
  5. A durable extraction_id (ctce-*) is present; needs_review entries carry a reason.

Usage:
  python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Extracted terms and citations only; no compliance determination, covenant "
              "test, or investment advice has been made.")

AMBIGUITY_MARKERS = ("subject to", "as defined", "to be determined", "tbd", "to be agreed",
                     "[•]", "[●]", "intentionally omitted", "unless otherwise",
                     "as the context requires", "at the issuer's discretion")

# Compliance/advice assertions an R2 extractor must never make (generated prose only):
DETERMINATION_PATTERNS = [
    r"\bin compliance\b", r"\bnon-?compliant\b", r"\bis compliant\b", r"\bin breach\b",
    r"covenant (is )?(breached|violated|tripped|satisfied|met)\b",
    r"\btest (passed|failed|is met|is satisfied)\b", r"\bample headroom\b",
    r"\b(sufficient|insufficient|adequate) (headroom|cushion|coverage)\b",
    r"\bheadroom is\b", r"\bin default\b", r"event of default has (occurred|been triggered)",
    r"\bsafe to invest\b", r"\bwe recommend (buy|sell|hold|to (buy|sell))\b",
    r"\bshould (buy|sell|invest|divest)\b", r"\b(over|under)weight\b",
    r"\brating should be\b", r"\bcures the (breach|default)\b",
]


def _has_marker(text: str) -> bool:
    low = str(text).lower()
    return any(mk in low for mk in AMBIGUITY_MARKERS)


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    fields = pack.get("fields") or []

    for r in fields:
        f = r.get("field", "?")
        status = r.get("status")
        if status in ("extracted", "needs_review"):
            ev = r.get("evidence") or {}
            page = ev.get("page")
            if not isinstance(page, int) or isinstance(page, bool) or page < 1:
                errors.append(f"field {f} (status={status}) missing page-level citation")
            elif not str(ev.get("citation", "")).strip():
                errors.append(f"field {f} evidence missing citation string")
        # HARD BOUNDARY: ambiguous source must not be resolved to a definitive value.
        if status == "extracted" and _has_marker(r.get("raw_value", "")):
            errors.append(f"field {f} resolved ambiguous language to a definitive value "
                          f"(needs_review required)")

    # Generated prose only — never the verbatim source captured in raw_value / value.raw.
    prose = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    prose += [str(r.get("reason", "")) for r in fields]
    text = " ".join(prose)
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/advice language detected: {m.group(0)!r} "
                          f"(R2 extracts and cites; it does not determine or advise)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    eid = str(pack.get("extraction_id", ""))
    if not eid.startswith("ctce-"):
        errors.append(f"missing/invalid durable extraction_id (got {eid!r})")

    for nr in pack.get("needs_review") or []:
        if not str(nr.get("reason", "")).strip():
            errors.append(f"needs_review entry for {nr.get('field','?')} missing a reason")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "extraction_package.json"
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
