#!/usr/bin/env python3
"""Deterministic output validation for data-quality-issue-investigator.

Enforces the R3 casework guardrails before the investigation output is presented:
  1. Every record carries a durable case_id.
  2. Only RECOMMENDATION dispositions are used (no closure/determination/remediated states).
  3. Recommendation records carry a complete, cited evidence bundle; every chronology event
     is cited.
  4. severity_band is consistent with severity_score using the same thresholds the engine
     used (the output's versioned severity_config, defaults otherwise) + regulatory-report
     override.
  5. possible-duplicate links a parent case; needs-data lists what is missing.
  6. No case-closure / root-cause-determination / remediation-complete / filing language.
  7. The standing note is present.

A NON-COMPLIANT fixture (closure or determination language, or a closure disposition) MUST
fail closed with exit 1.

Usage: python validate_output.py investigation.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {
    "recommend-remediation", "recommend-upstream-trace", "recommend-incident-escalation",
    "needs-data", "possible-duplicate",
}
BUNDLE_DISPOSITIONS = {"recommend-remediation", "recommend-upstream-trace", "recommend-incident-escalation"}
STANDING_NOTE = ("Investigation evidence and recommendations only; no data-quality issue has "
                 "been closed, no root cause confirmed, and no data remediated, waived, or "
                 "signed off.")
CLOSURE_PATTERNS = [
    r"\bcase closed\b", r"\bissue closed\b", r"\bclose the (case|issue)\b", r"\bmark(ed)? closed\b",
    r"\bresolved\b", r"\bremediation complete\b", r"\bremediated\b", r"\bfully corrected\b",
    r"\broot cause confirmed\b", r"\bfinal determination\b", r"\bdetermination\b",
    r"\bwaiv(e|ed|er)\b", r"\bno issue found\b", r"\bno data quality issue\b",
    r"\bsigned off\b", r"\bfile(d)? (the )?(report|form|attestation)\b", r"\bno further action\b",
    r"\bdata is (now )?clean\b", r"\bcorrected in production\b",
]


# Default band thresholds — MUST match calculate_or_transform.DEFAULT_SEVERITY. The engine
# derives bands from the (possibly overridden) severity_config, so the validator reads the
# same config from the output document instead of hardcoding thresholds. A configured
# threshold must tie out against the band the engine actually emitted.
DEFAULT_BAND_THRESHOLDS = {"s1_min": 9, "s2_min": 5, "s3_min": 2}


def _expected_band(score, has_reg_report, cfg):
    if score >= cfg.get("s1_min", 9) or has_reg_report:
        return "S1 (Critical)"
    if score >= cfg.get("s2_min", 5):
        return "S2 (High)"
    return "S3 (Moderate)" if score >= cfg.get("s3_min", 2) else "S4 (Low)"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    cfg = {**DEFAULT_BAND_THRESHOLDS, **(doc.get("severity_config") or {})}
    records = doc.get("investigation") or []
    if not records:
        return ["investigation output has no records"]

    for r in records:
        iid = r.get("issue_id", "?")
        if not r.get("case_id"):
            errors.append(f"{iid}: missing durable case_id")
        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{iid}: disallowed disposition {disp!r} (investigation recommends only; "
                          f"no closure/determination/remediation)")
        b = r.get("evidence_bundle") or {}
        has_reg_report = bool((b.get("consumers") or {}).get("regulatory_reports"))
        if disp in BUNDLE_DISPOSITIONS:
            if not b:
                errors.append(f"{iid}: {disp} requires an evidence_bundle")
            else:
                if not b.get("citations"):
                    errors.append(f"{iid}: evidence_bundle missing citations")
                if not b.get("case_id"):
                    errors.append(f"{iid}: evidence_bundle missing case_id")
                for ev in b.get("chronology") or []:
                    if not ev.get("citation"):
                        errors.append(f"{iid}: chronology event {ev.get('type')!r} missing citation")
            exp = _expected_band(r.get("severity_score", 0), has_reg_report, cfg)
            if r.get("severity_band") != exp:
                errors.append(f"{iid}: severity_band {r.get('severity_band')!r} != expected {exp!r} "
                              f"for score {r.get('severity_score')}")
        if disp == "possible-duplicate" and not r.get("linked_case_id"):
            errors.append(f"{iid}: possible-duplicate must carry a linked_case_id (link, never merge/close)")
        if disp == "needs-data" and not r.get("needs"):
            errors.append(f"{iid}: needs-data must list what is missing")

    scan = json.dumps(records) + " " + str(doc.get("narrative", ""))
    for pat in CLOSURE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"closure/determination/filing language detected: {m.group(0)!r} "
                          f"(investigation never closes, determines, or remediates)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "investigation_example.json"
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
