"""Source-bound corridor economics and separate customer/nostro obligations."""
from datetime import datetime, timezone
from payment_foundation import dec, finding, load_resource

SKILL = "cross-border-payment-designer"
SUPPORTED_JURISDICTIONS = {"US", "EA", "UK", "BR", "IN", "CA"}
CURRENCIES = {"US": "USD", "EA": "EUR", "UK": "GBP", "BR": "BRL", "IN": "INR", "CA": "CAD"}


def stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return result.astimezone(timezone.utc)


def validate(data):
    errors, identities = [], set()
    for side in ("payer", "payee"):
        party = data.get(side)
        if not isinstance(party, dict):
            errors.append(side + " must be an object")
            continue
        for key in ("entity_id", "account_ref", "jurisdiction", "currency"):
            if not isinstance(party.get(key), str) or not party[key].strip():
                errors.append(side + " requires " + key)
    if data.get("use_case") not in {"consumer-remittance", "commercial-payment", "correspondent-transfer"}:
        errors.append("unsupported corridor use_case")
    try:
        if dec(data.get("principal")) <= 0:
            errors.append("principal must be positive")
        stamp(data.get("evaluate_at"))
    except (ValueError, TypeError, AttributeError, ArithmeticError):
        errors.append("finite positive principal and aware evaluate_at required")
    if not isinstance(data.get("options"), list):
        return errors + ["options must be a list"]
    for option in data["options"]:
        if not isinstance(option, dict):
            errors.append("option must be an object")
            continue
        oid = option.get("option_id")
        if not isinstance(oid, str) or not oid.strip() or oid in identities:
            errors.append("unique option_id required")
        identities.add(oid)
        if option.get("charge_convention") not in {"OUR", "SHA", "BEN", "not-applicable", "unknown"}:
            errors.append("unsupported charge convention")
        if not isinstance(option.get("fees_complete"), bool):
            errors.append("fees_complete boolean required")
        for key in ("fees", "legs", "regulatory_reviews"):
            if not isinstance(option.get(key), list):
                errors.append(key + " must be a list")
        if not isinstance(option.get("sanctions_review", {}), dict):
            errors.append("sanctions_review must be an object")
        ids = set()
        for fee in option.get("fees", []):
            if fee.get("fee_id") in ids or not fee.get("fee_id"):
                errors.append("unique fee identity required per option")
            ids.add(fee.get("fee_id"))
            if fee.get("side") not in {"payer-addition", "principal-deduction", "recipient-deduction"} or fee.get("kind") not in {"fee", "tax"}:
                errors.append("fee requires explicit side and fee/tax kind")
            for key in ("currency", "charging_entity", "jurisdiction"):
                if not isinstance(fee.get(key), str) or not fee[key]:
                    errors.append("fee requires " + key)
            if fee.get("amount") is not None:
                try:
                    if dec(fee["amount"]) < 0:
                        errors.append("fee cannot be negative")
                except (ValueError, TypeError, ArithmeticError):
                    errors.append("finite fee amount or null required")
        ids, leg_ids = set(), set()
        for leg in option.get("legs", []):
            for key in ("leg_id", "economic_id", "from_entity", "from_account_ref", "to_entity", "to_account_ref", "currency", "method", "jurisdiction"):
                if not isinstance(leg.get(key), str) or not leg[key]:
                    errors.append("leg requires " + key)
            if leg.get("economic_id") in ids or leg.get("leg_id") in leg_ids:
                errors.append("duplicate leg or economic leg identity")
            ids.add(leg.get("economic_id"))
            leg_ids.add(leg.get("leg_id"))
            if leg.get("purpose") not in {"customer-collection", "correspondent-delivery", "local-payout", "nostro-funding"}:
                errors.append("unsupported leg purpose")
            if leg.get("amount") is not None:
                try:
                    if dec(leg["amount"]) < 0:
                        errors.append("leg amount cannot be negative")
                except (ValueError, TypeError, ArithmeticError):
                    errors.append("finite leg amount or null required")
        quote = option.get("fx_quote")
        if quote is not None:
            if not isinstance(quote, dict):
                errors.append("fx_quote must be object or null")
            else:
                try:
                    if dec(quote.get("rate")) <= 0:
                        errors.append("FX rate must be positive")
                    if stamp(quote["quoted_at"]) > stamp(quote["expires_at"]):
                        errors.append("FX quote window is reversed")
                except (KeyError, ValueError, TypeError, AttributeError, ArithmeticError):
                    errors.append("FX quote requires finite positive rate and aware timestamps")
                if quote.get("kind") not in {"firm", "indicative"}:
                    errors.append("FX kind must be firm or indicative")
        if not isinstance(option.get("source_ids"), list) or not option["source_ids"]:
            errors.append("each option requires source_ids")
        for review in option.get("regulatory_reviews", []) + [option.get("sanctions_review", {})]:
            for key in ("valid_from", "valid_until"):
                if review.get(key) is not None:
                    try:
                        stamp(review[key])
                    except (ValueError, AttributeError, TypeError):
                        errors.append("review timestamp must be timezone aware")
    return errors


def analyze(request):
    data = request["data"]
    payer, payee = data["payer"], data["payee"]
    findings, rows = [], []
    when, principal = stamp(data["evaluate_at"]), dec(data["principal"])
    profiles = load_resource("regional-profiles.json")["profiles"]
    global_gaps = []
    if payer["jurisdiction"] != request["jurisdiction"] or payer["jurisdiction"] == payee["jurisdiction"]:
        global_gaps.append("corridor-jurisdiction-mismatch")
    if any(CURRENCIES.get(p["jurisdiction"]) != p["currency"] for p in (payer, payee)):
        global_gaps.append("unsupported-corridor-currency-pair")
    if when.date().isoformat() != request["as_of"]:
        global_gaps.append("evaluation-date-mismatch")
    if not data.get("accountable_reviewer"):
        global_gaps.append("accountable-corridor-owner-missing")
    for option in data["options"]:
        gaps = list(global_gaps)
        pc, rc = payer["currency"], payee["currency"]
        additions = deductions = recipient_deductions = dec("0")
        known = option["fees_complete"]
        if not known:
            gaps.append("fee-inventory-incomplete")
        for fee in option["fees"]:
            expected = rc if fee["side"] == "recipient-deduction" else pc
            if fee.get("amount") is None or fee["currency"] != expected:
                known = False
                gaps.append("fee-value-or-currency-unresolved")
                continue
            value = dec(fee["amount"])
            if fee["side"] == "payer-addition":
                additions += value
            elif fee["side"] == "principal-deduction":
                deductions += value
            else:
                recipient_deductions += value
        rate, quote = (dec("1") if pc == rc else None), option.get("fx_quote")
        if pc != rc:
            if not quote:
                gaps.append("missing-fx-quote")
            elif (quote.get("base_currency"), quote.get("quote_currency")) == (pc, rc):
                rate = dec(quote["rate"])
            elif (quote.get("base_currency"), quote.get("quote_currency")) == (rc, pc):
                rate = dec("1") / dec(quote["rate"])
            else:
                gaps.append("fx-orientation-mismatch")
            if quote and (not stamp(quote["quoted_at"]) <= when <= stamp(quote["expires_at"]) or quote["kind"] != "firm" or not quote.get("quote_ref")):
                gaps.append("fx-not-current-firm-evidenced")
        sender = principal + additions if known else None
        receipt = (principal - deductions) * rate - recipient_deductions if known and rate is not None else None
        if deductions > principal or (receipt is not None and receipt < 0):
            gaps.append("fees-exceed-transfer-value")
            receipt = None
        convention = option["charge_convention"]
        if convention == "unknown" or not option.get("charge_convention_review_ref"):
            gaps.append("charge-convention-applicability-unresolved")
        if (convention == "OUR" and (deductions or recipient_deductions)) or (convention == "BEN" and additions):
            gaps.append("charge-convention-fee-allocation-conflict")
        legs = option["legs"]
        if not legs:
            gaps.append("missing-delivery-legs")
        payout = [leg for leg in legs if leg["purpose"] == "local-payout"]
        if len(payout) != 1 or any(payout[0].get(k) != v for k, v in (("to_entity", payee["entity_id"]), ("to_account_ref", payee["account_ref"]), ("currency", rc), ("jurisdiction", payee["jurisdiction"]))):
            gaps.append("final-beneficiary-payout-binding-unresolved")
        elif payout[0].get("amount") is None or receipt is None or dec(payout[0]["amount"]) != receipt:
            gaps.append("final-payout-receipt-unreconciled")
        collections = [leg for leg in legs if leg["purpose"] == "customer-collection"]
        if len(collections) != 1 or any(collections[0].get(k) != v for k, v in (("from_entity", payer["entity_id"]), ("from_account_ref", payer["account_ref"]), ("currency", pc), ("jurisdiction", payer["jurisdiction"]))):
            gaps.append("payer-collection-binding-unresolved")
        elif collections[0].get("amount") is None or sender is None or dec(collections[0]["amount"]) != sender:
            gaps.append("collection-debit-unreconciled")
        delivery = [leg for leg in legs if leg["purpose"] != "nostro-funding"]
        if delivery and (delivery[0]["purpose"] != "customer-collection" or delivery[-1]["purpose"] != "local-payout"):
            gaps.append("delivery-leg-order-unresolved")
        for previous, current in zip(delivery, delivery[1:]):
            if current.get("previous_leg_id") != previous["leg_id"] or current["from_entity"] != previous["to_entity"]:
                gaps.append("delivery-entity-chain-unresolved")
            if current["from_account_ref"] != previous["to_account_ref"] and not current.get("account_transition_review_ref"):
                gaps.append("intermediate-account-transition-unresolved")
        intermediate_reconciliation = []
        for leg in delivery:
            if leg["purpose"] != "correspondent-delivery":
                continue
            expected_amount = None
            if known and deductions <= principal:
                if leg["currency"] == pc:
                    expected_amount = principal - deductions
                elif leg["currency"] == rc and rate is not None:
                    expected_amount = (principal - deductions) * rate
            actual_amount = None if leg.get("amount") is None else dec(leg["amount"])
            difference = None if expected_amount is None or actual_amount is None else actual_amount - expected_amount
            if difference is None or difference != 0:
                gaps.append("intermediary-funding-amount-unreconciled")
            intermediate_reconciliation.append({"leg_id": leg["leg_id"], "currency": leg["currency"], "expected_transfer_principal": None if expected_amount is None else str(expected_amount), "declared_amount": None if actual_amount is None else str(actual_amount), "difference": None if difference is None else str(difference)})
        entities = {payer["entity_id"], payee["entity_id"]}
        jurisdictions = {payer["jurisdiction"], payee["jurisdiction"]}
        local_entities = {payer["jurisdiction"]: {payer["entity_id"]}, payee["jurisdiction"]: {payee["entity_id"]}}
        for fee in option["fees"]:
            entities.add(fee["charging_entity"])
            jurisdictions.add(fee["jurisdiction"])
            local_entities.setdefault(fee["jurisdiction"], set()).add(fee["charging_entity"])
        for leg in legs:
            entities.update((leg["from_entity"], leg["to_entity"]))
            jurisdictions.add(leg["jurisdiction"])
            local_entities.setdefault(leg["jurisdiction"], set()).update((leg["from_entity"], leg["to_entity"]))
            if leg["jurisdiction"] not in SUPPORTED_JURISDICTIONS:
                gaps.append("unsupported-intermediary-jurisdiction")
            if leg["currency"] not in CURRENCIES.values():
                gaps.append("unsupported-intermediary-currency")
            profile = profiles.get(leg["method"])
            if profile and (profile["jurisdiction"] != leg["jurisdiction"] or profile["currency"] != leg["currency"] or leg["purpose"] != "local-payout"):
                gaps.append("local-method-leg-scope-mismatch")
            if profile and not profile["reviewed_on"] <= request["as_of"] <= profile["review_due"]:
                gaps.append("local-method-profile-review-overdue")
            if not all(leg.get(k) for k in ("obligation_ref", "access_review_ref", "funding_review_ref", "timing_review_ref")) or leg.get("amount") is None:
                gaps.append("leg-obligation-operating-evidence-incomplete")
        reviews = option["regulatory_reviews"]
        for jurisdiction in sorted(jurisdictions):
            matches = [r for r in reviews if r.get("jurisdiction") == jurisdiction and r.get("use_case") == data["use_case"]]
            if jurisdiction not in SUPPORTED_JURISDICTIONS:
                gaps.append("unsupported-involved-jurisdiction")
            if len(matches) != 1 or not all(matches[0].get(k) for k in ("reviewer", "reference", "rule_version", "activity_scope_ref")) or not local_entities[jurisdiction].issubset(set(matches[0].get("entity_ids", []))) or not (matches[0].get("valid_from") and matches[0].get("valid_until") and stamp(matches[0]["valid_from"]) <= when <= stamp(matches[0]["valid_until"])):
                gaps.append("scoped-regulatory-review-unresolved:" + jurisdiction)
        sanctions = option.get("sanctions_review", {})
        if set(sanctions.get("entity_ids", [])) != entities or set(sanctions.get("jurisdictions", [])) != jurisdictions or not all(sanctions.get(k) for k in ("reference", "reviewer", "policy_version", "valid_from", "valid_until")):
            gaps.append("screening-scope-unresolved")
        elif not stamp(sanctions["valid_from"]) <= when <= stamp(sanctions["valid_until"]):
            gaps.append("screening-review-not-current")
        if not option.get("expected_delivery_review_ref"):
            gaps.append("delivery-comparability-unresolved")
        gaps = list(dict.fromkeys(gaps))
        findings.extend(finding(g, option["option_id"] + ": " + g.replace("-", " "), option["source_ids"]) for g in gaps)
        rows.append({"option_id": option["option_id"], "payer_total_debit": None if sender is None else {"amount": str(sender), "currency": pc}, "recipient_expected_receipt": None if receipt is None else {"amount": str(receipt), "currency": rc}, "fx_quote": quote, "applied_recipient_units_per_payer_unit": None if rate is None else str(rate), "fees": option["fees"], "charge_convention": convention, "customer_delivery_legs": [leg for leg in legs if leg["purpose"] != "nostro-funding"], "intermediary_reconciliation": intermediate_reconciliation, "separate_nostro_funding_obligations": [leg for leg in legs if leg["purpose"] == "nostro-funding"], "comparison_ready": not gaps, "gaps": gaps, "source_ids": option["source_ids"], "compliance_determined": False, "receipt_guaranteed": False})
    if not rows:
        findings.append(finding("missing-corridor-options", "Supply a concrete delivery option and separate funding legs."))
    return {"result": {"module": "corridor-design", "use_case": data["use_case"], "payer": payer, "payee": payee, "accountable_reviewer": data.get("accountable_reviewer"), "options": rows, "unlike_currency_totals_aggregated": False, "selection_made": False}, "findings": findings, "handoffs": [{"target_skill": "payment-liquidity-and-funding-analyzer", "reason": "Analyze each corridor funding obligation in the native corridor module by legal entity, account, currency and time; quoted FX does not create liquidity.", "required_inputs": ["corridor native accounts, obligations and separately evidenced funding events", "source snapshot", "unresolved corridor issues"]}, {"target_skill": "payment-initiation-control-reviewer", "reason": "Prepare separate exact instructions only under a supported native jurisdiction adapter; retain unsupported regional and legal gaps.", "required_inputs": ["one exact instruction per economically distinct leg", "access, consent and scoped legal/screening reviews", "unresolved corridor findings"]}], "limitations": ["Planning arithmetic is unrounded decimal scenario output, not a legally compliant customer disclosure, quote guarantee or payment instruction.", "Only USD/US, EUR/euro-area, GBP/UK, BRL/Brazil, INR/India and CAD/Canada source-oriented corridors are modeled; intermediary access is always supplied evidence.", "OUR/SHA/BEN are supplied contractual charging conventions and never establish which option a scheme permits or the amount actually delivered.", "Normalized leg obligations do not implement SWIFT MT/ISO messages, funds-transfer execution, sanctions screening or local regulatory determination."]}
