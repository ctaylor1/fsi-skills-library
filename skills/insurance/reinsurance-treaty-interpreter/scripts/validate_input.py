#!/usr/bin/env python3
"""Deterministic input validation for reinsurance-treaty-interpreter.

Validates a single reinsurance treaty against the documented schema BEFORE interpreting it.
Fails closed on structural problems (missing required fields, bad dates, a clause without a
citation, a malformed excess-of-loss layer). Warns (does not fail) on data-quality gaps the
interpretation must surface (missing aggregate limit, unrecognized clause types, losses at or
below the attachment, losses without a date).

Input schema (JSON) — one treaty:
{
  "treaty_id": "str",
  "cedent": "str",
  "treaty_type": "excess_of_loss|quota_share|surplus|stop_loss|facultative|other",
  "uw_year": "str",
  "currency": "USD",
  "inception_date": "YYYY-MM-DD",           # optional; validated if present
  "expiry_date": "YYYY-MM-DD",              # optional; validated if present
  "layer": {                                # required for excess_of_loss
    "attachment": num, "limit": num,
    "reinstatements": int(opt), "aggregate_limit": num(opt),
    "reinstatement_terms": [{"premium_pct": num}](opt), "layer_premium": num(opt)
  },
  "clauses": [
    {"clause_id","clause_type","heading","text","source":{"system","ref"}}
  ],
  "losses": [                               # optional; drives the illustration
    {"occurrence_id","date","gross_loss","description","source":{"system","ref"}}
  ]
}

Usage:
  python validate_input.py treaty.json
  python validate_input.py --selftest        # validate the bundled fixture
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("treaty_id", "treaty_type", "currency", "clauses")
KNOWN_TREATY_TYPES = {
    "excess_of_loss", "quota_share", "surplus", "stop_loss", "facultative", "other",
}
KNOWN_CLAUSE_TYPES = {
    "attachment", "limit", "exclusion", "reinstatement", "reporting",
    "definition", "condition", "recoverability", "other",
}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing required field '{k}'")
    if errors:
        return errors, warnings

    if str(doc["treaty_type"]).lower() not in KNOWN_TREATY_TYPES:
        warnings.append(
            f"treaty_type {doc['treaty_type']!r} not recognized — interpret generically and "
            f"confirm the structure")

    # Dates are optional, but validated when present.
    inc, exp = doc.get("inception_date"), doc.get("expiry_date")
    for label, val in (("inception_date", inc), ("expiry_date", exp)):
        if val and not DATE_RE.match(str(val)):
            errors.append(f"{label} must be YYYY-MM-DD, got {val!r}")
    if inc and exp and DATE_RE.match(str(inc)) and DATE_RE.match(str(exp)):
        if str(exp) < str(inc):
            errors.append(f"expiry_date {exp} precedes inception_date {inc}")

    # Clauses: non-empty, each with a citation.
    clauses = doc.get("clauses") or []
    if not isinstance(clauses, list) or not clauses:
        errors.append("clauses must be a non-empty list")
        return errors, warnings
    for i, c in enumerate(clauses):
        tag = f"clauses[{i}] ({c.get('clause_id', '?')})"
        for k in ("clause_id", "clause_type", "text"):
            v = c.get(k)
            if v is None or (isinstance(v, str) and not v.strip()):
                errors.append(f"{tag}: missing '{k}'")
        src = c.get("source") or {}
        if not (src.get("system") and src.get("ref")):
            errors.append(f"{tag}: source must include 'system' and 'ref' (citation)")
        if str(c.get("clause_type", "")).lower() not in KNOWN_CLAUSE_TYPES:
            warnings.append(f"{tag}: clause_type {c.get('clause_type')!r} not recognized — classify as 'other'")

    # Layer: required and well-formed for excess-of-loss.
    if str(doc["treaty_type"]).lower() == "excess_of_loss":
        layer = doc.get("layer") or {}
        att = _num(layer.get("attachment"))
        lim = _num(layer.get("limit"))
        if att is None or att < 0:
            errors.append("layer.attachment must be a non-negative number for excess_of_loss")
        if lim is None or lim <= 0:
            errors.append("layer.limit must be a positive number for excess_of_loss")
        reins = layer.get("reinstatements")
        if reins is None:
            warnings.append("layer.reinstatements missing — assuming 0 (no reinstatement); confirm")
        elif not isinstance(reins, int) or reins < 0:
            errors.append(f"layer.reinstatements must be a non-negative integer, got {reins!r}")
        if layer.get("aggregate_limit") is None and lim is not None:
            r = reins if isinstance(reins, int) and reins >= 0 else 0
            warnings.append(
                f"layer.aggregate_limit missing — derivable as limit*(1+reinstatements) = {lim * (1 + r):.2f}")
        if reins and layer.get("layer_premium") is None:
            warnings.append(
                "reinstatements present but layer.layer_premium missing — reinstatement premium not computable")

    # Losses (optional): each occurrence well-formed; surface below-attachment lines.
    losses = doc.get("losses")
    if losses is not None:
        if not isinstance(losses, list):
            errors.append("losses must be a list when present")
        else:
            att = _num((doc.get("layer") or {}).get("attachment"))
            for i, ls in enumerate(losses):
                tag = f"losses[{i}] ({ls.get('occurrence_id', '?')})"
                if not (ls.get("occurrence_id") or ""):
                    errors.append(f"{tag}: missing 'occurrence_id'")
                gl = _num(ls.get("gross_loss"))
                if gl is None:
                    warnings.append(f"{tag}: non-numeric or missing gross_loss — excluded from illustration")
                elif att is not None and gl <= att:
                    warnings.append(
                        f"{tag}: gross_loss {gl:.0f} at or below attachment {att:.0f} — no layer recovery")
                if not ls.get("date"):
                    warnings.append(f"{tag}: no date — occurrence ordering/aggregation unconfirmed")

    return errors, warnings


def _report(errors, warnings) -> int:
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "treaty_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif len(argv) >= 1:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    return _report(*validate(doc))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
