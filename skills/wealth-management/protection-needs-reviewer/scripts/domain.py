"""Transparent level-dollar protection scenarios from supplied assumptions only."""
from wealth_contract import make_output, validate_output_envelope, nonempty
from workflow_support import base_errors, rows, texts, enum, number, dec, money, cited, add, base_findings, common_result

SKILL = "protection-needs-reviewer"
FIELDS = {
    "survivor": ("annual_spending", "annual_survivor_income", "support_years", "debt_payoff", "one_time_costs", "life_benefit"),
    "disability": ("monthly_spending", "monthly_other_income", "disability_months", "waiting_months", "monthly_benefit"),
    "long-term-care": ("monthly_care_cost", "care_months", "waiting_months", "monthly_benefit", "benefit_month_limit", "lifetime_benefit_cap"),
    "liability": ("projected_loss", "defense_costs", "primary_applicable_amount", "umbrella_applicable_amount"),
}


def validate(doc):
    errors = base_errors(doc)
    if errors:
        return errors
    if doc.get("currency") != "USD":
        errors.append("currency must be USD; no FX conversion is supplied")
    policy = doc["policy"]
    if policy.get("methodology") != "level-undiscounted":
        errors.append("policy.methodology must be level-undiscounted; no implicit inflation, investment return or actuarial model")
    if not texts(policy.get("required_scenario_types")) or any(t not in FIELDS for t in policy["required_scenario_types"]):
        errors.append("policy.required_scenario_types must explicitly select supported scenario types")
    for row in rows(doc, "scenarios", errors, "scenario_id"):
        if not enum(row.get("type"), FIELDS) or not nonempty(row.get("subject_id")) or not nonempty(row.get("description")):
            errors.append("scenario requires supported type, subject_id and description")
            continue
        assumptions = row.get("assumptions")
        if not isinstance(assumptions, dict):
            errors.append("scenario.assumptions must be an object")
        else:
            unknown = set(assumptions) - set(FIELDS[row["type"]]) - {"source_ids", "basis"}
            if unknown:
                errors.append("unsupported scenario assumption fields: " + ", ".join(sorted(unknown)))
            if not nonempty(assumptions.get("basis")):
                errors.append("assumptions.basis must explain supplied scenario and benefit applicability assumptions")
            for key in FIELDS[row["type"]]:
                v = assumptions.get(key)
                if v is not None and not number(v):
                    errors.append(f"{key} must be a nonnegative finite number or explicit null")
                if v is not None and (key.endswith("months") or key == "benefit_month_limit") and (type(v) is not int or v > 1200):
                    errors.append(f"{key} must be integer months from 0 through 1200 or null")
                if key == "support_years" and v is not None and number(v) and v > 100:
                    errors.append("support_years exceeds supported 100-year scenario horizon")
        for resource in rows(row, "designated_resources", errors, "resource_id"):
            if not nonempty(resource.get("description")) or not enum(resource.get("availability"), {"available-for-scenario", "uncertain", "unavailable"}):
                errors.append("resource requires description and explicit scenario availability")
            if resource.get("amount") is not None and not number(resource["amount"]):
                errors.append("resource amount must be nonnegative finite number or null")
    return errors


def calculate(kind, a, resources):
    a = {k: dec(a[k]) for k in FIELDS[kind]}
    if kind == "survivor":
        annual = max(a["annual_spending"] - a["annual_survivor_income"], 0)
        gross = annual * a["support_years"] + a["debt_payoff"] + a["one_time_costs"]
        benefit = min(gross, a["life_benefit"])
        steps = {"annual_support_gap": money(annual), "support_years": str(a["support_years"]),
                 "support_need": money(annual * a["support_years"]), "debt_payoff": money(a["debt_payoff"]), "one_time_costs": money(a["one_time_costs"])}
        formula = "max(annual_spending - annual_survivor_income, 0) * support_years + debt_payoff + one_time_costs"
    elif kind == "disability":
        monthly = max(a["monthly_spending"] - a["monthly_other_income"], 0)
        eligible = max(a["disability_months"] - a["waiting_months"], 0)
        gross = monthly * a["disability_months"]
        benefit = min(monthly, a["monthly_benefit"]) * eligible
        steps = {"monthly_income_gap": money(monthly), "eligible_benefit_months": str(eligible),
                 "waiting_period_need": money(monthly * min(a["disability_months"], a["waiting_months"]))}
        formula = "monthly gap * disability months; offset min(monthly gap, supplied benefit) * max(disability months - waiting months, 0)"
    elif kind == "long-term-care":
        eligible = min(max(a["care_months"] - a["waiting_months"], 0), a["benefit_month_limit"])
        gross = a["monthly_care_cost"] * a["care_months"]
        benefit = min(min(a["monthly_care_cost"], a["monthly_benefit"]) * eligible, a["lifetime_benefit_cap"])
        steps = {"eligible_benefit_months": str(eligible), "uncapped_modeled_benefit": money(min(a["monthly_care_cost"], a["monthly_benefit"]) * eligible),
                 "lifetime_benefit_cap": money(a["lifetime_benefit_cap"])}
        formula = "care cost * months; offset min(min(care cost, monthly benefit) * eligible months, lifetime cap)"
    else:
        gross = a["projected_loss"] + a["defense_costs"]
        benefit = min(gross, a["primary_applicable_amount"] + a["umbrella_applicable_amount"])
        steps = {"projected_loss": money(a["projected_loss"]), "defense_costs": money(a["defense_costs"]),
                 "supplied_applicable_insurance_amount": money(a["primary_applicable_amount"] + a["umbrella_applicable_amount"])}
        formula = "supplied loss + defense costs; offset supplied applicable primary and umbrella amounts capped at gross scenario need"
    resource_total = sum((dec(r["amount"]) for r in resources if r["availability"] == "available-for-scenario"), dec(0))
    residual = max(gross - benefit - resource_total, 0)
    return {"formula": formula, "steps": steps, "gross_scenario_need": money(gross), "modeled_insurance_offset": money(benefit),
            "designated_resource_amount": money(resource_total), "remaining_scenario_gap": money(residual),
            "resource_surplus_under_assumptions": money(max(resource_total + benefit - gross, 0))}


def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    findings = base_findings(doc)
    results, shared = [], {}
    if not doc["scenarios"]:
        add(findings, "missing-scenarios", "No protection scenarios supplied", "scenarios")
    for kind in doc["policy"]["required_scenario_types"]:
        if not any(s["type"] == kind for s in doc["scenarios"]):
            add(findings, "missing-scenario-type", f"Required {kind} scenario not supplied", "scenarios")
    for row in doc["scenarios"]:
        path, a = row["scenario_id"], row["assumptions"]
        supported = cited(row, doc, findings, path)
        supported = cited(a, doc, findings, path + ".assumptions") and supported
        missing = [k for k in FIELDS[row["type"]] if a.get(k) is None]
        for key in missing:
            add(findings, "unknown-assumption", f"{key} is unknown; no scenario result calculated", path)
        for r in row["designated_resources"]:
            supported = cited(r, doc, findings, path + ".resources") and supported
            if r["availability"] == "uncertain" or r.get("amount") is None:
                add(findings, "resource-gap", "Resource amount or scenario availability is unresolved; no complete scenario result", path, resource_id=r["resource_id"])
                supported = False
            if r["availability"] == "available-for-scenario":
                shared.setdefault(r["resource_id"], []).append(row["scenario_id"])
        calculation = calculate(row["type"], a, row["designated_resources"]) if not missing and supported else None
        questions = []
        if calculation is not None and dec(calculation["remaining_scenario_gap"]) > 0:
            questions.append("Review the modeled funding gap, resource availability and assumptions with the licensed professional; no product or adequacy conclusion.")
        if row["type"] in {"disability", "long-term-care", "liability"}:
            questions.append("Confirm benefit applicability, exclusions, waiting periods and tax treatment from actual contracts before relying on this scenario.")
        results.append({"scenario_id": row["scenario_id"], "type": row["type"], "subject_id": row["subject_id"],
                        "description": row["description"], "source_ids": row.get("source_ids"), "assumptions": a,
                        "designated_resources": row["designated_resources"], "calculation": calculation,
                        "calculation_status": "calculated-scenario" if calculation is not None else "not-evaluable",
                        "professional_review_questions": questions})
    result = common_result(doc)
    result.update(currency="USD", methodology="level-undiscounted", scenarios=results,
                  resource_reuse=[{"resource_id": rid, "scenario_ids": ids, "note": "Same resource appears in alternative scenarios; never add coverage across concurrent events."} for rid, ids in shared.items() if len(ids) > 1],
                  portfolio_total=None,
                  limitations=["Independent scenarios are not added together. No mortality, disability probability, inflation, discount rate, longevity or legal minimum is inferred.",
                               "Benefits and available resources are supplied scenario assumptions, not coverage, tax, actuarial adequacy or product recommendations."],
                  review_summary={"scenarios_supplied": len(results), "scenarios_calculated": sum(r["calculation"] is not None for r in results), "open_items": len(findings)})
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    errors = validate_output_envelope(out, SKILL)
    snapshot = out.get("result", {}).get("input_snapshot") if isinstance(out, dict) and isinstance(out.get("result"), dict) else None
    try:
        expected = build(snapshot)
        if out != expected:
            errors.append("output differs from full reconstruction of source snapshot, arithmetic, identities or findings")
    except (ValueError, TypeError, KeyError) as exc:
        errors.append(f"invalid input snapshot: {exc}")
    return errors
