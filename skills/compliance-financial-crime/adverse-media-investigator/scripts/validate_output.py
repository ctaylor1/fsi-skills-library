#!/usr/bin/env python3
"""Deterministic output validation for adverse-media-investigator.

Enforces the R3 casework guardrails before an investigation is presented to a human:
  1. Every case carries a durable case_id (AMI-...).
  2. Disposition is a RECOMMENDATION only - closure / clearance / determination / filing
     dispositions are rejected (fail closed).
  3. Every evidence item is cited: matched hits, chronology entries, and the bundle's
     citation list are all non-empty.
  4. materiality_band ties out to materiality_score, and disposition is coherent with the
     band (escalate<->Material, monitor<->Watch, no-material<->Not material), routing carries
     a sanctions/PEP hit + specialist, and needs-data carries a needs list.
  5. No case-closure / determination / SAR-filing language and no tipping-off language.
  6. The standing note is present.

Usage: python validate_output.py investigation.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {
    "recommend-escalate-edd", "recommend-monitor", "recommend-no-material-adverse-media",
    "recommend-route-sanctions-pep", "needs-data",
}
CASE_ID_RE = re.compile(r"^AMI-[A-Za-z0-9_-]+$")
MATERIAL_MIN, WATCH_MIN = 9, 5
STANDING_NOTE = ("Adverse-media investigation is decision support only; no case has been "
                 "closed, no customer cleared or determined, and no filing has been made.")
LIST_ROUTE = {"sanctions", "pep"}

CLOSURE_PATTERNS = [
    r"\bcase closed\b", r"\bclose(d)? the case\b", r"\bclosed as\b",
    r"\bno further action\b", r"\bno-action\b",
    r"\bcleared (the|this) (customer|subject|case|matter)\b",
    r"\b(customer|subject) (is )?cleared\b", r"\bclear to onboard\b", r"\bexonerat",
    r"\bconfirmed (true )?match\b", r"\bis (a )?(confirmed )?sanctions? (hit|match)\b",
    r"\bwe (have )?(determined|concluded)\b", r"\bfinal determination\b",
    r"\bdetermination:\b", r"\bfile (the )?sar\b", r"\bsar (has been |was )?filed\b",
    r"\bfiled a sar\b", r"\btrue positive confirmed\b",
]
TIPPING_PATTERNS = [
    r"\btell the (customer|subject)\b", r"\bnotify the (customer|subject)\b",
    r"\binform the (customer|subject)\b", r"\blet the (customer|subject) know\b",
    r"\bwe are filing a sar\b", r"\bunder investigation for money laundering\b",
]


def _expected_band(score):
    if score >= MATERIAL_MIN:
        return "Material"
    return "Watch" if score >= WATCH_MIN else "Not material"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    cases = doc.get("cases") or []
    if not cases:
        return ["investigation output has no cases"]

    for c in cases:
        cid = c.get("case_id", "?")
        if not c.get("case_id") or not CASE_ID_RE.match(str(c.get("case_id"))):
            errors.append(f"{cid}: missing/invalid durable case_id (expect AMI-...)")
        disp = c.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{cid}: disallowed disposition {disp!r} (only recommendations; no "
                          f"closure/clearance/determination/filing in this skill)")

        # band tie-out
        score = c.get("materiality_score", 0)
        exp = _expected_band(score)
        if c.get("materiality_band") != exp:
            errors.append(f"{cid}: materiality_band {c.get('materiality_band')!r} != expected {exp!r} "
                          f"for score {score}")

        # disposition <-> band / routing / needs coherence
        band = c.get("materiality_band")
        if disp == "recommend-escalate-edd" and band != "Material":
            errors.append(f"{cid}: escalate-edd requires Material band, got {band!r}")
        if disp == "recommend-monitor" and band != "Watch":
            errors.append(f"{cid}: monitor requires Watch band, got {band!r}")
        if disp == "recommend-no-material-adverse-media" and band != "Not material":
            errors.append(f"{cid}: no-material requires 'Not material' band, got {band!r}")
        if disp == "recommend-route-sanctions-pep":
            if not any((h.get("list_type") in LIST_ROUTE) for h in c.get("matched_hits") or []):
                errors.append(f"{cid}: route-sanctions-pep with no matched sanctions/PEP list hit")
            if not c.get("route_specialist"):
                errors.append(f"{cid}: route-sanctions-pep must name a route_specialist")
        if disp == "needs-data" and not c.get("needs"):
            errors.append(f"{cid}: needs-data must list what is missing")

        # evidence bundle + citation coverage
        b = c.get("evidence_bundle") or {}
        if not b:
            errors.append(f"{cid}: missing evidence_bundle")
        else:
            if b.get("case_id") != c.get("case_id"):
                errors.append(f"{cid}: evidence_bundle.case_id mismatch")
            if not b.get("citations"):
                errors.append(f"{cid}: evidence_bundle has no citations")
            for ch in b.get("chronology") or []:
                if not ch.get("citation"):
                    errors.append(f"{cid}: chronology entry {ch.get('event')!r} is uncited")
        for h in c.get("matched_hits") or []:
            if not h.get("citation"):
                errors.append(f"{cid}: matched hit {h.get('hit_id')!r} is uncited")

    scan = json.dumps(cases) + " " + str(doc.get("narrative", ""))
    for pat in CLOSURE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"closure/determination/filing language detected: {m.group(0)!r} "
                          f"(this skill only recommends; humans decide)")
    for pat in TIPPING_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"possible tipping-off language detected: {m.group(0)!r}")

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
