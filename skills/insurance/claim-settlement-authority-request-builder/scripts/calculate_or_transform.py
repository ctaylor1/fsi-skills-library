#!/usr/bin/env python3
"""Package a supplied evaluation for unapproved authority review against an effective sourced matrix. Unknown amounts never become zero; no authority above the highest cap is inferred.

Usage: python calculate_or_transform.py input.json | --selftest
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from insurance_contract import build_artifact

DISCLAIMER = (
    "Authority-request packet only; not a settlement approval, a grant or exercise of "
    "authority, or a payment authorization. No settlement has been approved."
)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _calculate(doc: dict) -> dict:
    from insurance_contract import amount, iso_date

    claim, ev, matrix = doc["claim"], doc["evaluation"], doc["authority_matrix"]
    gaps, tiers = [], []

    def gap(item, reason):
        gaps.append({"item": item, "reason": reason, "citation": f"input:{item}"})

    values = {}
    for field in ("indemnity_estimate", "expense_estimate"):
        try:
            values[field] = amount(ev.get(field))
            if values[field] < 0:
                raise ValueError("must be nonnegative")
        except ValueError as exc:
            values[field] = None
            gap(field, str(exc))
    total = sum(values.values()) if all(v is not None for v in values.values()) else None
    version, currency = matrix.get("config_version"), ev.get("currency")
    if not version:
        gap("authority_matrix", "version unknown")
    if not isinstance(currency, str) or len(currency) != 3 or currency != matrix.get("currency"):
        gap("currency", "evaluation and matrix need the same explicit three-letter currency")
    try:
        when = iso_date(doc.get("as_of"))
        if not iso_date(matrix.get("effective_from")) <= when <= iso_date(matrix.get("effective_to")):
            gap("authority_matrix", "matrix not effective as of review date")
    except ValueError:
        gap("authority_matrix", "matrix effective dates or as_of unknown")
    if not matrix.get("source_ref"):
        gap("authority_matrix", "matrix source reference missing")
    seen_tiers, seen_caps = set(), set()
    for t in matrix.get("tiers", []):
        try:
            cap = amount(t.get("max_amount"))
            if (
                cap < 0
                or not t.get("tier")
                or not t.get("approver_role")
                or t["tier"] in seen_tiers
                or cap in seen_caps
            ):
                raise ValueError("tier IDs/caps must be unique and amounts nonnegative; approver required")
            seen_tiers.add(t["tier"])
            seen_caps.add(cap)
            tiers.append({**t, "max_amount": float(cap)})
        except ValueError as exc:
            gap("authority_matrix", str(exc))
    if not tiers:
        gap("authority_matrix", "no usable tiers")
    amount_matrix_valid = not gaps
    required = (
        next(
            (
                t
                for t in sorted(tiers, key=lambda t: t["max_amount"])
                if total is not None and total <= amount(t["max_amount"])
            ),
            None,
        )
        if amount_matrix_valid
        else None
    )
    exceeds = bool(amount_matrix_valid and total is not None and required is None)
    if exceeds:
        gap("authority_matrix", "exceeds all supplied caps; escalate outside this matrix")
    available = {
        "claim_summary": bool(claim.get("claim_id") and claim.get("summary")),
        "evaluation_basis": bool(ev.get("basis_note") and ev.get("source_ref")),
        "evidence_index": bool(doc.get("evidence_refs")) and all(e.get("ref") for e in doc.get("evidence_refs", [])),
        "coverage_confirmation": doc.get("coverage_confirmation") is True and bool(doc.get("coverage_source_ref")),
    }
    required_items = doc.get("checklist", {}).get("required_items")
    if not isinstance(required_items, list) or not required_items:
        gap("checklist", "explicit nonempty required-item list missing")
    for item in required_items or []:
        if not available.get(item, False):
            gap(item, "required source-backed item unavailable")
    return {
        "packet_id": f"csap-{claim.get('claim_id', 'UNKNOWN')}",
        "claim_id": claim.get("claim_id"),
        "claim_type": claim.get("claim_type"),
        "matrix_version": version,
        "exposure": {
            **{k: float(v) if v is not None else None for k, v in values.items()},
            "total_exposure": float(total) if total is not None else None,
            "currency": currency,
            "basis_note": ev.get("basis_note"),
        },
        "authority_basis": {
            "matrix": matrix,
            "as_of": doc.get("as_of"),
            "checklist": required_items,
            "available_items": available,
            "amount_matrix_valid": amount_matrix_valid,
        },
        "required_authority_tier": (required or {}).get("tier"),
        "required_approver": (required or {}).get("approver_role"),
        "exceeds_matrix": exceeds,
        "evidence_index": doc.get("evidence_refs", []),
        "completeness_gaps": gaps,
        "suggested_disposition": "gaps-for-review" if gaps else "packet-ready",
        "citation_tier": matrix.get("source_ref") or "input:authority_matrix",
        "disclaimer": DISCLAIMER,
    }


def compute(doc: dict) -> dict:
    from validate_input import validate

    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    output = _calculate(doc)
    issues = [g["item"] + ": " + g["reason"] for g in output["completeness_gaps"]]
    output["artifact"] = build_artifact(
        doc,
        output,
        producer="claim-settlement-authority-request-builder",
        artifact_type="claim-settlement-authority-packet-review",
        completeness="partial" if issues else "complete",
        evaluability="partial" if issues else "evaluable",
        issues=issues,
    )
    return output


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claim_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
