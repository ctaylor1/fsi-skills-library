"""Separate sourced risk dimensions and flag conflicts without assigning a rating."""
from __future__ import annotations

from copy import deepcopy
import math
import re

from wealth_contract import (iso_date, make_output, nonempty, source_errors,
                            validate_envelope, validate_output_envelope)

SKILL = "investment-risk-profile-reviewer"
DIMENSIONS = ("willingness", "loss_capacity", "liquidity", "horizon", "experience", "constraints")
EXPERIENCE = {"none", "limited", "experienced"}
NUMBERS = {
    "willingness": ("maximum_loss_pct",),
    "loss_capacity": ("investable_assets", "assessed_loss_capacity_amount"),
    "liquidity": ("available_liquid_amount", "required_amount", "required_within_months"),
    "horizon": ("months",),
    "proposed_exposure": ("scenario_loss_amount", "lockup_months"),
}


def number(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def validate_input(doc):
    errors = validate_envelope(doc)
    if not isinstance(doc, dict):
        return errors
    if not nonempty(doc.get("profile_id")):
        errors.append("profile_id must be a nonempty string")
    dims = doc.get("dimensions")
    if not isinstance(dims, dict):
        return errors + ["dimensions must be an object; missing dimensions are needs-data"]
    if set(dims) - set(DIMENSIONS):
        errors.append("unknown risk dimensions; ratings and combined scores are not supported")
    for key, obj in list(dims.items()) + ([("proposed_exposure", doc["proposed_exposure"])]
                                        if "proposed_exposure" in doc else []):
        if not isinstance(obj, dict):
            errors.append(f"{key} must be an object")
            continue
        for field in ("recorded_by", "recorded_on", "assessment_id", "method_id", "method_version",
                      "respondent_id", "assessment_reference", "basis", "goal_id"):
            if field in obj and not isinstance(obj[field], str):
                errors.append(f"{key}.{field} must be a string")
        for field in NUMBERS.get(key, ()):
            if field in obj and (not number(obj[field]) or obj[field] < 0):
                errors.append(f"{key}.{field} must be a finite nonnegative number")
        if key == "willingness" and number(obj.get("maximum_loss_pct")) and obj["maximum_loss_pct"] > 100:
            errors.append("willingness.maximum_loss_pct cannot exceed 100")
        if "currency" in obj and (not isinstance(obj["currency"], str)
                                   or not re.fullmatch(r"[A-Z]{3}", obj["currency"])):
            errors.append(f"{key}.currency must be a three-letter uppercase code")
        if key == "willingness" and "method_approval" in obj and not isinstance(obj["method_approval"], dict):
            errors.append("willingness.method_approval must be an object")
        if key in {"experience", "constraints"} and "items" in obj:
            if not isinstance(obj["items"], list):
                errors.append(f"{key}.items must be a list")
                continue
            seen = set()
            for item in obj["items"]:
                if not isinstance(item, dict):
                    errors.append(f"{key}.items entries must be objects")
                    continue
                identity = item.get("instrument_type" if key == "experience" else "constraint_id")
                if not nonempty(identity) or identity in seen:
                    errors.append(f"{key}: items need nonempty unique identities")
                else:
                    seen.add(identity)
                if key == "experience":
                    level = item.get("level")
                    if not isinstance(level, str) or level not in EXPERIENCE:
                        errors.append("experience level must be none, limited or experienced")
                elif not nonempty(item.get("description")):
                    errors.append("constraint description must be a nonempty string")
        if key == "constraints" and "none_identified" in obj and not isinstance(obj["none_identified"], bool):
            errors.append("constraints.none_identified must be boolean")
        if key == "proposed_exposure" and "instrument_types" in obj:
            items = obj["instrument_types"]
            if not isinstance(items, list) or not all(nonempty(x) for x in items):
                errors.append("proposed_exposure.instrument_types must be a string list")
    return errors


def compute(doc):
    errors = validate_input(doc)
    if errors:
        raise ValueError("; ".join(errors))
    findings, dimensions = [], []

    def issue(code, message):
        findings.append({"code": code, "message": message})

    def evidence(obj, label):
        messages = source_errors(obj.get("source_ids"), doc)
        for msg in messages:
            issue("source_coverage", f"{label}: {msg}")
        return bool(messages)

    def fields(obj, keys, label):
        missing = [key for key in keys if key not in obj or obj[key] in (None, "")]
        for key in missing:
            issue("missing_fact", f"{label}.{key} is missing")
        return bool(missing)

    review_date = iso_date(doc["as_of"])
    for name in DIMENSIONS:
        obj = doc["dimensions"].get(name)
        before = len(findings)
        if not obj:
            issue("missing_dimension", f"{name}: required risk dimension has no sourced assessment")
            dimensions.append({"dimension": name, "status": "missing", "facts": {}})
            continue
        evidence(obj, name)
        fields(obj, ("recorded_by", "recorded_on"), name)
        observed = iso_date(obj.get("recorded_on"))
        if observed is None or observed > review_date:
            issue("assessment_date", f"{name}: recorded_on must be valid and no later than review")
        fields(obj, NUMBERS.get(name, ()), name)
        if name in {"loss_capacity", "liquidity"}:
            fields(obj, ("currency",), name)
        if name == "willingness":
            fields(obj, ("assessment_id", "method_id", "method_version", "respondent_id"), name)
            approval = obj.get("method_approval") or {}
            fields(approval, ("owner", "reference"), "willingness.method_approval")
            if not all(nonempty(approval.get(k)) for k in ("owner", "reference")):
                issue("method_approval", "Assessment method needs a named owner and recorded approval reference")
            evidence(approval, "willingness.method_approval")
        if name == "loss_capacity":
            fields(obj, ("assessment_reference", "basis"), name)
            if number(obj.get("investable_assets")) and obj["investable_assets"] <= 0:
                issue("capacity_not_quantifiable", "Positive investable assets are needed for percentage comparison")
            if all(number(obj.get(k)) for k in NUMBERS[name]):
                if obj["assessed_loss_capacity_amount"] > obj["investable_assets"]:
                    issue("capacity_inconsistency", "Assessed loss capacity exceeds the stated investable assets")
        if name == "horizon":
            fields(obj, ("goal_id",), name)
        if name == "experience":
            if not obj.get("items"):
                issue("missing_fact", "experience.items must explicitly record relevant instrument experience")
            for item in obj.get("items", []):
                evidence(item, f"experience/{item['instrument_type']}")
        if name == "constraints":
            items = obj.get("items", [])
            if not items and obj.get("none_identified") is not True:
                issue("missing_fact", "constraints need items or a sourced none_identified attestation")
            if items and obj.get("none_identified") is True:
                issue("constraint_inconsistency", "Constraints are listed alongside none_identified=true")
            for item in items:
                evidence(item, f"constraint/{item['constraint_id']}")
        dimensions.append({"dimension": name, "status": "incomplete" if len(findings) > before else "recorded",
                           "facts": deepcopy(obj)})

    dims = doc["dimensions"]
    willingness, capacity = dims.get("willingness", {}), dims.get("loss_capacity", {})
    liquidity, horizon = dims.get("liquidity", {}), dims.get("horizon", {})
    metrics = {"capacity_loss_pct": None, "willingness_loss_amount": None, "liquidity_shortfall": None}
    if all(number(capacity.get(k)) for k in NUMBERS["loss_capacity"]) and capacity["investable_assets"] > 0:
        metrics["capacity_loss_pct"] = round(capacity["assessed_loss_capacity_amount"] / capacity["investable_assets"] * 100, 6)
        if number(willingness.get("maximum_loss_pct")):
            metrics["willingness_loss_amount"] = round(capacity["investable_assets"] * willingness["maximum_loss_pct"] / 100, 2)
            if metrics["willingness_loss_amount"] > capacity["assessed_loss_capacity_amount"]:
                issue("willingness_capacity_conflict", "Stated willingness exceeds assessed financial loss capacity; a human must reconcile")
    if all(number(liquidity.get(k)) for k in ("available_liquid_amount", "required_amount")):
        metrics["liquidity_shortfall"] = round(max(liquidity["required_amount"] - liquidity["available_liquid_amount"], 0), 2)
        if metrics["liquidity_shortfall"] > 0:
            issue("liquidity_shortfall", "Documented liquid resources do not cover the stated liquidity requirement")
    exposure = doc.get("proposed_exposure")
    if exposure is not None:
        evidence(exposure, "proposed_exposure")
        fields(exposure, ("currency", "scenario_loss_amount", "lockup_months", "instrument_types"), "proposed_exposure")
        if not exposure.get("instrument_types"):
            issue("missing_fact", "proposed_exposure.instrument_types cannot be empty")
        currency_match = nonempty(exposure.get("currency")) and exposure.get("currency") == capacity.get("currency")
        if not currency_match:
            issue("currency_mismatch", "Exposure/capacity currencies differ or are missing; no FX assumption is invented")
        if currency_match and number(exposure.get("scenario_loss_amount")):
            loss = exposure["scenario_loss_amount"]
            if number(capacity.get("assessed_loss_capacity_amount")) and loss > capacity["assessed_loss_capacity_amount"]:
                issue("exposure_capacity_conflict", "Scenario loss exceeds the sourced financial loss capacity")
            if metrics["willingness_loss_amount"] is not None and loss > metrics["willingness_loss_amount"]:
                issue("exposure_willingness_conflict", "Scenario loss exceeds the client's recorded willingness")
        if number(exposure.get("lockup_months")) and number(horizon.get("months")):
            if exposure["lockup_months"] > horizon["months"]:
                issue("horizon_lockup_conflict", "Proposed lockup extends beyond the recorded goal horizon")
        if number(exposure.get("lockup_months")) and number(liquidity.get("required_within_months")):
            if exposure["lockup_months"] > liquidity["required_within_months"] and metrics["liquidity_shortfall"]:
                issue("liquidity_lockup_conflict", "Illiquidity extends beyond an underfunded liquidity need")
        experience = {x["instrument_type"]: x["level"] for x in dims.get("experience", {}).get("items", [])}
        for instrument in exposure.get("instrument_types", []):
            if experience.get(instrument) in (None, "none"):
                issue("experience_review", f"{instrument}: relevant experience is missing or recorded as none")
    result = {"input_snapshot": deepcopy(doc), "dimensions": dimensions, "metrics": metrics,
              "assigned_risk_rating": None, "rating_decision": "not-made",
              "scope": "Separate sourced risk dimensions; no composite risk score or investment recommendation."}
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    errors = validate_output_envelope(out, SKILL)
    if not isinstance(out, dict):
        return errors
    result = out.get("result")
    snapshot = result.get("input_snapshot") if isinstance(result, dict) else None
    if not isinstance(snapshot, dict):
        return errors + ["result.input_snapshot is required for risk-dimension reconciliation"]
    try:
        expected = compute(snapshot)
    except (ValueError, TypeError, KeyError) as exc:
        return errors + [f"invalid output input snapshot: {exc}"]
    if out != expected:
        errors.append("output differs from recomputed dimensions, metrics, findings or no-rating posture")
    return errors
