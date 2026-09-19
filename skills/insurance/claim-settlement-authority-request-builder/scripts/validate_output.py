#!/usr/bin/env python3
"""Deterministic output validation for claim-settlement-authority-request-builder.

Enforces the R3 guardrails before the request packet is presented:
  1. total_exposure == indemnity + expense (within tolerance).
  2. Every completeness gap carries a citation.
  3. suggested_disposition is review-only (packet-ready | gaps-for-review).
  4. No settlement-approval / authority-grant / payment-authorization language.
  5. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from insurance_contract import validate_artifact

ALLOWED = {"packet-ready", "gaps-for-review"}
DISCLAIMER_RE = re.compile(r"not a settlement approval", re.I)
PROHIBITED = [
    r"\bsettlement approved\b",
    r"\bauthority granted\b",
    r"\bwe approve the settlement\b",
    r"\bapproved to settle\b",
    r"\bauthoriz(e|ed) the payment\b",
    r"\bsettle at\b",
    r"\bwe grant authority\b",
    r"\bpay the claimant\b",
]
TOL = 0.05


def _validate(p: dict) -> list[str]:
    errors = []
    exp = p.get("exposure") or {}
    ind, ex, tot = exp.get("indemnity_estimate"), exp.get("expense_estimate"), exp.get("total_exposure")
    if None not in (ind, ex, tot) and abs((ind + ex) - tot) > TOL:
        errors.append(f"total_exposure {tot} != indemnity {ind} + expense {ex}")
    from insurance_contract import amount, iso_date

    basis = p.get("authority_basis") or {}
    matrix = basis.get("matrix") or {}
    usable = True
    try:
        ind_d, ex_d, tot_d = amount(ind), amount(ex), amount(tot)
        if min(ind_d, ex_d) < 0 or ind_d + ex_d != tot_d:
            raise ValueError("invalid exposure")
        if (
            not exp.get("currency")
            or exp["currency"] != matrix.get("currency")
            or not matrix.get("config_version")
            or not matrix.get("source_ref")
        ):
            raise ValueError("unknown matrix/currency")
        if (
            not iso_date(matrix.get("effective_from"))
            <= iso_date(basis.get("as_of"))
            <= iso_date(matrix.get("effective_to"))
        ):
            raise ValueError("ineffective matrix")
        tiers = matrix.get("tiers", [])
        caps = [amount(t.get("max_amount")) for t in tiers]
        if (
            not tiers
            or any(v < 0 for v in caps)
            or len(set(caps)) != len(caps)
            or len({t.get("tier") for t in tiers}) != len(tiers)
            or any(not t.get("tier") or not t.get("approver_role") for t in tiers)
        ):
            raise ValueError("invalid tier table")
    except (ValueError, TypeError):
        usable = False
    if basis.get("amount_matrix_valid") is not usable:
        errors.append("amount/matrix evaluability mismatch")
    selected = (
        next(
            (
                t
                for t in sorted(matrix.get("tiers", []), key=lambda t: amount(t["max_amount"]))
                if tot_d <= amount(t["max_amount"])
            ),
            None,
        )
        if usable
        else None
    )
    if p.get("required_authority_tier") != (selected or {}).get("tier") or p.get("required_approver") != (
        selected or {}
    ).get("approver_role"):
        errors.append("required tier/approver does not match independent matrix lookup")
    if p.get("exceeds_matrix") is not bool(usable and selected is None):
        errors.append("exceeds_matrix mismatch")
    if p.get("suggested_disposition") == "packet-ready":
        if (
            not usable
            or selected is None
            or p.get("completeness_gaps")
            or not basis.get("checklist")
            or any(not basis.get("available_items", {}).get(k) for k in basis.get("checklist", []))
        ):
            errors.append("packet readiness requires evaluable amounts/matrix and completed checklist")
    for g in p.get("completeness_gaps") or []:
        if not (g.get("citation") or "").strip():
            errors.append(f"gap {g.get('item', '?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = " ".join(str(p.get(k, "")) for k in ("narrative", "notes", "conclusion", "decision", "action"))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(
                f"approval/authority-grant/payment language detected: {m.group(0)!r} (R3 requests, approver decides)"
            )
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (request packet only / no settlement approved)")
    return errors


def validate(doc: dict, *args, **kwargs) -> list[str]:
    if not isinstance(doc, dict):
        return ["output must be an object"]
    try:
        errors = _validate(doc, *args, **kwargs)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        errors = ["malformed output: " + str(exc)]
    return errors + validate_artifact(doc.get("artifact"), output=doc)


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "packet_example.json"
        p = json.loads(pth.read_text(encoding="utf-8"))
    elif argv:
        p = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        p = json.loads(sys.stdin.read())
    errors = validate(p)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
