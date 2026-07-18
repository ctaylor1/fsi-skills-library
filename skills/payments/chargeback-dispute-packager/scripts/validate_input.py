#!/usr/bin/env python3
"""Deterministic input validation for chargeback-dispute-packager.

Validates a chargeback/dispute intake file before a representment package is drafted. Fails
closed on structural problems (so a package is never assembled from an ill-formed record);
warns on data gaps that force an `insufficient-evidence` or `needs-data` disposition.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  ruleset_version, as_of_date, reason_code_catalog{} (optional override), disputes[
    {dispute_id, network, reason_code, chargeback_date, dispute_amount, currency,
     transaction{txn_id|arn, amount, currency, txn_date}, evidence[
       {exhibit_id, type, ref, txn_id?, arn?, amount?, date?}],
     prior_undisputed_txns[]?, narrative_points[{point, exhibit_id}]?}]

Usage: python validate_input.py disputes.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("ruleset_version", "disputes")
REQUIRED_DISPUTE = ("dispute_id", "network", "reason_code", "chargeback_date",
                    "dispute_amount", "currency", "transaction", "evidence")
KNOWN_REASON_CODES = {
    "VISA-10.4", "VISA-13.1", "VISA-13.3", "VISA-12.6", "MC-4853", "MC-4837",
}


def _is_iso_date(v) -> bool:
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

    if doc.get("as_of_date") and not _is_iso_date(doc.get("as_of_date")):
        errors.append("as_of_date is not an ISO date (YYYY-MM-DD)")
    if not doc.get("as_of_date"):
        warnings.append("no as_of_date -> deadline computed against the system date")

    disputes = doc.get("disputes") or []
    if not isinstance(disputes, list) or not disputes:
        errors.append("disputes must be a non-empty list")
        return errors, warnings

    catalog = doc.get("reason_code_catalog") or {}
    known = KNOWN_REASON_CODES | set(catalog.keys())

    ids = set()
    for i, d in enumerate(disputes):
        tag = f"disputes[{i}] ({d.get('dispute_id','?')})"
        for k in REQUIRED_DISPUTE:
            if k not in d or d[k] in (None, "", [], {}):
                errors.append(f"{tag}: missing '{k}'")
        did = d.get("dispute_id")
        if did in ids:
            errors.append(f"{tag}: duplicate dispute_id")
        ids.add(did)

        if d.get("chargeback_date") and not _is_iso_date(d.get("chargeback_date")):
            errors.append(f"{tag}: chargeback_date is not an ISO date")

        txn = d.get("transaction") or {}
        if isinstance(txn, dict):
            if not (txn.get("txn_id") or txn.get("arn")):
                errors.append(f"{tag}: transaction needs a txn_id or arn to establish identity")
            for k in ("amount", "currency", "txn_date"):
                if txn.get(k) in (None, ""):
                    errors.append(f"{tag}: transaction missing '{k}'")
        else:
            errors.append(f"{tag}: transaction must be an object")

        ev = d.get("evidence")
        if not isinstance(ev, list) or not ev:
            errors.append(f"{tag}: evidence must be a non-empty list")
            ev = []
        exhibit_ids = set()
        for j, e in enumerate(ev):
            if not e.get("exhibit_id") or not e.get("type"):
                errors.append(f"{tag}: evidence[{j}] needs exhibit_id and type")
            exhibit_ids.add(e.get("exhibit_id"))

        if d.get("reason_code") and d.get("reason_code") not in known:
            warnings.append(f"{tag}: reason_code {d.get('reason_code')!r} not in known catalog -> map it or set needs-data")

        for np in d.get("narrative_points") or []:
            if np.get("exhibit_id") not in exhibit_ids:
                warnings.append(f"{tag}: narrative point cites exhibit {np.get('exhibit_id')!r} not in evidence -> unsupported claim")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "disputes_example.json"
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
