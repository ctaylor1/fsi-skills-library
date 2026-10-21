"""Exact claim chains and supplied coding/contract/payment arithmetic, without adjudication."""

from decimal import Inexact, Rounded, localcontext
from design_support import total, validate_with
from specialist_support import SpecialistReview

METHOD = "health-claim-payment-v1"
IDENTITY = ("claim_id", "line_id", "provider_id", "product", "service_id", "service_on")
CODE_IDENTITY = ("provider_id", "product", "service_id", "code", "code_version", "modifiers")


def bound(r, row, label):
    return r.evidence(row, label) & r.fields(row, ("locator",))


def same(r, row, event, fields, code):
    return r.need(
        all(row.get(k) == event.get(k) and row.get(k) is not None for k in fields),
        code,
        "Exact identity binding required: " + ", ".join(fields),
        row,
    )


def _evaluate(doc):
    r = SpecialistReview(doc, METHOD)
    d = r.data
    r.need(
        doc["context"]["capacity"] == "payer-payment-integrity-review",
        "capacity",
        "Payer payment-integrity capacity is required",
    )
    r.need(doc["context"]["line_of_business"] == "health", "line", "Health line of business is required")
    r.fields(d, ("currency",))
    inventory = d.get("inventory") or {}
    if not isinstance(inventory, dict):
        raise ValueError("inventory must be an object or null")
    bound(r, inventory, "Claim inventory")
    r.fields(inventory, ("statement",))
    r.flag(inventory, "complete")
    events = r.rows("events", "event_id")
    chains = r.rows("chains", "chain_id")
    profiles = r.rows("code_profiles", "code_profile_id")
    contracts = r.rows("contracts", "contract_id")
    allocations = r.rows("allocations", "allocation_id", nonempty=False)
    payments = r.rows("payments", "payment_id", nonempty=False)
    by_event = {x["event_id"]: x for x in events}
    by_profile = {x["code_profile_id"]: x for x in profiles}
    by_contract = {x["contract_id"]: x for x in contracts}
    chain_ids = {x["chain_id"] for x in chains}
    for event in events:
        r.need(event.get("chain_id") in chain_ids, "orphan-event", "Every event requires a supplied chain", event)
    # Unknown/orphan events can change paired-code findings for every active line.
    # Freeze global prerequisites only after evidence and chain membership checks.
    global_valid = r.clear
    # Distinct chains cannot represent the same economic claim line.
    logical = {}
    resolved = []
    all_chain_valid = global_valid
    for chain in chains:
        begin = len(r.findings)
        bound(r, chain, "Event chain")
        r.fields(chain, ("terminal_event_id", "statement"))
        r.flag(chain, "complete")
        members = [e for e in events if e.get("chain_id") == chain["chain_id"]]
        roots = [e for e in members if e.get("event_type") == "original" and e.get("prior_event_id") is None]
        r.need(len(roots) == 1, "chain-root", "Exactly one original root is required", chain)
        for event in members:
            bound(r, event, "Claim event")
            r.fields(event, IDENTITY + ("code", "code_version"))
            r.strings(event, "modifiers")
            r.need(
                event.get("event_type") in {"original", "replacement", "void"},
                "event-type",
                "Event type must be original, replacement or void",
                event,
            )
            if event.get("event_type") == "original":
                r.need(
                    event.get("prior_event_id") is None,
                    "original-predecessor",
                    "An original event cannot have a predecessor",
                    event,
                )
            r.need(
                event.get("claim_id") == doc["context"]["object_id"] and event.get("product") == d.get("product"),
                "event-scope",
                "Event claim/product must match case scope",
                event,
            )
            service_on = r.date(event, "service_on")
            recorded_on = r.date(event, "recorded_on")
            r.need(
                service_on is not None and recorded_on is not None and service_on <= recorded_on,
                "service-chronology",
                "Claim service date cannot follow its recorded event date",
                event,
            )
            if event.get("event_type") != "original":
                parent = by_event.get(event.get("prior_event_id"))
                r.need(
                    parent is not None and parent in members and parent.get("event_type") != "void",
                    "chain-predecessor",
                    "Replacement/void requires an existing non-void predecessor in this chain",
                    event,
                )
                if parent:
                    same(r, event, parent, IDENTITY, "chain-identity")
                    r.need(
                        event.get("recorded_on") is not None
                        and parent.get("recorded_on") is not None
                        and event["recorded_on"] >= parent["recorded_on"],
                        "chain-date",
                        "Event chronology must be nondecreasing",
                        event,
                    )
        path = []
        current = roots[0] if len(roots) == 1 else None
        while current is not None and current["event_id"] not in path:
            path.append(current["event_id"])
            children = [e for e in members if e.get("prior_event_id") == current["event_id"]]
            if len(children) > 1:
                r.add("chain-branch", "Branched replacement history has no unique terminal", chain)
            current = children[0] if len(children) == 1 else None
        r.need(
            bool(path) and len(path) == len(members) and path[-1] == chain.get("terminal_event_id"),
            "chain-terminal",
            "Complete connected path and exact supplied terminal are required",
            chain,
        )
        terminal = by_event.get(chain.get("terminal_event_id"))
        valid = global_valid and not any(f["severity"] == "gap" for f in r.findings[begin:])
        if terminal and valid:
            key = tuple(terminal.get(k) for k in ("claim_id", "line_id"))
            logical.setdefault(key, []).append(chain["chain_id"])
        resolved.append((chain, terminal, valid, path))
        all_chain_valid &= valid
    duplicate_chains = {c for group in logical.values() if len(group) > 1 for c in group}
    if duplicate_chains:
        r.add(
            "duplicate-economic-line",
            "Multiple chains represent the same economic claim line; dependent totals withheld",
        )
    active = [e for c, e, v, p in resolved if v and c["chain_id"] not in duplicate_chains and e["event_type"] != "void"]
    results = []
    for chain, event, chain_valid, path in resolved:
        begin = len(r.findings)
        chain_valid &= all_chain_valid and not duplicate_chains
        line = {
            "chain_id": chain["chain_id"],
            "event_ids": path,
            "terminal_event_id": chain.get("terminal_event_id"),
            "chain_resolved": chain_valid,
            "excluded_void": bool(chain_valid and event and event["event_type"] == "void"),
            "coding_state": "not_determined",
            "expected_allowed": None,
            "expected_payable": None,
            "recorded_net_paid": None,
            "payment_variance": None,
            "allocation_identity_difference": None,
            "medical_necessity": "not_determined",
            "patient_liability": "not_determined",
            "source_refs": sorted(
                {s for e in events if e.get("chain_id") == chain["chain_id"] for s in e.get("source_refs", [])}
            ),
        }
        if not chain_valid or event is None:
            results.append(line)
            continue
        if event["event_type"] == "void":
            # A void excludes expected service amounts, but a net ledger snapshot may
            # still reveal an unreversed payment. Never silently count historical payments.
            line["coding_state"] = "excluded-void"
        else:
            units = r.num(event, "units")
            r.num(event, "billed")
            profile = by_profile.get(event.get("code_profile_id")) or {}
            bound(r, profile, "Code/edit profile")
            r.applicable(profile, event.get("service_on"), "Code/edit profile")
            same(r, profile, event, CODE_IDENTITY, "code-identity")
            r.fields(profile, ("file_version", "adoption_basis", "licensed_use_basis", "current_file_statement"))
            r.need(
                profile.get("replacement_status") == "current",
                "replacement-file",
                "Exact current quarterly or replacement edit file must be supplied",
                profile,
            )
            for key in ("market", "program"):
                r.need(
                    profile.get(key) == d.get(key), "code-scope", "Code/edit profile must match actual " + key, profile
                )
            max_units = r.num(profile, "max_units")
            if profile.get("incompatible_codes") is None:
                r.add("edit-inventory", "Explicit incompatible code inventory is required", profile)
                pairs = []
            else:
                pairs = r.strings(profile, "incompatible_codes")
            coding_issue = units is not None and max_units is not None and units > max_units
            paired = [
                a["event_id"]
                for a in active
                if a["event_id"] != event["event_id"]
                and all(a.get(k) == event.get(k) for k in ("claim_id", "provider_id", "service_on", "code_version"))
                and a.get("code") in pairs
            ]
            coding_issue |= bool(paired)
            if coding_issue:
                r.add(
                    "coding-edit",
                    "Supplied units/pair edit requires coding analyst review; no denial or zero-payment inference",
                    profile,
                    severity="review",
                )
            coding_valid = not any(f["severity"] == "gap" for f in r.findings[begin:])
            line["coding_state"] = (
                "flagged-for-review"
                if coding_valid and coding_issue
                else "no-supplied-edit-flag"
                if coding_valid
                else "not_determined"
            )
            line["paired_event_ids"] = paired
            contract = by_contract.get(event.get("contract_id")) or {}
            bound(r, contract, "Contract allowance")
            r.applicable(contract, event.get("service_on"), "Contract allowance")
            same(r, contract, event, CODE_IDENTITY, "contract-identity")
            r.fields(contract, ("allowance_basis",))
            r.need(
                contract.get("method") == "unit-rate-exact" and contract.get("rounding") == "none",
                "contract-method",
                "Only supplied exact unit-rate multiplication without implicit rounding is supported",
                contract,
            )
            r.need(
                contract.get("currency") == d.get("currency"),
                "currency",
                "Contract currency must match case currency",
                contract,
            )
            rate = r.num(contract, "rate_per_unit")
            expected = units * rate if units is not None and rate is not None else None
            if not any(f["severity"] == "gap" for f in r.findings[begin:]) and not coding_issue:
                line["expected_allowed"] = expected
            matched = [a for a in allocations if a.get("event_id") == event["event_id"]]
            r.need(
                len(matched) == 1,
                "allocation",
                "Exactly one independently supplied benefit allocation is required for the terminal event",
                event,
            )
            if len(matched) == 1:
                allocation_begin = len(r.findings)
                allocation = matched[0]
                bound(r, allocation, "Benefit allocation")
                same(r, allocation, event, IDENTITY, "allocation-identity")
                r.fields(allocation, ("benefit_basis",))
                r.need(
                    allocation.get("currency") == d.get("currency"),
                    "currency",
                    "Allocation currency must match case currency",
                    allocation,
                )
                amounts = [
                    r.num(allocation, k)
                    for k in ("allowed", "member_cost_share", "other_payer", "other_adjustment", "payable")
                ]
                if all(a is not None for a in amounts) and not any(
                    f["severity"] == "gap" for f in r.findings[allocation_begin:]
                ):
                    allowed, member, cob, adjustment, payable = amounts
                    difference = allowed - member - cob - adjustment - payable
                    line["allocation_identity_difference"] = difference
                    r.need(
                        difference == 0,
                        "allocation-tie",
                        "Supplied allowed minus cost-share, COB and other adjustment must equal supplied payable",
                        allocation,
                    )
                    if line["expected_allowed"] is not None:
                        r.need(
                            allowed == line["expected_allowed"],
                            "allowance-tie",
                            "Independent allocation allowed must equal source-bound contract allowance",
                            allocation,
                        )
                    if not any(f["severity"] == "gap" for f in r.findings[begin:]) and not coding_issue:
                        line["expected_payable"] = payable
        ledger = [p for p in payments if p.get("chain_id") == chain["chain_id"]]
        local = len(r.findings)
        r.need(
            len(ledger) == 1,
            "payment-snapshot",
            "Exactly one supplied net-payment snapshot per chain is required; incremental payments are unsupported",
            chain,
        )
        if len(ledger) == 1:
            payment = ledger[0]
            bound(r, payment, "Payment snapshot")
            same(r, payment, event, IDENTITY + ("event_id",), "payment-identity")
            paid_as_of = r.date(payment, "as_of")
            terminal_on = r.date(event, "recorded_on")
            r.need(
                paid_as_of is not None and terminal_on is not None and paid_as_of >= terminal_on,
                "payment-chronology",
                "Payment snapshot cannot predate the terminal event it represents",
                payment,
            )
            r.need(
                payment.get("record_kind") == "net-payment-snapshot" and payment.get("currency") == d.get("currency"),
                "payment-basis",
                "Matching currency and net-payment-snapshot kind are required",
                payment,
            )
            paid = r.num(payment, "net_paid", signed=True)
            if not any(f["severity"] == "gap" for f in r.findings[local:]):
                line["recorded_net_paid"] = paid
                if line["excluded_void"] and paid is not None and paid != 0:
                    r.add(
                        "void-ledger-balance",
                        "Voided line retains a supplied nonzero net-payment balance; analyst must reconcile reversals",
                        payment,
                        severity="review",
                    )
                if line["expected_payable"] is not None and paid is not None:
                    line["payment_variance"] = paid - line["expected_payable"]
                    if line["payment_variance"] != 0:
                        r.add(
                            "payment-variance",
                            "Recorded net payment differs from conditional payable; analyst investigation required",
                            payment,
                            severity="review",
                        )
        results.append(line)
    for allocation in allocations:
        r.need(
            allocation.get("event_id") in {e["event_id"] for e in active},
            "orphan-allocation",
            "Allocation must identify a current active terminal event",
            allocation,
        )
    for payment in payments:
        r.need(
            payment.get("chain_id") in chain_ids,
            "orphan-payment",
            "Payment snapshot must identify a supplied chain",
            payment,
        )
    eligible = [x for x in results if not x["excluded_void"]]
    valid_total = all_chain_valid and not duplicate_chains and r.clear
    return r.finish(
        {
            "lines": results,
            "currency": d.get("currency"),
            "expected_allowed_total": total(x["expected_allowed"] for x in eligible) if valid_total else None,
            "expected_payable_total": total(x["expected_payable"] for x in eligible) if valid_total else None,
            "recorded_net_paid_total": total(x["recorded_net_paid"] for x in results) if valid_total else None,
            "payment_executed": False,
            "adjudication_performed": False,
            "codes_selected": False,
            "denial_recommended": False,
            "patient_liability_inferred": False,
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
