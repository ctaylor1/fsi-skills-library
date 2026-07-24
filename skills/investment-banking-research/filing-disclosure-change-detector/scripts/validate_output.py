#!/usr/bin/env python3
"""Deterministic output validation for filing-disclosure-change-detector.

Validates the final change pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. Fails closed on any miss. Checks:
  1. Every finding has a top-level citation and >= 1 cited evidence row.
  2. change_summary (total_findings + by_type) ties out to the findings list.
  3. review_routing ties out to the deterministic lane mapping from the detected types.
  4. No materiality / legal-significance / investment-implication assertion in analyst-
     authored text (narrative + notes + finding.observation). Verbatim source quotes in
     evidence and the standing disclaimer are excluded from this screen.
  5. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Change detection and citations only; not a determination of materiality, legal "
             "significance, or investment implication. A qualified human makes those determinations.")

LANE_STRUCTURAL = "Covering analyst"
LANE_RISK = "Research supervisory analyst"
LANE_RESTATEMENT = "Financial-reporting / disclosure-controls reviewer"
LANE_CONTRACT = "Legal / contracts reviewer"

# Prohibited assertions for an R2 change detector. These target ANALYST CONCLUSIONS, not
# neutral change descriptions or verbatim source quotes. The HARD BOUNDARY is: never
# determine materiality, legal significance, or investment implication.
PROHIBITED_PATTERNS = [
    # materiality determinations
    r"\b(is|are|was|were)\s+material\b", r"\bimmaterial\b",
    r"\b(deemed|clearly|highly)\s+material\b", r"\bconstitutes?\s+a\s+material\b",
    r"\bmaterially\s+(misleading|adverse|affects?|impacts?|weakens?|reduces?)\b",
    r"\bmaterial\s+to\s+(investors|shareholders|the\s+thesis|valuation|the\s+stock)\b",
    r"\bmateriality\s+(is|has\s+been)\s+(established|met|clear|high)\b",
    # legal-significance determinations
    r"\blegally\s+(significant|material|actionable|binding)\b",
    r"\bconstitutes?\s+a\s+(violation|breach|default|misrepresentation)\b",
    r"\bviolat(e|es|ed|ion)\b", r"\bunlawful\b", r"\billegal\b", r"\bfraudulent\b",
    r"\bbreach(es|ed)?\s+(of|the)\b",
    # investment-implication determinations
    r"\b(buy|sell|hold|overweight|underweight|neutral)\s+(rating|recommendation)\b",
    r"\bprice\s+(target|objective)\b", r"\b(up|down)grade\b",
    r"\b(raise|raising|lower|lowering|cut|cutting|increase|reduce)\s+(our\s+|the\s+)?"
    r"(estimate|estimates|target|rating|forecast|guidance|price\s+target)\b",
    r"\bwe\s+recommend\s+(buying|selling|a\s+(buy|sell))\b", r"\b(bullish|bearish)\b",
    r"\binvestment\s+(implication|thesis|recommendation)\s+(is|:|would\s+be)\b",
    r"\bimpacts?\s+(the\s+|our\s+)?(valuation|thesis|share\s+price|stock\s+price|price\s+target)\b",
    r"\bshould\s+(buy|sell|own|avoid|invest)\b",
    r"\baccretive\s+to\s+(eps|earnings|the\s+thesis)\b",
    r"\battractive\s+(entry|valuation|risk[-\s]reward)\b",
]

STRUCTURAL = {"changed_language", "section_added", "section_removed"}
RISK = {"new_risk_factor", "removed_risk_factor"}


def _expected_routing(findings: list[dict]) -> list[str]:
    types = {f.get("type") for f in findings}
    lanes = set()
    if types & STRUCTURAL:
        lanes.add(LANE_STRUCTURAL)
    if types & RISK:
        lanes.add(LANE_RISK)
    if "restatement_language" in types:
        lanes.add(LANE_RESTATEMENT)
    if any(str(f.get("type", "")).startswith("exhibit_") and f.get("metrics", {}).get("material_contract")
           for f in findings):
        lanes.add(LANE_CONTRACT)
    return sorted(lanes)


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    # 1. citations + evidence
    for f in findings:
        fid = f.get("finding_id", "?")
        if not (f.get("citation") or "").strip():
            errors.append(f"finding {fid} missing top-level citation")
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {fid} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {fid} evidence row missing citation")

    # 2. change_summary tie-out
    cs = pack.get("change_summary") or {}
    by_type: dict[str, int] = {}
    for f in findings:
        by_type[f.get("type")] = by_type.get(f.get("type"), 0) + 1
    if cs.get("total_findings") != len(findings):
        errors.append(f"change_summary.total_findings {cs.get('total_findings')} != {len(findings)}")
    if dict(cs.get("by_type") or {}) != by_type:
        errors.append(f"change_summary.by_type {dict(cs.get('by_type') or {})} != recomputed {by_type}")

    # 3. routing tie-out
    exp_routing = _expected_routing(findings)
    if list(pack.get("review_routing") or []) != exp_routing:
        errors.append(f"review_routing {list(pack.get('review_routing') or [])} != deterministic {exp_routing}")

    # 4. prohibited-decision screen over analyst-authored text only
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("observation", "")) for f in findings])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited determination language detected: {m.group(0)!r} "
                          "(R2 detects and cites changes; it never determines materiality, legal "
                          "significance, or investment implication)")

    # 5. standing disclaimer
    present = DISCLAIMER.lower() in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if not present:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "compare_pack_example.json"
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
