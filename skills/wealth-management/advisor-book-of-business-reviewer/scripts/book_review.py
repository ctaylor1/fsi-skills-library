"""Evidence-bound book coverage, explicit service priority and bounded daily workload."""

from datetime import timedelta
from copy import deepcopy
from wealth_contract import iso_date, nonempty, make_output
from wealth_workflow import base_errors, rows, enum, number, dec, money, cited, add, base_findings, common_result

SKILL = "advisor-book-of-business-reviewer"
TRIGGERS = {
    "review-overdue",
    "review-due",
    "evidence-gap",
    "life-event",
    "service-request",
    "retention-concern",
    "client-requested-growth",
    "upstream-issue",
}
SIGNALS = {"life-event", "service-request", "retention-concern", "client-requested-growth"}
AMOUNTS = (
    "opening_assets",
    "closing_assets",
    "external_inflows",
    "external_outflows",
    "internal_net_transfer",
    "market_change",
    "fees_debited",
    "recognized_revenue",
    "direct_service_cost",
)


def whole(value, lo=0, hi=100000):
    return number(value, lo, hi) and dec(value) == dec(value).to_integral_value()


def sources(*items):
    return sorted(
        {
            sid
            for item in items
            if isinstance(item, dict)
            for ids in [item.get("source_ids")]
            if isinstance(ids, list)
            for sid in ids
            if isinstance(sid, str)
        }
    )


def plus_days(date, days):
    try:
        return date + timedelta(days=days)
    except OverflowError:
        return None


def validate(doc):
    errors = base_errors(doc)
    if errors:
        return errors
    if (
        doc.get("scope_type") != "advisor-book"
        or not nonempty(doc.get("book_id"))
        or doc["household_id"] != "book:" + str(doc.get("book_id"))
    ):
        errors.append("book scope requires scope_type advisor-book, book_id and household_id book:<book_id>")
    if doc.get("currency") != "USD":
        errors.append("one USD book only; no FX is modeled")
    start, end = iso_date(doc.get("period_start")), iso_date(doc.get("period_end"))
    as_of = iso_date(doc["as_of"])
    horizon = iso_date(doc.get("planning_end"))
    if not start or not end or not start <= end <= as_of:
        errors.append("period_start <= period_end <= as_of dates required")
    if not horizon or not 0 <= (horizon - as_of).days <= 366:
        errors.append("planning_end must be within 366 days after as_of")
    if doc.get("population_complete") is not None and not isinstance(doc["population_complete"], bool):
        errors.append("population_complete must be boolean or null")
    policy = doc["policy"]
    if policy.get("effort_basis") != "incremental-nonoverlapping-task-minutes":
        errors.append("policy effort_basis must explicitly confirm nonoverlapping task estimates")
    if horizon and horizon > iso_date(policy["valid_until"]):
        errors.append("planning horizon extends beyond policy validity")
    if not nonempty(policy.get("review_owner_id")):
        errors.append("policy.review_owner_id required")
    if not whole(policy.get("evidence_gap_effort_minutes"), 1, 100000):
        errors.append("policy.evidence_gap_effort_minutes must be a positive integer")
    priorities = rows(policy, "priority_rules", errors, "trigger")
    if {r.get("trigger") for r in priorities if isinstance(r.get("trigger"), str)} != TRIGGERS:
        errors.append("policy must explicitly rank all supported triggers")
    for row in priorities:
        if (
            not enum(row.get("trigger"), TRIGGERS)
            or not whole(row.get("rank"), 1, 100)
            or not nonempty(row.get("rationale"))
        ):
            errors.append("priority rule requires supported trigger, integer rank 1..100 and rationale")
    ranks = {
        r["trigger"]: int(dec(r["rank"]))
        for r in priorities
        if enum(r.get("trigger"), TRIGGERS) and whole(r.get("rank"), 1, 100)
    }
    if len(ranks) == len(TRIGGERS) and ranks["client-requested-growth"] <= max(
        v for k, v in ranks.items() if k != "client-requested-growth"
    ):
        errors.append("client-requested growth must rank after every service, retention and evidence concern")
    tiers = rows(policy, "service_tiers", errors, "tier_id")
    if not tiers:
        errors.append("policy requires explicit service tiers")
    for row in tiers:
        for field, lo, hi in [
            ("review_interval_days", 1, 3660),
            ("initial_review_days", 0, 3660),
            ("review_effort_minutes", 1, 100000),
        ]:
            if not whole(row.get(field), lo, hi):
                errors.append(f"service tier {field} must be an explicit integer in [{lo},{hi}]")
        if not nonempty(row.get("label")):
            errors.append("service tier label required")
    owners = rows(doc, "owners", errors, "owner_id")
    for row in owners:
        if row.get("availability_complete") is not None and not isinstance(row["availability_complete"], bool):
            errors.append("availability_complete must be boolean/null")
        if row.get("queue_overlap_reviewed") is not None and not isinstance(row["queue_overlap_reviewed"], bool):
            errors.append("queue_overlap_reviewed must be boolean/null")
        slots = rows(row, "availability", errors, "date")
        for slot in slots:
            date = iso_date(slot.get("date"))
            if date is None or horizon is None or not as_of <= date <= horizon:
                errors.append("capacity date outside as_of..planning_end")
            for field in ["working_minutes", "unrelated_committed_minutes"]:
                if slot.get(field) is not None and not whole(slot[field], 0, 1440):
                    errors.append("daily capacity minutes must be integers 0..1440 or null")
    households = rows(doc, "households", errors, "household_id")
    if not households:
        errors.append("at least one household record required; no empty book readiness")
    for row in households:
        if isinstance(row.get("household_id"), str) and row["household_id"].startswith("book:"):
            errors.append("household records require actual household IDs, never a book collection marker")
        for field in ["owner_id", "tier_id", "segment_id"]:
            if row.get(field) is not None and not nonempty(row[field]):
                errors.append(f"household {field} must be nonempty text or null")
        if row.get("segmentation_basis") is not None and not enum(
            row["segmentation_basis"], {"service-model", "documented-planning-complexity", "relationship-stage"}
        ):
            errors.append("unsupported segmentation basis; no wealth or protected-trait score")
        joined = iso_date(row.get("joined_on"))
        departed = iso_date(row.get("departed_on"))
        if row.get("joined_on") is not None and (joined is None or joined > as_of):
            errors.append("joined_on must be nonfuture date or null")
        if "departed_on" not in row:
            errors.append("departed_on must be explicit null for active or a dated departure")
        elif row["departed_on"] is not None and (
            departed is None or departed > as_of or (joined and departed < joined)
        ):
            errors.append("departed_on must be between joined_on and as_of")
        history = row.get("review_history")
        if not isinstance(history, dict):
            errors.append("review_history object required")
        else:
            if not enum(history.get("status"), {"known", "none", "unknown"}):
                errors.append("review_history.status must be known, none or unknown")
            reviewed = iso_date(history.get("last_completed_on"))
            if history.get("last_completed_on") is not None and (
                reviewed is None or reviewed > as_of or (joined and reviewed < joined)
            ):
                errors.append("last completed review must be dated between joined_on and as_of")
            if history.get("status") != "known" and history.get("last_completed_on") is not None:
                errors.append("none/unknown history cannot assert last completed date")
    signals = rows(doc, "signals", errors, "signal_id")
    for row in signals:
        if (
            not nonempty(row.get("household_id"))
            or not enum(row.get("kind"), SIGNALS)
            or not nonempty(row.get("description"))
        ):
            errors.append("signal needs household, supported kind and substantive description")
        observed = iso_date(row.get("observed_on"))
        due = iso_date(row.get("due_on"))
        if row.get("observed_on") is not None and (observed is None or observed > as_of):
            errors.append("signal observed_on must be nonfuture date or null")
        if row.get("due_on") is not None and (due is None or (observed and due < observed)):
            errors.append("signal due date must not precede observation")
        if row.get("estimated_minutes") is not None and not whole(row["estimated_minutes"], 1, 100000):
            errors.append("signal effort must be positive integer or null")
        if row.get("client_interest_confirmed") is not None and not isinstance(row["client_interest_confirmed"], bool):
            errors.append("client_interest_confirmed must be boolean/null")
    economics = doc.get("economics")
    if not isinstance(economics, dict) or not enum(economics.get("status"), {"provided", "not-provided"}):
        errors.append("economics requires explicit provided/not-provided status")
    elif economics["status"] == "provided":
        if not nonempty(economics.get("definition_version")):
            errors.append("economics definition_version required")
        for field in ["period_start", "period_end"]:
            if economics.get(field) != doc.get(field):
                errors.append("economics must match requested measurement period")
        for row in rows(economics, "household_records", errors, "household_id"):
            for field in AMOUNTS:
                lo = -(10**15) if field in {"internal_net_transfer", "market_change"} else 0
                if row.get(field) is not None and not number(row[field], lo, 10**15):
                    errors.append(f"economics {field} must be finite decimal in stated range or null")
    elif not nonempty(economics.get("reason")):
        errors.append("not-provided economics requires an explicit reason")
    return errors


def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    findings = base_findings(doc)
    as_of = iso_date(doc["as_of"])
    horizon = iso_date(doc["planning_end"])
    policy = doc["policy"]
    policy_ok = cited(policy, doc, findings, "policy")
    rules = {r["trigger"]: r for r in policy["priority_rules"]}
    tiers = {t["tier_id"]: t for t in policy["service_tiers"]}
    for key, row in rules.items():
        row_ok = cited(row, doc, findings, "policy.priority_rules." + key)
        policy_ok = policy_ok and row_ok
    tier_ok = {key: cited(row, doc, findings, "policy.service_tiers." + key) for key, row in tiers.items()}
    scope_ok = cited({"source_ids": doc.get("scope_source_ids")}, doc, findings, "book_scope")
    population_supported = doc.get("population_complete") is True and scope_ok
    if not population_supported:
        add(
            findings,
            "population-incomplete",
            "Complete beginning/end-period and current book population is not established. Rates and full-book totals remain unknown.",
            "population_complete",
        )
    households = {h["household_id"]: h for h in doc["households"]}
    owners = {o["owner_id"]: o for o in doc["owners"]}
    if policy["review_owner_id"] not in owners:
        add(
            findings,
            "review-owner-missing",
            "Policy review owner is absent from owner capacity register.",
            "policy.review_owner_id",
        )
    owner_state = {}
    capacity_calendar = []
    for owner in doc["owners"]:
        oid = owner["owner_id"]
        path = "owners." + oid
        complete = (
            cited(owner, doc, findings, path)
            and owner.get("availability_complete") is True
            and owner.get("queue_overlap_reviewed") is True
        )
        if not complete:
            add(
                findings,
                "capacity-unknown",
                "Owner availability completeness or queue/commitment overlap review is unknown. No capacity commitment can be inferred.",
                path,
            )
        slots = {}
        known_work = 0
        known_committed = 0
        for slot in owner["availability"]:
            sp = path + ".availability." + slot["date"]
            ok = cited(slot, doc, findings, sp)
            for field in ["working_minutes", "unrelated_committed_minutes"]:
                if slot.get(field) is None:
                    add(findings, "capacity-unknown", "Missing " + field + " is not zero.", sp)
                    ok = False
            available = None
            if ok:
                work = int(dec(slot["working_minutes"]))
                committed = int(dec(slot["unrelated_committed_minutes"]))
                known_work += work
                known_committed += committed
                if committed > work:
                    add(
                        findings, "capacity-overcommitted", "Existing unrelated commitments exceed working minutes.", sp
                    )
                    complete = False
                available = max(0, work - committed)
                slots[slot["date"]] = available
            else:
                complete = False
            capacity_calendar.append(
                {
                    "owner_id": oid,
                    "date": slot["date"],
                    "available_before_queue_minutes": available,
                    "source_ids": deepcopy(slot.get("source_ids")),
                }
            )
        owner_state[oid] = {
            "slots": slots,
            "complete": complete,
            "known_working_minutes": known_work,
            "known_committed_minutes": known_committed,
            "available_before_queue_minutes": sum(slots.values()),
            "allocated_minutes": 0,
            "unallocated_known_minutes": 0,
            "unknown_effort_actions": 0,
        }
    actions = []
    calendar = []
    cohort_known = True
    starting = []
    retained = []
    added = []
    departed = []

    def action(aid, hid, owner, trigger, due, minutes, description, source_ids, blocked=False):
        rule = rules[trigger]
        actions.append(
            {
                "action_id": aid,
                "household_id": hid,
                "owner_id": owner,
                "trigger": trigger,
                "category": "growth"
                if trigger == "client-requested-growth"
                else "retention"
                if trigger == "retention-concern"
                else "service",
                "priority_rank": int(dec(rule["rank"])),
                "priority_rationale": rule["rationale"],
                "policy_version": policy["version"],
                "due_on": due,
                "estimated_minutes": minutes,
                "description": description,
                "source_ids": sorted(
                    {
                        x
                        for ids in [source_ids, rule.get("source_ids")]
                        if isinstance(ids, list)
                        for x in ids
                        if isinstance(x, str)
                    }
                ),
                "evidence_state": "blocked" if blocked or not policy_ok else "documented-for-review",
                "work_allocations": [],
                "planned_completion_on": None,
                "deadline_met": None,
                "work_status": "not-planned",
            }
        )

    for h in doc["households"]:
        hid = h["household_id"]
        path = "households." + hid
        ok = cited(h, doc, findings, path)
        history = h["review_history"]
        history_ok = cited(history, doc, findings, path + ".review_history")
        joined = iso_date(h.get("joined_on"))
        left = iso_date(h.get("departed_on"))
        active = left is None
        if not joined:
            add(
                findings,
                "relationship-date-unknown",
                "Relationship start date is missing; cohort membership is unknown.",
                path + ".joined_on",
            )
            cohort_known = False
        elif ok:
            if joined < iso_date(doc["period_start"]) and (left is None or left >= iso_date(doc["period_start"])):
                starting.append(hid)
                if left is None or left > iso_date(doc["period_end"]):
                    retained.append(hid)
            if iso_date(doc["period_start"]) <= joined <= iso_date(doc["period_end"]):
                added.append(hid)
            if left and iso_date(doc["period_start"]) <= left <= iso_date(doc["period_end"]):
                departed.append(hid)
        else:
            cohort_known = False
        for field in ["owner_id", "tier_id", "segment_id", "segmentation_basis"]:
            if h.get(field) is None:
                add(findings, "household-context-unknown", "Missing " + field + " remains unknown.", path + "." + field)
        owner = h.get("owner_id")
        tier = tiers.get(h.get("tier_id"))
        due = None
        if active and owner not in owners:
            add(
                findings,
                "household-owner-unknown",
                "Household service owner has no capacity record.",
                path + ".owner_id",
            )
        if tier is None:
            add(findings, "tier-unknown", "Household service-tier policy is unavailable.", path + ".tier_id")
        elif ok and history_ok and tier_ok[tier["tier_id"]] and joined:
            if history["status"] == "known" and iso_date(history.get("last_completed_on")):
                due = plus_days(iso_date(history["last_completed_on"]), int(dec(tier["review_interval_days"])))
            elif history["status"] == "none":
                due = plus_days(joined, int(dec(tier["initial_review_days"])))
        status = (
            "departed"
            if not active
            else "unknown"
            if due is None
            else "overdue"
            if due < as_of
            else "due-today"
            if due == as_of
            else "due-in-window"
            if due <= horizon
            else "beyond-window"
        )
        calendar.append(
            {
                "household_id": hid,
                "owner_id": owner,
                "tier_id": h.get("tier_id"),
                "segment_id": h.get("segment_id"),
                "segmentation_basis": h.get("segmentation_basis"),
                "active_as_of": active,
                "last_completed_on": history.get("last_completed_on"),
                "next_review_due_on": due.isoformat() if due else None,
                "days_overdue": max(0, (as_of - due).days) if due else None,
                "coverage_state": status,
                "source_ids": sources(h, history, tier, policy),
            }
        )
        if active and due is None:
            add(
                findings,
                "review-coverage-unknown",
                "Next review cannot be determined from sourced relationship, tier and completion history.",
                path,
            )
            action(
                "review-evidence:" + hid,
                hid,
                owner,
                "evidence-gap",
                doc["as_of"],
                int(dec(policy["evidence_gap_effort_minutes"])),
                "Obtain the missing service-tier, relationship or completed-review evidence.",
                h.get("source_ids", []),
                not ok,
            )
        elif active and due <= horizon:
            trigger = "review-overdue" if due < as_of else "review-due"
            if due < as_of:
                add(
                    findings,
                    "review-overdue",
                    f"Review is {(as_of - due).days} days overdue under supplied service policy.",
                    path,
                    household_id=hid,
                )
            action(
                "review:" + hid,
                hid,
                owner,
                trigger,
                due.isoformat(),
                int(dec(tier["review_effort_minutes"])),
                "Prepare the policy-defined household review using current client evidence.",
                sources(h, history, tier, policy),
                not ok,
            )
    for signal in doc["signals"]:
        sid = signal["signal_id"]
        path = "signals." + sid
        ok = cited(signal, doc, findings, path)
        h = households.get(signal["household_id"])
        kind = signal["kind"]
        if h is None:
            add(findings, "signal-household-unknown", "Signal household is outside the declared book.", path)
            ok = False
        elif h["departed_on"] is not None:
            add(
                findings,
                "departed-household-signal",
                "Active service/growth signal on departed relationship requires owner review.",
                path,
            )
            ok = False
        if h is not None and not cited(h, doc, findings, path + ".household-owner"):
            ok = False
        for field in ["observed_on", "due_on", "estimated_minutes"]:
            if signal.get(field) is None:
                add(findings, "signal-data-unknown", "Missing " + field + " remains unknown.", path)
                ok = False
        if kind == "client-requested-growth" and signal.get("client_interest_confirmed") is not True:
            add(
                findings,
                "growth-interest-unconfirmed",
                "No confirmed client interest; do not invent an upsell task.",
                path,
            )
            ok = False
        due = signal.get("due_on")
        minutes = int(dec(signal["estimated_minutes"])) if signal.get("estimated_minutes") is not None else None
        if due is None or iso_date(due) <= horizon:
            action(
                "signal:" + sid,
                signal["household_id"],
                h.get("owner_id") if h else None,
                kind,
                due,
                minutes,
                signal["description"],
                sources(signal, h, policy),
                not ok,
            )
    for i, issue in enumerate(doc["upstream_issues"]):
        if issue["status"] == "unresolved":
            action(
                "upstream:" + str(i),
                None,
                policy["review_owner_id"],
                "upstream-issue",
                doc["as_of"],
                int(dec(policy["evidence_gap_effort_minutes"])),
                issue["message"],
                issue.get("source_ids", []),
            )
    actions.sort(
        key=lambda a: (a["priority_rank"], a["due_on"] or "0000-00-00", a["household_id"] or "", a["action_id"])
    )
    for order, a in enumerate(actions, 1):
        a["sequence"] = order
        state = owner_state.get(a["owner_id"])
        minutes = a["estimated_minutes"]
        if state is None or a["evidence_state"] == "blocked":
            a["work_status"] = "blocked-evidence-or-owner"
            continue
        if minutes is None:
            state["unknown_effort_actions"] += 1
            a["work_status"] = "unknown-effort"
            continue
        if not state["complete"]:
            a["work_status"] = "capacity-not-evaluable"
            state["unallocated_known_minutes"] += minutes
            continue
        remaining = minutes
        for date in sorted(state["slots"]):
            allocate = min(remaining, state["slots"][date])
            if allocate:
                a["work_allocations"].append({"date": date, "minutes": allocate})
                state["slots"][date] -= allocate
                state["allocated_minutes"] += allocate
                remaining -= allocate
            if remaining == 0:
                break
        state["unallocated_known_minutes"] += remaining
        a["work_status"] = "fully-allocated-draft" if remaining == 0 else "capacity-shortfall"
        if a["work_allocations"] and remaining == 0:
            a["planned_completion_on"] = a["work_allocations"][-1]["date"]
            a["deadline_met"] = a["due_on"] is not None and a["planned_completion_on"] <= a["due_on"]
            if a["due_on"] and not a["deadline_met"]:
                add(
                    findings,
                    "planned-deadline-miss",
                    "Available work slots complete this action after its supplied/policy deadline.",
                    "actions." + a["action_id"],
                )
        if remaining:
            add(
                findings,
                "capacity-shortfall",
                f"{remaining} action minutes cannot fit documented owner availability.",
                "actions." + a["action_id"],
            )
    coverage = {}
    for key in sorted({str(r["tier_id"]) for r in calendar}):
        group = [r for r in calendar if str(r["tier_id"]) == key and r["active_as_of"]]
        known = [r for r in group if r["coverage_state"] != "unknown"]
        over = [r for r in group if r["coverage_state"] == "overdue"]
        coverage[key] = {
            "active_received_households": len(group),
            "known_cadence_households": len(known),
            "overdue_households": len(over),
            "unknown_cadence_households": len(group) - len(known),
            "policy_cadence_coverage_fraction": float(dec(len(known) - len(over)) / len(group))
            if group and len(known) == len(group) and population_supported
            else None,
        }
    economic = analyze_economics(doc, findings, households, population_supported)
    workloads = []
    for oid, state in owner_state.items():
        workloads.append(
            {
                "owner_id": oid,
                "capacity_complete": state["complete"],
                "known_working_minutes": state["known_working_minutes"],
                "known_unrelated_committed_minutes": state["known_committed_minutes"],
                "available_before_queue_minutes": state["available_before_queue_minutes"]
                if state["complete"]
                else None,
                "known_available_minutes": state["available_before_queue_minutes"],
                "draft_allocated_minutes": state["allocated_minutes"],
                "unallocated_known_minutes": state["unallocated_known_minutes"],
                "unknown_effort_actions": sum(a["estimated_minutes"] is None for a in actions if a["owner_id"] == oid),
                "blocked_action_count": sum(a["evidence_state"] == "blocked" for a in actions if a["owner_id"] == oid),
                "total_reported_effort_minutes": sum(
                    a["estimated_minutes"] or 0 for a in actions if a["owner_id"] == oid
                ),
                "unallocated_capacity_minutes": sum(state["slots"].values()) if state["complete"] else None,
            }
        )
    result = common_result(doc)
    result.update(
        book_id=doc["book_id"],
        scope_type="advisor-book",
        planning_end=doc["planning_end"],
        review_calendar=calendar,
        tier_coverage=coverage,
        cohort={
            "period_start": doc["period_start"],
            "period_end": doc["period_end"],
            "starting_household_ids": starting,
            "retained_starting_household_ids": retained,
            "new_household_ids": added,
            "departed_household_ids": departed,
            "starting_cohort_retention_fraction": float(dec(len(retained)) / len(starting))
            if starting and cohort_known and population_supported
            else None,
        },
        action_plan=actions,
        signals_register=deepcopy(doc["signals"]),
        owner_workloads=workloads,
        capacity_calendar=capacity_calendar,
        economics=economic,
        boundaries={
            "priority_inputs": "Explicit service policy, due dates and documented signals only; economics and protected traits are not ranking inputs.",
            "calendar": "Internal work-allocation illustration only; no meetings booked, CRM writes, sends or reassignment.",
            "growth": "Only documented confirmed client-interest tasks; all service/retention/evidence priorities come first.",
            "scope_adapter": "book:<book_id> is a collection marker. Use each action household_id, not the collection marker, in a household skill.",
        },
    )
    result["draft_markdown"] = render(result)
    return make_output(SKILL, doc, result, findings)


def analyze_economics(doc, findings, households, population_supported):
    e = doc["economics"]
    ok = cited(e, doc, findings, "economics")
    if e["status"] == "not-provided":
        return {
            "status": "not-provided",
            "reason": e["reason"],
            "net_external_flows": None,
            "direct_contribution": None,
            "revenue": None,
            "asset_return": None,
        }
    expected = {
        hid
        for hid, h in households.items()
        if iso_date(h.get("joined_on"))
        and h["joined_on"] <= doc["period_end"]
        and (h["departed_on"] is None or h["departed_on"] >= doc["period_start"])
    }
    received = {r["household_id"] for r in e["household_records"]}
    population_evidence = [cited(h, doc, findings, "economics.population." + hid) for hid, h in households.items()]
    coverage = (
        ok
        and received == expected
        and all(population_evidence)
        and all(iso_date(h.get("joined_on")) for h in households.values())
    )
    if not coverage:
        add(
            findings,
            "economic-scope-gap",
            "Economic household records must exactly cover the declared period population; unknown relationship dates prevent full totals.",
            "economics",
        )
    totals = {key: dec(0) for key in AMOUNTS}
    field_complete = {key: coverage for key in AMOUNTS}
    register = []
    for row in e["household_records"]:
        path = "economics." + row["household_id"]
        supported = cited(row, doc, findings, path) and row["household_id"] in expected
        values = {}
        for key in AMOUNTS:
            value = row.get(key)
            if value is None:
                add(findings, "economic-input-unknown", "Missing " + key + " is not zero.", path + "." + key)
            values[key] = dec(value) if value is not None and supported else None
            if values[key] is None:
                field_complete[key] = False
            else:
                totals[key] += values[key]
        keys = AMOUNTS[:7]
        expected_close = None
        difference = None
        if all(values[k] is not None for k in keys):
            expected_close = (
                values["opening_assets"]
                + values["external_inflows"]
                - values["external_outflows"]
                + values["internal_net_transfer"]
                + values["market_change"]
                - values["fees_debited"]
            )
            difference = values["closing_assets"] - expected_close
            if abs(difference) > dec(".01"):
                add(
                    findings,
                    "asset-bridge-mismatch",
                    "Closing assets do not reconcile to sourced opening assets, flows, market change and fees.",
                    path,
                )
        register.append(
            {
                "household_id": row["household_id"],
                "values": {k: money(v) if v is not None else None for k, v in values.items()},
                "expected_closing_assets": money(expected_close) if expected_close is not None else None,
                "asset_bridge_difference": money(difference) if difference is not None else None,
                "source_ids": deepcopy(row.get("source_ids")),
            }
        )
    complete = population_supported
    total = lambda key: totals[key] if complete and field_complete[key] else None
    inflow, outflow, revenue, cost, internal = [
        total(k)
        for k in [
            "external_inflows",
            "external_outflows",
            "recognized_revenue",
            "direct_service_cost",
            "internal_net_transfer",
        ]
    ]
    if internal is not None and abs(internal) > dec(".01"):
        add(
            findings,
            "internal-transfer-mismatch",
            "Internal-to-book transfers must net to zero across a complete book.",
            "economics",
        )
    return {
        "status": "supplied-period-components",
        "definition_version": e["definition_version"],
        "household_register": register,
        "known_subtotals": {k: money(v) for k, v in totals.items()},
        "complete_totals": {k: money(total(k)) if total(k) is not None else None for k in AMOUNTS},
        "net_external_flows": money(inflow - outflow) if inflow is not None and outflow is not None else None,
        "revenue": money(revenue) if revenue is not None else None,
        "direct_contribution": money(revenue - cost) if revenue is not None and cost is not None else None,
        "asset_return": None,
        "definition": "Revenue minus supplied direct service cost is a component contribution, not fully allocated profit. Asset change is not investment performance. External flows exclude internal-to-book transfers, market change and fees.",
    }


def render(result):
    lines = [
        f"# Draft advisor book action plan — {result['book_id']}",
        f"As of {result['input_snapshot']['as_of']}; planning through {result['planning_end']}. Human review required.",
        "",
        "## Prioritized work",
        "",
    ]
    for action in result["action_plan"]:
        effort = "unknown" if action["estimated_minutes"] is None else str(action["estimated_minutes"])
        lines.append(
            f"{action['sequence']}. {action['household_id'] or 'Book evidence'} / {action['owner_id'] or 'owner unknown'}: {action['description']} Due {action['due_on'] or 'unknown'}; priority {action['priority_rank']} ({action['priority_rationale']}); {effort} minutes; {action['work_status']}. Sources: {', '.join(action['source_ids'])}."
        )
    lines += ["", "## Owner capacity", ""]
    for row in result["owner_workloads"]:
        available = (
            "unknown" if row["available_before_queue_minutes"] is None else str(row["available_before_queue_minutes"])
        )
        lines.append(
            f"- {row['owner_id']}: available {available} minutes; draft allocated {row['draft_allocated_minutes']}; unallocated known work {row['unallocated_known_minutes']}; blocked actions {row['blocked_action_count']}; actions with unknown effort {row['unknown_effort_actions']}."
        )
    lines += [
        "",
        "Review the attached household due calendar, service-tier coverage, cohort definitions and sourced economics. Revenue does not determine this action order. This draft creates no appointment, client message, CRM record or reassignment.",
    ]
    return "\n".join(lines)
