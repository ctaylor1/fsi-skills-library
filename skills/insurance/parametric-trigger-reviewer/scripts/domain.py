"""One contract event, explicit verifier/revision evidence and supplied tier schedule."""

from decimal import Decimal, Inexact, Rounded, localcontext
from design_support import total, validate_with
from specialist_support import SpecialistReview
from workflow_contract import timestamp

METHOD = "supplied-parametric-event-tiers-v1"


def _evaluate(doc):
    r = SpecialistReview(doc, METHOD)
    d = r.data
    r.need(
        doc["context"]["capacity"] == "parametric-claims-review",
        "capacity",
        "Parametric claims review capacity is required",
    )
    r.need(doc["context"]["line_of_business"] == "pc", "line", "This bounded package requires the P&C line")
    contract, event = d.get("contract"), d.get("event")
    if not isinstance(contract, dict) or not isinstance(event, dict):
        raise ValueError("contract and event must be objects")
    r.need(
        doc["context"]["object_id"] == str(contract.get("contract_id")) + "/" + str(event.get("event_id")),
        "object-binding",
        "Context object_id must bind exact contract_id/event_id",
    )
    inventory = d.get("inventory") or {}
    r.evidence(inventory, "Inventory attestation")
    r.fields(inventory, ("locator", "reading_statement", "ledger_statement"))
    r.need(
        inventory.get("contract_id") == contract.get("contract_id")
        and inventory.get("event_id") == event.get("event_id")
        and inventory.get("aggregate_period_id") == contract.get("aggregate_period_id"),
        "inventory-scope",
        "Inventory statements must bind exact contract, event and aggregate period",
        inventory,
    )
    r.evidence(event)
    r.fields(event, ("event_id", "parameter", "unit", "location"))
    occurred = r.moment(event, "occurred_at")
    start = r.moment(event, "window_start_at")
    end = r.moment(event, "window_end_at")
    r.need(
        start is not None and end is not None and occurred is not None and start <= occurred < end,
        "event-window",
        "Event must fall in its positive [start,end) measurement window",
        event,
    )
    r.applicable(contract, occurred.date() if occurred else None, "Contract version")
    r.fields(
        contract, ("contract_id", "parameter", "unit", "location", "primary_verifier", "currency", "basis_risk_note")
    )
    r.need(
        contract.get("aggregation") == "single-certified-value",
        "aggregation",
        "Only a single contract-defined certified index value is supported",
        contract,
    )
    r.flag(contract, "trigger_terms_reviewed")
    coverage_start = timestamp(contract["coverage_start_at"]) if contract.get("coverage_start_at") else None
    coverage_end = timestamp(contract["coverage_end_at"]) if contract.get("coverage_end_at") else None
    r.need(
        coverage_start is not None
        and coverage_end is not None
        and start is not None
        and end is not None
        and coverage_start <= start < end <= coverage_end,
        "coverage-window",
        "Measurement window must be contained in the supplied coverage interval",
        contract,
    )
    r.need(
        all(event.get(k) == contract.get(k) for k in ("parameter", "unit", "location")),
        "event-scope",
        "Event parameter, unit and exact location must match the contract",
        event,
    )
    fallback = r.strings(contract, "fallback_verifiers")
    r.need(
        contract.get("primary_verifier") not in fallback,
        "verifier-order",
        "Primary verifier cannot also be a fallback",
        contract,
    )
    states = r.rows("verifier_status", "verifier_id")
    state_by = {x["verifier_id"]: x for x in states}
    for row in states:
        observed = r.moment(row, "observed_at")
        r.need(
            observed is not None and end is not None and observed >= end,
            "availability-date",
            "Event-specific verifier status must be observed after window completion",
            row,
        )
        r.need(
            row.get("event_id") == event.get("event_id"),
            "verifier-scope",
            "Verifier availability evidence must name this event",
            row,
        )
        r.need(
            isinstance(row.get("available"), bool),
            "verifier-availability",
            "Verifier availability must be explicitly known",
            row,
        )
    readings = r.rows("readings", "reading_id")
    r.flag(d, "reading_inventory_complete")
    by = {x["reading_id"]: x for x in readings}
    issued, parents, children = {}, {}, {}
    valid_scope = {}
    for row in readings:
        r.fields(row, ("verifier_id", "revision"))
        r.need(
            row.get("finality") in {"final", "preliminary", "retracted"},
            "reading-finality",
            "Use final/preliminary/retracted",
            row,
        )
        r.num(row, "value", signed=True)
        when = r.moment(row, "issued_at")
        issued[row["reading_id"]] = when
        valid_scope[row["reading_id"]] = r.need(
            row.get("event_id") == event.get("event_id")
            and all(row.get(k) == event.get(k) for k in ("parameter", "unit", "location"))
            and row.get("window_start_at") is not None
            and row.get("window_end_at") is not None
            and timestamp(row["window_start_at"]) == start
            and timestamp(row["window_end_at"]) == end,
            "reading-scope",
            "Reading must bind exact event, parameter, unit, location and measurement window",
            row,
        )
        r.need(
            when is not None and end is not None and when >= end,
            "publication-order",
            "Observed index publication must not precede window completion",
            row,
        )
        r.need("supersedes_reading_id" in row, "revision-chain", "Explicit predecessor ID or null is required", row)
        previous = row.get("supersedes_reading_id")
        parents[row["reading_id"]] = previous
        if previous is not None:
            r.need(
                isinstance(previous, str) and previous in by and previous != row["reading_id"],
                "revision-parent",
                "Predecessor must be another supplied reading",
                row,
            )
            children.setdefault(previous, []).append(row["reading_id"])
    for rid, previous in parents.items():
        if previous in by:
            row, old = by[rid], by[previous]
            r.need(
                row["verifier_id"] == old["verifier_id"]
                and issued[rid] is not None
                and issued[previous] is not None
                and issued[rid] > issued[previous],
                "revision-order",
                "Revisions must preserve verifier and strictly advance publication time",
                row,
            )
    r.need(
        all(len(v) == 1 for v in children.values()),
        "revision-branch",
        "Competing revision branches require owner reconciliation",
    )
    # Strictly increasing predecessor timestamps also prevent cycles.
    selected = by.get(d.get("selected_reading_id"))
    r.need(selected is not None, "selection", "Explicit selected reading is missing")
    selected_verifier = selected.get("verifier_id") if selected else None
    r.need(
        selected_verifier in [contract.get("primary_verifier"), *fallback],
        "verifier-authority",
        "Selected verifier is not contractually designated",
    )
    terminals = [x for x in readings if x.get("verifier_id") == selected_verifier and x["reading_id"] not in children]
    r.need(
        len(terminals) == 1 and selected is not None and terminals[0]["reading_id"] == selected["reading_id"],
        "terminal-reading",
        "Exactly one latest explicitly linked reading must be selected; unrelated finals are conflicts",
    )
    if selected:
        r.need(selected.get("finality") == "final", "finality", "Selected terminal reading is not final", selected)
        current = state_by.get(selected_verifier)
        r.need(
            current is not None and current.get("available") is True,
            "selected-verifier",
            "Selected verifier needs affirmative event-specific availability evidence",
        )
        if selected_verifier != contract.get("primary_verifier"):
            primary = state_by.get(contract.get("primary_verifier"))
            r.need(
                primary is not None and primary.get("available") is False,
                "fallback-basis",
                "Fallback requires explicit primary unavailability evidence",
            )
            r.need(
                not any(
                    x.get("verifier_id") == contract.get("primary_verifier")
                    and x.get("finality") == "final"
                    and x["reading_id"] not in children
                    and valid_scope[x["reading_id"]]
                    for x in readings
                ),
                "contrary-primary",
                "Available final primary evidence conflicts with fallback use",
            )
    tiers = r.rows("tiers", "tier_id", contract)
    operator = contract.get("operator")
    r.need(operator in {">=", ">", "<=", "<"}, "operator", "Unsupported threshold operator", contract)
    amounts, thresholds = [], []
    for row in tiers:
        thresholds.append(r.num(row, "threshold", signed=True))
        amounts.append(r.num(row, "payout"))
    if all(v is not None for v in thresholds + amounts):
        higher = operator in {">=", ">"}
        r.need(
            all(
                (thresholds[i] < thresholds[i + 1] if higher else thresholds[i] > thresholds[i + 1])
                for i in range(len(thresholds) - 1)
            ),
            "tier-order",
            "Thresholds must be strictly ordered from lower to greater severity",
        )
        r.need(
            all(amounts[i] <= amounts[i + 1] for i in range(len(amounts) - 1)),
            "tier-payout",
            "Payouts must not decrease with severity",
        )
    event_cap = r.num(contract, "event_cap")
    aggregate_limit = r.num(contract, "aggregate_limit")
    r.fields(contract, ("aggregate_period_id",))
    period_start = r.date(contract, "aggregate_period_start", future=True)
    period_end = r.date(contract, "aggregate_period_end", future=True)
    r.need(
        period_start is not None
        and period_end is not None
        and occurred is not None
        and period_start <= occurred.date() <= period_end,
        "aggregate-period",
        "The event must fall within the explicit inclusive aggregate period",
        contract,
    )
    ledger = r.rows("aggregate_ledger", "entry_id", nonempty=False)
    r.flag(d, "aggregate_ledger_complete")
    paid, ids = [], set()
    for row in ledger:
        r.fields(row, ("event_id",))
        r.need(
            row["event_id"] not in ids,
            "duplicate-event",
            "Use one source-reconciled cumulative net-paid record per event; do not duplicate transactions",
            row,
        )
        ids.add(row["event_id"])
        r.need(
            row.get("contract_id") == contract.get("contract_id")
            and row.get("currency") == contract.get("currency")
            and row.get("aggregate_period_id") == contract.get("aggregate_period_id"),
            "ledger-scope",
            "Ledger must bind the same contract, currency and aggregate period",
            row,
        )
        paid_through = r.date(row, "paid_through")
        r.need(
            paid_through is not None
            and period_start is not None
            and period_end is not None
            and period_start <= paid_through <= period_end,
            "ledger-period",
            "Ledger paid-through date must fall inside the aggregate period",
            row,
        )
        if row["event_id"] == event.get("event_id"):
            r.need(
                paid_through is not None and occurred is not None and paid_through >= occurred.date(),
                "paid-chronology",
                "Current-event paid ledger cannot predate the event",
                row,
            )
        paid.append(r.num(row, "cumulative_net_paid"))
    value = r.num(selected, "value", signed=True) if selected else None
    matched = gross = current_paid = remaining = unpaid = None
    if r.clear:
        comparisons = {
            ">=": lambda x, t: x >= t,
            ">": lambda x, t: x > t,
            "<=": lambda x, t: x <= t,
            "<": lambda x, t: x < t,
        }
        matches = [i for i, t in enumerate(thresholds) if comparisons[operator](value, t)]
        matched = tiers[matches[-1]]["tier_id"] if matches else None
        gross = min(amounts[matches[-1]] if matches else Decimal(0), event_cap)
        current_paid = total(amount for row, amount in zip(ledger, paid) if row["event_id"] == event["event_id"])
        remaining = max(Decimal(0), aggregate_limit - total(paid))
        unpaid = min(remaining, max(Decimal(0), gross - current_paid))
        if total(paid) > aggregate_limit or current_paid > gross:
            r.add(
                "paid-control-break",
                "Recorded paid amount exceeds a supplied aggregate limit or the current scenario; no recovery decision inferred",
                severity="review",
            )
    return r.finish(
        {
            "event_id": event.get("event_id"),
            "selected_reading_id": d.get("selected_reading_id"),
            "selected_verifier": selected_verifier,
            "index_value": value if r.clear else None,
            "matched_tier_id": matched,
            "gross_event_scenario": gross,
            "current_event_recorded_paid": current_paid,
            "aggregate_remaining": remaining,
            "provisional_unpaid_scenario": unpaid,
            "currency": contract.get("currency"),
            "basis_risk_note": contract.get("basis_risk_note"),
            "coverage_determination": "not_performed",
            "payment_authorized": False,
            "verifier_authenticated": False,
            "physical_loss_estimated": False,
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
