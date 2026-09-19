#!/usr/bin/env python3
"""Validate evidence for an offline, exact field-correction plan. No execution authority."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from payment_contract import money, require_currency, stable_hash

CATALOG = {
    "invalid_beneficiary_detail": {"beneficiary_bic", "beneficiary_account", "beneficiary_name", "beneficiary_address"},
    "missing_remittance_info": {"remittance_info"},
    "missing_purpose_code": {"purpose_code"},
}
CATALOG_VERSION = "offline-field-repair-v1"
CLEARED_SCREENING = {"clear", "false_positive_cleared"}


def repair_binding(doc):
    """The screened instruction scope includes the exact correction and original snapshot."""
    return stable_hash({"payment_snapshot": doc.get("payment_snapshot"),
                        "proposed_repair": doc.get("proposed_repair")})


def _time(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamps must include timezone")
    return result.astimezone(timezone.utc)


def validate(doc):
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["input must be an object"], warnings
    for key in ("case_id", "payment_id", "type", "as_of", "catalog_version", "exception_confirmation",
                "payment_snapshot", "policy", "screening", "proposed_repair", "evidence"):
        if key not in doc or doc[key] in (None, "", {}):
            errors.append(f"missing {key}")
    if errors:
        return errors, warnings
    for key in ("exception_confirmation", "payment_snapshot", "policy", "screening", "proposed_repair", "evidence"):
        if not isinstance(doc[key], dict):
            errors.append(f"{key} must be an object")
    if errors:
        return errors, warnings
    snapshot, policy, repair = doc["payment_snapshot"], doc["policy"], doc["proposed_repair"]
    confirmed, screening = doc["exception_confirmation"], doc["screening"]
    if doc["catalog_version"] != CATALOG_VERSION:
        errors.append("unsupported catalog_version")
    if doc["type"] not in CATALOG:
        errors.append("exception type outside the field-repair catalog; servicing/release requires another workflow")
    if confirmed.get("status") != "confirmed" or not confirmed.get("source_ref") or confirmed.get("case_id") != doc["case_id"]:
        errors.append("confirmed exception evidence bound to case_id is required")
    for key in ("payment_id", "end_to_end_id", "entity_id", "rail", "currency", "amount", "state", "source_ref", "as_of"):
        if snapshot.get(key) in (None, ""):
            errors.append(f"payment_snapshot.{key} required")
    if snapshot.get("payment_id") != doc["payment_id"]:
        errors.append("payment identity mismatch")
    if snapshot.get("state") not in {"held", "rejected"}:
        errors.append("repair requires a held/rejected payment snapshot; settlement/unknown state cannot be repaired")
    if repair.get("action") != "repair_and_resubmit":
        errors.append("only repair_and_resubmit planning is supported")
    field = repair.get("field")
    if field not in CATALOG.get(doc["type"], set()):
        errors.append("field outside exception-specific repair catalog")
    fields = snapshot.get("fields")
    if not isinstance(fields, dict) or field not in fields:
        errors.append("original field must be explicitly present in payment_snapshot.fields")
    elif "old_value" not in repair or repair["old_value"] != fields[field]:
        errors.append("old_value must exactly match the original snapshot")
    if "new_value" not in repair or repair.get("new_value") in (None, "", {}, []):
        errors.append("verified new_value is required")
    elif repair.get("new_value") == repair.get("old_value"):
        errors.append("repair must change the specified field")
    for key in ("policy_id", "version", "source_ref", "entity_id", "rails", "currency", "max_amount",
                "allowed_fields", "allowed_exception_types", "required_approver_role", "effective_at", "expires_at"):
        if policy.get(key) in (None, "", [], {}):
            errors.append(f"policy.{key} required")
    for key in ("rails", "allowed_fields", "allowed_exception_types"):
        if not isinstance(policy.get(key), list):
            errors.append(f"policy.{key} must be a list")
    if errors:
        return errors, warnings
    if policy["entity_id"] != snapshot["entity_id"] or snapshot["rail"] not in policy["rails"]:
        errors.append("policy entity/rail authority scope mismatch")
    if field not in policy["allowed_fields"] or doc["type"] not in policy["allowed_exception_types"]:
        errors.append("policy does not authorize this field/exception type")
    try:
        currency = require_currency(snapshot["currency"])
        if currency != require_currency(policy["currency"]) or currency != require_currency(repair.get("currency")):
            errors.append("policy/repair/payment currency scope mismatch; no inferred FX conversion")
        amount, limit = money(snapshot["amount"]), money(policy["max_amount"])
        if amount <= 0 or limit <= 0 or money(repair.get("amount")) != amount:
            errors.append("positive exact amount matching the original payment required")
        if amount > limit:
            errors.append("amount exceeds policy authority limit")
        asof = _time(doc["as_of"])
        if not _time(policy["effective_at"]) <= asof < _time(policy["expires_at"]):
            errors.append("policy not effective at plan as_of")
        if _time(snapshot["as_of"]) > asof:
            errors.append("payment snapshot is later than plan as_of")
        if _time(screening.get("screened_at")) > asof:
            errors.append("screening evidence is later than plan as_of")
    except (ValueError, TypeError) as exc:
        errors.append(str(exc))
    if (screening.get("status") not in CLEARED_SCREENING or not screening.get("source_ref")
            or not screening.get("disposition_id") or screening.get("payment_id") != doc["payment_id"]):
        errors.append("screening not cleared with cited payment-bound disposition")
    if screening.get("repair_binding") != repair_binding(doc):
        errors.append("screening repair_binding does not bind the exact proposed instruction")
    if not doc["evidence"].get("verification_source"):
        errors.append("replacement-value verification_source required")
    warnings.append("Policy and screening are supplied evidence, not authenticated live authority; no execution is possible.")
    return errors, warnings


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/case_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
    doc = json.loads(path.read_text() if path else sys.stdin.read())
    errors, warnings = validate(doc)
    for item in warnings: print("WARN", item)
    for item in errors: print("ERROR", item)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return bool(errors)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
