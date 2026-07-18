#!/usr/bin/env python3
"""Deterministic input validation for subrogation-opportunity-screener.

Validates a claim file before recovery-signal computation. Fails closed on structural problems;
warns on data-quality gaps that limit which signals are evaluable (notably a missing limitation
date, which must be resolved before any reliance on the screen).

Input schema (JSON): see references/source-map.md. Key fields:
  claim_id, as_of (YYYY-MM-DD), config_version, line_of_business, paid_to_date,
  recovery_deductible, net_incurred, limitation_date (YYYY-MM-DD|null), waiver_of_subrogation,
  prior_recovery{status,amount_recovered},
  liability{indicated, basis, responsible_parties[{party_id,name,role,liability_pct,insurer,insured,assets_known,source_ref}]},
  evidence[{type,present,source_ref}], config{...thresholds...}

Usage:
  python validate_input.py claim.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("claim_id", "as_of", "config_version", "line_of_business", "paid_to_date")


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
        errors.append(f"as_of must be YYYY-MM-DD, got {doc['as_of']!r}")
    if _num(doc.get("paid_to_date")) is None:
        errors.append("paid_to_date not numeric")
    if "recovery_deductible" in doc and _num(doc.get("recovery_deductible")) is None:
        errors.append("recovery_deductible not numeric")

    lim = doc.get("limitation_date")
    if lim in (None, ""):
        warnings.append("no limitation_date on file — limitation_window_open is NOT evaluable; "
                        "resolve the controlling date before relying on the screen")
    elif not DATE_RE.match(str(lim)):
        errors.append(f"limitation_date must be YYYY-MM-DD, got {lim!r}")

    liab = doc.get("liability") or {}
    parties = liab.get("responsible_parties") or []
    if not isinstance(parties, list):
        errors.append("liability.responsible_parties must be a list")
        parties = []
    if not parties:
        warnings.append("no responsible_parties — liability and collectibility signals not evaluable")
    seen = set()
    for i, p in enumerate(parties):
        tag = f"responsible_parties[{i}] ({p.get('party_id','?')})"
        if _num(p.get("liability_pct")) is None:
            errors.append(f"{tag}: liability_pct not numeric")
        pid = p.get("party_id")
        if pid in seen:
            errors.append(f"{tag}: duplicate party_id")
        seen.add(pid)
        if not p.get("source_ref"):
            warnings.append(f"{tag}: no source_ref — evidence citation will be weak")
        if not (p.get("insured") or p.get("assets_known")):
            warnings.append(f"{tag}: collectibility unknown (not insured / no known assets)")

    evidence = doc.get("evidence")
    if not evidence:
        warnings.append("no evidence inventory — supporting_evidence_present not evaluable")
    else:
        for i, e in enumerate(evidence):
            if "type" not in e or "present" not in e:
                errors.append(f"evidence[{i}]: requires 'type' and 'present'")

    if doc.get("waiver_of_subrogation"):
        warnings.append("waiver_of_subrogation is true — recovery is likely unavailable (expect No-Action)")
    prior = (doc.get("prior_recovery") or {}).get("status")
    if prior and prior != "none":
        warnings.append(f"prior_recovery.status={prior!r} — recovery may already be pursued/closed (avoid duplicate referral)")
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
