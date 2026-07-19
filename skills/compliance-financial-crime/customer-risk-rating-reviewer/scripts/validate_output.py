#!/usr/bin/env python3
"""Deterministic output validation for customer-risk-rating-reviewer.

Validates the final risk-rating review pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. This is the R3 fail-closed gate. Checks:
  1. Every finding has >= 1 cited evidence row.
  2. recomputed_band equals the deterministic band mapping from score_pct + floor_band.
  3. recommended_review_outcome equals the deterministic precedence from the findings.
  4. recommended_band is a valid band and equals recomputed_band.
  5. A rating_discrepancy finding exists whenever recomputed_band != rating_of_record.band
     (the review may never silently agree with a divergent record).
  6. adjudication_required is present and true (R3 retains mandatory human adjudication).
  7. No regulated decision / closure / filing / override-approval / offboarding language
     anywhere in the free text (narrative + notes + finding descriptions).
  8. The standing disclaimer is present.
  9. recommended_next_steps present for any non-align outcome.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DEFAULT_THRESHOLDS = [
    {"band": "Low", "max_score": 30}, {"band": "Medium", "max_score": 60},
    {"band": "High", "max_score": 85}, {"band": "Prohibited", "max_score": 100},
]
BAND_ORDER = ["Low", "Medium", "High", "Prohibited"]

DISCLAIMER = (
    "Recommendation and cited evidence only; not a customer risk-rating decision. This review "
    "does not modify the rating of record, validate or approve any override, dispose of any "
    "trigger, close any case, or make any regulatory filing or system-of-record change. A "
    "qualified compliance officer must adjudicate every finding before any rating or case action."
)

# Regulated decision / closure / filing / action assertions an R3 skill must NOT make.
# Phrased as positive actions so the negated disclaimer text does not self-trigger.
PROHIBITED_PATTERNS = [
    r"\bchang(e|ed|ing) the (customer )?risk rating\b",
    r"\bset the (customer )?risk rating\b",
    r"\bupdat(e|ed|ing) the (customer )?risk rating\b",
    r"\bwe (have )?re-?rated (the customer|them)\b",
    r"\bhas been re-?rated to\b",
    r"\brating (has been|is now) set to\b",
    r"\bfinal (rating|decision|determination)\b",
    r"\bdecision:\s*(low|medium|high|prohibited)\b",
    r"\bclose(d)? the case\b", r"\bcase (is |has been )?closed\b",
    r"\bapproved the override\b", r"\boverride (is |has been )?approved\b",
    r"\bfile(d)? (a |the )?sar\b", r"\bfile(d)? (a |the )?suspicious activity report\b",
    r"\bfile(d)? (a |the )?(regulatory )?report\b", r"\bfile(d)? (the )?(cdd|kyc) update\b",
    r"\bwrit(e|ten|ing) to the system of record\b", r"\bupdat(e|ed|ing) the system of record\b",
    r"\bexit the (customer|relationship)\b", r"\boffboard(ed|ing)? the customer\b",
    r"\bblock the customer\b",
    r"\bconfirmed (money laundering|sanctions match)\b", r"\bis (a )?money launderer\b",
]


def band_for_score(pct, thresholds):
    for t in thresholds:
        if pct <= t["max_score"]:
            return t["band"]
    return thresholds[-1]["band"]


def max_band(a, b, order):
    if not b:
        return a
    if not a:
        return b
    return a if order.index(a) >= order.index(b) else b


def expected_outcome(finding_types, floor_band, recomputed_band, record_band):
    # Byte-identical to calculate_or_transform.expected_outcome.
    if floor_band == "Prohibited" or (finding_types & {"expired_override", "undocumented_override", "unassessed_trigger"}):
        return "Escalate-For-Adjudication"
    if "missing_required_factor" in finding_types:
        return "Remediate-Data-First"
    if recomputed_band != record_band:
        return "Re-Rate-Recommended"
    return "Align-No-Change"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    order = pack.get("band_order") or BAND_ORDER
    thresholds = pack.get("band_thresholds") or DEFAULT_THRESHOLDS

    for f in findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('finding_id', f.get('type'))} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {f.get('finding_id', f.get('type'))} evidence row missing citation")

    # deterministic band tie-out
    floor_band = pack.get("floor_band")
    score_pct = pack.get("score_pct")
    recomputed = pack.get("recomputed_band")
    if score_pct is not None:
        exp_band = max_band(band_for_score(score_pct, thresholds), floor_band, order)
        if recomputed != exp_band:
            errors.append(f"recomputed_band {recomputed!r} != deterministic {exp_band!r} "
                          f"(score_pct={score_pct}, floor_band={floor_band})")

    record_band = (pack.get("rating_of_record") or {}).get("band")
    ftypes = {f.get("type") for f in findings}
    exp_outcome = expected_outcome(ftypes, floor_band, recomputed, record_band)
    if pack.get("recommended_review_outcome") != exp_outcome:
        errors.append(f"recommended_review_outcome {pack.get('recommended_review_outcome')!r} != "
                      f"deterministic {exp_outcome!r} for finding types {sorted(t for t in ftypes if t)}")

    rec_band = pack.get("recommended_band")
    if rec_band not in order:
        errors.append(f"recommended_band {rec_band!r} not a valid band {order}")
    elif recomputed and rec_band != recomputed:
        errors.append(f"recommended_band {rec_band!r} != recomputed_band {recomputed!r}")

    if recomputed and record_band and recomputed != record_band and "rating_discrepancy" not in ftypes:
        errors.append("recomputed_band differs from rating of record but no rating_discrepancy finding is present")

    if pack.get("adjudication_required") is not True:
        errors.append("adjudication_required must be true (R3 retains mandatory human adjudication)")

    # scan free text (narrative + notes + finding descriptions); disclaimer field excluded
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("description", "")) for f in findings])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing language detected: {m.group(0)!r} "
                          f"(R3 recommends + evidences; a human adjudicates, decides, and files)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if exp_outcome != "Align-No-Change" and not pack.get("recommended_next_steps"):
        errors.append(f"outcome {exp_outcome} requires recommended_next_steps (human/specialist routing)")

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
