from decimal import Decimal, InvalidOperation
from datetime import datetime
from payment_foundation import finding


def amount(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("amount must be a decimal string or integer")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid amount") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("amount must be finite and nonnegative")
    return result


def text(value):
    return isinstance(value, str) and bool(value.strip())


def stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp requires timezone")
    return result


def rows(data, key, fields, errors, nullable=()):
    items = data.get(key)
    if not isinstance(items, list):
        errors.append(key + " must be an explicit list")
        return []
    seen = set()
    for row in items:
        if not isinstance(row, dict):
            errors.append(key + " row must be an object")
            continue
        for field in fields:
            if not text(row.get(field)):
                errors.append(key + "." + field + " required")
        rid = row.get(fields[0])
        if rid in seen:
            errors.append(key + " duplicate " + fields[0])
        seen.add(rid)
        if not isinstance(row.get("source_ids"), list) or not row["source_ids"]:
            errors.append(key + " row needs source_ids")
        if "currency" in fields and (len(row.get("currency", "")) != 3 or not row.get("currency", "").isupper()):
            errors.append(key + " currency requires uppercase three-letter code")
        for field in nullable:
            if row.get(field) is not None:
                try:
                    amount(row[field])
                except ValueError as exc:
                    errors.append(key + "." + field + ": " + str(exc))
    return items


def handoff(target, reason, required):
    return {"target_skill": target, "reason": reason, "required_inputs": required}

SKILL = "platform-payment-flow-designer"
MODELS = {"marketplace", "payfac", "merchant-of-record", "vertical-saas"}
RESPONSIBILITIES = {"seller-onboarding", "customer-contract", "refunds", "chargebacks", "payouts", "safeguarding-assessment"}


def validate(data):
    errors = []
    if data.get("model") not in MODELS:
        errors.append("model must distinguish marketplace, payfac, merchant-of-record or vertical-saas")
    rows(data, "entities", ["entity_id", "legal_name", "role"], errors)
    rows(data, "accounts", ["account_id", "owner_entity_id", "currency", "custody_role"], errors)
    rows(data, "responsibilities", ["activity", "entity_id", "contract_ref"], errors)
    charges = rows(data, "charges", ["charge_id", "customer_contract_entity_id", "collecting_account_id", "currency", "state"], errors, ["amount"])
    for row in charges:
        if isinstance(row, dict) and row.get("state") not in {"settled", "pending", "unknown"}:
            errors.append("charge state must be settled, pending or unknown")
    allocations = rows(data, "allocations", ["allocation_id", "charge_id", "beneficiary_entity_id", "currency", "type"], errors, ["amount"])
    for row in allocations:
        if isinstance(row, dict) and row.get("type") not in {"seller", "platform-fee", "processor-fee"}:
            errors.append("allocation type must be seller, platform-fee or processor-fee")
    adjustments = rows(data, "adjustments", ["adjustment_id", "allocation_id", "currency", "type"], errors, ["amount"])
    for row in adjustments:
        if isinstance(row, dict) and row.get("type") not in {"refund", "chargeback", "reserve"}:
            errors.append("adjustment type must be refund, chargeback or reserve; supplied ledger is cumulative as-of")
    payouts = rows(data, "payouts", ["payout_id", "allocation_id", "destination_account_id", "currency", "state"], errors, ["amount"])
    for row in payouts:
        if isinstance(row, dict) and row.get("state") not in {"paid", "pending", "proposed"}:
            errors.append("payout state must be paid, pending or proposed")
    if type(data.get("ledger_complete")) is not bool:
        errors.append("ledger_complete boolean required; absent history is unknown")
    for key in ["entities", "accounts", "charges", "allocations"]:
        if not data.get(key):
            errors.append(key + " requires at least one record")
    return errors


def analyze(request):
    data = request["data"]
    findings = []
    entities = {r["entity_id"]: r for r in data["entities"]}
    accounts = {r["account_id"]: r for r in data["accounts"]}
    charges = {r["charge_id"]: r for r in data["charges"]}
    allocations = {r["allocation_id"]: r for r in data["allocations"]}
    def gap(code, message, row=None):
        findings.append(finding(code, message, (row or {}).get("source_ids", [])))
    if not data["ledger_complete"]:
        gap("incomplete-ledger", "Complete charges, allocations, holds and prior/pending payouts are needed; capacity is unknown.")
    for account in accounts.values():
        if account["owner_entity_id"] not in entities:
            gap("unknown-account-owner", account["account_id"], account)
    assigned = {r["activity"] for r in data["responsibilities"]}
    for missing in sorted(RESPONSIBILITIES - assigned):
        gap("unassigned-responsibility", missing)
    for row in data["responsibilities"]:
        if row["entity_id"] not in entities:
            gap("unknown-responsibility-owner", row["activity"], row)
    if data["model"] == "merchant-of-record":
        mors = {r["entity_id"] for r in entities.values() if r["role"] == "merchant-of-record"}
        if not mors or any(r["customer_contract_entity_id"] not in mors for r in charges.values()):
            gap("mor-contract-mismatch", "Merchant-of-record design must identify the customer-contract entity; marketplace labels do not establish this role.")
    if data["model"] == "payfac" and not any(r["role"] == "sponsor-acquirer" for r in entities.values()):
        gap("payfac-sponsor-missing", "Identify the sponsor/acquirer and its supplied contract; software capability grants no PayFac permission.")
    unknown_links = False
    for row in data["adjustments"] + data["payouts"]:
        if row["allocation_id"] not in allocations:
            unknown_links = True
            gap("unknown-allocation-link", str(row), row)
    totals = []
    invalid_charges = set()
    for cid, charge in charges.items():
        linked = [a for a in allocations.values() if a["charge_id"] == cid]
        account = accounts.get(charge["collecting_account_id"])
        bad = not account or account["currency"] != charge["currency"] or account["owner_entity_id"] not in entities or charge["customer_contract_entity_id"] not in entities
        if bad:
            gap("charge-ownership-or-currency", cid, charge)
        known = not bad and charge.get("amount") is not None and all(a.get("amount") is not None and a["currency"] == charge["currency"] for a in linked)
        allocated = sum((amount(a["amount"]) for a in linked), Decimal(0)) if known else None
        difference = amount(charge["amount"]) - allocated if known else None
        if difference != 0 or not linked:
            gap("charge-allocation-tie", "Charge " + cid + " must tie exactly to all seller and fee allocations; unknown is not zero.", charge)
            bad = True
        if bad or not known:
            invalid_charges.add(cid)
        totals.append({"charge_id": cid, "currency": charge["currency"], "gross": charge.get("amount"), "allocated": str(allocated) if known else None, "difference": str(difference) if known else None, "state": charge["state"]})
    positions = []
    for aid, allocation in allocations.items():
        charge = charges.get(allocation["charge_id"])
        adjustments = [r for r in data["adjustments"] if r["allocation_id"] == aid]
        payouts = [r for r in data["payouts"] if r["allocation_id"] == aid]
        bad = unknown_links or not data["ledger_complete"] or not charge or allocation["charge_id"] in invalid_charges or allocation["beneficiary_entity_id"] not in entities
        if not charge or charge["currency"] != allocation["currency"] or allocation["beneficiary_entity_id"] not in entities:
            gap("allocation-ownership-or-currency", aid, allocation)
            bad = True
        for row in adjustments + payouts:
            if row["currency"] != allocation["currency"]:
                bad = True
                gap("cross-currency-allocation", aid, row)
        for payout in payouts:
            destination = accounts.get(payout["destination_account_id"])
            if not destination or destination["owner_entity_id"] != allocation["beneficiary_entity_id"] or destination["currency"] != allocation["currency"]:
                bad = True
                gap("payout-owner-mismatch", payout["payout_id"], payout)
        known = not bad and all(r.get("amount") is not None for r in [allocation] + adjustments + payouts)
        if not known:
            gap("unknown-position", "Allocation " + aid + " has unknown amounts or unresolved links; no payout capacity asserted.", allocation)
            owed = held = paid = pending = proposed = capacity = None
        else:
            refunds = sum((amount(r["amount"]) for r in adjustments if r["type"] == "refund"), Decimal(0))
            disputes = sum((amount(r["amount"]) for r in adjustments if r["type"] == "chargeback"), Decimal(0))
            held = sum((amount(r["amount"]) for r in adjustments if r["type"] == "reserve"), Decimal(0))
            paid = sum((amount(r["amount"]) for r in payouts if r["state"] == "paid"), Decimal(0))
            pending = sum((amount(r["amount"]) for r in payouts if r["state"] == "pending"), Decimal(0))
            proposed = sum((amount(r["amount"]) for r in payouts if r["state"] == "proposed"), Decimal(0))
            owed = amount(allocation["amount"]) - refunds - disputes - paid
            capacity = owed - held - pending if charge["state"] == "settled" else None
            if charge["state"] != "settled":
                gap("not-collected", aid + ": allocation entitlement is not available cash; collection is " + charge["state"], allocation)
            if owed < 0 or (capacity is not None and (capacity < 0 or proposed > capacity)):
                gap("overallocated-or-insufficient", aid + ": offsets, holds, pending or proposed payouts exceed evidenced capacity.", allocation)
        positions.append({"allocation_id": aid, "beneficiary_entity_id": allocation["beneficiary_entity_id"], "currency": allocation["currency"], "allocation_type": allocation["type"], **{k: str(v) if v is not None else None for k, v in {"owed_after_paid": owed, "reserve_held": held, "pending_payouts": pending, "proposed_payouts": proposed, "available_before_proposed": capacity}.items()}})
    return {"result": {"model": data["model"], "role_and_responsibility_map": data["responsibilities"], "account_ownership": data["accounts"], "charge_reconciliation": totals, "allocation_positions": positions, "permission_determination": "not-performed"}, "findings": findings, "handoffs": [handoff("payment-regulatory-applicability-reviewer", "Review actual contracting, custody and entity roles before design adoption.", ["entity and account ownership", "contracts", "funds-flow map"]), handoff("payment-initiation-control-reviewer", "Any eventual payout requires a separately validated exact instruction.", ["payee and account", "currency and amount", "mandate and approval", "remaining capacity"]), handoff("merchant-onboarding-risk-reviewer", "Review onboarding and submerchant risk ownership.", ["seller population", "business model", "sponsor contracts"])]}
