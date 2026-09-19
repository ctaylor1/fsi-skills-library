from native_helpers import Decimal, data, date, finding, fmt, num, pack, profile, refs, txt, validate_with


def evaluate(doc):
    d = data(doc)
    f = []
    profile(doc, f)
    p = d.get("premium", {})
    l = d.get("losses", {})
    e = d.get("exposure", {})
    a = d.get("assumptions", {})
    for label, row in [("premium", p), ("losses", l), ("exposure", e), ("assumptions", a)]:
        refs(doc, row, f, label)
    start = date(d.get("period_start"))
    end = date(d.get("period_end"))
    if start is None or end is None or start > end:
        finding(f, "period-gap", "A valid experience period is required")
    for label, row in [("premium", p), ("losses", l), ("exposure", e)]:
        rs = date(row.get("period_start"))
        re = date(row.get("period_end"))
        if rs != start or re != end or rs is None or re is None:
            finding(
                f, "period-mismatch", label + " period must match the experience cohort", row.get("source_refs", [])
            )
    if p.get("basis") != "earned":
        finding(f, "premium-basis", "Premium must be earned, before supplied on-level/trend adjustment")
    if l.get("basis") != "ultimate_loss_and_lae":
        finding(f, "loss-basis", "Losses must be reviewed ultimate loss plus LAE; no development is selected here")
    if not txt(p.get("currency")) or p.get("currency") != l.get("currency") or p.get("currency") != a.get("currency"):
        finding(f, "currency-mismatch", "Premium, losses and monetary assumptions must share one currency")
    if not txt(e.get("unit")) or e.get("unit") != a.get("exposure_unit"):
        finding(f, "exposure-unit", "Exposure and per-exposure assumptions require identical units")
    for key, expected in [
        ("catastrophe_basis", "excluded_from_losses"),
        ("reinsurance_basis", "net_cost_after_expected_recoveries"),
        ("alignment_reviewed", True),
    ]:
        if a.get(key) != expected:
            finding(f, "assumption-basis", key + " requires the documented supported basis")
    premium = num(p, "amount", f, "premium")
    loss = num(l, "amount", f, "losses")
    exposure = num(e, "amount", f, "exposure")
    values = {}
    for key in (
        "on_level_factor",
        "premium_trend_factor",
        "loss_trend_factor",
        "fixed_expense_per_exposure",
        "catastrophe_provision_per_exposure",
        "reinsurance_net_cost_per_exposure",
    ):
        values[key] = num(
            a, key, f, "assumptions", minimum=None if key == "reinsurance_net_cost_per_exposure" else Decimal("0")
        )
    for key in ("credibility", "variable_expense_ratio", "profit_ratio"):
        values[key] = num(a, key, f, "assumptions", maximum=Decimal("1"))
    z = values["credibility"]
    complement = None if z == 1 else num(a, "complement_loss_and_lae_per_exposure", f, "assumptions")
    if premium is not None and premium <= 0:
        finding(f, "zero-denominator", "Positive earned premium required")
    if exposure is not None and exposure <= 0:
        finding(f, "zero-denominator", "Positive earned exposure required")
    for key in ("on_level_factor", "premium_trend_factor", "loss_trend_factor"):
        if values[key] is not None and values[key] <= 0:
            finding(f, "factor-gap", key + " must be positive")
    v = values["variable_expense_ratio"]
    profit = values["profit_ratio"]
    denominator = None if v is None or profit is None else 1 - v - profit
    if denominator is not None and denominator <= 0:
        finding(f, "expense-denominator", "1-variable expense-profit must be positive")
    results = {
        "method": "single_cohort_pure_premium_indication",
        "currency": p.get("currency"),
        "exposure_unit": e.get("unit"),
        "indicated_change": None,
        "indicated_premium_per_exposure": None,
        "current_adjusted_premium_per_exposure": None,
        "experience_loss_lae_per_exposure": None,
        "credibility_blended_loss_lae_per_exposure": None,
        "rate_selection": "not_performed",
        "filing_approval": "not_determined",
        "assumptions": a,
    }
    if any(x["severity"] == "gap" for x in f):
        return pack(results, f, False)
    current = premium * values["on_level_factor"] * values["premium_trend_factor"] / exposure
    experience = loss * values["loss_trend_factor"] / exposure
    blended = z * experience + (1 - z) * (complement if complement is not None else Decimal("0"))
    indicated = (
        blended
        + values["fixed_expense_per_exposure"]
        + values["catastrophe_provision_per_exposure"]
        + values["reinsurance_net_cost_per_exposure"]
    ) / denominator
    if indicated < 0:
        raise ValueError("negative indicated cost is outside supported method")
    results.update(
        {
            "indicated_change": fmt(indicated / current - 1),
            "indicated_premium_per_exposure": fmt(indicated),
            "current_adjusted_premium_per_exposure": fmt(current),
            "experience_loss_lae_per_exposure": fmt(experience),
            "credibility_blended_loss_lae_per_exposure": fmt(blended),
        }
    )
    return pack(results, f)


def validate(doc):
    return validate_with(evaluate, doc)
