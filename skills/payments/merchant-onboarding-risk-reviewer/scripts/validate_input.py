#!/usr/bin/env python3
"""Deterministic input validation for merchant-onboarding-risk-reviewer.

Validates a merchant onboarding application file before risk-finding computation. Fails
closed on structural problems; warns on data-quality gaps that make individual findings
not evaluable (so the reviewer sees exactly which risk dimensions the data cannot support).

Input schema (JSON): see references/source-map.md. Key fields:
  case_id, as_of (YYYY-MM-DD), config_version,
  merchant{legal_name,country,mcc,business_model,website,expected_monthly_volume,
           expected_avg_ticket,requested_processing_limit},
  beneficial_owners[{name,ownership_pct,country,verified,pep,source_ref}],
  screening{sanctions{status,source_ref}, adverse_media{status,categories,source_ref}},
  credit{assessment,source_ref},
  evidence{kyb_registration,ubo_verification,website_review,expected_activity,financials},
  config{...thresholds and lists...}

Usage:
  python validate_input.py application.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("case_id", "as_of", "config_version", "merchant", "beneficial_owners",
                "screening", "evidence")
REQUIRED_MERCHANT = ("legal_name", "country", "mcc", "business_model",
                     "expected_monthly_volume")
REQUIRED_OWNER = ("name", "ownership_pct", "country", "verified")
SANCTIONS_STATUS = {"cleared", "hit", "pending"}
ADVERSE_STATUS = {"none", "resolved", "unresolved"}
REQUIRED_EVIDENCE = ("kyb_registration", "ubo_verification", "website_review",
                     "expected_activity", "financials")


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

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    m = doc.get("merchant") or {}
    if not isinstance(m, dict):
        errors.append("merchant must be an object")
        return errors, warnings
    for k in REQUIRED_MERCHANT:
        if k not in m or m[k] in (None, ""):
            errors.append(f"merchant: missing '{k}'")
    if _num(m.get("expected_monthly_volume")) is None:
        errors.append("merchant.expected_monthly_volume not numeric")
    if not m.get("website"):
        warnings.append("merchant.website missing — website_product_risk not evaluable")
    if _num(m.get("requested_processing_limit")) is None:
        warnings.append("merchant.requested_processing_limit missing/non-numeric — credit_exposure not evaluable")

    owners = doc.get("beneficial_owners")
    if not isinstance(owners, list) or not owners:
        errors.append("beneficial_owners must be a non-empty list")
    else:
        pct_sum = 0.0
        for i, o in enumerate(owners):
            tag = f"beneficial_owners[{i}] ({o.get('name','?')})"
            for k in REQUIRED_OWNER:
                if k not in o or o[k] in (None, ""):
                    errors.append(f"{tag}: missing '{k}'")
            p = _num(o.get("ownership_pct"))
            if p is None:
                errors.append(f"{tag}: ownership_pct not numeric")
            else:
                pct_sum += p
            if "verified" in o and not isinstance(o.get("verified"), bool):
                errors.append(f"{tag}: verified must be true/false")
        if pct_sum and abs(pct_sum - 100.0) > 0.01:
            warnings.append(f"beneficial_owners ownership_pct sums to {pct_sum:g} (not 100) — coverage may be incomplete")

    scr = doc.get("screening") or {}
    sanc = (scr.get("sanctions") or {})
    if sanc.get("status") not in SANCTIONS_STATUS:
        errors.append(f"screening.sanctions.status must be one of {sorted(SANCTIONS_STATUS)}")
    am = (scr.get("adverse_media") or {})
    if am.get("status") not in ADVERSE_STATUS:
        warnings.append(f"screening.adverse_media.status not in {sorted(ADVERSE_STATUS)} — adverse_media not evaluable")

    if not (doc.get("credit") or {}).get("assessment"):
        warnings.append("no credit.assessment — credit_exposure treated as not_assessed")

    ev = doc.get("evidence") or {}
    for k in REQUIRED_EVIDENCE:
        if not ev.get(k):
            warnings.append(f"evidence.{k} missing — counts toward evidence_incomplete finding")

    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds/lists will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "application_example.json"
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
