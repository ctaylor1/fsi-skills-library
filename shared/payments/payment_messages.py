"""Bounded native payment-message inspection; never full rail certification."""
from __future__ import annotations
from datetime import date
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from payment_contract import money, stable_hash
from payment_foundation import load_resource


def inspect_message(doc):
    if not isinstance(doc, dict):
        raise ValueError("message input must be an object")
    contracts = load_resource("message-contracts.json")["contracts"]
    rails = load_resource("rail-profiles.json")["profiles"]
    rail = rails.get(doc.get("profile_id"))
    contract = contracts.get(doc.get("message_contract_id"))
    if not rail or not contract or rail["message_contract_id"] != doc.get("message_contract_id"):
        raise ValueError("explicit matching rail and message contract required")
    if not contract["supported_adapter"]:
        return {"status": "unsupported-adapter", "profile_id": rail["profile_id"], "required_native_fields": contract["required_fields"], "limitations": contract["limitations"], "full_conformance": False, "authority_granted": False}
    raw = doc.get("raw")
    context = doc.get("context", {})
    if not isinstance(raw, str) or not isinstance(context, dict) or not context.get("source_ref"):
        raise ValueError("raw message and context.source_ref required")
    if len(raw) > 1000000:
        raise ValueError("message exceeds bounded inspection size")
    records = []
    if contract["format"] == "ach-94":
        if len(raw) != 94 or not raw.isascii() or raw[0] != "6":
            raise ValueError("one ASCII 94-character ACH Entry Detail record required")
        if context.get("sec_code") not in contract["accepted_sec_codes"]:
            raise ValueError("only declared CCD and PPD Entry Detail supported")
        date.fromisoformat(context.get("effective_entry_date", ""))
        code = raw[1:3]
        if code not in {"22", "27", "32", "37"}:
            raise ValueError("unsupported ACH transaction code; no prenote or return inference")
        routing, amount, trace = raw[3:12], raw[29:39], raw[79:94]
        if not (routing.isdigit() and amount.isdigit() and trace.isdigit()) or raw[78] not in {"0", "1"}:
            raise ValueError("invalid ACH routing/amount/trace/addenda fields")
        if sum(int(x) * w for x, w in zip(routing, (3, 7, 1, 3, 7, 1, 3, 7, 1))) % 10:
            raise ValueError("ACH routing check digit mismatch")
        account = raw[12:29].strip()
        if not account:
            raise ValueError("ACH receiving account required")
        records.append({"trace_id": trace, "direction": "credit" if code in {"22", "32"} else "debit", "amount": format(money(amount) / 100, ".2f"), "currency": "USD", "account_suffix": account[-4:], "sec_code": context["sec_code"], "effective_entry_date": context["effective_entry_date"], "addenda_required_by_indicator": raw[78] == "1"})
    else:
        if "<!DOCTYPE" in raw.upper() or "<!ENTITY" in raw.upper():
            raise ValueError("DTD/entity declarations are not accepted")
        try:
            document = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise ValueError("invalid XML: " + str(exc)) from None
        namespace = document.tag.split("}")[0][1:] if document.tag.startswith("{") else ""
        if namespace not in contract["namespaces"] or document.tag != "{" + namespace + "}Document":
            raise ValueError("unsupported exact ISO namespace/document root")
        q = lambda name: "{" + namespace + "}" + name
        message = document.find(q(contract["message_root"]))
        if message is None or not message.findtext(q("GrpHdr") + "/" + q("MsgId")):
            raise ValueError("native message root and group message identifier required")
        txns = message.findall(".//" + q(contract["transaction_element"]))
        if not txns:
            raise ValueError("native transaction element required")
        seen = set()
        for txn in txns:
            e2e = txn.findtext(q("PmtId") + "/" + q("EndToEndId"))
            txid = txn.findtext(q("PmtId") + "/" + q("TxId"))
            identity = txid or e2e
            if not identity or identity == "NOTPROVIDED" or identity in seen:
                raise ValueError("distinct transaction identity required for inspection")
            seen.add(identity)
            amounts = txn.findall(".//" + q(contract["amount_element"]))
            if len(amounts) != 1:
                raise ValueError("exactly one native amount per transaction required")
            value = money(amounts[0].text)
            currency = amounts[0].get("Ccy")
            if value <= 0 or currency not in rail["currencies"]:
                raise ValueError("positive amount in rail currency required")
            for field in contract["required_fields"]:
                if field.startswith("GrpHdr/"):
                    continue
                query = ".//" + "/".join(q(part) for part in field.split("/"))
                # Debtor/creditor context may be at PmtInf level in customer messages.
                present = txn.find(query)
                if present is None and contract["message_root"] != "FIToFICstmrCdtTrf" and "/" not in field and field != "MndtId":
                    parent = next((p for p in message.findall(q("PmtInf")) if txn in list(p)), None)
                    present = parent.find(q(field)) if parent is not None else None
                if present is None or not "".join(present.itertext()).strip():
                    raise ValueError("missing native field " + field)
            records.append({"transaction_id": identity, "end_to_end_id": e2e, "amount": str(value), "currency": currency})
    return {"status": "inspected-subset", "profile_id": rail["profile_id"], "message_contract_id": doc["message_contract_id"], "source_ref": context["source_ref"], "input_hash": stable_hash(doc), "records": records, "full_conformance": False, "authority_granted": False, "source_refs": contract["source_refs"], "limitations": contract["limitations"]}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    try:
        result = inspect_message(json.loads(Path(args.path).read_text()))
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}))
        return 1
