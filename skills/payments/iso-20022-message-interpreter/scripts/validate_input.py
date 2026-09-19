#!/usr/bin/env python3
"""Validate this package's normalized JSON adapter, not raw XML or an ISO XSD."""
from __future__ import annotations
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from payment_contract import money, require_currency

MSG_TYPE_RE = re.compile(r"^[a-z]{3,4}\.\d{3}\.\d{3}\.\d{2}$")
TRANSACTION_MESSAGES = {"pain.001", "pain.008", "pacs.003", "pacs.004", "pacs.007", "pacs.008", "pacs.009"}
STATUS_MESSAGES = {"pain.002", "pacs.002"}


def profile(message_type):
    short = ".".join(str(message_type).split(".")[:2])
    if short in TRANSACTION_MESSAGES: return "normalized_transactions"
    if short in STATUS_MESSAGES: return "normalized_status"
    return "classification_only"


def validate(doc):
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["input must be normalized JSON object; raw XML is not supported"], warnings
    if not MSG_TYPE_RE.fullmatch(str(doc.get("message_type", ""))):
        return ["message_type must be <family>.<NNN>.<VVV>.<NN>"], warnings
    mode = profile(doc["message_type"])
    if mode == "classification_only":
        source = doc.get("source") or {}
        if not isinstance(source, dict) or not source.get("system") or not source.get("ref"):
            errors.append("classification-only input requires source.system and source.ref")
        warnings.append("classification only: no implemented family-specific schema, balance, or business-rule validation")
        return errors, warnings
    header = doc.get("group_header")
    if not isinstance(header, dict) or not header.get("msg_id"):
        errors.append("normalized group_header.msg_id required")
    else:
        try: datetime.fromisoformat(str(header["cre_dt_tm"]).replace("Z", "+00:00"))
        except (KeyError, ValueError): errors.append("normalized group_header.cre_dt_tm must be an ISO datetime")
        nb = header.get("nb_of_txs")
        if nb is not None and (isinstance(nb, bool) or not re.fullmatch(r"[0-9]+", str(nb))):
            errors.append("group_header.nb_of_txs must be a nonnegative integer")
        if "ctrl_sum" in header:
            try: money(header["ctrl_sum"])
            except ValueError as exc: errors.append(f"ctrl_sum: {exc}")
    transactions = doc.get("transactions", [])
    if not isinstance(transactions, list):
        return errors + ["transactions must be a list"], warnings
    if mode == "normalized_transactions" and not transactions:
        errors.append("transaction message requires normalized transactions")
    if mode == "normalized_status" and not transactions and not isinstance(doc.get("group_status"), dict):
        errors.append("status report requires group_status or normalized transaction statuses")
    for i, tx in enumerate(transactions):
        if not isinstance(tx, dict):
            errors.append(f"transactions[{i}] must be an object"); continue
        source = tx.get("source") or {}
        if not isinstance(source, dict) or not source.get("system") or not source.get("ref"):
            errors.append(f"transactions[{i}] requires cited source.system/ref")
        if mode == "normalized_transactions" and not tx.get("end_to_end_id"):
            errors.append(f"transactions[{i}] end_to_end_id required by normalized transaction adapter")
        if mode == "normalized_status" and (not isinstance(tx.get("status"), dict) or not tx["status"].get("code")):
            errors.append(f"transactions[{i}] status.code required")
        amount = tx.get("amount")
        if amount is None and mode == "normalized_transactions":
            errors.append(f"transactions[{i}] amount required")
        elif amount is not None:
            try:
                if not isinstance(amount, dict): raise ValueError("amount must be an object")
                if money(amount.get("value")) < 0: raise ValueError("amount must be nonnegative")
                require_currency(amount.get("currency"))
            except ValueError as exc: errors.append(f"transactions[{i}]: {exc}")
        for key in ("status", "debtor", "creditor", "debtor_agent", "creditor_agent", "remittance_info"):
            if key in tx and not isinstance(tx[key], dict): errors.append(f"transactions[{i}].{key} must be an object")
    mapping = doc.get("mapping_profile")
    if mapping is not None:
        if not isinstance(mapping, dict) or not mapping.get("source_ref"):
            errors.append("mapping_profile must include source_ref")
        elif mapping.get("max_remittance_length") is not None:
            limit = mapping["max_remittance_length"]
            if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
                errors.append("mapping_profile.max_remittance_length must be a positive integer")
            elif any(len(str(line)) > limit for tx in transactions for line in (tx.get("remittance_info") or {}).get("unstructured", [])):
                warnings.append("truncation risk under the supplied mapping_profile")
    return errors, warnings


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/pacs008_message.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
    try: doc = json.loads(path.read_text() if path else sys.stdin.read())
    except json.JSONDecodeError:
        print("ERROR raw XML is unsupported; supply normalized JSON with source provenance"); return 1
    errors, warnings = validate(doc)
    for item in warnings: print("WARN", item)
    for item in errors: print("ERROR", item)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return bool(errors)

if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
