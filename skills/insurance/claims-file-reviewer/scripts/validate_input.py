#!/usr/bin/env python3
"""Deterministic input validation for claims-file-reviewer.

Validates a claim-file JSON before review computation. Fails closed on structural problems
(missing identifiers, malformed dates, non-numeric money); warns on data-quality gaps that
limit which review checks are evaluable. It never renders a coverage or reserve opinion —
those gaps become *findings* in calculate_or_transform.py, not input errors here.

Input schema (JSON): see references/source-map.md. Key fields:
  claim_id, as_of (YYYY-MM-DD), config_version, claim_type, loss_date, report_date,
  policy{policy_number, effective_date, expiration_date, coverages[{code,limit,deductible,citation}], endorsements[]},
  documents[{doc_id,type,date,source_ref}], events[{date,type,description,source_ref}],
  reserves[{category,amount,supporting_ref,source_ref}],
  payments[{payment_id,amount,date,authority_ref,supporting_ref,source_ref}],
  decisions[{decision_id,type,rationale,authority_ref,source_ref}], config{...}

Usage:
  python validate_input.py claim.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("claim_id", "as_of", "config_version", "claim_type",
                "loss_date", "report_date", "policy")
DATE_FIELDS = ("as_of", "loss_date", "report_date")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    for f in DATE_FIELDS:
        if not DATE_RE.match(str(doc.get(f, ""))):
            errors.append(f"{f} must start YYYY-MM-DD, got {doc.get(f)!r}")

    pol = doc.get("policy") or {}
    if not isinstance(pol, dict):
        errors.append("policy must be an object")
        return errors, warnings
    for k in ("effective_date", "expiration_date"):
        if not DATE_RE.match(str(pol.get(k, ""))):
            errors.append(f"policy.{k} must start YYYY-MM-DD, got {pol.get(k)!r}")
    covs = pol.get("coverages")
    if not isinstance(covs, list) or not covs:
        errors.append("policy.coverages must be a non-empty list")
    else:
        seen = set()
        for i, c in enumerate(covs):
            if not c.get("code"):
                errors.append(f"policy.coverages[{i}]: missing 'code'")
            elif c["code"] in seen:
                errors.append(f"policy.coverages[{i}]: duplicate code {c['code']!r}")
            seen.add(c.get("code"))
            if not (c.get("citation") or "").strip():
                warnings.append(f"coverage {c.get('code','?')} has no citation — coverage_citation_missing will fire")

    # optional collections: validate structure when present
    docs = doc.get("documents") or []
    if not docs:
        warnings.append("no documents — missing-document detection limited to the required-set check")
    for i, d in enumerate(docs):
        for k in ("doc_id", "type", "date", "source_ref"):
            if not d.get(k):
                errors.append(f"documents[{i}] ({d.get('doc_id','?')}): missing '{k}'")

    for i, p in enumerate(doc.get("payments") or []):
        tag = f"payments[{i}] ({p.get('payment_id','?')})"
        for k in ("payment_id", "date", "source_ref"):
            if not p.get(k):
                errors.append(f"{tag}: missing '{k}'")
        if _num(p.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        if not p.get("authority_ref"):
            warnings.append(f"{tag}: no authority_ref — payment_authority_missing will fire")

    for i, r in enumerate(doc.get("reserves") or []):
        tag = f"reserves[{i}]"
        if r.get("category") not in ("indemnity", "expense"):
            errors.append(f"{tag}: category must be 'indemnity' or 'expense', got {r.get('category')!r}")
        if _num(r.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        if not r.get("source_ref"):
            errors.append(f"{tag}: missing 'source_ref'")

    for i, d in enumerate(doc.get("decisions") or []):
        tag = f"decisions[{i}] ({d.get('decision_id','?')})"
        for k in ("decision_id", "type", "source_ref"):
            if not d.get(k):
                errors.append(f"{tag}: missing '{k}'")

    for i, e in enumerate(doc.get("events") or []):
        if not DATE_RE.match(str(e.get("date", ""))):
            errors.append(f"events[{i}]: date must start YYYY-MM-DD, got {e.get('date')!r}")
        if not e.get("type"):
            errors.append(f"events[{i}]: missing 'type'")

    cfg = doc.get("config") or {}
    req = (cfg.get("required_documents") or {})
    if doc.get("claim_type") not in req and "default" not in req:
        warnings.append(f"claim_type {doc.get('claim_type')!r} not in config.required_documents and no 'default' — required-doc check will be skipped")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claim_example.json"
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
