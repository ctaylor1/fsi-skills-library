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

SKILL = "commercial-payment-workflow-designer"


def validate(data):
    errors = []
    rows(data, "suppliers", ["supplier_id", "legal_entity_id", "payee_account_ref", "erp_supplier_ref"], errors)
    rows(data, "invoices", ["invoice_id", "invoice_number", "supplier_id", "buyer_entity_id", "currency", "erp_invoice_ref", "due_date"], errors, ["amount"])
    rows(data, "credit_notes", ["credit_note_id", "invoice_id", "currency", "erp_credit_ref"], errors, ["amount"])
    payments = rows(data, "payments", ["payment_id", "supplier_id", "payer_entity_id", "payee_account_ref", "currency", "method", "state", "erp_payment_ref"], errors, ["amount"])
    for row in payments:
        if isinstance(row, dict) and row.get("state") not in {"settled", "pending", "proposed", "unknown"}:
            errors.append("payment state must be settled, pending, proposed or unknown")
    rows(data, "allocations", ["allocation_id", "payment_id", "invoice_id", "currency"], errors, ["amount"])
    rows(data, "remittances", ["remittance_id", "payment_id", "supplier_id", "delivery_reference"], errors)
    for supplier in data.get("suppliers", []):
        if not isinstance(supplier, dict) or not isinstance(supplier.get("enabled_methods"), list) or any(not text(m) for m in supplier.get("enabled_methods", [])):
            errors.append("supplier enabled_methods explicit list required")
    if type(data.get("history_complete")) is not bool:
        errors.append("history_complete boolean required")
    if not isinstance(data.get("approval_policy"), dict):
        errors.append("approval_policy object required")
    for row in data.get("remittances", []):
        if isinstance(row, dict) and (not isinstance(row.get("allocation_ids"), list) or any(not text(v) for v in row.get("allocation_ids", []))):
            errors.append("remittance allocation_ids must be a list of strings")
    for key in ["suppliers", "invoices"]:
        if not data.get(key):
            errors.append(key + " requires at least one record")
    return errors


def analyze(request):
    from datetime import date
    data = request["data"]
    findings = []
    suppliers = {r["supplier_id"]: r for r in data["suppliers"]}
    invoices = {r["invoice_id"]: r for r in data["invoices"]}
    payments = {r["payment_id"]: r for r in data["payments"]}
    def gap(code, message, row=None):
        findings.append(finding(code, message, (row or {}).get("source_ids", [])))
    if not data["history_complete"]:
        gap("incomplete-history", "Prior and pending allocations must be complete; remaining invoice amounts are unknown.")
    policy = data["approval_policy"]
    try:
        policy_ok = text(policy.get("owner")) and text(policy.get("policy_ref")) and date.fromisoformat(policy["effective_from"]) <= date.fromisoformat(request["as_of"]) <= date.fromisoformat(policy["review_due"])
    except (ValueError, KeyError, TypeError):
        policy_ok = False
    if not policy_ok:
        gap("approval-policy-missing-or-stale", "Supply current AP approval ownership; invoice approval is not authority for a specific payment.")
    seen = set()
    invalid_invoices = set()
    for key, field in [("invoices", "erp_invoice_ref"), ("credit_notes", "erp_credit_ref"), ("payments", "erp_payment_ref")]:
        refs = [r[field] for r in data[key]]
        if len(refs) != len(set(refs)):
            invalid_invoices.update(invoices)
            gap("duplicate-erp-record", key + ": reused " + field + " can duplicate economic records.")
    for invoice in invoices.values():
        natural = (invoice["buyer_entity_id"], invoice["supplier_id"], invoice["invoice_number"].strip().casefold())
        if natural in seen:
            gap("duplicate-invoice-business-key", invoice["invoice_id"], invoice)
            invalid_invoices.update(r["invoice_id"] for r in invoices.values() if (r["buyer_entity_id"], r["supplier_id"], r["invoice_number"].strip().casefold()) == natural)
        seen.add(natural)
        if invoice["supplier_id"] not in suppliers:
            invalid_invoices.add(invoice["invoice_id"])
            gap("unknown-supplier", invoice["invoice_id"], invoice)
        try:
            date.fromisoformat(invoice["due_date"])
        except ValueError:
            invalid_invoices.add(invoice["invoice_id"])
            gap("invalid-due-date", invoice["invoice_id"], invoice)
    unknown_link = False
    for row in data["allocations"]:
        if row["invoice_id"] not in invoices or row["payment_id"] not in payments:
            unknown_link = True
            gap("unknown-allocation-link", row["allocation_id"], row)
    for row in data["credit_notes"]:
        if row["invoice_id"] not in invoices:
            unknown_link = True
            gap("unknown-credit-link", row["credit_note_id"], row)
    payment_results = []
    for pid, payment in payments.items():
        allocations = [r for r in data["allocations"] if r["payment_id"] == pid]
        supplier = suppliers.get(payment["supplier_id"])
        valid = bool(supplier and supplier["payee_account_ref"] == payment["payee_account_ref"] and payment["method"] in supplier["enabled_methods"])
        if not valid:
            gap("supplier-not-enabled-or-payee-mismatch", pid, payment)
        for row in allocations:
            invoice = invoices.get(row["invoice_id"])
            if not invoice or invoice["supplier_id"] != payment["supplier_id"] or invoice["buyer_entity_id"] != payment["payer_entity_id"] or invoice["currency"] != payment["currency"] or row["currency"] != payment["currency"]:
                valid = False
                invalid_invoices.add(row["invoice_id"])
                gap("allocation-owner-or-currency", row["allocation_id"], row)
        known = valid and payment.get("amount") is not None and all(r.get("amount") is not None for r in allocations)
        allocated = sum((amount(r["amount"]) for r in allocations), Decimal(0)) if known else None
        if not known or not allocations or allocated != amount(payment["amount"]):
            valid = False
            gap("payment-allocation-tie", pid + ": allocation sum must equal the exact payment amount.", payment)
        remittances = [r for r in data["remittances"] if r["payment_id"] == pid]
        expected = {r["allocation_id"] for r in allocations}
        remittance_ok = len(remittances) == 1 and remittances[0]["supplier_id"] == payment["supplier_id"] and isinstance(remittances[0].get("allocation_ids"), list) and len(remittances[0]["allocation_ids"]) == len(expected) and set(remittances[0]["allocation_ids"]) == expected
        if not remittance_ok:
            gap("remittance-link-mismatch", pid + ": exact linked invoice allocations and one remittance required.", payment)
        if payment["state"] == "unknown":
            valid = False
            gap("uncertain-payment-outcome", pid + ": investigate outcome before replacement or retry.", payment)
        if not valid:
            invalid_invoices.update(r["invoice_id"] for r in allocations)
        payment_results.append({"payment_id": pid, "currency": payment["currency"], "amount": payment.get("amount"), "allocated_amount": str(allocated) if allocated is not None else None, "state": payment["state"], "remittance_tied": remittance_ok, "workflow_evidence_complete": valid and remittance_ok and policy_ok, "initiation_authorized": False, "erp_payment_ref": payment["erp_payment_ref"]})
    for row in data["remittances"]:
        if row["payment_id"] not in payments:
            gap("orphan-remittance", row["remittance_id"], row)
    balances = []
    for iid, invoice in invoices.items():
        credits = [r for r in data["credit_notes"] if r["invoice_id"] == iid]
        allocations = [r for r in data["allocations"] if r["invoice_id"] == iid]
        known = not unknown_link and data["history_complete"] and iid not in invalid_invoices and all(r.get("amount") is not None for r in [invoice] + credits + allocations)
        if any(r["currency"] != invoice["currency"] for r in credits):
            known = False
            gap("credit-currency-mismatch", iid, invoice)
        if known:
            credit = sum((amount(r["amount"]) for r in credits), Decimal(0))
            by_state = {state: sum((amount(r["amount"]) for r in allocations if payments[r["payment_id"]]["state"] == state), Decimal(0)) for state in ["settled", "pending", "proposed"]}
            open_amount = amount(invoice["amount"]) - credit - by_state["settled"]
            remaining = open_amount - by_state["pending"]
            if open_amount < 0 or remaining < 0 or by_state["proposed"] > remaining:
                gap("invoice-overallocated", iid + ": credits or payment allocations exceed invoice capacity.", invoice)
        else:
            credit = open_amount = remaining = None
            by_state = dict.fromkeys(["settled", "pending", "proposed"])
            gap("unknown-invoice-balance", iid + ": missing or conflicting evidence prevents a reliable payable balance.", invoice)
        balances.append({"invoice_id": iid, "supplier_id": invoice["supplier_id"], "buyer_entity_id": invoice["buyer_entity_id"], "currency": invoice["currency"], "erp_invoice_ref": invoice["erp_invoice_ref"], **{k: str(v) if v is not None else None for k, v in {"credit_notes": credit, "open_after_settled": open_amount, "remaining_before_proposed": remaining, **by_state}.items()}})
    if any(item["severity"] == "gap" for item in findings):
        for row in payment_results:
            row["workflow_evidence_complete"] = False
    return {"result": {"invoice_balances": balances, "payment_remittance_ties": payment_results, "supplier_enablement": data["suppliers"], "approval_policy_reviewed": policy_ok, "workflow": ["ERP invoice and credit identity", "AP exception and approval evidence", "supplier and payee enablement", "exact initiation review", "payment status correlation", "remittance delivery and supplier allocation", "ERP reconciliation"], "system_of_record_updated": False}, "findings": findings, "handoffs": [handoff("payment-initiation-control-reviewer", "Review exact payment instruction separately from AP approval.", ["supplier account reference", "exact payment amount and currency", "approval evidence", "duplicate and mandate evidence"]), handoff("bank-payment-workflow-designer", "Choose evidenced method and remittance transport for supplier requirements.", ["supplier enablement", "due dates", "ERP linkage and remittance fields"]), handoff("payment-lifecycle-diagnoser", "Investigate pending or uncertain outcomes before issuing replacements.", ["payment identity", "native lifecycle events", "settlement and ERP evidence"])]}
