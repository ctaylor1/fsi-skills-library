"""Construct bounded, model-derived candidates without inventing investment forecasts."""
from copy import deepcopy
from review_base import EPS, Review, numeric_fields, require_objects, rows, upstream_errors, validate_artifact
from wealth_contract import make_output, nonempty, validate_envelope

SKILL = "portfolio-construction-assistant"


def validate_input(doc):
    errors = validate_envelope(doc)
    if not isinstance(doc, dict):
        return errors
    errors += upstream_errors(doc)
    require_objects(doc, ("mandate",), errors)
    numeric_fields(doc, ("portfolio_value",), errors, "request")
    if not nonempty(doc.get("currency")):
        errors.append("currency required; no FX conversion is implemented")
    universe = rows(doc.get("universe"), "security_id", errors, "universe", 1)
    for security in universe:
        numeric_fields(security, ("max_weight",), errors, "universe", 1)
        if security.get("eligible") is not None and not isinstance(security["eligible"], bool):
            errors.append("universe.eligible must be boolean or null")
    mandate = doc.get("mandate")
    if isinstance(mandate, dict):
        if mandate.get("method") != "proportional-within-model-sleeve":
            errors.append("mandate.method must explicitly select proportional-within-model-sleeve")
        for band in rows(mandate.get("class_bands"), "asset_class", errors, "class_bands"):
            numeric_fields(band, ("min_weight", "max_weight"), errors, "class_bands", 1)
        numeric_fields(mandate, ("cash_min", "cash_max", "max_position_weight"), errors, "mandate", 1)
        if not isinstance(mandate.get("restricted_security_ids"), list) or any(
            not nonempty(x) for x in mandate.get("restricted_security_ids", [])
        ):
            errors.append("restricted_security_ids must be an explicit list of IDs")
    for model in rows(doc.get("models"), "model_id", errors, "models", 1):
        numeric_fields(model, ("cash_weight",), errors, "model", 1)
        if not isinstance(model.get("approval_record"), dict):
            errors.append("model.approval_record must be an object")
        for allocation in rows(model.get("allocations"), "security_id", errors, "model.allocations", 1):
            numeric_fields(allocation, ("weight",), errors, "model allocation", 1)
    return errors


def distribute(target, seeds, caps):
    """Allocate a sleeve by explicit model proportions, clipping caps and redistributing."""
    weights = dict.fromkeys(seeds, 0.0)
    active = {sid for sid in seeds if seeds[sid] > 0 and caps[sid] > 0}
    remaining = target
    while active and remaining > EPS:
        total_seed = sum(seeds[sid] for sid in sorted(active))
        capped = {sid for sid in sorted(active) if remaining * seeds[sid] / total_seed > caps[sid] + EPS}
        if not capped:
            for sid in sorted(active):
                weights[sid] = remaining * seeds[sid] / total_seed
            remaining = 0.0
            break
        for sid in sorted(capped):
            weights[sid] = caps[sid]
            remaining -= caps[sid]
        active -= capped
    return weights, max(0.0, remaining)


def compute(doc):
    errors = validate_input(doc)
    if errors:
        raise ValueError("; ".join(errors))
    review = Review(doc)
    value = review.num(doc, "portfolio_value", "request", True)
    mandate = doc["mandate"]
    review.policy(mandate, "mandate")
    limits = {key: review.num(mandate, key, "mandate")
              for key in ("cash_min", "cash_max", "max_position_weight")}
    if limits["cash_min"] is not None and limits["cash_max"] is not None and limits["cash_min"] > limits["cash_max"]:
        review.gap("infeasible-mandate", "cash minimum exceeds maximum")
    bands = {}
    for band in mandate["class_bands"]:
        review.source(band, f"class {band['asset_class']}")
        lo, hi = (review.num(band, key, band["asset_class"]) for key in ("min_weight", "max_weight"))
        bands[band["asset_class"]] = (lo, hi)
        if lo is not None and hi is not None and lo > hi:
            review.gap("infeasible-mandate", f"{band['asset_class']}: minimum exceeds maximum")
    universe = {s["security_id"]: s for s in doc["universe"]}
    restrictions = set(mandate["restricted_security_ids"])
    if restrictions - set(universe):
        review.gap("restriction-identity", f"Restricted IDs not resolved in supplied universe: {sorted(restrictions - set(universe))}")
    eligible, caps = {}, {}
    for sid, security in universe.items():
        covered = review.source(security, f"universe {sid}")
        review.text(security, "asset_class", sid)
        if not isinstance(security.get("eligible"), bool):
            review.gap("eligibility-unknown", f"{sid}: eligibility review is unknown")
        eligible[sid] = covered and security.get("eligible") is True and sid not in restrictions
        cap = review.num(security, "max_weight", sid)
        caps[sid] = min(cap, limits["max_position_weight"]) if cap is not None and limits["max_position_weight"] is not None else None
    shared_gap_count = len(review.findings)
    candidates = []
    for model in doc["models"]:
        start = len(review.findings)
        mid = model["model_id"]
        review.source(model, mid)
        review.text(model, "version", mid)
        approval = model["approval_record"]
        review.source(approval, f"{mid} approval record")
        for key in ("owner", "reference"):
            review.text(approval, key, f"{mid} approval record")
        if approval.get("status") != "recorded-approved":
            review.gap("model-review", f"{mid}: supplied model approval record is missing or unresolved")
        cash = review.num(model, "cash_weight", mid)
        seeds, class_targets, model_classes = {}, {}, {}
        evaluable = cash is not None
        for allocation in model["allocations"]:
            sid = allocation["security_id"]
            review.source(allocation, f"{mid}/{sid}")
            weight = review.num(allocation, "weight", f"{mid}/{sid}")
            if sid not in universe:
                review.gap("unknown-security", f"{mid}/{sid}: not in supplied universe")
                evaluable = False
                continue
            asset_class = universe[sid].get("asset_class")
            if weight is None or not nonempty(asset_class) or caps[sid] is None:
                evaluable = False
                continue
            seeds[sid] = weight
            model_classes[sid] = asset_class
            class_targets[asset_class] = class_targets.get(asset_class, 0.0) + weight
        model_sum = cash + sum(seeds.values()) if evaluable else None
        if model_sum is not None and abs(model_sum - 1) > EPS:
            review.gap("model-total", f"{mid}: model weights plus cash sum to {model_sum}; never normalized")
            evaluable = False
        output_weights, unallocated = {}, {}
        if evaluable:
            for asset_class, target in class_targets.items():
                sub = {sid: seed for sid, seed in seeds.items() if model_classes[sid] == asset_class and eligible[sid]}
                weights, remainder = distribute(target, sub, {sid: caps[sid] for sid in sub})
                output_weights.update(weights)
                unallocated[asset_class] = round(remainder, 12)
                if remainder > EPS:
                    review.gap("infeasible-sleeve", f"{mid}/{asset_class}: {remainder:.8f} cannot be allocated within approved model names and caps")
            for sid in seeds:
                output_weights.setdefault(sid, 0.0)
        class_actual = {asset_class: sum(weight for sid, weight in output_weights.items() if model_classes[sid] == asset_class)
                        for asset_class in class_targets} if evaluable else None
        checks = []
        for asset_class in sorted(set(class_targets) | set(bands)):
            actual = class_actual.get(asset_class, 0.0) if class_actual is not None else None
            lo, hi = bands.get(asset_class, (None, None))
            passed = lo <= actual <= hi if actual is not None and lo is not None and hi is not None else None
            checks.append({"constraint": "class-band", "asset_class": asset_class, "actual": actual,
                           "minimum": lo, "maximum": hi, "met": passed})
            if passed is not True:
                review.gap("class-constraint", f"{mid}/{asset_class}: allocation band is unknown or not met")
        cash_met = limits["cash_min"] <= cash <= limits["cash_max"] if cash is not None and limits["cash_min"] is not None and limits["cash_max"] is not None else None
        checks.append({"constraint": "cash-band", "actual": cash, "minimum": limits["cash_min"],
                       "maximum": limits["cash_max"], "met": cash_met})
        if cash_met is not True:
            review.gap("cash-constraint", f"{mid}: cash band is unknown or not met")
        candidate_findings = deepcopy(review.findings[:shared_gap_count] + review.findings[start:])
        candidates.append({
            "candidate_id": f"candidate-{mid}", "model_id": mid,
            "status": "needs-review" if candidate_findings else "constraint-consistent",
            "holdings": [{"security_id": sid, "asset_class": model_classes[sid], "weight": round(weight, 12),
                          "amount": round(value * weight, 2) if value is not None else None,
                          "model_weight": seeds[sid], "deviation_weight": round(weight - seeds[sid], 12),
                          "source_ids": deepcopy(universe[sid].get("source_ids"))}
                         for sid, weight in sorted(output_weights.items())],
            "cash_weight": cash, "cash_amount": round(value * cash, 2) if value is not None and cash is not None else None,
            "model_weight_sum": model_sum, "class_weights": class_actual, "unallocated_by_class": unallocated,
            "constraint_checks": checks, "findings": candidate_findings,
        })
    result = {"input_snapshot": deepcopy(doc), **review.context(), "candidates": candidates,
              "method": mandate["method"], "selected_candidate": None,
              "scope": "Model-derived continuous-weight candidates; no trade sizing, return forecast or investment approval."}
    return make_output(SKILL, doc, result, review.findings)


def validate_output(out):
    return validate_artifact(out, SKILL, compute)
