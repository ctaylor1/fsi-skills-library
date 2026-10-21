"""Payer evidence packaging; supplied observations are never clinical decisions."""

from datetime import timedelta
from decimal import Decimal, Inexact, Rounded, localcontext
from design_support import text, validate_with
from specialist_support import SpecialistReview

METHOD = "health-utilization-evidence-v1"


def bound(r, row, label):
    return r.evidence(row, label) & r.fields(row, ("locator",))


def utc(r, row, key):
    value = row.get(key)
    valid = r.need(
        isinstance(value, str) and (value.endswith("Z") or value.endswith("+00:00")),
        "utc-clock",
        key + " requires an explicit UTC timestamp",
        row,
    )
    return r.moment(row, key) if valid else None


def _evaluate(doc):
    r = SpecialistReview(doc, METHOD)
    d = r.data
    r.need(
        doc["context"]["capacity"] == "payer-utilization-review",
        "capacity",
        "This package requires payer-utilization-review capacity; map member advocacy separately",
    )
    r.need(doc["context"]["line_of_business"] == "health", "line", "Health line of business is required")
    request = d.get("request") or {}
    if not isinstance(request, dict):
        raise ValueError("request must be an object or null")
    bound(r, request, "Request")
    r.fields(request, ("request_id", "member_token", "provider_id", "service_id", "requested_service"))
    r.need(
        request.get("request_id") == doc["context"]["object_id"],
        "request-binding",
        "Request must match context.object_id",
        request,
    )
    r.need(
        request.get("service_type") in {"non-drug", "drug"},
        "service-type",
        "Known drug/non-drug classification is required",
        request,
    )
    service_on = r.date(request, "service_on", future=True)
    received = utc(r, request, "received_at")
    r.need(
        request.get("urgency") in {"standard", "expedited"},
        "urgency",
        "Known supplied standard or expedited urgency is required",
        request,
    )
    request_valid = r.clear
    inventory = d.get("inventory") or {}
    if not isinstance(inventory, dict):
        raise ValueError("inventory must be an object or null")
    bound(r, inventory, "Inventory statement")
    r.fields(inventory, ("statement",))
    criteria_complete = r.flag(inventory, "criteria_complete")
    observations_complete = r.flag(inventory, "observations_complete")
    inventory_valid = r.clear
    criteria = r.rows("criteria", "criterion_id")
    observations = r.rows("observations", "observation_id", nonempty=False)
    ids = {x["criterion_id"] for x in criteria}
    for obs in observations:
        r.need(obs.get("criterion_id") in ids, "orphan-observation", "Observation has no supplied criterion", obs)
    rows = []
    for criterion in criteria:
        begin = len(r.findings)
        bound(r, criterion, "Criterion")
        r.fields(criterion, ("statement",))
        r.applicable(criterion, service_on, "Criterion")
        for key in ("market", "program", "product"):
            r.need(criterion.get(key) == d.get(key), "criterion-scope", "Criterion must match actual " + key, criterion)
        r.need(
            criterion.get("service_id") == request.get("service_id"),
            "criterion-service",
            "Criterion service must match the request",
            criterion,
        )
        r.need(
            criterion.get("kind") in {"benefit", "clinical"},
            "criterion-kind",
            "Criterion kind must be benefit or clinical",
            criterion,
        )
        mode = criterion.get("mode")
        r.need(
            mode in {"professional-observation", "numeric-threshold"},
            "criterion-mode",
            "Supported criterion mode is required",
            criterion,
        )
        threshold = None
        if mode == "numeric-threshold":
            threshold = r.num(criterion, "threshold", signed=True)
            r.fields(criterion, ("unit",))
            r.need(
                criterion.get("comparator") in {"ge", "le", "eq"},
                "comparator",
                "Comparator must be ge, le or eq",
                criterion,
            )
        matched = [o for o in observations if o.get("criterion_id") == criterion["criterion_id"]]
        r.need(bool(matched), "missing-observation", "Criterion has no supplied observation", criterion)
        evidence_states = []
        for obs in matched:
            local = len(r.findings)
            bound(r, obs, "Observation")
            r.fields(obs, ("summary",))
            r.need(
                obs.get("request_id") == request.get("request_id")
                and obs.get("service_id") == request.get("service_id"),
                "observation-binding",
                "Observation must bind the exact request and service",
                obs,
            )
            r.date(obs, "observed_on")
            r.need(
                isinstance(obs.get("contrary"), bool),
                "contrary-flag",
                "Observation must explicitly identify contrary evidence",
                obs,
            )
            state = "unknown"
            if mode == "professional-observation":
                r.fields(obs, ("professional_reviewer", "professional_role"))
                r.need(
                    obs.get("state") in {"met", "unmet", "unknown", "conflicting"},
                    "observation-state",
                    "Professional state must be met, unmet, unknown or conflicting",
                    obs,
                )
                state = obs.get("state", "unknown")
                if state == "unknown":
                    r.add("unknown-observation", "Professional observation remains unknown", obs)
            elif mode == "numeric-threshold":
                value = r.num(obs, "value", signed=True)
                same_unit = r.need(
                    text(obs.get("unit")) and obs.get("unit") == criterion.get("unit"),
                    "numeric-unit",
                    "Numeric observation and threshold require identical declared units",
                    obs,
                )
                if threshold is not None and value is not None and same_unit:
                    comparator = criterion.get("comparator")
                    comparison = {"ge": value >= threshold, "le": value <= threshold, "eq": value == threshold}
                    if comparator in comparison:
                        state = "met" if comparison[comparator] else "unmet"
            if any(f["severity"] == "gap" for f in r.findings[local:]):
                state = "unknown"
            evidence_states.append(
                {
                    "observation_id": obs["observation_id"],
                    "state": state,
                    "contrary": obs.get("contrary"),
                    "source_refs": obs.get("source_refs", []),
                }
            )
        states = {x["state"] for x in evidence_states}
        valid = request_valid and inventory_valid and not any(f["severity"] == "gap" for f in r.findings[begin:])
        if valid and (
            "conflicting" in states or {"met", "unmet"} <= states or any(x["contrary"] is True for x in evidence_states)
        ):
            state = "conflicting"
            r.add(
                "contrary-evidence",
                "Contrary or conflicting observations require qualified review",
                criterion,
                severity="review",
            )
        elif valid and states in ({"met"}, {"unmet"}):
            state = next(iter(states))
        else:
            state = "unknown"
        rows.append(
            {
                "criterion_id": criterion["criterion_id"],
                "kind": criterion.get("kind"),
                "mode": mode,
                "evidence_state": state,
                "observations": evidence_states,
                "source_refs": criterion.get("source_refs", []),
                "clinical_appropriateness": "not_determined",
            }
        )
    # The administrative clock is independent of missing clinical observations.
    begin = len(r.findings)
    clock = d.get("clock") or {}
    if not isinstance(clock, dict):
        raise ValueError("clock must be an object or null")
    bound(r, clock, "Administrative rule")
    r.fields(clock, ("rule_id", "rule_basis"))
    r.applicable(clock, received.date() if received else None, "Administrative rule")
    for key in ("market", "program", "product"):
        r.need(clock.get(key) == d.get(key), "clock-scope", "Administrative rule must match actual " + key, clock)
    r.need(
        clock.get("service_type") == request.get("service_type") and clock.get("urgency") == request.get("urgency"),
        "clock-applicability",
        "Administrative rule must match exact service type and urgency",
        clock,
    )
    r.need(
        clock.get("start_event") == "request-received" and clock.get("clock_basis") == "elapsed-hours",
        "clock-basis",
        "Only an explicitly supplied request-received elapsed-hours rule is supported; business days are unsupported",
        clock,
    )
    hours = r.num(clock, "hours")
    r.need(hours is not None and hours > 0, "clock-duration", "Positive explicit clock duration is required", clock)
    if hours is not None:
        r.need(
            hours <= Decimal("87600") and hours * 3600000000 == (hours * 3600000000).to_integral_value(),
            "clock-precision",
            "Clock must fit ten years and exact microsecond precision",
            clock,
        )
    assessed = utc(r, d, "assessment_at")
    r.need(
        received is not None and assessed is not None and assessed >= received,
        "clock-sequence",
        "Assessment cannot precede receipt",
        clock,
    )
    clock_valid = request_valid and not any(f["severity"] == "gap" for f in r.findings[begin:])
    target = received + timedelta(microseconds=int(hours * 3600000000)) if clock_valid else None
    remaining = (
        Decimal(
            (target - assessed).days * 86400000000
            + (target - assessed).seconds * 1000000
            + (target - assessed).microseconds
        )
        / Decimal(1000000)
        if target
        else None
    )
    return r.finish(
        {
            "request": request,
            "criteria": rows,
            "supplied_observations": observations,
            "criteria_inventory_complete": criteria_complete,
            "observation_inventory_complete": observations_complete,
            "administrative_target_utc": target.isoformat().replace("+00:00", "Z") if target else None,
            "remaining_seconds": remaining,
            "administrative_rule_id": clock.get("rule_id"),
            "administrative_target_is_legal_opinion": False,
            "medical_necessity": "not_determined",
            "benefit_decision": "not_determined",
            "denial_recommended": False,
            "submission_performed": False,
        }
    )


def evaluate(doc):
    with localcontext() as context:
        context.prec = 256
        context.Emax = 1000
        context.Emin = -1000
        context.traps[Inexact] = True
        context.traps[Rounded] = True
        return _evaluate(doc)


def validate(doc):
    return validate_with(evaluate, doc)
