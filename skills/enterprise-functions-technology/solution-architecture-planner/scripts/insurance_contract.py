"""Small, portable insurance evidence contract. Content hashes are not authentication.

This helper never grants approval, executes an action, or certifies a domain result.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

VERSION = "insurance-evidence/1.0"
COMPLETENESS = {"complete", "partial", "unknown"}
EVALUABILITY = {"evaluable", "partial", "not_evaluable"}
CONTEXT_FIELDS = ("capacity", "represented_party", "object_id")


def amount(value):
    """Finite decimal; missing, boolean, infinity and NaN are never zero."""
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError("amount must be a finite number, not an unknown or boolean")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("amount must be a finite number") from None
    if not result.is_finite():
        raise ValueError("amount must be finite")
    return result


def iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("date must be YYYY-MM-DD")
    return date.fromisoformat(value)


def timestamp(value):
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("timestamp requires ISO date, time and timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("invalid ISO timestamp") from None
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp requires an explicit timezone")
    return result.astimezone(timezone.utc)


def as_of_value(value):
    return timestamp(value) if isinstance(value, str) and "T" in value else iso_date(value)


def stable_hash(value):
    """SHA256 of canonical JSON; excludes no fields and rejects non-JSON values."""
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"content must be finite JSON: {exc}") from None
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _strings(value):
    return isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value)


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {"unknown", "na", "n/a"}


def _payload(output):
    return {k: v for k, v in output.items() if k != "artifact"}


def _input_state(doc):
    """Independently derive missingness and carry inherited unresolved issues."""
    issues, incomplete, unevaluable = [], False, False
    context = doc.get("context")
    if not isinstance(context, dict):
        context = {}
    for field in CONTEXT_FIELDS:
        if not _text(context.get(field)):
            issues.append(f"context.{field} unknown")
            incomplete = True
    try:
        as_of_value(doc.get("as_of"))
    except (TypeError, ValueError):
        issues.append("as_of missing or invalid")
        incomplete = True
    sources = doc.get("sources")
    if not isinstance(sources, list) or not sources:
        issues.append("versioned sources unavailable")
        incomplete = True
    else:
        for i, source in enumerate(sources):
            if not isinstance(source, dict) or any(not _text(source.get(k)) for k in ("source_ref", "version")):
                issues.append(f"sources[{i}] requires source_ref and version")
                incomplete = True
            elif source.get("as_of") is not None:
                try:
                    as_of_value(source["as_of"])
                except (TypeError, ValueError):
                    issues.append(f"sources[{i}].as_of invalid")
                    incomplete = True
    unresolved = doc.get("unresolved_issues", [])
    if not _strings(unresolved):
        issues.append("unresolved_issues must be a list of nonempty strings")
        incomplete = True
    else:
        issues.extend(unresolved)
        # Unclassified inherited input questions are not a completed input scope.
        # A newly computed, fully evaluated finding can still be reported separately.
        if unresolved:
            incomplete = True
    upstream = doc.get("upstream_artifacts", [])
    if not isinstance(upstream, list):
        issues.append("upstream_artifacts must be a list")
        incomplete = True
    else:
        for i, artifact in enumerate(upstream):
            errors = validate_artifact(artifact)
            if errors:
                issues.append(f"upstream_artifacts[{i}] invalid: {'; '.join(errors)}")
                incomplete = unevaluable = True
                continue
            issues.extend(artifact["unresolved_issues"])
            incomplete |= artifact["completeness"] != "complete"
            unevaluable |= artifact["evaluability"] == "not_evaluable"
            if artifact["evaluability"] == "partial":
                incomplete = True
    return list(dict.fromkeys(issues)), incomplete, unevaluable


def build_artifact(input_doc, output, *, producer, artifact_type, completeness="complete", evaluability="evaluable", issues=()):
    if not isinstance(input_doc, dict) or not isinstance(output, dict):
        raise ValueError("input and output must be JSON objects")
    if completeness not in COMPLETENESS or evaluability not in EVALUABILITY:
        raise ValueError("invalid completeness or evaluability state")
    if not _text(producer) or not _text(artifact_type):
        raise ValueError("producer and artifact_type are required")
    supplied_issues = list(issues)
    if not _strings(supplied_issues):
        raise ValueError("issues must contain nonempty strings")
    inherited, incomplete, unevaluable = _input_state(input_doc)
    payload = _payload(output)
    output_issues = payload.get("unresolved_issues", [])
    if not _strings(output_issues):
        raise ValueError("output.unresolved_issues must be a list of nonempty strings")
    if payload.get("completeness") in {"partial", "unknown"}:
        incomplete = True
    if payload.get("evaluability") == "not_evaluable":
        unevaluable = True
    elif payload.get("evaluability") == "partial":
        incomplete = True
    if incomplete and completeness == "complete":
        completeness = "partial"
    if unevaluable:
        evaluability = "not_evaluable"
    elif incomplete and evaluability == "evaluable":
        evaluability = "partial"
    envelope = {
        "contract_version": VERSION,
        "producer": producer,
        "artifact_type": artifact_type,
        "as_of": input_doc.get("as_of"),
        "context": copy.deepcopy(input_doc.get("context")) if isinstance(input_doc.get("context"), dict) else {},
        "sources": copy.deepcopy(input_doc.get("sources")) if isinstance(input_doc.get("sources"), list) else [],
        "input_hash": stable_hash(input_doc),
        "output_hash": stable_hash(payload),
        "completeness": completeness,
        "evaluability": evaluability,
        "unresolved_issues": list(dict.fromkeys(inherited + supplied_issues + output_issues)),
        "approval": "not_requested",
        "execution": "not_performed",
        "evidence_assurance": "supplied_not_authenticated",
    }
    envelope["artifact_hash"] = stable_hash(envelope)
    return envelope


def validate_artifact(envelope, input_doc=None, output=None):
    if not isinstance(envelope, dict):
        return ["artifact must be an object"]
    errors = []
    for field in ("producer", "artifact_type"):
        if not _text(envelope.get(field)):
            errors.append(f"artifact.{field} required")
    if envelope.get("contract_version") != VERSION:
        errors.append("unsupported insurance contract version")
    for field, allowed in (("completeness", COMPLETENESS), ("evaluability", EVALUABILITY)):
        if not isinstance(envelope.get(field), str) or envelope[field] not in allowed:
            errors.append(f"invalid artifact.{field}")
    for field, value in (("approval", "not_requested"), ("execution", "not_performed"), ("evidence_assurance", "supplied_not_authenticated")):
        if envelope.get(field) != value:
            errors.append(f"artifact.{field} must be {value}")
    if not isinstance(envelope.get("context"), dict):
        errors.append("artifact.context must be an object")
    if not isinstance(envelope.get("sources"), list):
        errors.append("artifact.sources must be a list")
    if not _strings(envelope.get("unresolved_issues")):
        errors.append("artifact.unresolved_issues must be a list of nonempty strings")
    for field in ("input_hash", "output_hash", "artifact_hash"):
        if not isinstance(envelope.get(field), str) or not re.fullmatch(r"[0-9a-f]{64}", envelope[field]):
            errors.append(f"invalid artifact.{field}")
    try:
        if stable_hash({k: v for k, v in envelope.items() if k != "artifact_hash"}) != envelope.get("artifact_hash"):
            errors.append("artifact content hash mismatch")
        # Metadata defects must remain explicit, even without the original input.
        metadata = {k: envelope.get(k) for k in ("context", "as_of", "sources")}
        required_issues, incomplete, _ = _input_state(metadata)
        if incomplete and envelope.get("completeness") == "complete":
            errors.append("incomplete metadata cannot claim completeness")
        if incomplete and envelope.get("evaluability") == "evaluable":
            errors.append("incomplete metadata cannot claim full evaluability")
        actual_issues = envelope.get("unresolved_issues") if _strings(envelope.get("unresolved_issues")) else []
        if not set(required_issues).issubset(actual_issues):
            errors.append("metadata issues were dropped")
        if input_doc is not None:
            if not isinstance(input_doc, dict):
                errors.append("input_doc must be an object")
            else:
                if stable_hash(input_doc) != envelope.get("input_hash"):
                    errors.append("input content hash mismatch")
                for field in ("context", "as_of", "sources"):
                    expected = input_doc.get(field, {} if field == "context" else [] if field == "sources" else None)
                    if envelope.get(field) != expected:
                        errors.append(f"artifact.{field} differs from input")
                retained, partial, blocked = _input_state(input_doc)
                if not set(retained).issubset(actual_issues):
                    errors.append("input/upstream unresolved issues were dropped")
                if partial and envelope.get("completeness") == "complete":
                    errors.append("input/upstream missingness cannot become complete")
                if (partial and envelope.get("evaluability") == "evaluable") or (blocked and envelope.get("evaluability") != "not_evaluable"):
                    errors.append("input/upstream evaluability was promoted")
        if output is not None:
            if not isinstance(output, dict):
                errors.append("output must be an object")
            else:
                payload = _payload(output)
                if stable_hash(payload) != envelope.get("output_hash"):
                    errors.append("output content hash mismatch")
                declared = payload.get("unresolved_issues", [])
                if not _strings(declared) or not set(declared).issubset(actual_issues):
                    errors.append("output unresolved issues were dropped")
                if payload.get("completeness") in {"partial", "unknown"} and envelope.get("completeness") == "complete":
                    errors.append("output missingness was promoted")
                if payload.get("evaluability") in EVALUABILITY:
                    rank = {"not_evaluable": 0, "partial": 1, "evaluable": 2}
                    if rank.get(envelope.get("evaluability"), -1) > rank[payload["evaluability"]]:
                        errors.append("output evaluability was promoted")
    except (TypeError, ValueError, RecursionError) as exc:
        errors.append(f"invalid contract content: {exc}")
    return errors


def make_handoff(source_artifact, *, target_skill, target_input, requested_output):
    if validate_artifact(source_artifact):
        raise ValueError("source artifact is invalid")
    if not isinstance(target_input, dict) or not _text(target_skill) or not _text(requested_output):
        raise ValueError("handoff requires target, requested output and target input object")
    target = copy.deepcopy(target_input)
    issues = target.get("unresolved_issues", [])
    upstream = target.get("upstream_artifacts", [])
    if not _strings(issues) or not isinstance(upstream, list):
        raise ValueError("invalid target unresolved_issues/upstream_artifacts")
    target["unresolved_issues"] = list(dict.fromkeys(issues + source_artifact["unresolved_issues"]))
    target["upstream_artifacts"] = upstream + [copy.deepcopy(source_artifact)]
    return {"contract_version": VERSION, "source_artifact": copy.deepcopy(source_artifact),
            "target_skill": target_skill, "target_input": target, "target_input_hash": stable_hash(target),
            "requested_output": requested_output, "authority_granted": False, "action_mode": "review-only"}


def validate_handoff(packet, *, target_skill, receiver_validator):
    if not isinstance(packet, dict):
        return ["handoff must be an object"]
    errors = []
    if packet.get("contract_version") != VERSION or packet.get("target_skill") != target_skill:
        errors.append("handoff version or receiver mismatch")
    if packet.get("authority_granted") is not False or packet.get("action_mode") != "review-only":
        errors.append("handoff cannot grant execution authority")
    if not _text(packet.get("requested_output")):
        errors.append("requested_output required")
    source = packet.get("source_artifact")
    errors.extend(validate_artifact(source))
    target = packet.get("target_input")
    if not isinstance(target, dict):
        return errors + ["target_input must be an object"]
    try:
        if stable_hash(target) != packet.get("target_input_hash"):
            errors.append("target input hash mismatch")
        if isinstance(source, dict):
            if source not in target.get("upstream_artifacts", []):
                errors.append("source artifact not retained by receiver input")
            unresolved = target.get("unresolved_issues")
            if not _strings(unresolved) or not set(source.get("unresolved_issues", [])).issubset(unresolved):
                errors.append("source unresolved issues dropped")
    except (TypeError, ValueError) as exc:
        errors.append(f"invalid handoff content: {exc}")
    if not callable(receiver_validator):
        return errors + ["actual receiver validator required"]
    try:
        result = receiver_validator(copy.deepcopy(target))
        receiver_errors = result[0] if isinstance(result, tuple) and len(result) == 2 else result
        if not isinstance(receiver_errors, list) or not all(isinstance(v, str) for v in receiver_errors):
            errors.append("receiver validator must return errors or (errors, warnings)")
        else:
            errors.extend(f"receiver: {err}" for err in receiver_errors)
    except Exception as exc:
        errors.append(f"receiver validation failed: {type(exc).__name__}: {exc}")
    return errors
