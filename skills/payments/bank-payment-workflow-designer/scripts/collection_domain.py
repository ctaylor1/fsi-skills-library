"""Request-for-payment/pay-by-bank collection design; messages are not funds or intent."""
from datetime import date
from payment_foundation import dec, finding, load_rail_profile

SKILL = "bank-payment-workflow-designer"
BOUND = ("request_id", "payer_ref", "beneficiary_ref", "amount", "currency")


def validate(data):
    errors, ids, messages, responses = [], set(), set(), set()
    rows = data.get("requests")
    if not isinstance(rows, list):
        return ["requests must be a list"]
    for row in rows:
        if not isinstance(row, dict):
            errors.append("collection request must be an object")
            continue
        for key in (*BOUND, "message_id", "rail_profile_id", "requester_ref"):
            if key != "amount" and (not isinstance(row.get(key), str) or not row[key].strip()):
                errors.append("request requires " + key)
        if row.get("request_id") in ids or row.get("message_id") in messages:
            errors.append("duplicate request or immutable message ID")
        ids.add(row.get("request_id")); messages.add(row.get("message_id"))
        if row.get("channel") not in {"request-for-payment", "pay-by-bank"} or row.get("state") not in {"open", "cancelled", "expired", "unknown"}:
            errors.append("unsupported collection channel/state")
        try:
            if dec(row.get("amount")) < 0:
                errors.append("request amount must be nonnegative")
        except (TypeError, ValueError, ArithmeticError):
            errors.append("finite request amount required")
        for key in ("issued_on", "expires_on"):
            try:
                date.fromisoformat(row[key])
            except (KeyError, TypeError, ValueError):
                errors.append("valid " + key + " date required")
        if not isinstance(row.get("source_ids"), list) or not row["source_ids"]:
            errors.append("each request requires source_ids")
        if not isinstance(row.get("payer_response", {}), dict) or not isinstance(row.get("access_review", {}), dict):
            errors.append("response/access_review must be objects")
        response = row.get("payer_response", {})
        if not isinstance(response, dict):
            continue
        response_id = response.get("response_id")
        if response_id is not None:
            if not isinstance(response_id, str) or not response_id.strip():
                errors.append("payer response ID must be a nonempty string")
            elif response_id in responses:
                errors.append("duplicate immutable payer response ID")
            else:
                responses.add(response_id)
        if response and response.get("decision") not in {"accept", "reject", "unknown"}:
            errors.append("unsupported payer response")
    return errors


def analyze(request):
    findings, rows = [], []
    for row in request["data"]["requests"]:
        gaps = []
        profile = load_rail_profile(row["rail_profile_id"])
        if not profile or profile["jurisdiction"] != request["jurisdiction"] or row["currency"] not in profile["currencies"] or "credit" not in profile["directions"]:
            gaps.append("unsupported-collection-rail")
        elif not profile["reviewed_on"] <= request["as_of"] <= profile["review_due"]:
            gaps.append("rail-profile-review-required")
        if row["channel"] == "request-for-payment" and row["rail_profile_id"] not in {"US-FEDNOW", "US-RTP"}:
            gaps.append("request-for-payment-profile-not-implemented")
        if not row["issued_on"] <= request["as_of"] <= row["expires_on"] or row["state"] != "open":
            gaps.append("collection-not-current-open")
        if any(not row.get("access_review", {}).get(k) for k in ("participant_reach_ref", "scheme_profile_ref", "requester_legitimacy_ref")):
            gaps.append("collection-access-review-unresolved")
        response = row.get("payer_response", {})
        expected = {key: row[key] for key in BOUND}
        if response.get("decision") != "accept":
            gaps.append("payer-acceptance-not-evidenced")
        elif response.get("binding") != expected or not response.get("consent_ref") or not response.get("review_ref") or not response.get("response_id"):
            gaps.append("payer-response-binding-unresolved")
        if dec(row["amount"]) == 0:
            gaps.append("zero-value-probe-not-payment")
        for gap in gaps:
            findings.append(finding(gap, row["request_id"] + ": " + gap.replace("-", " "), row["source_ids"]))
        rows.append({"request_id": row["request_id"], "message_id": row["message_id"], "channel": row["channel"], "rail_profile_id": row["rail_profile_id"], "exact_collection_binding": expected, "payer_response": response, "next_step": "resolve-evidence" if gaps else "assemble-separate-native-initiation-review", "gaps": gaps, "source_ids": row["source_ids"], "payment_authorized": False, "payment_submitted": False, "settlement_inferred": False})
    if not rows:
        findings.append(finding("missing-collection-requests", "Supply exact collection request and response evidence."))
    return {"result": {"module": "collection-design", "requests": rows, "creates_funds_movement": False}, "findings": findings, "handoffs": [{"target_skill": "payment-initiation-control-reviewer", "reason": "Prepare an exact separate credit instruction after scoped acceptance evidence; recheck intent, screening, account, duplicate and authority controls.", "required_inputs": ["native exact instruction", "payer consent and bound request/response evidence", "access and authority policy", "unresolved collection issues"]}], "limitations": ["Normalized request/response review only; no native pain.013 parser, signature verification or network participation check.", "Request, customer acceptance, payment initiation and settlement are separate records. Request cancellation does not reverse an existing payment.", "Pay-by-bank here is a supplied credit-push collection design; direct-debit mandates remain separate. No SEPA Request-to-Pay or UK Request-to-Pay adapter is implemented."]}
