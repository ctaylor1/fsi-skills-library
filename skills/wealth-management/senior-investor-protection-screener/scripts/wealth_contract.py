"""Versioned, stdlib-only evidence envelope for wealth P0 draft workflows.

Canonical source. tools/sync_wealth_contract.py bundles identical copies into skills.
This contract validates supplied evidence metadata, not source truth, permissions,
professional approval or regulatory compliance. It performs no external operations.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date

SCHEMA_VERSION = "wealth-p0-v1"
CAPACITIES = {"advisory", "brokerage", "private-bank", "trust"}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def iso_date(value):
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        parsed = date.fromisoformat(value)
        return parsed if parsed.isoformat() == value else None
    except ValueError:
        return None


def _json_errors(value, path="input"):
    errors = []
    if isinstance(value, float) and not math.isfinite(value):
        errors.append(f"{path}: non-finite number")
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                errors.append(f"{path}: keys must be strings")
            errors.extend(_json_errors(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_json_errors(item, f"{path}[{index}]"))
    elif value is not None and not isinstance(value, (str, bool, int, float)):
        errors.append(f"{path}: unsupported JSON value")
    return errors


def input_hash(doc):
    """Bind a draft to the complete input; this digest is not authorization."""
    return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def validate_envelope(doc):
    if not isinstance(doc, dict):
        return ["request must be an object"]
    errors = _json_errors(doc)
    if doc.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    for key in ("request_id", "household_id"):
        if not nonempty(doc.get(key)):
            errors.append(f"{key} must be a nonempty string")
    as_of = iso_date(doc.get("as_of"))
    if as_of is None:
        errors.append("as_of must be YYYY-MM-DD")
    engagement = doc.get("engagement")
    if not isinstance(engagement, dict):
        errors.append("engagement must be an object")
    else:
        if not isinstance(engagement.get("capacity"), str) or engagement["capacity"] not in CAPACITIES:
            errors.append("engagement.capacity must select one supported professional capacity")
        if engagement.get("jurisdiction") != "US":
            errors.append("unsupported jurisdiction: this contract requires an approved US deployment profile")
    sources = doc.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a nonempty evidence registry")
        return errors
    seen = set()
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        for key in ("source_id", "reference", "owner"):
            if not nonempty(source.get(key)):
                errors.append(f"{label}.{key} must be nonempty")
        sid = source.get("source_id")
        if isinstance(sid, str):
            if sid in seen:
                errors.append(f"duplicate source_id: {sid}")
            seen.add(sid)
        observed = iso_date(source.get("as_of"))
        until = iso_date(source.get("valid_until"))
        if observed is None or until is None:
            errors.append(f"{label} requires dated as_of and valid_until")
        elif until < observed:
            errors.append(f"{label} valid_until precedes source as_of")
        elif as_of is not None:
            if observed > as_of:
                errors.append(f"{label} is future-dated relative to request")
            if until < as_of:
                errors.append(f"{label} is stale relative to request")
    return errors


def source_errors(source_ids, doc):
    """Check explicit item-level source coverage against the validated registry."""
    if not isinstance(source_ids, list) or not source_ids:
        return ["material item requires source_ids"]
    registry = {s["source_id"] for s in doc.get("sources", [])
                if isinstance(s, dict) and nonempty(s.get("source_id"))}
    errors, seen = [], set()
    for sid in source_ids:
        if not nonempty(sid):
            errors.append("source_ids must contain nonempty strings")
        elif sid not in registry:
            errors.append(f"unknown source_id: {sid}")
        elif sid in seen:
            errors.append(f"duplicate item source_id: {sid}")
        if isinstance(sid, str):
            seen.add(sid)
    return errors


def make_output(skill, doc, result, findings):
    errors = validate_envelope(doc)
    if errors:
        raise ValueError("; ".join(errors))
    digest = input_hash(doc)
    return {
        "schema_version": SCHEMA_VERSION,
        "skill": skill,
        "request_id": doc["request_id"],
        "household_id": doc["household_id"],
        "as_of": doc["as_of"],
        "engagement": doc["engagement"],
        "sources": doc["sources"],
        "input_hash": digest,
        "artifact_id": f"{skill}-{digest[:20]}",
        "status": "needs-data" if findings else "review-ready",
        "findings": findings,
        "result": result,
        "human_review_required": True,
        "action_taken": False,
        "delivery_status": "not-delivered",
    }


def validate_output_envelope(out, skill):
    if not isinstance(out, dict):
        return ["output must be an object"]
    errors = validate_envelope(out)
    if out.get("skill") != skill:
        errors.append("output skill does not match validator")
    digest = out.get("input_hash")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        errors.append("input_hash must be a SHA256 digest")
    elif out.get("artifact_id") != f"{skill}-{digest[:20]}":
        errors.append("artifact_id does not match input digest")
    findings = out.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
    else:
        for finding in findings:
            if not isinstance(finding, dict) or not nonempty(finding.get("code")) or not nonempty(finding.get("message")):
                errors.append("each finding requires code and message")
        if out.get("status") != ("needs-data" if findings else "review-ready"):
            errors.append("status does not reflect unresolved findings")
    if not isinstance(out.get("result"), dict) or not out.get("result"):
        errors.append("result must be a nonempty object")
    if out.get("human_review_required") is not True or out.get("action_taken") is not False:
        errors.append("human review and no-action posture required")
    if out.get("delivery_status") != "not-delivered":
        errors.append("external delivery is not permitted by this package")
    return errors
