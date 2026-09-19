"""Bounded local-method design; alias resolution never establishes payment authority."""
from datetime import date
from payment_foundation import dec, finding, load_resource

SKILL = "bank-payment-workflow-designer"
SUPPORTED_JURISDICTIONS = {"BR", "IN", "CA"}


def validate(data):
    errors, ids = [], set()
    if not isinstance(data.get("proposals"), list):
        return ["proposals must be a list"]
    for row in data["proposals"]:
        if not isinstance(row, dict):
            errors.append("proposal must be an object")
            continue
        for key in ("proposal_id", "profile_id", "use_case", "payer_entity", "payer_account_ref", "payee_entity", "payee_account_ref", "currency"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                errors.append("proposal requires " + key)
        if row.get("proposal_id") in ids:
            errors.append("duplicate proposal identity")
        ids.add(row.get("proposal_id"))
        try:
            if dec(row.get("amount")) <= 0:
                errors.append("amount must be positive")
        except (ValueError, TypeError, ArithmeticError):
            errors.append("finite amount required")
        for key in ("participant_review", "beneficiary_review", "rule_review"):
            if not isinstance(row.get(key, {}), dict):
                errors.append(key + " must be an object")
        for review in ("rule_review", "beneficiary_review"):
            for key in ("reviewed_on", "review_due"):
                value = row.get(review, {}).get(key) if isinstance(row.get(review, {}), dict) else None
                if value is not None:
                    try:
                        date.fromisoformat(value)
                    except (TypeError, ValueError):
                        errors.append("invalid review date")
        if not isinstance(row.get("source_ids"), list) or not row["source_ids"]:
            errors.append("proposal requires source_ids")
    return errors


def analyze(request):
    profiles = load_resource("regional-profiles.json")["profiles"]
    rows, findings = [], []
    for row in request["data"]["proposals"]:
        profile, gaps = profiles.get(row["profile_id"]), []
        if not profile or profile["jurisdiction"] != request["jurisdiction"] or profile["currency"] != row["currency"]:
            gaps.append("unsupported-local-method-scope")
        elif row["use_case"] not in profile["supported_use_cases"]:
            gaps.append("unsupported-local-use-case")
        if profile and not profile["reviewed_on"] <= request["as_of"] <= profile["review_due"]:
            gaps.append("public-profile-review-overdue")
        participant = row.get("participant_review", {})
        if any(not participant.get(k) for k in ("access_ref", "payer_reach_ref", "payee_reach_ref", "funding_arrangement_ref", "limits_review_ref", "fees_review_ref", "operational_support_ref")):
            gaps.append("participant-operating-evidence-incomplete")
        beneficiary = row.get("beneficiary_review", {})
        exact_binding = {k: row[k] for k in ("payer_entity", "payer_account_ref", "payee_entity", "payee_account_ref", "amount", "currency")}
        if beneficiary.get("binding") != exact_binding or not beneficiary.get("verification_ref") or not beneficiary.get("alias_resolution_ref") or beneficiary.get("match_status") != "matched":
            gaps.append("alias-beneficiary-binding-unresolved")
        for key in ("beneficiary_review", "rule_review"):
            review = row.get(key, {})
            if not (review.get("reviewed_on", "9999") <= request["as_of"] <= review.get("review_due", "0000")):
                gaps.append(key.replace("_", "-") + "-not-current")
        rules = row.get("rule_review", {})
        if not row.get("accountable_reviewer") or any(not rules.get(k) for k in ("reviewer", "reference", "rule_version", "activity_scope_ref")):
            gaps.append("local-specialist-review-unresolved")
        if rules.get("profile_id") != row["profile_id"] or rules.get("jurisdiction") != request["jurisdiction"] or rules.get("use_case") != row["use_case"]:
            gaps.append("local-rule-applicability-mismatch")
        if row["profile_id"] == "CA-INTERAC-ETRANSFER" and beneficiary.get("delivery_mode") not in {"autodeposit", "security-question-review"}:
            gaps.append("interac-delivery-mode-unresolved")
        if row["profile_id"] == "CA-INTERAC-ETRANSFER" and beneficiary.get("delivery_mode") == "autodeposit" and not beneficiary.get("displayed_legal_name_review_ref"):
            gaps.append("interac-displayed-name-review-missing")
        if row["profile_id"] == "CA-INTERAC-ETRANSFER" and beneficiary.get("delivery_mode") == "security-question-review" and not beneficiary.get("secure-recipient-channel_review_ref"):
            gaps.append("interac-recipient-channel-review-missing")
        if not row.get("intent_ref"):
            gaps.append("payer-intent-unresolved")
        findings.extend(finding(g, row["proposal_id"] + ": " + g.replace("-", " "), row["source_ids"]) for g in gaps)
        rows.append({"proposal_id": row["proposal_id"], "profile": profile, "exact_binding": exact_binding, "accountable_reviewer": row.get("accountable_reviewer"), "next_step": "resolve-evidence" if gaps else "prepare-separate-local-initiation-adapter-review", "gaps": gaps, "source_ids": row["source_ids"], "source_truth_authenticated": False, "scheme_approval_granted": False, "payment_submitted": False, "settlement_inferred": False})
    if not rows:
        findings.append(finding("missing-local-proposals", "Supply a specific local-method use case and participant."))
    return {"result": {"module": "regional-design", "proposals": rows}, "findings": findings, "handoffs": [{"target_skill": "payment-initiation-control-reviewer", "reason": "Preserve local gaps and require a separately supported native initiation adapter; the current core US/EA/UK reviewer must not relabel BR/IN/CA instructions.", "required_inputs": ["exact local instruction and binding", "current scoped specialist and participant evidence", "supported downstream adapter or explicit unsupported result"]}], "limitations": ["Normalized domestic credit-push planning only. No Pix automatic debit, UPI collect/mandate/international link or Interac international-transfer adapter.", "Aliases and recipient displays do not prove authority; no DICT, UPI, Interac, QR, cryptographic or raw network validation.", "Public method availability does not establish participant access, finality of this payment, rule compliance, limits or fees."]}
