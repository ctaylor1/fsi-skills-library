#!/usr/bin/env python3
"""Deterministic output validation for valuation-exception-packet.

Enforces the casework guardrails before the packet is presented:
  1. Durable job_id + per-case case_id present.
  2. Only recommendation dispositions are used (no price-selection / NAV / closure states).
  3. No prohibited decision fields anywhere (final_price, selected_price, certified_nav, ...).
  4. Every candidate price carries a price_type CONSISTENT with its source_type
     (no hypothesis presented as an observation, no observation mislabelled hypothesis).
  5. Every exception-confirmed case has a cited evidence bundle + adjudication: human-required.
  6. severity_band ties to the deterministic mapping (score + open-challenge override).
  7. No price-selection / override / NAV-certification language.
  8. The standing note is present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {"exception-confirmed", "needs-data", "no-exception-detected"}
PROHIBITED_DISPOSITIONS = {
    "price-selected", "valuation-overridden", "override-applied", "nav-certified",
    "nav-struck", "mark-approved", "closed", "resolved", "final",
}
PROHIBITED_FIELDS = {
    "final_price", "selected_price", "chosen_price", "override_price",
    "certified_nav", "struck_nav", "nav",
}
OBSERVATION_SOURCES = {"exchange_close", "vendor_evaluated", "executable_quote", "trade_print"}
HYPOTHESIS_SOURCES = {"indicative_quote", "matrix_price", "model_price", "carry_forward"}
STANDING_NOTE = ("Valuation exception packet only; no price has been selected or overridden and "
                 "no NAV has been certified or struck. Observed prices and hypotheses are "
                 "evidence for the valuation committee's decision.")

DECISION_PATTERNS = [
    r"\bthe correct price is\b",
    r"\bfinal (mark|price)\b",
    r"\bwe (select|choose|set|override|overrode|certify|certified|strike|struck|approve|approved)\b",
    r"\boverride the (vendor )?(price|mark)\b",
    r"\bcertif\w* (the )?nav\b",
    r"\bstrike the nav\b",
    r"\bnav (is|was) (certified|struck)\b",
    r"\buse \$?\d[\d.,]* as the (final )?(mark|price)\b",
    r"\bmark(ed)? (it|the security|the position) at \$?\d",
    r"\bapprove(d)? the (fair[- ]?value|mark|price)\b",
]


def _expected_band(score, open_challenge):
    if (score or 0) >= 7 or open_challenge:
        return "P1 (Elevated)"
    return "P2 (Standard)" if (score or 0) >= 3 else "P3 (Low)"


def _expected_price_type(source_type):
    if source_type in OBSERVATION_SOURCES:
        return "observation"
    if source_type in HYPOTHESIS_SOURCES:
        return "hypothesis"
    return None  # unknown source_type


def _prohibited_keys(obj, path="root"):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in PROHIBITED_FIELDS:
                hits.append(f"{path}.{k}")
            hits.extend(_prohibited_keys(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_prohibited_keys(v, f"{path}[{i}]"))
    return hits


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    if not doc.get("job_id"):
        errors.append("packet missing durable job_id")

    for key in _prohibited_keys(doc):
        errors.append(f"prohibited field present: {key} (packet never selects a price or NAV)")

    records = doc.get("exceptions") or []
    if not records:
        return errors + ["packet has no exception records"]

    for r in records:
        iid = r.get("instrument_id", "?")
        if not r.get("case_id"):
            errors.append(f"{iid}: missing durable case_id")
        disp = r.get("disposition")
        if disp in PROHIBITED_DISPOSITIONS:
            errors.append(f"{iid}: disallowed disposition {disp!r} (decision/closure not permitted)")
        elif disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{iid}: unknown disposition {disp!r}")

        for p in r.get("candidate_prices", []) or []:
            exp = _expected_price_type(p.get("source_type"))
            if exp is None:
                errors.append(f"{iid}: candidate {p.get('source_id')!r} has unknown source_type "
                              f"{p.get('source_type')!r}")
            elif p.get("price_type") != exp:
                if exp == "observation":
                    errors.append(f"{iid}: candidate {p.get('source_id')!r} observation mislabelled "
                                  f"{p.get('price_type')!r}")
                else:
                    errors.append(f"{iid}: hypothesis presented as observation for "
                                  f"{p.get('source_id')!r} ({p.get('source_type')})")

        if disp == "exception-confirmed":
            b = r.get("evidence_bundle") or {}
            if not b:
                errors.append(f"{iid}: exception-confirmed but no evidence_bundle")
            elif not b.get("citations"):
                errors.append(f"{iid}: evidence_bundle missing citations")
            if r.get("adjudication") != "human-required":
                errors.append(f"{iid}: exception-confirmed must set adjudication 'human-required'")
            if not r.get("exception_type"):
                errors.append(f"{iid}: exception-confirmed missing exception_type")
            oc = bool((b.get("parties") and any(pt.get("role") == "challenger" for pt in b["parties"])))
            exp_band = _expected_band(r.get("severity_score", 0), oc)
            if r.get("severity_band") != exp_band:
                errors.append(f"{iid}: severity_band {r.get('severity_band')!r} != expected "
                              f"{exp_band!r} for score {r.get('severity_score')}")

    scan = json.dumps(records) + " " + str(doc.get("narrative", "")) + " " + str(doc.get("standing_note", ""))
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m and m.group(0).lower() not in STANDING_NOTE.lower():
            errors.append(f"price-selection/override/NAV-certification language detected: {m.group(0)!r}")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "packet_example.json"
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
