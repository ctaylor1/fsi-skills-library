#!/usr/bin/env python3
"""Deterministic interpretation transform for iso-20022-message-interpreter.

Parses a normalized ISO 20022 payment-message JSON (see validate_input.py for the schema)
and emits a source-linked, plain-language INTERPRETATION object: message classification,
control-total tie-outs, identifier checks (IBAN mod-97, BIC shape, UETR UUIDv4),
truncation / character-set detection, and status-code interpretation for status reports
(pacs.002 / pain.002). It is descriptive only: it never proposes a repair, a resubmission,
a fund movement, or a fraud / sanctions / compliance determination.

Stdlib-only, self-contained, no network. Output conforms to the schema validated by
validate_output.py.

Usage:
  python calculate_or_transform.py message.json     # print interpretation JSON, exit 0
  python calculate_or_transform.py --selftest       # transform + self-check bundled fixture
Exit 0 on success, 1 on structural failure / self-check error.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

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
}
# ExternalPaymentTransactionStatus / group status -> (category, plain-language)
STATUS = {
    "ACSC": ("accepted", "Accepted Settlement Completed — settlement on the creditor side is complete."),
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


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _cite(tx) -> str:
    src = tx.get("source") or {}
    return f"{src.get('system', '?')}:{src.get('ref', '?')}"


def iban_ok(acct: str) -> bool:
    acct = re.sub(r"\s+", "", str(acct)).upper()
    if not IBAN_RE.match(acct):
        return False
    rearranged = acct[4:] + acct[:4]
    digits = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
    try:
        return int(digits) % 97 == 1
    except ValueError:
        return False


def looks_like_iban(acct: str) -> bool:
    return bool(re.match(r"^[A-Z]{2}\d{2}", re.sub(r"\s+", "", str(acct)).upper()))


def _bad_chars(text: str):
    return sorted({c for c in str(text) if c not in PERMITTED})


def classify(mt: str) -> dict:
    parts = mt.split(".")
    family = parts[0] if parts else ""
    short = ".".join(parts[:2]) if len(parts) >= 2 else mt
    return {
        "message_type": mt,
        "message_family": family,
        "family_description": FAMILY_DESC.get(family, "Non-core ISO 20022 message"),
        "message_name": f"{MESSAGE_NAMES.get(short, 'ISO 20022 message')} ({short})",
    }


def interpret(doc: dict) -> dict:
    mt = str(doc.get("message_type", ""))
    cls = classify(mt)
    short = ".".join(mt.split(".")[:2])
    gh = doc.get("group_header") or {}
    txs = doc.get("transactions") or []

    findings: list[dict] = []
    out_txs: list[dict] = []
    total = 0.0
    currencies: set = set()

    for tx in txs:
        cite = _cite(tx)
        amt = tx.get("amount") or {}
        val = _num(amt.get("value"))
        ccy = amt.get("currency")
        if val is not None:
            total += val
        if ccy:
            currencies.add(ccy)

        tx_out = {
            "end_to_end_id": tx.get("end_to_end_id"),
            "uetr": tx.get("uetr"),
            "amount": {"value": val, "currency": ccy},
            "citation": cite,
        }

        # Identifier checks
        uetr = tx.get("uetr")
        if uetr and not UUID4_RE.match(str(uetr)):
            findings.append({"severity": "high", "code": "UETR_INVALID", "field": "uetr",
                             "message": f"UETR {uetr!r} is not a valid UUIDv4.", "citation": cite})
        for role in ("debtor_agent", "creditor_agent"):
            bic = (tx.get(role) or {}).get("bic")
            if bic and not BIC_RE.match(str(bic)):
                findings.append({"severity": "high", "code": "BIC_INVALID", "field": role,
                                 "message": f"{role} BIC {bic!r} is not a valid BIC (8 or 11).",
                                 "citation": cite})
        for role in ("debtor", "creditor"):
            acct = (tx.get(role) or {}).get("account")
            if acct and looks_like_iban(acct) and not iban_ok(acct):
                findings.append({"severity": "high", "code": "IBAN_INVALID", "field": role,
                                 "message": f"{role} IBAN fails the mod-97 check digit.",
                                 "citation": cite})

        # Truncation / character-set detection
        rmt = (tx.get("remittance_info") or {}).get("unstructured") or []
        for j, line in enumerate(rmt):
            if len(str(line)) > MT_NARR_LINE:
                findings.append({"severity": "medium", "code": "TRUNCATION_RISK",
                                 "field": f"remittance.unstructured[{j}]",
                                 "message": f"Remittance line is {len(str(line))} chars; exceeds the "
                                            "140-char legacy MT :70: limit and would be truncated on "
                                            "down-mapping.", "citation": cite})
            if _bad_chars(line):
                findings.append({"severity": "medium", "code": "CHARSET_RISK",
                                 "field": f"remittance.unstructured[{j}]",
                                 "message": f"Remittance line contains non-permitted character(s) "
                                            f"{_bad_chars(line)}; replacement or rejection risk on "
                                            "SWIFT-x networks.", "citation": cite})

        # Status interpretation (status-report messages)
        st = tx.get("status") or {}
        code = str(st.get("code", "")).upper()
        if code:
            cat, plain = STATUS.get(code, ("unknown", f"Status {code} — not in the interpreted set; "
                                                       "consult the message usage guideline."))
            rc = str(st.get("reason_code", "")).upper()
            reason_plain = REASON.get(rc) if rc else None
            si = {"code": code, "category": cat, "plain": plain,
                  "reason_code": rc or None, "reason_plain": reason_plain,
                  "reason_text": st.get("reason_text")}
            tx_out["status_interpretation"] = si
            if cat in ("rejected", "returned") and not (rc or st.get("reason_text")):
                findings.append({"severity": "high", "code": "REJECT_NO_REASON", "field": "status",
                                 "message": f"Status {code} reports a rejection but carries no reason "
                                            "code or text; the cause cannot be explained.",
                                 "citation": cite})
            elif cat in ("rejected", "returned"):
                detail = reason_plain or st.get("reason_text") or rc
                findings.append({"severity": "high", "code": "STATUS_REJECTED", "field": "status",
                                 "message": f"Transaction reported {code} (rejected). Reason {rc or '—'}: "
                                            f"{detail}", "citation": cite})

        out_txs.append(tx_out)

    # Control-total tie-outs
    nb = gh.get("nb_of_txs")
    nb_ok = nb is None or (_num(nb) is not None and int(_num(nb)) == len(txs))
    if nb is not None and not nb_ok:
        findings.append({"severity": "high", "code": "NBTX_MISMATCH", "field": "group_header.nb_of_txs",
                         "message": f"NbOfTxs {nb} does not match the {len(txs)} transactions present.",
                         "citation": f"{(gh.get('msg_id') or 'grphdr')}"})
    cs = gh.get("ctrl_sum")
    cs_ok = cs is None or (_num(cs) is not None and abs(_num(cs) - total) <= max(0.01, abs(total) * 0.0001))
    if cs is not None and not cs_ok:
        findings.append({"severity": "high", "code": "CTRLSUM_MISMATCH", "field": "group_header.ctrl_sum",
                         "message": f"CtrlSum {cs} does not match the summed amount {total:.2f}.",
                         "citation": f"{(gh.get('msg_id') or 'grphdr')}"})

    balanced = nb_ok and cs_ok
    ccy_list = sorted(currencies)
    total_str = f"{ccy_list[0] + ' ' if len(ccy_list) == 1 else ''}{total:,.2f}"

    narrative = _narrate(cls, doc, out_txs, balanced, total_str, ccy_list)

    return {
        "message_type": mt,
        "message_family": cls["message_family"],
        "family_description": cls["family_description"],
        "message_name": cls["message_name"],
        "usage_guideline": doc.get("usage_guideline", "base ISO 20022 schema"),
        "summary": {
            "nb_of_txs": len(txs),
            "total_amount": round(total, 2),
            "currencies": ccy_list,
            "control_totals_balanced": balanced,
        },
        "transactions": out_txs,
        "findings": findings,
        "narrative": narrative,
        "disclaimer": DISCLAIMER,
    }


def _narrate(cls, doc, out_txs, balanced, total_str, ccy_list) -> str:
    ug = doc.get("usage_guideline", "base ISO 20022 schema")
    n = len(out_txs)
    ccy_phrase = f"totalling {total_str}" if len(ccy_list) == 1 else \
        f"across {len(ccy_list)} currencies ({', '.join(ccy_list)})"
    tie = ("The declared control totals match the transactions present."
           if balanced else
           "The declared control totals do NOT match the transactions present (see findings).")
    lines = [
        f"This message is {cls['message_name']} — {cls['family_description']} — under the "
        f"{ug} usage guideline, carrying {n} transaction(s) {ccy_phrase}. {tie}"
    ]
    for tx in out_txs:
        amt = tx.get("amount") or {}
        piece = (f"Transaction {tx.get('end_to_end_id')} states "
                 f"{(amt.get('currency') or '')} {(_num(amt.get('value')) or 0):,.2f}")
        si = tx.get("status_interpretation")
        if si:
            piece += f"; status {si['code']} ({si['category']}) — {si['plain']}"
            if si.get("reason_plain"):
                piece += f" Reason {si['reason_code']}: {si['reason_plain']}"
        piece += f" [source: {tx.get('citation')}]."
        lines.append(piece)
    lines.append("Every figure above is traceable to the cited source reference. " + DISCLAIMER)
    return " ".join(lines)


# --- prohibited-language guard reused by the self-check (kept minimal, mirrors output check) ---
_ADVICE = [r"\byou (should|must|need to|ought to)\b", r"\bwe (recommend|advise|suggest)\b",
           r"\bresubmit\b", r"\bre-?send\b", r"\bsafe to release\b", r"\bsanctions[- ]clear"]


def _selfcheck(result: dict) -> list[str]:
    errs = []
    if "ISO 20022 message" == result.get("message_name", "").split(" (")[0]:
        errs.append("message_type was not classified to a known name")
    if not result.get("summary", {}).get("currencies"):
        errs.append("no currency resolved")
    for t in result.get("transactions", []):
        if not (t.get("citation") or "").strip():
            errs.append(f"transaction {t.get('end_to_end_id')} missing citation")
    for f in result.get("findings", []):
        if not (f.get("citation") or "").strip():
            errs.append(f"finding {f.get('code')} missing citation")
    if DISCLAIMER not in result.get("disclaimer", ""):
        errs.append("standing disclaimer missing")
    text = result.get("narrative", "")
    for pat in _ADVICE:
        if re.search(pat, text, re.I):
            errs.append(f"narrative contains prohibited advice/action phrasing matching {pat!r}")
    if result.get("summary", {}).get("control_totals_balanced") is not True:
        errs.append("bundled fixture unexpectedly failed control-total tie-out")
    return errs


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "pacs008_message.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
        result = interpret(doc)
        errs = _selfcheck(result)
        for e in errs:
            print("ERROR", e)
        print(f"transform selftest: {len(errs)} error(s)")
        return 1 if errs else 0
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    if not isinstance(doc, dict) or "transactions" not in doc or "message_type" not in doc:
        print("ERROR input is not a normalized ISO 20022 message (missing message_type/transactions)")
        return 1
    print(json.dumps(interpret(doc), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
