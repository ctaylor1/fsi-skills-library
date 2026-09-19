"""Symmetric comparison with explicit unknowns and constituent exposure reconciliation."""
from copy import deepcopy
from itertools import combinations
from review_base import EPS, Review, numeric_fields, require_objects, rows, upstream_errors, validate_artifact
from wealth_contract import make_output, nonempty, validate_envelope

SKILL = "portfolio-proposal-comparator"
COST_FIELDS = ("advisory_fee_bps", "custody_fee_bps", "other_annual_cost_bps", "transaction_cost_amount")
BOOL_FIELDS = ("proprietary", "revenue_sharing", "cheaper_share_class_available")


def validate_input(doc):
    errors = validate_envelope(doc)
    if not isinstance(doc, dict):
        return errors
    errors += upstream_errors(doc)
    require_objects(doc, ("policy",), errors)
    if isinstance(doc.get("policy"), dict):
        numeric_fields(doc["policy"], ("max_issuer_weight", "max_sector_weight", "max_illiquid_weight"), errors, "policy", 1)
        numeric_fields(doc["policy"], ("liquidity_horizon_days", "annual_cost_limit_bps"), errors, "policy")
    for proposal in rows(doc.get("proposals"), "proposal_id", errors, "proposals", 2):
        if not nonempty(proposal.get("currency")):
            errors.append("proposal.currency required; no FX conversion is performed")
        numeric_fields(proposal, ("portfolio_value", "reported_first_year_cost_amount") + COST_FIELDS, errors, "proposal")
        for holding in rows(proposal.get("holdings"), "holding_id", errors, "holdings", 1):
            if not nonempty(holding.get("security_id")):
                errors.append("holding.security_id required")
            numeric_fields(holding, ("weight",), errors, "holding", 1)
            numeric_fields(holding, ("market_value", "expense_ratio_bps", "liquidity_days"), errors, "holding")
            for field in BOOL_FIELDS:
                if holding.get(field) is not None and not isinstance(holding[field], bool):
                    errors.append(f"holding.{field} must be boolean or null")
            if holding.get("exposures") is not None:
                for exposure in rows(holding["exposures"], "exposure_id", errors, "exposures"):
                    numeric_fields(exposure, ("weight",), errors, "exposure", 1)
    return errors


def compute(doc):
    errors = validate_input(doc)
    if errors:
        raise ValueError("; ".join(errors))
    r = Review(doc)
    policy = doc["policy"]
    r.policy(policy, "policy")
    limits = {key: r.num(policy, key, "policy") for key in
              ("max_issuer_weight", "max_sector_weight", "max_illiquid_weight", "liquidity_horizon_days", "annual_cost_limit_bps")}
    proposals = []
    for p in doc["proposals"]:
        pid = p["proposal_id"]
        r.source(p, pid)
        value = r.num(p, "portfolio_value", pid, True)
        weights = [r.num(h, "weight", f"{pid}/{h['holding_id']}") for h in p["holdings"]]
        weight_sum = sum(weights) if all(x is not None for x in weights) else None
        normalized = weight_sum is not None and abs(weight_sum - 1) <= EPS
        if not normalized:
            r.gap("economic-total", f"{pid}: weights do not reconcile to one; no silent normalization")
        partial_expense = 0.0
        cost_coverage = liquidity_coverage = 0.0
        illiquid_known = 0.0
        conflict_known = dict.fromkeys(BOOL_FIELDS, 0.0)
        conflict_coverage = dict.fromkeys(BOOL_FIELDS, 0.0)
        exposures = {key: {} for key in ("issuer_id", "sector", "asset_class")}
        exposure_coverage = dict.fromkeys(exposures, 0.0)
        holding_rows = []
        for h, weight in zip(p["holdings"], weights):
            hid = f"{pid}/{h['holding_id']}"
            sourced = r.source(h, hid)
            expense = r.num(h, "expense_ratio_bps", hid)
            days = r.num(h, "liquidity_days", hid)
            if h.get("market_value") is not None and value is not None and weight is not None:
                if abs(h["market_value"] - weight * value) > 0.01:
                    r.gap("economic-total", f"{hid}: market value does not equal weight times proposal value", h.get("source_ids"))
            if weight is not None and sourced:
                if expense is not None:
                    partial_expense += weight * expense
                    cost_coverage += weight
                if days is not None and limits["liquidity_horizon_days"] is not None:
                    liquidity_coverage += weight
                    if days > limits["liquidity_horizon_days"]:
                        illiquid_known += weight
            for field in BOOL_FIELDS:
                flag = h.get(field)
                if not isinstance(flag, bool):
                    r.gap("unknown-conflict", f"{hid}: {field} is unknown")
                elif weight is not None and sourced:
                    conflict_coverage[field] += weight
                    if flag:
                        conflict_known[field] += weight
                        r.gap("conflict-review", f"{hid}: {field} recorded; professional review required", h.get("source_ids"))
            rows_in = h.get("exposures")
            exposure_sum = None
            if not isinstance(rows_in, list) or not rows_in:
                r.gap("look-through-gap", f"{hid}: constituent exposures missing; diversification labels do not establish coverage")
            else:
                constituent_weights = [r.num(e, "weight", f"{hid}/{e['exposure_id']}") for e in rows_in]
                exposure_sum = sum(constituent_weights) if all(x is not None for x in constituent_weights) else None
                valid_sum = exposure_sum is not None and exposure_sum <= 1 + EPS
                if exposure_sum is None or abs(exposure_sum - 1) > EPS:
                    r.gap("look-through-total", f"{hid}: constituent weights sum to {exposure_sum}; expected one")
                for e, ew in zip(rows_in, constituent_weights):
                    esourced = r.source(e, f"{hid}/{e['exposure_id']}")
                    for field in exposures:
                        key = r.text(e, field, f"{hid}/{e['exposure_id']}")
                        if key is not None and weight is not None and ew is not None and valid_sum and esourced and sourced:
                            contribution = weight * ew
                            exposures[field][key] = exposures[field].get(key, 0.0) + contribution
                            exposure_coverage[field] += contribution
            holding_rows.append({"holding_id": h["holding_id"], "security_id": h["security_id"],
                                 "weight": weight, "expense_ratio_bps": expense, "liquidity_days": days,
                                 "exposure_weight_sum": exposure_sum, "source_ids": deepcopy(h.get("source_ids")),
                                 **{field: h.get(field) for field in BOOL_FIELDS}})
        expense_complete = normalized and abs(cost_coverage - 1) <= EPS
        expense_bps = partial_expense if expense_complete else None
        components = {key: r.num(p, key, pid) for key in COST_FIELDS}
        annual_complete = expense_bps is not None and all(components[key] is not None for key in COST_FIELDS[:3])
        ongoing_bps = expense_bps + sum(components[key] for key in COST_FIELDS[:3]) if annual_complete else None
        annual_amount = value * ongoing_bps / 10000 if value is not None and ongoing_bps is not None else None
        first_year = annual_amount + components["transaction_cost_amount"] if annual_amount is not None and components["transaction_cost_amount"] is not None else None
        if p.get("reported_first_year_cost_amount") is not None and first_year is not None:
            if abs(p["reported_first_year_cost_amount"] - first_year) > 0.01:
                r.gap("economic-total", f"{pid}: reported first-year cost does not reconcile to components", p.get("source_ids"))
        concentration = {}
        for field in exposures:
            full = normalized and abs(exposure_coverage[field] - 1) <= EPS
            known = max(exposures[field].values()) if exposures[field] else 0.0
            concentration[field] = {"known_weights": {key: round(val, 12) for key, val in sorted(exposures[field].items())},
                                    "coverage_weight": round(exposure_coverage[field], 12),
                                    "unknown_weight": round(max(0, 1 - exposure_coverage[field]), 12) if normalized else None,
                                    "max_weight": round(known, 12) if full else None,
                                    "known_max_lower_bound": round(known, 12)}
            limit_key = {"issuer_id": "max_issuer_weight", "sector": "max_sector_weight"}.get(field)
            limit = limits.get(limit_key)
            if limit is not None and known > limit + EPS:
                r.gap("concentration-review", f"{pid}: known {field} exposure {known:.6f} exceeds supplied {limit_key} {limit}", p.get("source_ids"))
        illiquid = illiquid_known if normalized and abs(liquidity_coverage - 1) <= EPS else None
        if limits["max_illiquid_weight"] is not None and illiquid_known > limits["max_illiquid_weight"] + EPS:
            r.gap("liquidity-review", f"{pid}: known illiquid weight exceeds supplied limit", p.get("source_ids"))
        if ongoing_bps is not None and limits["annual_cost_limit_bps"] is not None and ongoing_bps > limits["annual_cost_limit_bps"] + EPS:
            r.gap("cost-review", f"{pid}: annual modeled costs exceed supplied limit", p.get("source_ids"))
        metrics = {"weight_sum": weight_sum, "weighted_expense_bps": expense_bps,
                   "known_expense_bps_lower_bound": partial_expense, "expense_coverage_weight": cost_coverage,
                   "ongoing_cost_bps": ongoing_bps, "ongoing_cost_amount": annual_amount,
                   "first_year_cost_amount": first_year, "cost_components": components,
                   "exposures": concentration, "illiquid_weight": illiquid,
                   "known_illiquid_lower_bound": illiquid_known, "liquidity_coverage_weight": liquidity_coverage,
                   "conflicts": {key: {"weight": conflict_known[key] if normalized and abs(conflict_coverage[key] - 1) <= EPS else None,
                                      "known_weight_lower_bound": conflict_known[key], "coverage_weight": conflict_coverage[key]}
                                 for key in BOOL_FIELDS}}
        proposals.append({"proposal_id": pid, "currency": p["currency"], "portfolio_value": value,
                          "holdings": holding_rows, "metrics": metrics})
    differences = []
    for a, b in combinations(proposals, 2):
        comparable = a["currency"] == b["currency"] and a["portfolio_value"] == b["portfolio_value"] and a["portfolio_value"] is not None
        if not comparable:
            r.gap("comparison-basis", f"{a['proposal_id']}/{b['proposal_id']}: currency or portfolio value differs/unknown; dollar difference not comparable")
        left, right = a["metrics"], b["metrics"]
        differences.append({"left": a["proposal_id"], "right": b["proposal_id"], "direction": "right-minus-left",
                            "ongoing_cost_bps": right["ongoing_cost_bps"] - left["ongoing_cost_bps"] if left["ongoing_cost_bps"] is not None and right["ongoing_cost_bps"] is not None else None,
                            "first_year_cost_amount": right["first_year_cost_amount"] - left["first_year_cost_amount"] if comparable and left["first_year_cost_amount"] is not None and right["first_year_cost_amount"] is not None else None})
    result = {"input_snapshot": deepcopy(doc), **r.context(), "proposals": proposals, "pairwise_differences": differences,
              "selected_proposal": None, "tax_estimate": None,
              "scope": "Supplied candidate economics and constituent exposures; no winner, return forecast, tax estimate or legal determination."}
    return make_output(SKILL, doc, result, r.findings)


def validate_output(out):
    return validate_artifact(out, SKILL, compute)
