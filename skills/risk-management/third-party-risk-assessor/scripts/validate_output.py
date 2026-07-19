#!/usr/bin/env python3
"""Deterministic output validation for third-party-risk-assessor (R3 fail-closed screen).

Validates the final vendor-assessment pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks:
  1. Every material finding (dimension severity >= 2) has >= 1 cited evidence row.
  2. suggested_risk_tier equals the deterministic mapping from the dimension severities,
     recomputed with the SAME high_dimension_count the engine used (read from the pack's
     config), so a tightened config cannot tie out against a stale hard-coded threshold.
  3. No prohibited DECISION / closure / filing / risk-acceptance language (R3 recommends;
     humans decide). Scans narrative + notes + reasons + recommended_actions.
  4. The standing disclaimer is present.
  5. When any material finding exists, recommended_actions include an explicit
     human-adjudication note, and evidence_gaps is present (list).

This is the archetype's prohibited-decision screen and the R3 fail-closed gate: a pack that
asserts a vendor decision, closes/files the assessment, or drops the disclaimer FAILS.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise (prints a line ending "N error(s)").
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DEFAULT_HIGH_DIMENSION_COUNT = 3
DISCLAIMER = ("Assessment evidence and recommendations only; not an approval, rejection, or "
              "risk-acceptance decision. Human adjudication and sign-off are required before any "
              "onboarding, renewal, termination, or system-of-record change.")

# Autonomous vendor-decision / closure / filing / risk-acceptance assertions an R3
# decision-support skill must never make. Phrasings are specific so factual finding text
# and the disclaimer do not false-positive.
PROHIBITED_PATTERNS = [
    r"\bapprove the (vendor|third[- ]party|supplier)\b",
    r"\bapproved for onboarding\b", r"\bcleared for onboarding\b",
    r"\bonboard the (vendor|third[- ]party|supplier)\b",
    r"\b(we|i) (will|should) onboard\b",
    r"\breject the (vendor|third[- ]party|supplier)\b",
    r"\bdo not engage (the|this) (vendor|third[- ]party|supplier)\b",
    r"\bterminate the contract\b", r"\baward the contract\b", r"\boffboard the (vendor|third[- ]party)\b",
    r"\brisk[- ]accept(ed|ance)?\b",
    r"\bdecision:\s*(approve|reject|proceed|onboard)",
    r"\bfinal decision\b", r"\bfinal determination\b",
    r"\bclose(d)? the assessment\b", r"\bassessment (is )?closed\b",
    r"\bsign(ed)?[- ]off\b", r"\bsign off\b",
    r"\bfile the (assessment|attestation)\b", r"\bwrite (to|the) system of record\b",
]


def _high_dimension_count(pack) -> int:
    """The High-dimension escalation threshold the ENGINE used, read from the pack's config.

    The engine (calculate_or_transform.suggested_tier) reads ``config.high_dimension_count``;
    the validator must recompute the deterministic tier with the SAME threshold or a tightened
    config would tie out against a stale hard-coded 3 and let an under-escalated tier through.
    Missing/invalid values fall back to the default so the check never crashes or opens up.
    """
    hdc = (pack.get("config") or {}).get("high_dimension_count", DEFAULT_HIGH_DIMENSION_COUNT)
    if isinstance(hdc, bool) or not isinstance(hdc, int) or hdc < 1:
        return DEFAULT_HIGH_DIMENSION_COUNT
    return hdc


def _expected_tier(sevs, high_dimension_count=DEFAULT_HIGH_DIMENSION_COUNT):
    sevs = [s for s in sevs if isinstance(s, int)]
    if not sevs:
        return "Low"
    mx = max(sevs)
    n_high = sum(1 for s in sevs if s >= 2)
    if mx == 3:
        return "Critical"
    if mx == 2:
        return "Critical" if n_high >= high_dimension_count else "High"
    if mx == 1:
        return "Moderate"
    return "Low"


def validate(pack: dict) -> list:
    errors = []
    dims = pack.get("dimensions") or []

    # 1. material findings have cited evidence
    for d in dims:
        if d.get("fired") or (isinstance(d.get("severity"), int) and d["severity"] >= 2):
            ev = d.get("evidence") or []
            if not ev:
                errors.append(f"material finding {d.get('dimension')} has no cited evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"material finding {d.get('dimension')} evidence row missing citation")

    # 2. deterministic tier tie-out (recomputed with the engine's configured threshold)
    sevs = [d.get("severity") for d in dims]
    exp = _expected_tier(sevs, _high_dimension_count(pack))
    if pack.get("suggested_risk_tier") != exp:
        errors.append(f"suggested_risk_tier {pack.get('suggested_risk_tier')!r} != deterministic {exp!r} for severities {sevs}")

    # 3. prohibited decision/closure/filing language (NOT the disclaimer field)
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
        + [str(d.get("reason", "")) for d in dims]
        + [str(a) for a in (pack.get("recommended_actions") or [])]
    )
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing language detected: {m.group(0)!r} (R3 recommends; humans decide)")

    # 4. standing disclaimer present
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    # 5. adjudication note + evidence_gaps present when material findings exist
    material = [d for d in dims if d.get("fired") or (isinstance(d.get("severity"), int) and d["severity"] >= 2)]
    if material:
        acts = " ".join(str(a) for a in (pack.get("recommended_actions") or []))
        if "adjudicate" not in acts.lower() and "adjudication" not in acts.lower():
            errors.append("material findings present but recommended_actions lack a human-adjudication note")
        if not isinstance(pack.get("evidence_gaps"), list):
            errors.append("evidence_gaps must be present (list) when material findings exist")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_pack.json"
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
