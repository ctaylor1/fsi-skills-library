#!/usr/bin/env python3
"""Deterministic output validation for payment-fraud-case-investigator.

Enforces the R3 casework guardrails before the case bundle / recommendation is presented:
  1. Every record carries a durable case_id (format PFC-*).
  2. Disposition is a RECOMMENDATION only — one of the allowed recommend/route/needs values;
     no decision, closure, determination, or filing state may appear.
  3. Recommendation consistency: the bundle's recommended_disposition matches the record.
  4. Evidence completeness: recommend/route records carry an evidence_bundle whose EVERY
     evidence item is cited, and the bundle carries citations; needs-evidence records list
     what is missing.
  5. Risk-band consistency: risk_band agrees with risk_score (documented thresholds).
  6. No autonomous closure / fraud determination / block / SAR-filing language.
  7. The standing note is present.

Fails closed (exit 1) on any miss, so a bundle with closure/determination language cannot be
presented as a finished disposition.

Usage: python validate_output.py case_bundle.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {
    "recommend-fraud", "recommend-legitimate", "recommend-elevated-monitoring",
    "needs-evidence", "route-specialist",
}
BUNDLE_DISPOSITIONS = {"recommend-fraud", "recommend-legitimate",
                       "recommend-elevated-monitoring", "route-specialist"}
STANDING_NOTE = (
    "Investigation evidence and a disposition recommendation only; no case has been closed, "
    "no fraud determination has been made, and no filing has been performed. Human "
    "adjudication is required before any block, closure, filing, or customer commitment."
)
HIGH_MIN, LOW_MAX = 8, 3

# Autonomous decision / closure / determination / filing / action language. These describe a
# regulated action being TAKEN — none of which this R3 skill may do. Recommendation phrasing
# ("recommend a fraud adjudicator review", "recommend-fraud") is deliberately not matched.
PROHIBITED_PATTERNS = [
    r"\bcase (is |was |has been )?closed\b", r"\bclosed the case\b", r"\bclose the case\b",
    r"\bconfirmed fraud\b", r"\bfraud (is |was )?confirmed\b", r"\bfraud confirmed\b",
    r"\bconfirmed as fraud\b", r"\bis fraudulent\b",
    r"\bfinal(ized)? determination\b", r"\bwe (have )?determined\b", r"\bdetermination:\s",
    r"\bfiled (the |a )?sar\b", r"\bsar (has been |was )?filed\b", r"\bwe filed\b",
    r"\breported to law enforcement\b",
    r"\baccount (has been |was )?blocked\b", r"\bblocked the (account|beneficiary)\b",
    r"\bhave blocked\b", r"\bfunds (have been |were )?recovered\b",
    r"\bno further action\b", r"\bexonerat", r"\bcleared the customer\b", r"\bcleared\b",
]


def _expected_band(score) -> str:
    s = int(score or 0)
    if s >= HIGH_MIN:
        return "High"
    if s <= LOW_MAX:
        return "Low"
    return "Elevated"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    records = doc.get("cases") or []
    if not records:
        return ["case output has no records"]

    for r in records:
        aid = r.get("alert_id", "?")
        cid = r.get("case_id")
        if not cid or not str(cid).startswith("PFC-") or len(str(cid)) <= 4:
            errors.append(f"{aid}: missing/invalid durable case_id {cid!r} (must start with 'PFC-')")

        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{aid}: disallowed disposition {disp!r} "
                          f"(only recommendations permitted; no closure/determination/filing state)")

        bundle = r.get("evidence_bundle") or {}
        if disp in BUNDLE_DISPOSITIONS:
            if not bundle:
                errors.append(f"{aid}: {disp} but no evidence_bundle")
            else:
                if bundle.get("recommended_disposition") != disp:
                    errors.append(f"{aid}: bundle.recommended_disposition "
                                  f"{bundle.get('recommended_disposition')!r} != disposition {disp!r}")
                items = bundle.get("evidence_items")
                if not items:
                    errors.append(f"{aid}: evidence_bundle has no evidence_items")
                else:
                    for k, it in enumerate(items):
                        if not it.get("citation"):
                            errors.append(f"{aid}: evidence_items[{k}] ({it.get('category')}."
                                          f"{it.get('signal')}) missing citation")
                if not bundle.get("citations"):
                    errors.append(f"{aid}: evidence_bundle missing citations")
                # band consistency
                exp = _expected_band(bundle.get("risk_score"))
                if bundle.get("risk_band") != exp:
                    errors.append(f"{aid}: risk_band {bundle.get('risk_band')!r} != expected "
                                  f"{exp!r} for score {bundle.get('risk_score')}")
            if disp == "route-specialist" and not r.get("route_specialist"):
                errors.append(f"{aid}: route-specialist but no route_specialist target named")
        elif disp == "needs-evidence":
            if not r.get("needs"):
                errors.append(f"{aid}: needs-evidence but no 'needs' list of what is missing")

    scan = json.dumps(records) + " " + str(doc.get("narrative", ""))
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing language detected: {m.group(0)!r} "
                          f"(this skill recommends only; humans decide, close, and file)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_bundle_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
