#!/usr/bin/env python3
"""Deterministic input validation for phishing-and-bec-investigator.

Validates a reported-message bundle before investigation. Fails closed on structural
problems; warns on data gaps that force a `needs-data` disposition (so an analyst is never
handed an investigation that silently guessed missing header/authentication evidence).

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, known_domains[], impersonation_watchlist[], vendor_bank_registry[],
  open_cases[], reports[
    {report_id, reported_by, reported_at, source_ref,
     message{message_id, received_at, from_display, from_addr, reply_to, subject,
             recipients[], auth_results{spf,dkim,dmarc}, urls[{display,href}],
             attachments[{name,type}]},
     payment_request{requested, type, amount, currency, beneficiary_account, vendor,
                     vendor_bank_change},
     behavior{first_contact_external, urgency, requests_secrecy},
     related_report_ids[]}]

Usage: python validate_input.py reports.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "reports")
REQUIRED_REPORT = ("report_id", "reported_by", "source_ref", "message")
AUTH_KEYS = ("spf", "dkim", "dmarc")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    reports = doc.get("reports") or []
    if not isinstance(reports, list) or not reports:
        errors.append("reports must be a non-empty list")
        return errors, warnings

    if not doc.get("known_domains"):
        warnings.append("no known_domains provided -> lookalike/impersonation detection limited")
    if doc.get("open_cases") is None:
        warnings.append("no open_cases provided -> duplicate detection limited")

    ids = set()
    for i, r in enumerate(reports):
        tag = f"reports[{i}] ({r.get('report_id','?')})"
        for k in REQUIRED_REPORT:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        rid = r.get("report_id")
        if rid in ids:
            errors.append(f"{tag}: duplicate report_id")
        ids.add(rid)

        msg = r.get("message") or {}
        if not isinstance(msg, dict):
            errors.append(f"{tag}: message must be an object")
            continue
        if not msg.get("from_addr"):
            errors.append(f"{tag}: message.from_addr is required")
        elif "@" not in str(msg.get("from_addr")):
            errors.append(f"{tag}: message.from_addr is not an email address")

        auth = msg.get("auth_results")
        if not isinstance(auth, dict) or not all(auth.get(k) for k in AUTH_KEYS):
            warnings.append(f"{tag}: message.auth_results missing SPF/DKIM/DMARC -> needs-data")
        if not msg.get("received_at"):
            warnings.append(f"{tag}: message.received_at missing -> chronology will be incomplete")

        pay = r.get("payment_request") or {}
        if pay.get("requested"):
            if pay.get("amount") in (None, ""):
                warnings.append(f"{tag}: payment_request.requested but no amount -> BEC amount evidence incomplete")
            if pay.get("vendor_bank_change") and not pay.get("vendor"):
                warnings.append(f"{tag}: vendor_bank_change without vendor -> cannot check vendor bank registry")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reports_example.json"
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
