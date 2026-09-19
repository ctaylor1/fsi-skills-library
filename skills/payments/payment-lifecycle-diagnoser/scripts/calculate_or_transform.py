#!/usr/bin/env python3
"""Deterministic payment-trace interpretation for payment-lifecycle-diagnoser.

Reads a payment-trace file (see validate_input.py), interprets each leg's status/reason code
against a bundled representative code set (ISO 8583 card, NACHA ACH, ISO 20022 pacs.002 status
reasons), locates the decisive leg and root-cause category, and maps that category to exactly
one suggested downstream route plus a retry-eligibility read. Emits a machine-readable
diagnosis core the SKILL wraps in a plain-language pack.

IMPORTANT: This produces an explainable *diagnosis and a routing suggestion* only. It never
repairs, resubmits, reverses, releases, cancels, refunds, or authorizes a payment, and never
makes a fraud/sanctions determination. The route/retry mapping is deterministic and
documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py trace.json | --selftest
Prints the diagnosis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from payment_contract import stable_hash
from pathlib import Path

DISCLAIMER = ("Diagnostic assessment only; not a payment instruction, repair, or "
              "fraud/sanctions determination. No payment has been modified, resubmitted, "
              "reversed, or released.")

SETTLED_STATUSES = {"ACCC", "SETTLED"}
# statuses that indicate the payment is still moving and carry no failure of their own
PROGRESS_STATUSES = {"RCVD", "ACTC", "ACCP", "ACSP", "PDNG", "PENDING", "IN_PROCESS"}
PENDING_STATUSES = {"PDNG", "PENDING", "ACSP", "IN_PROCESS"}

# Bundled representative code set: rail -> code -> (meaning, category). No external code-set loader is shipped; supplied version labels are metadata.
CODES = {
    "card": {  # ISO 8583 response codes
        "00": ("Authorization approved; clearing and settlement are not evidenced", "authorized"),
        "05": ("Do not honor", "authorization_decline"),
        "12": ("Invalid transaction", "format_reference_error"),
        "14": ("Invalid card number", "account_invalid"),
        "41": ("Lost card", "suspected_fraud"),
        "43": ("Stolen card", "suspected_fraud"),
        "51": ("Insufficient funds", "insufficient_funds"),
        "54": ("Expired card", "expired_or_restricted"),
        "57": ("Transaction not permitted to cardholder", "authorization_decline"),
        "59": ("Suspected fraud", "suspected_fraud"),
        "61": ("Exceeds withdrawal amount limit", "expired_or_restricted"),
        "62": ("Restricted card", "expired_or_restricted"),
        "63": ("Security violation", "screening_hold"),
        "65": ("Exceeds withdrawal frequency limit", "expired_or_restricted"),
        "91": ("Issuer or switch inoperative", "system_timeout"),
        "96": ("System malfunction", "system_timeout"),
    },
    "ach": {  # NACHA return codes
        "R01": ("Insufficient funds", "insufficient_funds"),
        "R02": ("Account closed", "account_invalid"),
        "R03": ("No account / unable to locate account", "account_invalid"),
        "R04": ("Invalid account number structure", "format_reference_error"),
        "R05": ("Unauthorized debit to consumer account", "unauthorized_return"),
        "R07": ("Authorization revoked by customer", "unauthorized_return"),
        "R08": ("Payment stopped", "unauthorized_return"),
        "R10": ("Customer advises originator not authorized", "unauthorized_return"),
        "R16": ("Account frozen / blocked", "screening_hold"),
        "R20": ("Non-transaction account", "account_invalid"),
        "R29": ("Corporate customer advises not authorized", "unauthorized_return"),
    },
    "iso20022": {  # pacs.002 status reason external codes (+ settled statuses)
        "ACSC": ("Settlement-completed status reported; inspect settlement side and scheme evidence", "settlement_reported"),
        "ACCC": ("Creditor-account completion reported; inspect source settlement evidence", "settlement_reported"),
        "AC01": ("Incorrect account number", "format_reference_error"),
        "AC02": ("Invalid debtor account number", "format_reference_error"),
        "AC04": ("Closed account number", "account_invalid"),
        "AC06": ("Blocked account", "screening_hold"),
        "AG01": ("Transaction forbidden", "authorization_decline"),
        "AG02": ("Invalid bank operation code", "format_reference_error"),
        "AM04": ("Insufficient funds", "insufficient_funds"),
        "AM05": ("Duplication", "duplicate"),
        "BE01": ("Inconsistent end customer / name mismatch", "format_reference_error"),
        "BE04": ("Missing creditor address", "format_reference_error"),
        "DT01": ("Invalid date", "format_reference_error"),
        "FF01": ("Invalid file format", "message_unparseable"),
        "MS03": ("Reason not specified (agent generated)", "unknown"),
        "RC01": ("Bank identifier (BIC) incorrect", "format_reference_error"),
        "RC03": ("Debtor bank identifier invalid", "format_reference_error"),
        "RR04": ("Regulatory reason", "screening_hold"),
        "NARR": ("Narrative reason - see message", "message_unparseable"),
    },
}
# Wire and instant rails require an explicitly identified code system; a rail is not a format.

# Deterministic root-cause -> route / retry (see references/domain-rules.md)
ROUTE_BY_CATEGORY = {
    "settled": "none",
    "authorized": "none", "in_progress": "none",
    "settlement_reported": "payment-operations-review",
    "insufficient_funds": "customer-remediation",
    "expired_or_restricted": "customer-remediation",
    "authorization_decline": "customer-remediation",
    "system_timeout": "bank-payment-exception-investigator",
    "format_reference_error": "bank-payment-exception-investigator",
    "account_invalid": "bank-payment-exception-investigator",
    "duplicate": "bank-payment-exception-investigator",
    "screening_hold": "bank-payment-exception-investigator",
    "recall_return": "bank-payment-exception-investigator",
    "unknown": "bank-payment-exception-investigator",
    "message_unparseable": "iso-20022-message-interpreter",
    "suspected_fraud": "payment-fraud-and-scam-investigator",
    "unauthorized_return": "issuer-payment-dispute-reviewer",
}
RETRY_ELIGIBLE = set()  # No scheme-specific retry authorization is implemented.
DUP_RISK = {"system_timeout", "duplicate"}


def _cite(rail: str, lg: dict) -> str:
    return f"scheme:{lg.get('source_ref','?')}@{lg.get('timestamp', lg.get('seq','?'))}"


def route_for(category, rail):
    route = ROUTE_BY_CATEGORY.get(category, "bank-payment-exception-investigator")
    if rail == "card" and route in {"bank-payment-exception-investigator", "iso-20022-message-interpreter"}:
        return "payment-operations-review"
    return route


def _interpret(rail: str, lg: dict, doc: dict) -> tuple[str, str]:
    status = str(lg.get("status", "")).upper()
    code = lg.get("reason_code")
    evidence = lg.get("settlement_evidence") or {}
    if (lg.get("stage") == "settlement" and status in SETTLED_STATUSES
            and evidence.get("status") == "confirmed" and evidence.get("source_ref")
            and evidence.get("payment_id") == doc.get("payment_id")):
        return ("Settlement confirmed by the cited settlement evidence for this payment", "settled")
    if status == "APPROVED" or (rail == "card" and str(code) == "00"):
        return ("Authorization approved; this does not establish clearing or settlement", "authorized")
    if status in {"ACSC", "ACCC", "SETTLED"} and not code:
        return (f"{status}: completion reported; independently linked settlement evidence absent", "settlement_reported")
    if code:
        system = doc.get("code_system", rail)
        book = CODES.get(system, {})
        if str(code) in book:
            return book[str(code)]
        return (f"Unrecognized {system} reason code {code}", "unknown")
    if status in PROGRESS_STATUSES:
        return (f"{status}: in progress; elapsed time alone has not been evaluated", "in_progress")
    return (f"{status or 'no status'}: uninterpreted", "unknown")


def compute(doc: dict) -> dict:
    from validate_input import validate
    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    rail = doc["rail"]
    legs = sorted(doc["legs"], key=lambda l: l["seq"])
    trace, unknown_codes = [], []
    for lg in legs:
        meaning, category = _interpret(rail, lg, doc)
        row = {
            "seq": lg["seq"], "stage": lg.get("stage"), "status": lg.get("status"),
            "reason_code": lg.get("reason_code"), "meaning": meaning, "category": category,
            "citation": _cite(rail, lg),
        }
        trace.append(row)
        if category == "unknown" and lg.get("reason_code"):
            unknown_codes.append(lg["reason_code"])

    terminal = trace[-1]
    # Preserve unresolved earlier failures; a later authorization does not cure them.
    failures = [r for r in trace if r["category"] not in
                {"settled", "authorized", "in_progress", "settlement_reported"}]
    decisive = terminal if terminal["category"] == "settled" else (failures[-1] if failures else terminal)
    category = decisive["category"]
    route = route_for(category, rail)
    retry = False

    cautions = []
    if category in DUP_RISK:
        cautions.append("Confirm no prior settlement/credit before any re-presentment to avoid a duplicate payment.")
    if category in ("insufficient_funds", "expired_or_restricted", "authorization_decline"):
        cautions.append("Re-presentment only after the account-holder condition is resolved by the account holder or authorized originating system.")
    if category == "screening_hold":
        cautions.append("Screening hold is not a sanctions determination; do not release or clear the hold - route to investigation.")
    if category == "format_reference_error":
        cautions.append("A confirmed bank-payment defect may support an offline payment-repair-planner handoff; a code alone is insufficient.")

    seqs = [r["seq"] for r in trace]
    trace_complete = (trace[0]["stage"] == "initiation" and terminal["category"] == "settled"
                      and seqs == list(range(seqs[0], seqs[-1] + 1)))
    return {
        "diagnosis_id": "pld-" + stable_hash(doc)[:20],
        "source_trace": doc,
        "source_hash": stable_hash(doc),
        "interpretation_scope": "bundled representative codes; no live scheme validation",
        "resolved_codeset": "representative-v1",
        "payment_id": doc["payment_id"],
        "as_of": doc["as_of"],
        "rail": rail,
        "amount": doc.get("amount"),
        "currency": doc.get("currency"),
        "codeset_version": doc.get("codeset_version"),
        "config_version": doc.get("config_version"),
        "halt_stage": decisive.get("stage"),
        "terminal_status": terminal["status"],
        "trace": trace,
        "trace_complete": trace_complete,
        "root_cause": {
            "category": category,
            "reason_code": decisive.get("reason_code"),
            "meaning": decisive.get("meaning"),
            "evidence": [{"seq": decisive.get("seq"), "citation": decisive.get("citation")}],
        },
        "suggested_route": route,
        "retry_eligible": retry,
        "retry_rationale": (
            "Underlying condition can clear; a human or authorized originating system may "
            "re-present later (confirm no prior settlement first)." if retry
            else "Not retry-eligible as diagnosed; route to the suggested workflow."),
        "cautions": cautions,
        "unknown_codes": unknown_codes,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "trace_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    try:
        result = compute(doc)
    except (ValueError, TypeError) as exc:
        print("ERROR", exc)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
