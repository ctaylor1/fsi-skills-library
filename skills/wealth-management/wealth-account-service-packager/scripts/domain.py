"""Service-instruction evidence packaging. No service instruction is executed."""
from wealth_contract import make_output, validate_output_envelope, iso_date, nonempty, source_errors
from workflow_support import base_errors, rows, texts, enum, number, dec, money, cited, add, base_findings, common_result

SKILL = "wealth-account-service-packager"
TYPES = {"transfer", "distribution", "authority", "beneficiary"}


def validate(doc):
    errors = base_errors(doc)
    if errors:
        return errors
    reqs = doc["policy"].get("service_requirements")
    if not isinstance(reqs, dict) or set(reqs) != TYPES or any(not texts(v) for v in reqs.values()):
        errors.append("policy.service_requirements must explicitly map all four service types to nonempty unique requirement lists")
    for p in rows(doc, "parties", errors, "party_id"):
        if not nonempty(p.get("display_name")):
            errors.append("party requires masked display_name")
    for a in rows(doc, "accounts", errors, "account_id"):
        if a.get("currency") != "USD" or not enum(a.get("registration"), {"individual", "joint", "ira", "trust", "entity"}) or not texts(a.get("owner_party_ids")):
            errors.append("account requires USD currency, supported registration and explicit owners")
        if a.get("available_cash") is not None and not number(a["available_cash"]):
            errors.append("available_cash must be nonnegative finite number or null")
        if a.get("positions") is not None:
            for pos in rows(a, "positions", errors, "security_id"):
                if not number(pos.get("quantity")):
                    errors.append("account position quantity must be nonnegative finite number")
    for r in rows(doc, "requests", errors, "service_request_id"):
        if not enum(r.get("type"), TYPES):
            errors.append("unsupported service request type")
            continue
        if not nonempty(r.get("account_id")) or not nonempty(r.get("requested_by_party_id")):
            errors.append("request requires account_id and requested_by_party_id")
        if iso_date(r.get("requested_date")) is None or r["requested_date"] > doc["as_of"]:
            errors.append("requested_date must be historical ISO date")
        d = r.get("details")
        if not isinstance(d, dict):
            errors.append("request details must be an object")
            continue
        if r["type"] == "transfer":
            if not enum(d.get("method"), {"cash", "in-kind"}) or not enum(d.get("transfer_scope"), {"full", "partial"}) or not nonempty(d.get("destination_ref_masked")):
                errors.append("transfer requires method, scope and masked destination reference")
            if not texts(d.get("destination_owner_party_ids")):
                errors.append("transfer requires explicit destination owner IDs")
            if d.get("method") == "cash":
                if d.get("amount") is not None and not number(d["amount"], 0.01):
                    errors.append("cash transfer amount must be positive or null")
                if d.get("positions") not in (None, []):
                    errors.append("cash transfer cannot contain in-kind positions")
            else:
                if d.get("amount") is not None:
                    errors.append("in-kind transfer uses positions rather than a cash amount")
                for pos in rows(d, "positions", errors, "security_id"):
                    if not number(pos.get("quantity"), 0.00000001):
                        errors.append("requested position quantity must be positive finite number")
        elif r["type"] == "distribution":
            if d.get("currency") != "USD" or not nonempty(d.get("payee_ref_masked")) or not nonempty(d.get("purpose")):
                errors.append("distribution requires USD currency, masked payee reference and purpose")
            if d.get("amount") is not None and not number(d["amount"], 0.01):
                errors.append("distribution amount must be positive or null")
            if d.get("tax_instruction_ref") is not None and not nonempty(d["tax_instruction_ref"]):
                errors.append("tax_instruction_ref must be a source locator or null")
        elif r["type"] == "authority":
            if not nonempty(d.get("subject_party_id")) or not enum(d.get("change"), {"add", "remove", "replace"}) or not nonempty(d.get("authority_scope")):
                errors.append("authority request requires subject, change and supplied scope")
        else:
            if not enum(d.get("change"), {"replace", "remove"}):
                errors.append("beneficiary change must be replace or remove")
            beneficiaries = rows(d, "beneficiaries", errors)
            seen = set()
            for b in beneficiaries:
                if not nonempty(b.get("party_id")) or not enum(b.get("tier"), {"primary", "contingent"}) or not number(b.get("share"), 0, 1):
                    errors.append("beneficiary requires party_id, tier and fractional share")
                    continue
                key = (b["party_id"], b["tier"])
                if key in seen:
                    errors.append("duplicate beneficiary in the same tier")
                seen.add(key)
            if d.get("change") == "remove" and beneficiaries:
                errors.append("remove means remove all recorded designations; targeted changes require an explicit replacement schedule")
    for c in rows(doc, "conditions", errors, "condition_id"):
        if any(not nonempty(c.get(k)) for k in ("service_request_id", "requirement", "description")) or not enum(c.get("status"), {"received", "missing", "conflicting", "not-applicable"}):
            errors.append("condition requires request ID, requirement, description and supported status")
    return errors


def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    findings = base_findings(doc)
    parties = {r["party_id"] for r in doc["parties"]}
    accounts = {r["account_id"]: r for r in doc["accounts"]}
    request_ids = {r["service_request_id"] for r in doc["requests"]}
    cash_requests, position_requests = {}, {}
    for group in ("parties", "accounts", "conditions"):
        for i, row in enumerate(doc[group]):
            cited(row, doc, findings, f"{group}[{i}]")
    for a in doc["accounts"]:
        if any(pid not in parties for pid in a["owner_party_ids"]):
            add(findings, "unknown-owner", "Account owner IDs do not resolve", a["account_id"])
        for pos in a.get("positions") or []:
            cited(pos, doc, findings, a["account_id"] + ".positions")
    for c in doc["conditions"]:
        if c["status"] == "conflicting":
            add(findings, "condition-conflict", "Supplied condition evidence is conflicting even if the requirement is outside the configured required list", c["condition_id"], service_request_id=c["service_request_id"])
        if c["service_request_id"] not in request_ids:
            add(findings, "unknown-request", "Condition references an unknown service request", c["condition_id"])
    if not doc["requests"]:
        add(findings, "missing-requests", "No service requests supplied", "requests")
    packages = []
    for r in doc["requests"]:
        rid, d = r["service_request_id"], r["details"]
        start = len(findings)
        cited(r, doc, findings, rid)
        cited(d, doc, findings, rid + ".details")
        account = accounts.get(r["account_id"])
        if account is None:
            add(findings, "unknown-account", "Account reference does not resolve", rid)
        if r["requested_by_party_id"] not in parties:
            add(findings, "unknown-requestor", "Requestor identity reference does not resolve; authority is not inferred from identity", rid)
        conditions = [c for c in doc["conditions"] if c["service_request_id"] == rid]
        matrix = []
        for requirement in doc["policy"]["service_requirements"][r["type"]]:
            matches = [c for c in conditions if c["requirement"] == requirement]
            recorded = len(matches) == 1 and matches[0]["status"] == "received" and not source_errors(matches[0].get("source_ids"), doc)
            if not recorded:
                add(findings, "condition-gap", f"{requirement} needs one received evidence record; duplicates, missing, conflicts and applicability exceptions require operations review", rid)
            matrix.append({"requirement": requirement, "evidence": matches, "recorded": recorded,
                           "meaning": "Evidence received, not authenticated approval or execution authority"})
        cash = None
        if r["type"] in {"transfer", "distribution"} and (r["type"] == "distribution" or d["method"] == "cash"):
            cash = d.get("amount")
            if cash is None:
                add(findings, "unknown-amount", "Cash amount is unspecified; do not infer the balance even for a full transfer", rid)
            elif account is not None:
                cash_requests.setdefault(account["account_id"], []).append((rid, dec(cash)))
                if account.get("available_cash") is None:
                    add(findings, "cash-data-gap", "Available cash is unknown; requested amount is not validated", rid)
                elif dec(cash) > dec(account["available_cash"]):
                    add(findings, "cash-shortfall", "Requested cash exceeds supplied available cash", rid)
            if r["type"] == "distribution" and d.get("tax_instruction_ref") is None:
                add(findings, "tax-instruction-gap", "Tax/withholding instruction evidence is not supplied; no tax default is selected", rid)
        if r["type"] == "transfer":
            if d["method"] == "cash" and d["transfer_scope"] == "full" and account is not None:
                if account.get("positions") is None or account.get("positions"):
                    add(findings, "full-cash-scope-review", "Full cash transfer cannot imply liquidation or disposition of unknown/nonempty holdings", rid)
                if cash is not None and account.get("available_cash") is not None and dec(cash) != dec(account["available_cash"]):
                    add(findings, "full-cash-amount-review", "Full cash instruction differs from supplied available cash; confirm scope without adjusting the instruction", rid)
            if any(pid not in parties for pid in d["destination_owner_party_ids"]):
                add(findings, "destination-owner-gap", "Destination owner reference does not resolve", rid)
            if account and set(d["destination_owner_party_ids"]) != set(account["owner_party_ids"]):
                add(findings, "ownership-change-review", "Destination owners differ; route to operations and the appropriate tax/legal reviewer", rid)
            if d["method"] == "in-kind":
                if not d["positions"]:
                    add(findings, "missing-positions", "In-kind request requires explicit security quantities, including a full transfer", rid)
                holdings = {p["security_id"]: p for p in (account or {}).get("positions") or []}
                for p in d["positions"]:
                    cited(p, doc, findings, rid + ".positions")
                    position_requests.setdefault((r["account_id"], p["security_id"]), []).append((rid, dec(p["quantity"])))
                    if p["security_id"] not in holdings or dec(p["quantity"]) > dec(holdings[p["security_id"]]["quantity"]):
                        add(findings, "position-data-gap", "Requested security quantity exceeds or lacks supplied holdings evidence", rid, security_id=p["security_id"])
                if d["transfer_scope"] == "full" and {p["security_id"]: dec(p["quantity"]) for p in d["positions"]} != {sid: dec(p["quantity"]) for sid, p in holdings.items()}:
                    add(findings, "full-transfer-gap", "Full in-kind instruction does not match the supplied complete holdings list", rid)
        elif r["type"] == "authority":
            if d["subject_party_id"] not in parties:
                add(findings, "authority-party-gap", "Authority subject does not resolve; no legal authority is determined", rid)
            if d["change"] == "replace" and (not nonempty(d.get("replaces_party_id")) or d["replaces_party_id"] not in parties or d["replaces_party_id"] == d["subject_party_id"]):
                add(findings, "authority-replacement-gap", "Replacement must identify the distinct existing party whose recorded authority is being replaced", rid)
        elif r["type"] == "beneficiary":
            if d["change"] == "replace" and not d["beneficiaries"]:
                add(findings, "beneficiary-gap", "Replacement schedule is empty", rid)
            for b in d["beneficiaries"]:
                cited(b, doc, findings, rid + ".beneficiaries")
                if b["party_id"] not in parties:
                    add(findings, "beneficiary-party-gap", "Beneficiary party reference does not resolve", rid)
            for tier in sorted({b["tier"] for b in d["beneficiaries"]}):
                if sum(dec(b["share"]) for b in d["beneficiaries"] if b["tier"] == tier) != 1:
                    add(findings, "beneficiary-total", f"{tier} replacement shares do not total 100 percent", rid)
        packages.append({"service_request_id": rid, "request": r, "account_evidence": account,
                         "condition_matrix": matrix, "supplied_conditions": conditions,
                         "request_questions": findings[start:], "instruction_status": "draft-not-submitted"})
    aggregate = []
    for aid, requested in cash_requests.items():
        total = sum((v for _, v in requested), dec(0))
        balance = accounts[aid].get("available_cash")
        aggregate.append({"account_id": aid, "request_ids": [r for r, _ in requested], "requested_cash_total": money(total), "available_cash": None if balance is None else money(balance)})
        if balance is not None and total > dec(balance) and len(requested) > 1:
            add(findings, "aggregate-cash-shortfall", "Combined requests exceed supplied available cash; no sequencing or funding is inferred", aid)
    for (aid, sid), requested in position_requests.items():
        holding = next((p for p in accounts.get(aid, {}).get("positions") or [] if p["security_id"] == sid), None)
        if holding and len(requested) > 1 and sum(v for _, v in requested) > dec(holding["quantity"]):
            add(findings, "aggregate-position-shortfall", "Combined transfers exceed supplied holding quantity", aid, security_id=sid)
    result = common_result(doc)
    result.update(parties=doc["parties"], service_packages=packages, aggregate_cash_requests=aggregate,
                  operations_open_items=findings, submission_status="not-submitted",
                  limitations=["Received documents and named requestors are not verified authority, signatures, entitlements, sanctions clearance or destination authentication.",
                               "No account, custody, CRM, money movement or beneficiary/authority write API is called. Tax, eligibility and legal decisions remain with the appropriate owner."])
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    errors = validate_output_envelope(out, SKILL)
    snapshot = out.get("result", {}).get("input_snapshot") if isinstance(out, dict) and isinstance(out.get("result"), dict) else None
    try:
        expected = build(snapshot)
        if out != expected:
            errors.append("output differs from full reconstruction of source snapshot, request identities, conditions or arithmetic")
    except (ValueError, TypeError, KeyError) as exc:
        errors.append(f"invalid input snapshot: {exc}")
    return errors
