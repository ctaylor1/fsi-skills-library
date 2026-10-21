#!/usr/bin/env python3
"""Deterministic output validation for aml-alert-triager.

Enforces the triage guardrails before the queue/escalations are presented:
  1. Only allowed dispositions are used (no closure/filing states).
  2. Any suppression uses an APPROVED rule id and carries evidence.
  3. Escalated alerts carry a complete, cited escalation bundle.
  4. priority_band is consistent with priority_score (+ sanctions override).
  5. No closure/exoneration/filing or tipping-off language.
  6. The standing note is present.

Native output must match exact reconstruction from the separately retained, validated input.
Additional narrative or fields require a separate reviewed artifact.

Usage: python validate_output.py triage.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from native_integrity import validate_reconstruction
from validate_input import validate as validate_source
from calculate_or_transform import triage

ALLOWED_DISPOSITIONS = {"escalate-to-investigation", "approved-suppressed", "needs-data", "possible-duplicate"}
APPROVED_SUPPRESSIONS = {"SUP-DUP-01", "SUP-WL-INTERNAL", "SUP-SEASONAL-01"}
STANDING_NOTE = ("First-line triage only; no case has been closed, no customer exonerated, "
                 "and no SAR filed.")
CLOSURE_PATTERNS = [
    r"\bclose the case\b", r"\bcase closed\b", r"\bcleared\b", r"\bno sar (needed|required)\b",
    r"\bexonerat", r"\bfile (the )?sar\b", r"\bno further action\b", r"\bno-action\b",
    r"\bclosed as (a )?false positive\b",
]
TIPPING_PATTERNS = [
    r"\btell the customer\b", r"\bnotify the customer\b", r"\binform the customer\b",
    r"\blet the customer know\b", r"\bwe are filing a sar\b",
    r"\bunder investigation for money laundering\b",
]


def _expected_band(score, sanctions, thresholds):
    if score >= thresholds.get("p1_min", 7) or sanctions:
        return "P1 (Elevated)"
    return "P2 (Standard)" if score >= thresholds.get("p2_min", 3) else "P3 (Low)"


def _validate_structure(doc: dict) -> list[str]:
    errors: list[str] = []
    records = doc.get("triage") or []
    if not records:
        return ["triage output has no records"]

    for r in records:
        aid = r.get("alert_id", "?")
        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{aid}: disallowed disposition {disp!r} (closure/filing not permitted in triage)")
        sup = r.get("suppression")
        if disp == "approved-suppressed":
            if not sup or sup.get("rule_id") not in APPROVED_SUPPRESSIONS:
                errors.append(f"{aid}: suppression must use an approved rule id, got {sup and sup.get('rule_id')!r}")
            elif not sup.get("evidence"):
                errors.append(f"{aid}: suppression {sup.get('rule_id')} missing evidence")
        if sup and sup.get("rule_id") not in APPROVED_SUPPRESSIONS:
            errors.append(f"{aid}: unapproved suppression rule {sup.get('rule_id')!r}")
        if disp == "escalate-to-investigation":
            b = r.get("escalation_bundle") or {}
            if not b:
                errors.append(f"{aid}: escalated but no escalation_bundle")
            elif not b.get("citations"):
                errors.append(f"{aid}: escalation_bundle missing citations")
        # priority band consistency
        sanctions = bool(((r.get("escalation_bundle") or {}).get("flags") or {}).get("sanctions_adverse_media"))
        exp = _expected_band(r.get("priority_score", 0), sanctions, doc.get("priority_thresholds") or {})
        if r.get("priority_complete") is False and not sanctions:
            exp = "Unrated"
        if r.get("priority_band") != exp:
            errors.append(f"{aid}: priority_band {r.get('priority_band')!r} != expected {exp!r} for score {r.get('priority_score')}")

    scan = json.dumps(records) + " " + str(doc.get("narrative", ""))
    for pat in CLOSURE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"closure/filing language detected: {m.group(0)!r} (triage never closes/files)")
    for pat in TIPPING_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"possible tipping-off language detected: {m.group(0)!r}")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors



def validate(doc, original_input=None):
    try:
        errors = _validate_structure(doc)
    except (TypeError, ValueError, KeyError, AttributeError, IndexError) as exc:
        errors = [f"malformed native output: {exc}"]
    if isinstance(original_input, dict):
        try:
            input_errors, _ = validate_source(original_input)
            errors.extend("original input: " + error for error in input_errors)
        except (TypeError, ValueError, KeyError, AttributeError, IndexError) as exc:
            errors.append(f"malformed original input: {exc}")
    validate_reconstruction(doc, triage, errors, original_input=original_input)
    return errors

def main(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Validate against separately retained original input; no source authentication is claimed.")
    parser.add_argument("output", nargs="?")
    parser.add_argument("--input", dest="original")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    folder = Path(__file__).resolve().parents[1] / "evals" / "files"
    path = folder / "triage_example.json" if args.selftest else args.output
    source = folder / "alerts_example.json" if args.selftest else args.original
    try:
        doc = json.loads(Path(path).read_text()) if path else json.loads(sys.stdin.read())
        original = json.loads(Path(source).read_text()) if source else None
        errors = validate(doc, original)
    except (OSError, ValueError, TypeError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("ERROR", error)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
