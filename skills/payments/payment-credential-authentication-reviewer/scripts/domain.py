"""Evidence-bound credential lifecycle and authentication review; no verification service."""
from datetime import date
from payment_foundation import finding, dec

SKILL = "payment-credential-authentication-reviewer"
KINDS = {"network-token", "psp-token", "wallet", "stored-account-reference"}
ACTIONS = {"use", "provision", "update", "suspend", "delete"}
STATES = {"active", "suspended", "deleted", "unknown"}
PROTOCOLS = {"3ds", "fido", "bank-app", "otp", "other"}


def validate(data):
    errors = []
    for name, key in (("credentials", "credential_id"), ("authentications", "authentication_id"), ("requests", "operation_id")):
        rows = data.get(name)
        if not isinstance(rows, list):
            errors.append(name + " must be a list")
            continue
        ids = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get(key), str) or not row[key].strip():
                errors.append(name + " requires " + key)
                continue
            if row[key] in ids:
                errors.append("duplicate " + key)
            ids.add(row[key])
            if not isinstance(row.get("source_ids"), list) or not row["source_ids"]:
                errors.append(name + " rows require source_ids")
    for row in data.get("credentials", []):
        if not isinstance(row, dict):
            continue
        if row.get("kind") not in KINDS or row.get("state") not in STATES:
            errors.append("credential kind/state unsupported")
        if not isinstance(row.get("scope"), dict) or not isinstance(row.get("provisioning", {}), dict):
            errors.append("credential scope/provisioning must be objects")
        for key in ("valid_from", "valid_until"):
            if row.get(key) is not None:
                try:
                    date.fromisoformat(row[key])
                except (ValueError, TypeError):
                    errors.append("invalid credential " + key)
    for row in data.get("authentications", []):
        if not isinstance(row, dict):
            continue
        if row.get("protocol") not in PROTOCOLS or row.get("result") not in {"authenticated", "failed", "unknown"}:
            errors.append("unsupported authentication protocol/result")
        if not isinstance(row.get("binding"), dict):
            errors.append("authentication binding must be object")
        for key in ("valid_from", "valid_until"):
            if row.get(key) is not None:
                try:
                    date.fromisoformat(row[key])
                except (ValueError, TypeError):
                    errors.append("invalid authentication " + key)
    for row in data.get("requests", []):
        if not isinstance(row, dict):
            continue
        if row.get("action") not in ACTIONS or not isinstance(row.get("credential_id"), str):
            errors.append("operation requires supported action and credential_id")
        if not isinstance(row.get("scope"), dict) or not isinstance(row.get("binding", {}), dict):
            errors.append("operation scope/binding must be objects")
        if row.get("action") == "use":
            binding = row.get("binding", {})
            if any(not isinstance(binding.get(k), str) or not binding[k].strip() for k in ("instruction_id", "payer_ref", "payee_ref", "currency")):
                errors.append("use binding needs exact instruction/payer/payee/currency")
            try:
                if dec(binding.get("amount")) <= 0:
                    errors.append("use amount must be positive")
            except (ValueError, TypeError, ArithmeticError):
                errors.append("use amount required")
    return errors


def analyze(request):
    data = request["data"]
    creds = {r["credential_id"]: r for r in data["credentials"]}
    auths = {r["authentication_id"]: r for r in data["authentications"]}
    findings, assessments = [], []
    for operation in data["requests"]:
        sid = operation["source_ids"]
        gaps = []
        credential = creds.get(operation["credential_id"])
        if not credential:
            gaps.append("credential-reference-unresolved")
        else:
            scope = credential["scope"]
            if not scope or any(not isinstance(v, str) or not v.strip() for v in scope.values()):
                gaps.append("credential-domain-unresolved")
            if not operation["scope"] or operation["scope"] != scope:
                gaps.append("credential-domain-mismatch")
            if credential["kind"] == "network-token" and any(not scope.get(k) for k in ("merchant_ref", "token_requestor_ref")):
                gaps.append("network-token-domain-unresolved")
            provisioning = credential.get("provisioning", {})
            if any(not provisioning.get(k) for k in ("identity_review_ref", "consent_ref", "account_binding_ref")):
                gaps.append("provisioning-evidence-unresolved")
            if operation["action"] == "use":
                if credential["state"] != "active":
                    gaps.append("credential-not-active")
                if not credential.get("valid_from") or not credential.get("valid_until"):
                    gaps.append("credential-validity-unresolved")
                elif not credential["valid_from"] <= request["as_of"] <= credential["valid_until"]:
                    gaps.append("credential-outside-validity")
        auth = auths.get(operation.get("authentication_id"))
        if operation["action"] == "use":
            if not operation.get("payment_intent_ref"):
                gaps.append("payment-intent-unresolved")
            if not auth or auth["result"] != "authenticated":
                gaps.append("authentication-unresolved")
            elif auth.get("binding") != operation["binding"]:
                gaps.append("authentication-binding-mismatch")
            if auth:
                if auth.get("credential_id") != operation["credential_id"]:
                    gaps.append("authentication-credential-mismatch")
                if not auth.get("valid_from") or not auth.get("valid_until") or not auth["valid_from"] <= request["as_of"] <= auth["valid_until"]:
                    gaps.append("authentication-validity-unresolved")
            # A frictionless result, exemption claim or passkey is not legal/SCA clearance.
            if not operation.get("authentication_applicability_review_ref"):
                gaps.append("authentication-applicability-unresolved")
        if operation["action"] in {"provision", "update", "suspend", "delete"}:
            if not operation.get("lifecycle_authority_ref") or not operation.get("notification_plan_ref"):
                gaps.append("lifecycle-authority-or-notification-unresolved")
        if operation["action"] == "update":
            update = operation.get("update", {})
            if not isinstance(update, dict) or any(not update.get(k) for k in ("provider_event_ref", "before_reference", "after_reference", "account_linkage_review_ref", "consent_status_ref")):
                gaps.append("updater-evidence-unresolved")
            elif update.get("extends_mandate") is not False or update.get("consent_revoked") is not False:
                gaps.append("updater-cannot-create-or-restore-consent")
            elif update["before_reference"] != operation["credential_id"]:
                gaps.append("updater-before-reference-mismatch")
        for gap in gaps:
            findings.append(finding(gap, operation["operation_id"] + ": " + gap.replace("-", " "), sid))
        assessments.append({"operation_id": operation["operation_id"], "credential_id": operation["credential_id"], "action": operation["action"], "assessment": "needs-evidence" if gaps else "supplied-evidence-for-review", "source_ids": sid, "credential_scope": credential["scope"] if credential else None, "authentication_result": auth["result"] if auth else None, "gaps": gaps, "credential_changed": False, "payment_authorized": False, "sca_or_liability_shift_determined": False})
    if not assessments:
        findings.append(finding("missing-operations", "Supply credential operations to assess."))
    return {"result": {"operations": assessments, "cryptographic_verification_performed": False, "lifecycle_actions_executed": False}, "findings": findings, "handoffs": [{"target_skill": "payment-initiation-control-reviewer", "reason": "Review exact payment intent and instruction controls separately from credential/authentication evidence.", "required_inputs": ["exact native instruction", "payer intent and scoped policy", "unresolved credential/authentication findings"]}, {"target_skill": "payment-platform-architecture-reviewer", "reason": "Review token/provider/event propagation, revocation and idempotency design.", "required_inputs": ["credential operation assessment", "source-linked system flows", "revocation and recovery design"]}], "limitations": ["Opaque credential references only. No token value, PAN, authentication secret, cryptographic assertion or biometric material is processed.", "Declared authentication, credential scope and review references are not verified identity, payment authority, regulatory compliance or network liability-shift determinations."]}
