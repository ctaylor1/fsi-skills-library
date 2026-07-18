#!/usr/bin/env python3
"""Deterministic input validation for complaint-resolution-assistant.

Validates a complaints intake file before drafting. Fails closed on structural problems;
warns on data gaps that will force a `needs-data` / `needs-review` disposition rather than a
guessed outcome.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, redress_config{}, category_severity{}, standards_map{}, root_cause_map{},
  complaints[
    {complaint_id, product, category, channel, received_date, resolution_date,
     regulatory_reportable, customer{id, name_masked, vulnerability_flag},
     firm_error(bool|null), root_cause_code, di_severity, amount_claimed, goodwill_requested,
     events[{date, description, source_ref}],
     financial_loss_items[{description, amount, loss_date, source_ref}], source_ref}]

Usage: python validate_input.py complaints.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("config_version", "complaints")
REQUIRED_COMPLAINT = ("complaint_id", "product", "category", "received_date", "source_ref")
DI_BANDS = {"none", "low", "moderate", "substantial", "severe"}


def _is_date(v):
    try:
        date.fromisoformat(str(v))
        return True
    except Exception:
        return False


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    complaints = doc.get("complaints") or []
    if not isinstance(complaints, list) or not complaints:
        errors.append("complaints must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, c in enumerate(complaints):
        tag = f"complaints[{i}] ({c.get('complaint_id','?')})"
        for k in REQUIRED_COMPLAINT:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        cid = c.get("complaint_id")
        if cid in ids:
            errors.append(f"{tag}: duplicate complaint_id")
        ids.add(cid)

        if c.get("received_date") and not _is_date(c.get("received_date")):
            errors.append(f"{tag}: received_date not ISO yyyy-mm-dd")
        if not isinstance(c.get("customer") or {}, dict):
            errors.append(f"{tag}: customer must be an object")

        # data-gap warnings (drive needs-data / needs-review, not a hard fail)
        if "firm_error" not in c or c.get("firm_error") is None:
            warnings.append(f"{tag}: firm_error undetermined -> needs-review")
        if not c.get("events"):
            warnings.append(f"{tag}: no events -> chronology will be empty")
        di = c.get("di_severity")
        if di is not None and di not in DI_BANDS:
            warnings.append(f"{tag}: di_severity {di!r} not a known band -> treated as 'none'")

        items = c.get("financial_loss_items") or []
        for j, it in enumerate(items):
            if it.get("amount") is None or not it.get("loss_date"):
                warnings.append(f"{tag}: loss item[{j}] missing amount/loss_date -> needs-data")
            elif not _is_date(it.get("loss_date")):
                errors.append(f"{tag}: loss item[{j}] loss_date not ISO yyyy-mm-dd")
        if items and not c.get("resolution_date"):
            warnings.append(f"{tag}: financial loss present but no resolution_date -> interest cannot be computed (needs-data)")
        if (c.get("customer") or {}).get("vulnerability_flag"):
            warnings.append(f"{tag}: vulnerability indicator -> refer for accommodation review")

    if doc.get("standards_map") is None:
        warnings.append("no standards_map provided -> using engine defaults; confirm the approved standards pack at deployment")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "complaints_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
