#!/usr/bin/env python3
"""Deterministic output validation for coverage-initiation-researcher.

Validates the assembled coverage pack (the calculate_or_transform core + a narrative) before
it is presented or delivered. Enforces the R2 prohibited-decision/advice screen and fails
closed on any miss. Checks:
  1. Every required section is present and evidenced (no missing / unevidenced sections).
  2. readiness equals the deterministic mapping from the pack fields.
  3. Valuation is complete: weights sum ~ 1.0 and a blended draft midpoint exists.
  4. No personalized-advice / guarantee / buy-sell-hold decision language, and no approved
     "price target" / "official rating" language (narrative + notes only, not the disclaimer).
  5. Proposed rating carries status 'draft-unapproved' unless both approvals are recorded.
  6. MNPI attestation is present and true.
  7. The standing disclaimer and the DRAFT banner are present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DRAFT_BANNER = "DRAFT — not approved for distribution."
DISCLAIMER = (
    "Research draft for internal review only; not investment advice, not an approved rating "
    "or price target, and subject to Reg AC certification and supervisory analyst and research "
    "committee approval before publication."
)
# Prohibited personalized-advice / decision / approved-call language for an R2 draft:
ADVICE_PATTERNS = [
    r"\byou should (buy|sell|hold|short)\b",
    r"\bwe recommend (that )?you\b",
    r"\bmy (personal )?recommendation\b",
    r"\bpersonalized (investment )?(advice|recommendation)\b",
    r"\bguarantee(d|s)?\b",
    r"\brisk[- ]free\b",
    r"\b(can ?not|can'?t) lose\b",
    r"\bsure thing\b",
    r"\bwill (definitely|certainly|surely) (rise|increase|go up|double|outperform)\b",
    r"\bprice target\b",
    r"\bofficial rating\b",
    r"\bapproved rating\b",
    r"\binitiate coverage at\b",
]


def expected_readiness(missing_sections, unevidenced_sections, forecast_errors,
                       valuation_complete, data_gaps, evidence_coverage) -> str:
    """Verbatim copy of calculate_or_transform.expected_readiness (kept local so this
    validator is self-contained and stdlib-only)."""
    blocking = bool(missing_sections) or bool(unevidenced_sections) \
        or bool(forecast_errors) or not valuation_complete
    if blocking:
        return "Not ready"
    if data_gaps or (evidence_coverage is not None and evidence_coverage < 1.0):
        return "Analyst review"
    return "Ready for supervisory review"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    # 1. section completeness / evidence
    if pack.get("missing_sections"):
        errors.append(f"required sections missing: {pack['missing_sections']}")
    if pack.get("unevidenced_sections"):
        errors.append(f"sections present but not fully cited: {pack['unevidenced_sections']}")

    # 3. valuation completeness (checked before readiness tie-out uses it)
    val = pack.get("valuation") or {}
    valuation_complete = bool(val.get("complete"))
    if val.get("blended_midpoint") is None:
        errors.append("valuation has no blended draft midpoint (triangulation incomplete)")
    ws = val.get("weights_sum")
    if ws is not None and abs(float(ws) - 1.0) > 0.01:
        errors.append(f"valuation weights sum {ws} != 1.0")

    # 2. deterministic readiness tie-out
    exp = expected_readiness(pack.get("missing_sections"), pack.get("unevidenced_sections"),
                             (pack.get("forecast_checks") or {}).get("errors"),
                             valuation_complete, pack.get("data_gaps"),
                             pack.get("evidence_coverage"))
    if pack.get("readiness") != exp:
        errors.append(f"readiness {pack.get('readiness')!r} != deterministic {exp!r}")

    # 4. prohibited advice / decision / approved-call language (scan free text only,
    #    NOT the disclaimer/banner fields which legitimately contain 'price target' etc.)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))])
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited advice/decision language detected: {m.group(0)!r} "
                          f"(R2 drafts evidence a thesis; they do not advise, decide, or issue an approved call)")

    # 5. rating must stay draft-unapproved unless both approvals recorded
    appr = pack.get("approvals") or {}
    both_approved = bool(appr.get("supervisory_analyst")) and bool(appr.get("research_committee"))
    status = (pack.get("proposed_rating") or {}).get("status")
    if not both_approved and status != "draft-unapproved":
        errors.append(f"proposed_rating.status {status!r} must be 'draft-unapproved' without dual approval")

    # 6. MNPI attestation
    if not pack.get("mnpi_attestation"):
        errors.append("MNPI attestation missing or false — draft cannot proceed")

    # 7. disclaimer + DRAFT banner present
    narrative = str(pack.get("narrative", ""))
    if DISCLAIMER.lower() not in (narrative + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")
    if DRAFT_BANNER.lower() not in (narrative + " " + str(pack.get("draft_banner", ""))).lower():
        errors.append("missing DRAFT banner")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "coverage_pack_example.json"
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
