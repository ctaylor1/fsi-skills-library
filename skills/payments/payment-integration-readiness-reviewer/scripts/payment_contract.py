"""Portable payments contract v1.0.0. Offline validation, never authorization.

Canonical source: shared/payments/payment_contract.py. Bundle with
tools/sync_payment_contract.py; do not edit package copies.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

VERSION = "1.0.0"
EVIDENCE_STATUSES = frozenset(
    {"supplied", "retrieved", "authenticated", "inspected", "corroborated", "sufficient", "unresolved"}
)
RULE_STATUSES = frozenset({"draft", "proposed", "adopted", "active", "withdrawn", "superseded"})
LIFECYCLE_STAGES = frozenset(
    {
        "instruction",
        "attempt",
        "authentication",
        "authorization",
        "capture",
        "clearing",
        "settlement",
        "funding",
        "posting",
        "refund",
        "return",
        "reversal",
        "cancellation-request",
        "unknown",
    }
)


def money(value) -> Decimal:
    """Parse an explicit finite amount. Missing, boolean and nonfinite are errors."""
    if value is None or isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("amount must be an explicit finite decimal")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("amount must be an explicit finite decimal") from None
    if not result.is_finite():
        raise ValueError("amount must be finite")
    return result


def require_currency(value: str) -> str:
    """Validate an uppercase currency identifier; not an ISO membership assertion."""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z]{3}", value):
        raise ValueError("currency must be an explicit three-letter uppercase code")
    return value


def stable_hash(payload) -> str:
    """Content lineage only; a digest is not a signature, permission or approval."""

    def encode(value):
        if isinstance(value, Decimal):
            return str(money(value))
        raise TypeError(f"unsupported hash value: {type(value).__name__}")

    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False, default=encode
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO string with UTC offset")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("timestamp must be an ISO string with UTC offset") from None
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp requires UTC offset")
    return result


def evidence_status(record: dict) -> str:
    """Return the declared evidence state; never promote a nonempty reference."""
    if not isinstance(record, dict):
        return "unresolved"
    state = record.get("status", "supplied")
    if state not in EVIDENCE_STATUSES or not record.get("source_ref"):
        return "unresolved"
    return state


def validate_evidence(record: dict) -> list[str]:
    if not isinstance(record, dict):
        return ["evidence must be an object"]
    errors = []
    for key in ("evidence_id", "source_ref", "status"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            errors.append(f"evidence.{key} required")
    state = record.get("status")
    if state not in EVIDENCE_STATUSES:
        errors.append("unsupported evidence status")
    if state in {"authenticated", "inspected", "corroborated", "sufficient"}:
        review = record.get("review")
        if not isinstance(review, dict) or any(
            not review.get(k) for k in ("actor", "method", "reviewed_at", "scope", "result_ref")
        ):
            errors.append("reviewed evidence requires actor, method, time, scope and result reference")
        else:
            try:
                timestamp(review["reviewed_at"])
            except ValueError as exc:
                errors.append(str(exc))
    return errors


def validate_rule_profile(profile: dict, as_of: str, *, participant: str, jurisdiction: str) -> list[str]:
    """Check declared profile scope/date. Does not authenticate source or interpret law."""
    if not isinstance(profile, dict):
        return ["rule profile required"]
    errors = []
    for key in ("profile_id", "version", "source_ref", "authority", "review_owner"):
        if not profile.get(key):
            errors.append(f"rule profile {key} required")
    if profile.get("status") != "active":
        errors.append("rule profile is not active")
    for key, expected in (("participants", participant), ("jurisdictions", jurisdiction)):
        values = profile.get(key)
        if not isinstance(values, list) or expected not in values:
            errors.append(f"rule profile does not cover {key}: {expected}")
    try:
        current = date.fromisoformat(as_of)
        start = date.fromisoformat(profile["effective_from"])
        end = date.fromisoformat(profile["effective_to"]) if profile.get("effective_to") else None
        review_due = date.fromisoformat(profile["review_due"])
        if current < start or (end is not None and current > end):
            errors.append("rule profile outside effective interval")
        if current > review_due:
            errors.append("rule profile review overdue")
        if end is not None and end < start:
            errors.append("rule profile interval reversed")
    except (KeyError, TypeError, ValueError):
        errors.append("rule profile requires valid ISO effective/review dates and as_of")
    return errors


def validate_handoff(packet: dict, available_targets=None) -> list[str]:
    """Validate the transport envelope; target must still validate its own input."""
    if not isinstance(packet, dict):
        return ["handoff must be an object"]
    errors = []
    for key in ("handoff_id", "source_skill", "target_skill", "case_id", "lead_owner", "requested_output"):
        if not isinstance(packet.get(key), str) or not packet[key].strip():
            errors.append(f"handoff.{key} required")
    if packet.get("contract_version") != VERSION:
        errors.append("unsupported handoff contract version")
    if packet.get("action_mode") not in {"read-only", "draft-only"}:
        errors.append("handoff may request analysis or drafting only")
    if available_targets is not None and packet.get("target_skill") not in available_targets:
        errors.append("target is not available")
    for key in ("source_refs", "unresolved_issues"):
        if not isinstance(packet.get(key), list):
            errors.append(f"handoff.{key} must be a list")
    if not packet.get("source_refs"):
        errors.append("handoff requires source references")
    if not isinstance(packet.get("target_input"), dict):
        errors.append("handoff.target_input must be an object")
    if packet.get("target_validation") != "required":
        errors.append("independent target validation is required")
    if packet.get("authority_granted") is not False:
        errors.append("handoff must not grant authority")
    return errors


def partition_key(record: dict, *extra: str) -> tuple:
    """Missing scope stays explicit, never a shared zero/default account."""
    keys = ("legal_entity_id", "account_id", "currency") + extra
    if any(record.get(k) in (None, "") for k in keys):
        raise ValueError("missing partition fields: " + ", ".join(k for k in keys if record.get(k) in (None, "")))
    require_currency(record["currency"])
    return tuple(record[k] for k in keys)
