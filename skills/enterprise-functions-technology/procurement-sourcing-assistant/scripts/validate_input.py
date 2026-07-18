#!/usr/bin/env python3
"""Deterministic input validation for procurement-sourcing-assistant.

Validates a sourcing intake bundle before pack assembly. Fails closed on structural problems;
warns on data gaps that will surface as `needs-data` flags or open items (unscored criteria,
missing requirement owners, weights not summing to 100, missing response evidence).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version, sourcing_id, category, jurisdiction, as_of_date,
  required_sections[], required_approvals[], weight_total_expected,
  sponsor{sponsor_id, name, business_unit},
  requirements[{req_id, category, text, priority, owner, source_ref}],
  market_scan[{supplier_id, name, segment, source_ref}],
  evaluation_criteria[{criterion_id, name, weight, mandatory, source_ref}],
  rfp_content[{section_id, title, status, source_ref}],
  bidders[{bidder_id, name, scores{criterion_id: 0-10}, mandatory_met{criterion_id: bool},
           risk_flags[], response_ref}],
  approvals[{approval_id, type, approver_role, approver, status, date, source_ref}],
  risk_inputs[{risk_id, type, description, route, status, source_ref}]

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "sourcing_id", "as_of_date",
                "requirements", "evaluation_criteria", "bidders")
REQUIRED_REQUIREMENT = ("req_id", "text", "source_ref")
REQUIRED_CRITERION = ("criterion_id", "weight")
REQUIRED_BIDDER = ("bidder_id", "name")


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    # requirements
    reqs = doc.get("requirements")
    if not isinstance(reqs, list) or not reqs:
        errors.append("requirements must be a non-empty list")
        return errors, warnings
    req_ids = set()
    for i, r in enumerate(reqs):
        tag = f"requirements[{i}] ({r.get('req_id','?')})"
        for k in REQUIRED_REQUIREMENT:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        rid = r.get("req_id")
        if rid in req_ids:
            errors.append(f"{tag}: duplicate req_id")
        req_ids.add(rid)
        if not r.get("owner"):
            warnings.append(f"{tag}: no owner -> open item (missing-requirement-owner)")

    # evaluation criteria + weight total
    crits = doc.get("evaluation_criteria")
    if not isinstance(crits, list) or not crits:
        errors.append("evaluation_criteria must be a non-empty list")
        return errors, warnings
    crit_ids = []
    weight_total = 0.0
    for i, c in enumerate(crits):
        tag = f"evaluation_criteria[{i}] ({c.get('criterion_id','?')})"
        for k in REQUIRED_CRITERION:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if not _is_number(c.get("weight")):
            errors.append(f"{tag}: weight must be a number")
        else:
            weight_total += float(c["weight"])
        cid = c.get("criterion_id")
        if cid in crit_ids:
            errors.append(f"{tag}: duplicate criterion_id")
        crit_ids.append(cid)
    expected = doc.get("weight_total_expected", 100)
    if _is_number(expected) and abs(weight_total - float(expected)) > 1e-9:
        warnings.append(f"evaluation criteria weights sum to {weight_total:g}, expected "
                        f"{float(expected):g} -> scoring may be miscalibrated (flag)")

    # bidders
    bidders = doc.get("bidders")
    if not isinstance(bidders, list) or not bidders:
        errors.append("bidders must be a non-empty list")
        return errors, warnings
    bidder_ids = set()
    scored_crit = [c.get("criterion_id") for c in crits]
    for i, b in enumerate(bidders):
        tag = f"bidders[{i}] ({b.get('bidder_id','?')})"
        for k in REQUIRED_BIDDER:
            if k not in b or b[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        bid = b.get("bidder_id")
        if bid in bidder_ids:
            errors.append(f"{tag}: duplicate bidder_id")
        bidder_ids.add(bid)
        scores = b.get("scores") or {}
        if not isinstance(scores, dict):
            errors.append(f"{tag}: scores must be an object mapping criterion_id -> 0-10")
            continue
        for cid, val in scores.items():
            if not _is_number(val) or not (0 <= float(val) <= 10):
                errors.append(f"{tag}: score for {cid!r} must be a number 0-10, got {val!r}")
        missing = [cid for cid in scored_crit if cid not in scores]
        if missing:
            warnings.append(f"{tag}: missing score(s) for {missing} -> needs-data (unscored-criterion)")
        if not b.get("response_ref"):
            warnings.append(f"{tag}: no response_ref -> bidder scores will lack citable evidence")

    # market scan (optional)
    if not doc.get("market_scan"):
        warnings.append("no market_scan provided -> market-scan section will be empty")

    # approvals
    for i, a in enumerate(doc.get("approvals") or []):
        if not a.get("type") or not a.get("status"):
            errors.append(f"approvals[{i}]: requires 'type' and 'status'")
        if a.get("status") == "recorded" and not a.get("source_ref"):
            errors.append(f"approvals[{i}] ({a.get('type','?')}): recorded approval missing 'source_ref'")
    if not doc.get("required_approvals"):
        warnings.append("no required_approvals configured -> approval capture limited")
    if doc.get("approvals") is None:
        warnings.append("no approvals provided -> all required approvals will be outstanding")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "sourcing_intake_example.json"
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
