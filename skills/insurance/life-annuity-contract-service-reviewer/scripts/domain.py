"""Evidence-supported life/annuity servicing review; no transaction or rights adjudication."""

from domain_support import day, finding, money, num, profile_findings, result, structural


def validate(doc):
    errors = structural(
        doc,
        objects=("contract", "request", "service_terms"),
        arrays=("consents",),
        amounts=(
            "contract.account_value",
            "request.requested_amount",
            "service_terms.surrender_charge",
            "service_terms.market_value_adjustment_signed",
            "service_terms.loan_offset",
            "service_terms.withholding",
            "service_terms.benefit_before",
            "service_terms.benefit_after",
        ),
        dates=("contract.value_date",),
    )
    d = doc.get("data", {})
    for obj, keys in (
        ("contract", ("beneficiary_ids", "assignee_ids")),
        ("service_terms", ("authorized_actor_ids", "consents_required")),
    ):
        value = d.get(obj, {})
        if not isinstance(value, dict):
            continue
        for key in keys:
            if not isinstance(value.get(key), list) or not all(isinstance(v, str) and v for v in value.get(key, [])):
                errors.append(f"{obj}.{key} must be an explicit array of identity strings")
    return errors


def evaluate(doc):
    d, f = doc["data"], []
    c, r, t = d["contract"], d["request"], d["service_terms"]
    f += profile_findings(doc, t, "service_terms")
    for obj, fields in (
        (c, ("contract_id", "owner_id", "product_type", "currency", "source_ref")),
        (r, ("request_id", "requester_id", "contract_id", "action", "source_ref")),
    ):
        for key in fields:
            if not obj.get(key):
                f.append(finding("identity_or_request_gap", f"{key} missing", [obj.get("source_ref")]))
    scope_ok = c.get("contract_id") == doc["context"]["object_id"] == r.get("contract_id")
    if not scope_ok:
        f.append(
            finding(
                "identity_mismatch",
                "Contract, request and context object differ",
                [c.get("source_ref"), r.get("source_ref")],
            )
        )
    requester = r.get("requester_id")
    actor_supported = bool(
        requester and (requester == c.get("owner_id") or requester in t.get("authorized_actor_ids", []))
    )
    if not actor_supported:
        f.append(
            finding(
                "requester_authority_unresolved",
                "Requester is not a supplied owner or documented authorized actor; beneficiary status alone supplies no servicing authority",
                [c.get("source_ref"), r.get("source_ref"), t.get("source_ref")],
                "review",
            )
        )
    needed = sorted(set(t.get("consents_required", []) + c.get("assignee_ids", [])))
    consent_checks = []
    for actor in needed:
        candidate = [
            x
            for x in d["consents"]
            if x.get("actor_id") == actor
            and x.get("contract_id") == c.get("contract_id")
            and x.get("request_id") == r.get("request_id")
        ]
        conflicting = any(x.get("status") in ("revoked", "disputed", "conflicting") for x in candidate)
        evidence = [x for x in candidate if x.get("status") == "received" and x.get("source_ref")]
        valid = []
        for item in evidence:
            try:
                if day(item["as_of"]) <= day(doc["as_of"]):
                    valid.append(item)
            except (ValueError, KeyError, TypeError):
                pass
        supported = bool(valid) and not conflicting
        consent_checks.append(
            {
                "actor_id": actor,
                "supported": supported,
                "conflicting": conflicting,
                "source_refs": sorted(set(x.get("source_ref") for x in candidate if x.get("source_ref"))),
            }
        )
        if not supported:
            f.append(
                finding(
                    "consent_gap",
                    f"Request-specific consent missing for {actor}",
                    [t.get("source_ref"), c.get("source_ref")],
                )
            )
        if conflicting:
            f.append(
                finding(
                    "consent_conflict",
                    f"Conflicting or revoked consent retained for {actor}",
                    [x.get("source_ref") for x in candidate],
                    "review",
                )
            )
    action = r.get("action")
    scenario = None
    if action == "beneficiary_change":
        if not r.get("proposed_beneficiary_id"):
            f.append(finding("beneficiary_request_gap", "Proposed beneficiary identity missing", [r.get("source_ref")]))
    elif action in ("withdrawal", "surrender"):
        account = num(c.get("account_value"))
        gross = account if action == "surrender" else num(r.get("requested_amount"))
        deductions = {
            k: num(t.get(k))
            for k in ("surrender_charge", "market_value_adjustment_signed", "loan_offset", "withholding")
        }
        value_date = c.get("value_date")
        try:
            snapshot_day, review_day = day(value_date), day(doc["as_of"])
            dated = snapshot_day == review_day
            if not dated:
                relation = "stale" if snapshot_day < review_day else "future"
                f.append(
                    finding(
                        f"valuation_date_{relation}",
                        f"Contract value_date {value_date} is {'before' if relation == 'stale' else 'after'} "
                        f"review as_of {doc['as_of']}; withdrawal/surrender scenarios require a sourced "
                        "valuation on that exact review date. Preserve the supplied date and obtain a same-day snapshot.",
                        [c.get("source_ref")],
                    )
                )
        except (ValueError, KeyError, TypeError):
            dated = False
            f.append(
                finding(
                    "valuation_date_missing",
                    f"Contract value_date is missing or unusable for review as_of {doc['as_of']}; "
                    "supply a sourced valuation dated exactly on the review date. No valuation date is inferred.",
                    [c.get("source_ref")],
                )
            )
        usable = (
            scope_ok
            and dated
            and t.get("formula") == "supplied_deduction_bridge"
            and not any(x["code"].startswith("profile_") for x in f)
        )
        if account is None or gross is None or any(v is None for v in deductions.values()) or not usable:
            f.append(
                finding(
                    "scenario_not_evaluable",
                    "Current value, same scope, valid profile and every supplied deduction (including explicit zero) required",
                    [c.get("source_ref"), t.get("source_ref")],
                )
            )
        elif (
            account < 0
            or gross < 0
            or gross > account
            or any(deductions[k] < 0 for k in ("surrender_charge", "loan_offset", "withholding"))
        ):
            f.append(
                finding(
                    "scenario_invalid_amount",
                    "Requested gross/deductions exceed supported nonnegative amount domain",
                    [r.get("source_ref"), t.get("source_ref")],
                )
            )
        else:
            net = (
                gross
                - deductions["surrender_charge"]
                + deductions["market_value_adjustment_signed"]
                - deductions["loan_offset"]
                - deductions["withholding"]
            )
            scenario = {
                "currency": c.get("currency"),
                "gross_requested": money(gross),
                **{k: money(v) for k, v in deductions.items()},
                "illustrative_cash_proceeds": money(net),
                "account_value_before": money(account),
                "account_value_after_gross_withdrawal_only": money(account - gross),
                "basis": "supplied gross reduction bridge; deductions assumed inside gross except signed MVA; verify actual contract debit mechanics",
                "source_refs": [c.get("source_ref"), t.get("source_ref"), r.get("source_ref")],
            }
            if net < 0:
                f.append(
                    finding(
                        "negative_proceeds",
                        "Supplied deductions imply negative proceeds; servicing specialist review required",
                        scenario["source_refs"],
                        "review",
                    )
                )
        before, after = num(t.get("benefit_before")), num(t.get("benefit_after"))
        if before is None or after is None:
            f.append(
                finding(
                    "benefit_effect_unknown",
                    "No complete supplied before/after benefit illustration; cash value is not the guaranteed benefit base",
                    [t.get("source_ref")],
                )
            )
    else:
        f.append(
            finding(
                "unsupported_service",
                "Only withdrawal, surrender and beneficiary-change preparation supported",
                [r.get("source_ref")],
            )
        )
    return result(
        f,
        {
            "contract_id": c.get("contract_id"),
            "request_id": r.get("request_id"),
            "action": action,
            "rights_evidence": {
                "owner_id": c.get("owner_id"),
                "requester_id": requester,
                "requester_is_beneficiary": requester in c.get("beneficiary_ids", []),
                "supplied_actor_basis_supported": actor_supported,
                "legal_authority_determined": False,
                "consents": consent_checks,
            },
            "value_scenario": scenario,
            "supplied_benefit_effect": {
                "before": t.get("benefit_before"),
                "after": t.get("benefit_after"),
                "source_ref": t.get("source_ref"),
            },
            "transaction_instructions": None,
        },
    )
