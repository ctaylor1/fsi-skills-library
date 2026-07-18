#!/usr/bin/env python3
"""Deterministic input validation for iso-20022-message-interpreter.

Validates a de-identified, normalized JSON view of an ISO 20022 payment message
(pain / pacs / camt families) BEFORE it is interpreted or explained. Fails closed on
structural problems that would make interpretation unreliable; warns (does not fail) on
data-quality and message-integrity gaps that the explanation must surface (control-total
mismatches, truncation risk, character-set risk, missing rejection reasons).

This script operates only on the documented JSON schema below and bundled de-identified
fixtures. It makes no network calls and binds to no live payment system.

Input schema (JSON):
{
  "message_type": "pacs.008.001.08",         # <family>.<NNN>.<VVV>.<NN>
  "usage_guideline": "CBPR+" (opt),          # CBPR+, HVPS+, SEPA, FedNow, RTP, ...
  "direction": "inbound|outbound" (opt),
  "group_header": {
    "msg_id": "str", "cre_dt_tm": "YYYY-MM-DDThh:mm:ss",
    "nb_of_txs": "int-like" (opt), "ctrl_sum": number (opt)
  },
  "transactions": [
    {"end_to_end_id","instr_id"(opt),"tx_id"(opt),"uetr"(opt),
     "amount": {"value": number, "currency": "USD"},
     "settlement_amount": {...}(opt),
     "debtor": {"name","account"(opt)}(opt),
     "creditor": {"name","account"(opt)}(opt),
     "debtor_agent": {"bic"(opt),"clearing_member_id"(opt)}(opt),
     "creditor_agent": {...}(opt),
     "charge_bearer": "DEBT|CRED|SHAR|SLEV" (opt),
     "remittance_info": {"unstructured": ["..."], "structured": {...}} (opt),
     "purpose_code": "str" (opt),
     "status": {"code","reason_code"(opt),"reason_text"(opt)} (opt),  # pacs.002/pain.002
     "source": {"system": "str", "ref": "str"}}
  ]
}

Usage:
  python validate_input.py message.json
  python validate_input.py --selftest        # validate the bundled fixture
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

MSG_TYPE_RE = re.compile(r"^[a-z]{3,4}\.\d{3}\.\d{3}\.\d{2}$")
DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$")
CCY_RE = re.compile(r"^[A-Z]{3}$")
UUID4_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")

CORE_FAMILIES = {"pain", "pacs", "camt"}
CHARGE_BEARERS = {"DEBT", "CRED", "SHAR", "SLEV"}
# ISO 20022 / SWIFT-x permitted character set for cross-border payment text fields.
PERMITTED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/-?:().,'+ \n\r")
# Currency minor units (default 2); only exceptions listed.
MINOR_UNITS = {"JPY": 0, "KRW": 0, "CLP": 0, "VND": 0, "ISK": 0,
               "BHD": 3, "KWD": 3, "OMR": 3, "JOD": 3, "TND": 3}
# ISO Max35Text identifier limit; legacy MT :70:/name mapping limit.
MAX35 = 35
MT_NARR_LINE = 140

REQUIRED_TOP = ("message_type", "group_header", "transactions")
REQUIRED_TX = ("end_to_end_id", "amount", "source")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _decimals(v) -> int:
    s = repr(v) if isinstance(v, float) else str(v)
    if "." in s and "e" not in s and "E" not in s:
        return len(s.split(".", 1)[1].rstrip("0"))
    return 0


def _bad_chars(text: str):
    return sorted({c for c in str(text) if c not in PERMITTED})


def validate(doc: dict):
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(doc, dict):
        return ["top-level document must be a JSON object"], warnings
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    mt = str(doc["message_type"])
    if not MSG_TYPE_RE.match(mt):
        errors.append(f"message_type must be <family>.<NNN>.<VVV>.<NN>, got {mt!r}")
        family = short = ""
    else:
        family, short = mt.split(".")[0], ".".join(mt.split(".")[:2])
        if family not in CORE_FAMILIES:
            warnings.append(f"message_type family {family!r} is outside core payment families "
                            "(pain/pacs/camt) — interpret with the applicable usage guideline")

    gh = doc.get("group_header") or {}
    if not isinstance(gh, dict) or not gh.get("msg_id"):
        errors.append("group_header.msg_id is required")
    if not gh.get("cre_dt_tm"):
        errors.append("group_header.cre_dt_tm is required")
    elif not DT_RE.match(str(gh["cre_dt_tm"])):
        errors.append(f"group_header.cre_dt_tm must be ISO 8601 datetime, got {gh['cre_dt_tm']!r}")

    txs = doc.get("transactions")
    if not isinstance(txs, list) or not txs:
        errors.append("transactions must be a non-empty list")
        return errors, warnings

    amount_sum = 0.0
    summable = True
    for i, tx in enumerate(txs):
        tag = f"transactions[{i}] ({tx.get('end_to_end_id', '?')})"
        for k in REQUIRED_TX:
            if k not in tx or tx[k] in (None, "", {}):
                errors.append(f"{tag}: missing '{k}'")
        src = tx.get("source") or {}
        if not (src.get("system") and src.get("ref")):
            errors.append(f"{tag}: source must include 'system' and 'ref' (citation)")

        amt = tx.get("amount") or {}
        val = _num(amt.get("value"))
        ccy = amt.get("currency")
        if val is None:
            errors.append(f"{tag}: amount.value must be numeric")
            summable = False
        else:
            amount_sum += val
        if not ccy or not CCY_RE.match(str(ccy)):
            warnings.append(f"{tag}: amount.currency {ccy!r} is not a 3-letter ISO 4217 code")
        elif val is not None and _decimals(val) > MINOR_UNITS.get(ccy, 2):
            warnings.append(f"{tag}: amount {val} has more decimals than {ccy} minor units "
                            f"({MINOR_UNITS.get(ccy, 2)}) — rounding/rejection risk")

        e2e = tx.get("end_to_end_id")
        if e2e and len(str(e2e)) > MAX35:
            warnings.append(f"{tag}: end_to_end_id exceeds {MAX35} chars — truncation risk (Max35Text)")

        uetr = tx.get("uetr")
        if uetr and not UUID4_RE.match(str(uetr)):
            warnings.append(f"{tag}: uetr {uetr!r} is not a valid UUIDv4")
        elif not uetr and family == "pacs" and short in ("pacs.008", "pacs.009"):
            warnings.append(f"{tag}: no uetr — end-to-end tracking (SWIFT gpi) recommended for {short}")

        cb = tx.get("charge_bearer")
        if cb and cb not in CHARGE_BEARERS:
            warnings.append(f"{tag}: charge_bearer {cb!r} not in {sorted(CHARGE_BEARERS)}")

        rmt = (tx.get("remittance_info") or {}).get("unstructured") or []
        for j, line in enumerate(rmt):
            if len(str(line)) > MT_NARR_LINE:
                warnings.append(f"{tag}: remittance line {j} exceeds {MT_NARR_LINE} chars — "
                                "truncation risk when mapped to legacy MT :70:")
            bad = _bad_chars(line)
            if bad:
                warnings.append(f"{tag}: remittance line {j} has non-permitted character(s) "
                                f"{bad} — replacement/rejection risk on SWIFT-x networks")

        for party in ("debtor", "creditor"):
            nm = (tx.get(party) or {}).get("name")
            if nm and len(str(nm)) > MT_NARR_LINE:
                warnings.append(f"{tag}: {party} name exceeds {MT_NARR_LINE} chars — truncation risk")
            if nm and _bad_chars(nm):
                warnings.append(f"{tag}: {party} name has non-permitted character(s) "
                                f"{_bad_chars(nm)} — replacement/rejection risk")

        st = tx.get("status") or {}
        code = str(st.get("code", "")).upper()
        if code in ("RJCT", "RJPT") and not (st.get("reason_code") or st.get("reason_text")):
            warnings.append(f"{tag}: status {code} carries no reason_code/reason_text — "
                            "rejection cannot be explained without a reason")

    nb = gh.get("nb_of_txs")
    if nb is not None and _num(nb) is not None and int(_num(nb)) != len(txs):
        warnings.append(f"group_header.nb_of_txs {nb} != actual transaction count {len(txs)} "
                        "(control-total mismatch)")
    cs = gh.get("ctrl_sum")
    if cs is not None and _num(cs) is not None and summable:
        if abs(_num(cs) - amount_sum) > max(0.01, abs(amount_sum) * 0.0001):
            warnings.append(f"group_header.ctrl_sum {cs} != sum of amounts {amount_sum:.2f} "
                            "(control-total mismatch)")

    return errors, warnings


def _report(errors, warnings) -> int:
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "pacs008_message.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    return _report(*validate(doc))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
