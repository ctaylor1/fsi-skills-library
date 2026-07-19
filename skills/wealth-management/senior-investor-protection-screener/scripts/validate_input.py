#!/usr/bin/env python3
"""Deterministic input validation for senior-investor-protection-screener.

Validates a senior-investor case file before concern-signal computation. Fails closed on
structural problems; warns on data-quality gaps that limit which signals are evaluable.
This is a READ-ONLY screen: it never decides, holds, reports, or contacts anyone.

Input schema (JSON): see references/source-map.md. Key fields:
  client_id, as_of (YYYY-MM-DD), config_version, lookback_days, focal_txn_ids[],
  client{age,impairment_flag}, trusted_contact{on_file,last_confirmed},
  observations{...structured booleans supplied by a trained human...},
  recent_changes[{type,date,source_ref}],
  transactions[{txn_id,date,amount,direction,channel,counterparty,country,source_ref}],
  config{...thresholds...}

Usage:
  python validate_input.py case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("client_id", "as_of", "config_version", "focal_txn_ids", "transactions")
REQUIRED_TXN = ("txn_id", "date", "amount", "direction", "source_ref")
BEHAVIORAL_FLAGS = (
    "third_party_present", "new_caregiver_or_poa", "unusual_urgency", "requests_secrecy",
    "refuses_family_involvement", "scam_narrative_flag", "confusion_observed",
    "cannot_recall_transaction", "repeated_questions",
)


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

    txns = doc.get("transactions") or []
    if not isinstance(txns, list) or not txns:
        errors.append("transactions must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, t in enumerate(txns):
        tag = f"transactions[{i}] ({t.get('txn_id','?')})"
        for k in REQUIRED_TXN:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(t.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        if t.get("direction") not in ("debit", "credit"):
            errors.append(f"{tag}: direction must be 'debit' or 'credit'")
        tid = t.get("txn_id")
        if tid in ids:
            errors.append(f"{tag}: duplicate txn_id")
        ids.add(tid)
        if not t.get("counterparty"):
            warnings.append(f"{tag}: no counterparty — new_external_payee not evaluable for this row")

    if not isinstance(doc["focal_txn_ids"], list) or not doc["focal_txn_ids"]:
        errors.append("focal_txn_ids must be a non-empty list")
    else:
        for fid in doc["focal_txn_ids"]:
            if fid not in ids:
                errors.append(f"focal_txn_ids references unknown txn_id {fid!r}")

    # Data-quality warnings (limit which concern signals are evaluable, never fail closed)
    client = doc.get("client") or {}
    if _num(client.get("age")) is None and not client.get("impairment_flag"):
        warnings.append("no client age or impairment_flag — specified-adult status not evaluable")
    if "trusted_contact" not in doc:
        warnings.append("no 'trusted_contact' block — trusted_contact_gap treated as a gap by default")
    obs = doc.get("observations")
    if not obs:
        warnings.append("no 'observations' block — behavioral signals (third-party, capacity, communication) not evaluable")
    else:
        for f in BEHAVIORAL_FLAGS:
            if f in obs and not isinstance(obs[f], bool):
                errors.append(f"observations['{f}'] must be a boolean, got {type(obs[f]).__name__}")
    baseline_n = len([t for t in txns if t.get("txn_id") not in set(doc["focal_txn_ids"]) and t.get("direction") == "debit"])
    if baseline_n < 10:
        warnings.append(f"thin baseline ({baseline_n} non-focal debits) — unusual_disbursement is low-confidence")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_example.json"
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
