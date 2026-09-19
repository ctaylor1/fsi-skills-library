"""Household-scoped investor-side manager diligence, no selection or authorization."""
from datetime import timedelta
from wealth_contract import make_output, validate_output_envelope, iso_date, nonempty
from workflow_support import base_errors, rows, enum, number, dec, money, cited, add, base_findings, common_result

SKILL = "investment-manager-due-diligence-reviewer"
DIMENSIONS = {"investment", "operations", "fees", "liquidity", "evidence"}
FEE_FIELDS = ("capital", "management_bps", "other_bps", "gross_return", "hurdle_return", "incentive_rate")


def validate(doc):
    errors = base_errors(doc)
    if errors:
        return errors
    if doc.get("currency") != "USD":
        errors.append("currency must be USD")
    manager = doc.get("manager")
    if not isinstance(manager, dict) or any(not nonempty(manager.get(k)) for k in ("manager_id", "name", "strategy_id", "strategy_name")):
        errors.append("manager requires manager and strategy IDs and names")
    policy = doc["policy"]
    if type(policy.get("monitoring_interval_days")) is not int or not 1 <= policy["monitoring_interval_days"] <= 366:
        errors.append("policy monitoring_interval_days must be 1 through 366")
    criteria = rows(policy, "criteria", errors, "criterion_id")
    for c in criteria:
        if not enum(c.get("dimension"), DIMENSIONS) or not enum(c.get("operator"), {"minimum", "maximum", "equals", "documented"}) or not nonempty(c.get("description")):
            errors.append("criterion requires supported dimension/operator and description")
        if type(c.get("required")) is not bool or type(c.get("independent_evidence_required")) is not bool:
            errors.append("criterion must explicitly state required and independent_evidence_required booleans")
        op, threshold = c.get("operator"), c.get("threshold")
        if enum(op, {"minimum", "maximum"}) and not number(threshold, -10**15):
            errors.append("numeric comparison criterion requires a finite threshold")
        if op == "equals" and not (nonempty(threshold) or type(threshold) is bool):
            errors.append("equals threshold must be explicit nonempty text or boolean")
        if op == "documented" and threshold is not None:
            errors.append("documented criterion has null threshold; no scoring inference")
    if any(not any(c.get("dimension") == dim and c.get("required") is True for c in criteria) for dim in DIMENSIONS):
        errors.append("policy requires at least one required criterion for each of five diligence dimensions")
    for e in rows(doc, "evidence", errors, "evidence_id"):
        if not nonempty(e.get("criterion_id")) or not nonempty(e.get("narrative")) or not enum(e.get("origin"), {"manager-reported", "independent", "firm-record"}):
            errors.append("evidence requires criterion_id, narrative and origin")
        if e.get("value") is not None and not (nonempty(e["value"]) or type(e["value"]) is bool or number(e["value"], -10**15)):
            errors.append("evidence value must be text, boolean, finite number or null")
        for key in ("observed_date", "review_by"):
            if e.get(key) is not None and iso_date(e[key]) is None:
                errors.append(f"evidence {key} must be ISO date or null")
    fees = doc.get("fee_illustration")
    if fees is not None:
        if not isinstance(fees, dict):
            errors.append("fee_illustration must be an object or null")
        else:
            if fees.get("method") != "one-period-no-high-water-mark":
                errors.append("unsupported fee illustration method; supply an independently calculated fee analysis instead of imposing this model")
            for key in FEE_FIELDS:
                low, high = (-1, 10) if key in {"gross_return", "hurdle_return"} else ((0, 1) if key == "incentive_rate" else (0, 10**15))
                if fees.get(key) is not None and not number(fees[key], low, high):
                    errors.append(f"fee illustration {key} is outside supported range")
            if fees.get("capital") == 0:
                errors.append("fee illustration capital must be positive")
    liquidity = doc.get("liquidity")
    if liquidity is not None:
        if not isinstance(liquidity, dict):
            errors.append("liquidity must be an object or null")
        else:
            if type(liquidity.get("gate_or_suspension_possible")) is not bool:
                errors.append("liquidity must explicitly disclose gate_or_suspension_possible")
            for key in ("notice_deadline", "request_date", "expected_settlement_date"):
                if liquidity.get(key) is not None and iso_date(liquidity[key]) is None:
                    errors.append(f"liquidity {key} must be ISO date or null")
            if liquidity.get("amount_under_review") is not None and not number(liquidity["amount_under_review"]):
                errors.append("liquidity amount_under_review must be nonnegative number or null")
    for need in rows(doc, "household_liquidity_needs", errors, "need_id"):
        if not nonempty(need.get("description")) or iso_date(need.get("needed_by")) is None or need["needed_by"] < doc["as_of"]:
            errors.append("household need requires description and current/future needed_by")
        if need.get("amount") is not None and not number(need["amount"]):
            errors.append("household need amount must be nonnegative number or null")
    return errors


def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    findings = base_findings(doc)
    cited(doc["manager"], doc, findings, "manager")
    criteria = {c["criterion_id"]: c for c in doc["policy"]["criteria"]}
    evidence_support = {}
    for e in doc["evidence"]:
        supported = cited(e, doc, findings, e["evidence_id"])
        if e["criterion_id"] not in criteria:
            add(findings, "unknown-criterion", "Evidence references an unknown criterion", e["evidence_id"])
        observed, until = iso_date(e.get("observed_date")), iso_date(e.get("review_by"))
        if observed is None or until is None or not observed <= iso_date(doc["as_of"]) <= until:
            add(findings, "evidence-date-gap", "Evidence observation/review dates are missing, stale, future or inconsistent", e["evidence_id"])
            supported = False
        evidence_support[e["evidence_id"]] = supported
    matrix = []
    for cid, c in criteria.items():
        policy_supported = cited(c, doc, findings, "policy.criteria." + cid)
        matches = [e for e in doc["evidence"] if e["criterion_id"] == cid]
        result = "not-evaluable"
        reason = "No unique current source-supported observation"
        if len(matches) == 1 and policy_supported and evidence_support[matches[0]["evidence_id"]]:
            e, value = matches[0], matches[0].get("value")
            if c["independent_evidence_required"] and e["origin"] != "independent":
                reason = "Criterion requires independent evidence; supplied origin does not meet policy"
            elif value is None:
                reason = "Observed value is unknown"
            elif c["operator"] in {"minimum", "maximum"} and not number(value, -10**15):
                reason = "Observed value is not numeric for configured comparison"
            else:
                op = c["operator"]
                passes = ((dec(value) >= dec(c["threshold"])) if op == "minimum" else
                          (dec(value) <= dec(c["threshold"])) if op == "maximum" else
                          (type(value) is type(c["threshold"]) and value == c["threshold"]) if op == "equals" else value is not False)
                result = "meets-supplied-criterion" if passes else "criterion-concern"
                reason = "Literal comparison with the supplied versioned criterion; not a manager endorsement"
        if result != "meets-supplied-criterion" and c["required"]:
            add(findings, "diligence-concern" if result == "criterion-concern" else "diligence-data-gap", c["description"] + ": " + reason, cid)
        matrix.append({"criterion_id": cid, "dimension": c["dimension"], "criterion": c, "evidence": matches, "result": result, "reason": reason})
    fee_result = None
    f = doc.get("fee_illustration")
    if f is None:
        add(findings, "fee-model-gap", "No supplied fee illustration; the criterion record alone does not calculate household fee impact", "fee_illustration")
    else:
        supported = cited(f, doc, findings, "fee_illustration")
        if any(f.get(k) is None for k in FEE_FIELDS):
            add(findings, "fee-input-gap", "Fee illustration assumptions are incomplete", "fee_illustration")
        elif supported:
            capital = dec(f["capital"])
            base_fee = capital * (dec(f["management_bps"]) + dec(f["other_bps"])) / 10000
            incentive_base = max(capital * (dec(f["gross_return"]) - dec(f["hurdle_return"])) - base_fee, 0)
            incentive = incentive_base * dec(f["incentive_rate"])
            fee_result = {"assumptions": f, "capital": money(capital), "base_fee": money(base_fee), "incentive_fee_base": money(incentive_base),
                          "incentive_fee": money(incentive), "total_illustrated_fee": money(base_fee + incentive),
                          "illustrated_net_gain": money(capital * dec(f["gross_return"]) - base_fee - incentive),
                          "formula": "base fee = capital*(management_bps+other_bps)/10000; incentive = max(capital*(gross_return-hurdle_return)-base fee,0)*incentive_rate",
                          "limitation": "One-period scenario on starting capital, no high-water mark, tiers, fee timing, catch-up, taxes or valuation effects; not a quote or forecast."}
    l, liquidity_rows = doc.get("liquidity"), []
    liquid_supported = False
    if l is None:
        add(findings, "liquidity-data-gap", "No dated liquidity scenario supplied", "liquidity")
    else:
        liquid_supported = cited(l, doc, findings, "liquidity")
        if any(l.get(k) is None for k in ("notice_deadline", "request_date", "expected_settlement_date", "amount_under_review")):
            add(findings, "liquidity-data-gap", "Liquidity dates or amount are unknown", "liquidity")
            liquid_supported = False
        elif l["request_date"] > l["notice_deadline"] or l["expected_settlement_date"] < l["request_date"]:
            add(findings, "liquidity-schedule-conflict", "Request misses supplied notice deadline or settlement precedes request", "liquidity")
            liquid_supported = False
        if l["gate_or_suspension_possible"]:
            add(findings, "contingent-liquidity", "Gates or suspension may prevent the modeled settlement; availability is not assured", "liquidity")
    if not doc["household_liquidity_needs"]:
        add(findings, "household-context-gap", "Household liquidity needs not supplied; do not infer none", "household_liquidity_needs")
    cumulative = dec(0)
    cumulative_complete = True
    for n in sorted(doc["household_liquidity_needs"], key=lambda x: (x["needed_by"], x["need_id"])):
        supported = cited(n, doc, findings, n["need_id"])
        if n.get("amount") is None:
            add(findings, "need-amount-gap", "Household liquidity amount is unknown", n["need_id"])
            supported = False
        row = {"need": n, "assessment": "not-evaluable", "cumulative_amount": None}
        if not supported:
            cumulative_complete = False
        if supported and liquid_supported and cumulative_complete:
            cumulative += dec(n["amount"])
            timely = l["expected_settlement_date"] <= n["needed_by"]
            enough = cumulative <= dec(l["amount_under_review"])
            row.update(assessment="modeled-timing-and-amount-fit" if timely and enough else "liquidity-concern", cumulative_amount=money(cumulative),
                       expected_settlement_date=l["expected_settlement_date"], modeled_timing_fit=timely, modeled_amount_fit=enough,
                       contingent=l["gate_or_suspension_possible"])
            if not timely or not enough:
                add(findings, "household-liquidity-concern", "Modeled settlement is late or cumulative household needs exceed the amount under review", n["need_id"])
        liquidity_rows.append(row)
    result = common_result(doc)
    result.update(manager=doc["manager"], diligence_by_dimension={d: [r for r in matrix if r["dimension"] == d] for d in sorted(DIMENSIONS)},
                  fee_illustration=fee_result, supplied_liquidity=l, household_liquidity_review=liquidity_rows,
                  monitoring_plan={"next_scheduled_review": (iso_date(doc["as_of"]) + timedelta(days=doc["policy"]["monitoring_interval_days"])).isoformat(),
                                   "open_item_followup": [{"owner": doc["policy"]["owner"], "criterion_or_path": f["path"], "question": f["message"]} for f in findings],
                                   "event_triggers": "Use supplied criterion/evidence changes and unresolved findings; no live monitoring is configured."},
                  selection_decision="not-made", limitations=["Investor-side evidence review only, initially scoped to one household and one manager strategy.",
                    "Manager statements are attributed assertions. Independent origin labels are supplied metadata and require human source verification.",
                    "No performance forecast, fund rating, legal eligibility, investment recommendation, manager appointment, redemption or DDQ answer delivery."])
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    errors = validate_output_envelope(out, SKILL)
    snapshot = out.get("result", {}).get("input_snapshot") if isinstance(out, dict) and isinstance(out.get("result"), dict) else None
    try:
        expected = build(snapshot)
        if out != expected:
            errors.append("output differs from full reconstruction of source snapshot, criterion evidence, arithmetic or monitoring")
    except (ValueError, TypeError, KeyError) as exc:
        errors.append(f"invalid input snapshot: {exc}")
    return errors
