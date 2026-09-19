"""Normalized agent-commerce evidence review, never a signer or protocol adapter."""
from datetime import datetime, timezone
from decimal import Decimal
from payment_foundation import dec, finding
from payment_contract import stable_hash

MODES = {"initiation", "credential", "platform"}
PROPOSAL_FIELDS = ("instruction_id", "principal_ref", "agent_ref", "merchant_ref",
                   "payee_account_ref", "credential_ref", "checkout_id", "cart_hash",
                   "amount", "currency", "execution_at", "merchant_origin", "idempotency_key")
REVIEWS = ("accountable_owner_ref", "principal_identity_ref", "agent_identity_ref", "intent_review_ref",
           "merchant_verification_ref", "revocation_check_ref", "policy_review_ref",
           "human_oversight_ref", "atomic_reservation_review_ref")


def instant(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("offset timestamp required")
    return result.astimezone(timezone.utc)


def amount(value, positive=False):
    if not isinstance(value, str):
        raise ValueError("decimal-string amount required")
    result = dec(value)
    if result < 0 or (positive and result == 0):
        raise ValueError("amount outside nonnegative/positive domain")
    return result


def text(value):
    return isinstance(value, str) and bool(value.strip())


def validate(data, mode):
    errors = []
    if mode not in MODES:
        return ["unknown agent-commerce module"]
    for key in ("intent", "proposal", "cart", "review", "protocol"):
        if not isinstance(data.get(key), dict):
            errors.append(key + " must be an object")
    for key in ("history",):
        if not isinstance(data.get(key), list):
            errors.append(key + " must be a list; completeness is declared separately")
    if mode in {"credential", "platform"} and not isinstance(data.get(mode), dict):
        errors.append(mode + " must be an object")
    if errors:
        return errors
    intent, proposal, cart = data["intent"], data["proposal"], data["cart"]
    required = [("intent", intent, ("intent_id", "principal_ref", "agent_ref", "currency", "purpose")),
                ("proposal", proposal, PROPOSAL_FIELDS),
                ("cart", cart, ("checkout_id", "merchant_ref", "currency")),
                ("protocol", data["protocol"], ("family", "version"))]
    for name, row, keys in required:
        for key in keys:
            if not text(row.get(key)):
                errors.append(name + " requires " + key)
    for key in ("merchant_refs", "item_refs"):
        values = intent.get(key)
        if not isinstance(values, list) or not values or any(not text(x) for x in values) or len(values) != len(set(values)):
            errors.append("intent requires unique nonempty " + key)
    for key in ("max_payments", "delegation_depth", "max_delegation_depth"):
        value = intent.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append("intent requires nonnegative integer " + key)
    for key in ("revoked", "allows_subdelegation"):
        if intent.get(key) is not None and not isinstance(intent[key], bool):
            errors.append("intent " + key + " must be boolean or null")
    if data.get("ledger_complete") is not None and not isinstance(data["ledger_complete"], bool):
        errors.append("ledger_complete must be boolean or null")
    numbers = [(proposal, "amount", True), (intent, "max_per_payment", False), (intent, "total_limit", False)]
    dates = [(data, "review_at"), (intent, "valid_from"), (intent, "valid_until"), (proposal, "execution_at")]
    for key in ("observed_at", "valid_until"):
        if data["review"].get(key) is not None:
            dates.append((data["review"], key))
    for row, key in dates:
        try:
            instant(row.get(key))
        except (AttributeError, ValueError, TypeError):
            errors.append("valid offset timestamp required: " + key)
    items = cart.get("items")
    if not isinstance(items, list):
        errors.append("cart.items must be a list")
        items = []
    for row in items:
        if not isinstance(row, dict) or not text(row.get("item_ref")):
            errors.append("cart item requires item_ref")
            continue
        if not isinstance(row.get("quantity"), int) or isinstance(row["quantity"], bool) or row["quantity"] <= 0:
            errors.append("item quantity must be positive integer")
        numbers.append((row, "unit_amount", False))
    for key in ("tax", "shipping", "discount"):
        numbers.append((cart, key, False))
    ids, keys, checkouts = set(), set(), set()
    for row in data["history"]:
        if not isinstance(row, dict):
            errors.append("history row must be an object")
            continue
        for key in ("instruction_id", "intent_id", "idempotency_key", "checkout_id", "currency"):
            if not text(row.get(key)):
                errors.append("history requires " + key)
        if text(row.get("instruction_id")) and text(row.get("idempotency_key")):
            if row["instruction_id"] in ids or row["idempotency_key"] in keys:
                errors.append("duplicate immutable history identity")
            ids.add(row["instruction_id"]); keys.add(row["idempotency_key"])
        if text(row.get("checkout_id")):
            if row["checkout_id"] in checkouts:
                errors.append("duplicate economic checkout in spend history")
            checkouts.add(row["checkout_id"])
        if row.get("state") not in {"settled", "pending", "failed", "unknown"}:
            errors.append("unsupported history state")
        if row.get("amount") is not None:
            numbers.append((row, "amount", True))
        dates.append((row, "observed_at"))
    if mode == "credential":
        row = data["credential"]
        if row.get("state") not in {"active", "disabled", "unknown"}:
            errors.append("unsupported credential state")
        if not isinstance(row.get("prior_use_ids"), list) or any(not text(x) for x in row.get("prior_use_ids", [])):
            errors.append("credential prior_use_ids must be a list of opaque references")
        numbers.append((row, "max_amount", False))
        dates.extend((row, key) for key in ("valid_from", "valid_until"))
    for row, key, positive in numbers:
        try:
            amount(row.get(key), positive)
        except (ValueError, TypeError, ArithmeticError):
            errors.append("finite decimal-string " + key + " required")
    for row, key in dates:
        try:
            instant(row.get(key))
        except (AttributeError, ValueError, TypeError):
            errors.append("valid offset timestamp required: " + key)
    evidence_rows = [intent, proposal, cart, data["review"], data["protocol"], *items, *data["history"]]
    if mode in {"credential", "platform"}:
        evidence_rows.append(data[mode])
    for row in evidence_rows:
        if isinstance(row, dict) and (not isinstance(row.get("source_ids"), list) or not row["source_ids"]):
            errors.append("every native evidence row requires source_ids")
    return errors


def analyze(request, mode):
    data = request["data"]
    intent, proposal, cart, review = (data[key] for key in ("intent", "proposal", "cart", "review"))
    now, execution = instant(data["review_at"]), instant(proposal["execution_at"])
    gaps = []
    add = lambda code: gaps.append(code) if code not in gaps else None
    if now.date().isoformat() != request["as_of"] or execution < now:
        add("review-or-execution-time-unresolved")
    if not instant(intent["valid_from"]) <= now <= execution <= instant(intent["valid_until"]):
        add("intent-outside-validity")
    if intent.get("revoked") is not False:
        add("intent-revocation-unresolved")
    if proposal["principal_ref"] != intent["principal_ref"] or proposal["agent_ref"] != intent["agent_ref"]:
        add("principal-or-agent-mismatch")
    if proposal["merchant_ref"] not in intent["merchant_refs"]:
        add("merchant-outside-intent")
    if proposal["currency"] != intent["currency"]:
        add("currency-outside-intent")
    if intent["delegation_depth"] > intent["max_delegation_depth"] or (intent["delegation_depth"] > 0 and intent.get("allows_subdelegation") is not True):
        add("subdelegation-outside-intent")
    if proposal["cart_hash"] != stable_hash(cart):
        add("cart-hash-mismatch")
    if cart["checkout_id"] != proposal["checkout_id"] or cart["merchant_ref"] != proposal["merchant_ref"] or cart["currency"] != proposal["currency"]:
        add("checkout-binding-mismatch")
    if not cart["items"] or any(row["item_ref"] not in intent["item_refs"] for row in cart["items"]):
        add("cart-items-outside-intent")
    if len({row["item_ref"] for row in cart["items"]}) != len(cart["items"]):
        add("duplicate-cart-item")
    subtotal = sum((amount(r["unit_amount"]) * r["quantity"] for r in cart["items"]), Decimal(0))
    total = subtotal + amount(cart["tax"]) + amount(cart["shipping"]) - amount(cart["discount"])
    proposed = amount(proposal["amount"], True)
    if total <= 0 or total != proposed:
        add("cart-total-mismatch")
    if proposed > amount(intent["max_per_payment"]):
        add("per-payment-limit-exceeded")
    if any(not text(review.get(key)) for key in REVIEWS):
        add("trust-or-oversight-review-missing")
    if review.get("jurisdiction") != request["jurisdiction"] or review.get("participant") != request["participant"]:
        add("review-participant-or-jurisdiction-mismatch")
    if review.get("intent_hash") != stable_hash(intent) or review.get("proposal_hash") != stable_hash(proposal):
        add("review-binding-mismatch")
    if not review.get("observed_at") or not review.get("valid_until"):
        add("review-validity-unresolved")
    elif not instant(review["observed_at"]) <= now <= execution <= instant(review["valid_until"]):
        add("review-outside-validity")
    protocol = data["protocol"]
    if protocol["family"] not in {"ap2", "acp", "institution-defined"} or any(not text(protocol.get(key)) for key in ("source_ref", "deployment_profile_ref", "interoperability_review_ref", "verification_review_ref")):
        add("protocol-deployment-review-unresolved")
    if protocol["family"] in {"ap2", "acp"} and intent["delegation_depth"] > 0:
        add("protocol-subdelegation-not-implemented")
    history_ok = data.get("ledger_complete") is True
    if not history_ok:
        add("spend-history-incomplete")
    committed, count = Decimal(0), 0
    for row in data["history"]:
        if row["intent_id"] != intent["intent_id"] or row["currency"] != intent["currency"] or instant(row["observed_at"]) > now:
            add("spend-history-scope-conflict"); history_ok = False
        if row["instruction_id"] == proposal["instruction_id"] or row["idempotency_key"] == proposal["idempotency_key"] or row["checkout_id"] == proposal["checkout_id"]:
            add("replay-or-retry-requires-investigation")
        if row["state"] == "unknown" or (row["state"] == "failed" and not text(row.get("terminal_nonexecution_ref"))):
            add("prior-outcome-unresolved"); history_ok = False
        if row["state"] in {"settled", "pending"}:
            if row.get("amount") is None:
                add("prior-spend-amount-unknown"); history_ok = False
            else:
                committed += amount(row["amount"], True)
            count += 1
    headroom = amount(intent["total_limit"]) - committed if history_ok else None
    if headroom is not None and proposed > headroom:
        add("aggregate-limit-exceeded")
    if history_ok and count + 1 > intent["max_payments"]:
        add("payment-count-limit-exceeded")
    if mode == "credential":
        credential = data["credential"]
        for key in ("credential_ref", "principal_ref", "agent_ref", "merchant_ref", "merchant_origin", "currency"):
            if credential.get(key) != proposal[key]:
                add("credential-scope-mismatch")
        if credential["state"] != "active" or credential.get("single_use") is not True or credential["prior_use_ids"]:
            add("credential-state-or-use-unresolved")
        if not instant(credential["valid_from"]) <= now <= execution <= instant(credential["valid_until"]):
            add("credential-outside-validity")
        if proposed > amount(credential["max_amount"]):
            add("credential-allowance-exceeded")
        if credential.get("authentication_binding_hash") != stable_hash(proposal) or any(not text(credential.get(key)) for key in ("authentication_review_ref", "token_domain_review_ref", "revocation_review_ref")):
            add("credential-authentication-unresolved")
    if mode == "platform":
        platform = data["platform"]
        for key in ("merchant_ref", "payee_account_ref", "checkout_id", "cart_hash"):
            if platform.get(key) != proposal[key]:
                add("platform-checkout-or-payee-mismatch")
        if any(not text(platform.get(key)) for key in ("platform_ref", "seller_ref", "merchant_of_record_ref", "customer_disclosure_ref", "terms_ref", "refund_owner_ref", "dispute_owner_ref", "payout_owner_ref", "delegation_acceptance_review_ref")):
            add("platform-responsibility-unresolved")
    evidence_rows = [intent, proposal, cart, review, protocol, *cart["items"], *data["history"]]
    if mode in {"credential", "platform"}:
        evidence_rows.append(data[mode])
    source_ids = sorted({sid for row in evidence_rows for sid in row["source_ids"]})
    result = {"module": "agent-commerce-" + mode, "intent_id": intent["intent_id"],
              "accountable_owner_ref": review.get("accountable_owner_ref"),
              "proposal_binding": proposal, "cart_calculated_amount": str(total),
              "currency": intent["currency"], "known_committed_amount": str(committed) if history_ok else None,
              "remaining_budget_before_proposal": str(headroom) if headroom is not None else None,
              "remaining_payment_count_before_proposal": intent["max_payments"] - count if history_ok else None,
              "assessment": "needs-evidence" if gaps else "supplied-evidence-for-human-review",
              "gaps": gaps, "source_ids": source_ids, "protocol_conformance_verified": False,
              "cryptographic_verification_performed": False, "payment_authorized": False,
              "credential_released": False, "reservation_created": False, "payment_submitted": False}
    target = "payment-credential-authentication-reviewer" if mode == "initiation" else "payment-initiation-control-reviewer"
    return {"result": result, "findings": [finding(code, code.replace("-", " "), source_ids) for code in gaps],
            "handoffs": [{"target_skill": target, "reason": "Prepare separate exact credential and native initiation evidence after agent-commerce review.", "required_inputs": ["original intent/cart/proposal and sources", "current native target schema", "all unresolved trust, budget and execution findings"]}],
            "limitations": ["Normalized library evidence contract; no AP2/ACP serializer, signature validation, live revocation check or token/payment connector.",
                            "Every review reference and declared prior outcome needs independent source verification. A hash detects internal changes, not false source data.",
                            "Budget arithmetic is a snapshot, not an atomic reservation. Pending spend consumes headroom; unknown outcomes make available headroom unknown.",
                            "No mandate, credential or platform declaration supplies legal authority, SCA compliance, agent interoperability or approval to execute."]}
