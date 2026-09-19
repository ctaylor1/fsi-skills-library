#!/usr/bin/env python3
"""Interpret supported normalized ISO transaction/status profiles; classify other families only.
No XML, XSD, live code-set or scheme validator is implemented. No payment actions."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from decimal import Decimal
from payment_contract import money, stable_hash
from validate_input import validate as validate_input, profile

UUID4_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
BIC_RE = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")
IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$")
PERMITTED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/-?:().,'+ \n\r")
MT_NARR_LINE = 140

DISCLAIMER = ("Interpretation and explanation only; not a payment instruction, repair "
              "authorization, or compliance/fraud determination.")

FAMILY_DESC = {
    "pain": "Payments Initiation (customer-to-bank)",
    "pacs": "Payments Clearing and Settlement (FI-to-FI)",
    "camt": "Cash Management (reporting, notifications, exceptions)",
}
MESSAGE_NAMES = {
    "pain.001": "Customer Credit Transfer Initiation",
    "pain.002": "Customer Payment Status Report",
    "pain.007": "Customer Payment Reversal",
    "pain.008": "Customer Direct Debit Initiation",
    "pacs.002": "FI To FI Payment Status Report",
    "pacs.003": "FI To FI Customer Direct Debit",
    "pacs.004": "Payment Return",
    "pacs.007": "FI To FI Payment Reversal",
    "pacs.008": "FI To FI Customer Credit Transfer",
    "pacs.009": "Financial Institution Credit Transfer",
    "pacs.028": "FI To FI Payment Status Request",
    "camt.029": "Resolution Of Investigation",
    "camt.052": "Bank To Customer Account Report (intraday)",
    "camt.053": "Bank To Customer Statement (end-of-day)",
    "camt.054": "Bank To Customer Debit/Credit Notification",
    "camt.055": "Customer Payment Cancellation Request",
    "camt.056": "FI To FI Payment Cancellation Request",
    "camt.060": "Account Reporting Request",
    "camt.087": "Request To Modify Payment",
    "camt.110": "Investigation Request",
    "camt.111": "Investigation Response",
    "admi.024": "Notification Of Correspondence",
}
# ExternalPaymentTransactionStatus / group status -> (category, plain-language)
STATUS = {
    "ACSC": ("accepted", "Accepted Settlement Completed — settlement completion is reported; side and finality depend on the applicable message and scheme."),
    "ACCC": ("accepted", "Accepted Settlement Completed on the creditor account."),
    "ACSP": ("accepted", "Accepted Settlement In Process — accepted; settlement is in progress."),
    "ACCP": ("accepted", "Accepted Customer Profile — preceding format/customer checks passed."),
    "ACTC": ("accepted", "Accepted Technical Validation — syntax/authentication checks passed."),
    "ACWP": ("accepted", "Accepted Without Posting — accepted, not yet posted to the creditor account."),
    "ACWC": ("accepted-with-change", "Accepted With Change — accepted after a modification was applied."),
    "PDNG": ("pending", "Pending — not yet processed; awaiting action or further information."),
    "RCVD": ("received", "Received — the message was received but not yet processed."),
    "PART": ("partial", "Partially Accepted — inspect each transaction's own status."),
    "RJCT": ("rejected", "Rejected — the message reports the payment as rejected; a reason code should accompany it."),
}
# ExternalStatusReason / return-reason subset -> plain-language
REASON = {
    "AC01": "Incorrect Account Number — the account number is invalid or malformed.",
    "AC02": "Invalid Debtor Account Number.",
    "AC03": "Invalid Creditor Account Number.",
    "AC04": "Closed Account Number — the account is reported closed.",
    "AC06": "Blocked Account — the account is blocked for this transaction.",
    "AG01": "Transaction Forbidden on this account type.",
    "AG02": "Invalid Bank Operation / message code.",
    "AM04": "Insufficient Funds on the debtor account.",
    "AM05": "Duplication — suspected duplicate submission.",
    "BE01": "Inconsistent With End Customer — name and account do not correspond.",
    "BE04": "Missing or incorrect Creditor address.",
    "BE05": "Unrecognised Initiating Party.",
    "CH03": "Requested execution/value date too far in the future.",
    "CUST": "Requested By Customer.",
    "DT01": "Invalid Date.",
    "DUPL": "Duplicate Payment.",
    "FF01": "Invalid File Format / syntax.",
    "FRAD": "Fraudulent-origin reason asserted by a party in the message (a claim carried in the "
            "data, not a determination made here).",
    "MS02": "Reason not specified — customer generated.",
    "MS03": "Reason not specified — agent generated.",
    "NARR": "Narrative — see the accompanying free-text reason.",
    "RC01": "Bank Identifier Incorrect (e.g., invalid BIC / routing id).",
    "RR01": "Missing debtor account or identification (regulatory).",
    "RR02": "Missing debtor name or address (regulatory).",
    "RR03": "Missing creditor name or address (regulatory).",
    "RR04": "Regulatory reason.",
    "TM01": "Cut-Off Time — received after the processing cut-off.",
}


def _cite(record):
    source = record.get("source") or {}
    return f"{source.get('system', '?')}:{source.get('ref', '?')}"


def iban_ok(account):
    account = re.sub(r"\s+", "", str(account)).upper()
    if not IBAN_RE.fullmatch(account): return False
    digits = "".join(str(ord(c) - 55) if c.isalpha() else c for c in account[4:] + account[:4])
    return int(digits) % 97 == 1


def status_interpretation(status):
    code = str(status.get("code", "")).upper()
    category, plain = STATUS.get(code, ("unknown", "Unmapped status; applicable scheme documentation is required."))
    reason = str(status.get("reason_code", "")).upper()
    return {"code": code, "category": category, "plain": plain,
            "reason_code": reason or None, "reason_plain": REASON.get(reason),
            "reason_text": status.get("reason_text"),
            "codeset_scope": "bundled representative ISO meanings; not scheme/version validation"}


def interpret(doc):
    errors, warnings = validate_input(doc)
    if errors: raise ValueError("; ".join(errors))
    mt = doc["message_type"]
    short, family = ".".join(mt.split(".")[:2]), mt.split(".")[0]
    mode = profile(mt)
    result = {"source_message": doc, "source_hash": stable_hash(doc), "input_format": "normalized-json",
              "interpretation_mode": mode, "schema_validated": False, "scheme_validated": False,
              "message_type": mt, "message_family": family,
              "message_name": MESSAGE_NAMES.get(short, "Unmapped ISO 20022 message") + f" ({short})",
              "usage_guideline": doc.get("usage_guideline"), "transactions": [], "findings": [],
              "summary": {"nb_of_txs": None, "total_amount": None, "currency_totals": {},
                          "currencies": [], "raw_control_sum": None, "control_totals_balanced": None,
                          "control_totals_status": "not_evaluated"},
              "limitations": warnings + ["No raw XML, XSD, live external code-set, account ownership, directory, or scheme validation is implemented."],
              "disclaimer": DISCLAIMER}
    if mode == "classification_only":
        result["findings"].append({"severity": "info", "code": "CLASSIFICATION_ONLY", "citation": _cite(doc),
                                   "message": "Message family identified only; structured interpretation for this family is not implemented."})
        result["narrative"] = f"{result['message_name']}: classification only. No payment, balance, or finality assertion is made. " + DISCLAIMER
        return result
    findings = result["findings"]
    totals = {}
    amount_count = 0
    txs = doc.get("transactions", [])
    mapping = doc.get("mapping_profile") or {}
    for tx in txs:
        citation = _cite(tx)
        out = {"end_to_end_id": tx.get("end_to_end_id"), "uetr": tx.get("uetr"), "citation": citation, "amount": None}
        if tx.get("amount") is not None:
            amount = tx["amount"]
            value = money(amount["value"])
            out["amount"] = {"value": str(value), "currency": amount["currency"]}
            totals[amount["currency"]] = totals.get(amount["currency"], Decimal(0)) + value
            amount_count += 1
        if tx.get("uetr") and not UUID4_RE.fullmatch(str(tx["uetr"])):
            findings.append({"severity": "high", "code": "UETR_INVALID", "message": "UETR is not UUIDv4 shaped.", "citation": citation})
        for role in ("debtor_agent", "creditor_agent"):
            bic = (tx.get(role) or {}).get("bic")
            if bic and not BIC_RE.fullmatch(str(bic)):
                findings.append({"severity": "high", "code": "BIC_INVALID", "message": f"{role} BIC fails the 8/11-character shape check.", "citation": citation})
        for role in ("debtor", "creditor"):
            account = (tx.get(role) or {}).get("account")
            if account and re.match(r"^[A-Z]{2}\d{2}", str(account)) and not iban_ok(account):
                findings.append({"severity": "high", "code": "IBAN_INVALID", "message": f"{role} IBAN fails its check digit.", "citation": citation})
        for line in (tx.get("remittance_info") or {}).get("unstructured", []):
            limit = mapping.get("max_remittance_length")
            if limit is not None and len(str(line)) > limit:
                findings.append({"severity": "medium", "code": "TRUNCATION_RISK", "citation": citation,
                    "message": f"Remittance exceeds supplied mapping limit {limit}; loss depends on mapping behavior.", "mapping_source": mapping["source_ref"]})
            if mapping.get("charset") == "SWIFT-X" and any(c not in PERMITTED for c in str(line)):
                findings.append({"severity": "medium", "code": "CHARSET_RISK", "citation": citation,
                    "message": "Characters fall outside the supplied SWIFT-X mapping profile.", "mapping_source": mapping["source_ref"]})
        if tx.get("status"):
            out["status_interpretation"] = status_interpretation(tx["status"])
            si = out["status_interpretation"]
            if si["category"] == "rejected":
                findings.append({"severity": "high", "code": "STATUS_REJECTED" if si["reason_code"] or si["reason_text"] else "REJECT_NO_REASON",
                    "message": f"Reported {si['code']} (rejected). {si['reason_plain'] or si['reason_text'] or 'Reason unknown.'}", "citation": citation})
        result["transactions"].append(out)
    if doc.get("group_status"):
        result["group_status_interpretation"] = status_interpretation(doc["group_status"])
    header = doc["group_header"]
    count, control = header.get("nb_of_txs"), header.get("ctrl_sum")
    complete_amounts = bool(txs) and amount_count == len(txs)
    raw_sum = sum(totals.values(), Decimal(0)) if complete_amounts else None
    checks = []
    if count is not None: checks.append(int(count) == len(txs))
    if control is not None and raw_sum is not None: checks.append(money(control) == raw_sum)
    unavailable = control is not None and raw_sum is None
    balance = None if not checks or unavailable else all(checks)
    if balance is False:
        findings.append({"severity": "high", "code": "CONTROL_TOTAL_MISMATCH", "message": "Declared control totals differ from normalized records.", "citation": header["msg_id"]})
    if unavailable:
        findings.append({"severity": "info", "code": "CONTROL_TOTAL_UNRESOLVED", "message": "Declared sum cannot be evaluated because amounts are absent.", "citation": header["msg_id"]})
    result["summary"] = {"nb_of_txs": len(txs), "currency_totals": {k: str(v) for k, v in sorted(totals.items())},
        "total_amount": str(raw_sum) if complete_amounts and len(totals) == 1 else None,
        "currencies": sorted(totals), "raw_control_sum": str(raw_sum) if raw_sum is not None else None,
        "control_totals_balanced": balance, "control_totals_status": "not_evaluated" if balance is None else ("balanced" if balance else "mismatch")}
    result["narrative"] = (f"{result['message_name']}: {len(txs)} normalized record(s). "
        f"Control-total assessment: {result['summary']['control_totals_status']}. "
        "Amounts are partitioned by currency; absent status-report amounts remain unknown. "
        "Message statuses describe reports and do not independently establish legal finality. " + DISCLAIMER)
    return result


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/pacs008_message.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
    try:
        doc = json.loads(path.read_text() if path else sys.stdin.read())
        result = interpret(doc)
    except (ValueError, TypeError) as exc:
        print("ERROR", exc); return 1
    if "--selftest" in argv:
        from validate_output import validate
        errors = validate(result)
        for error in errors: print("ERROR", error)
        print(f"transform selftest: {len(errors)} error(s)")
        return bool(errors)
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
