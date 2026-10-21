"""Conditional cohort pricing arithmetic, never filed or approved premium rates."""

from decimal import Decimal, localcontext
from fractions import Fraction
from design_support import validate_with
from specialist_support import SpecialistReview

METHOD = "reviewed-health-cohort-pricing-v1"
ALIGN = ("cohort_id", "population_basis", "currency", "benefit_basis")
BASE = ALIGN + ("period_start", "period_end", "valuation_date")


class PricingReview(SpecialistReview):
    def num(self, row, key, **options):
        value = super().num(row, key, **options)
        if value is None:
            return None
        digits = value.as_tuple()
        if len(digits.digits) > 256 or abs(digits.exponent) > 1000:
            raise ValueError(key + ": numeric evidence exceeds 256 significant digits or exponent magnitude 1000")
        return Fraction(value)


def total(values):
    values = list(values)
    return None if any(v is None for v in values) else sum(values, Fraction(0))


def ratio(a, b):
    return None if a is None or b is None or b == 0 else a / b


def display_exact(value):
    """Keep terminating results exact; render recurring rational ratios at 50 digits."""
    if isinstance(value, Fraction):
        denominator = value.denominator
        twos = fives = 0
        while denominator % 2 == 0:
            twos += 1
            denominator //= 2
        while denominator % 5 == 0:
            fives += 1
            denominator //= 5
        if denominator == 1:
            scale = max(twos, fives)
            coefficient = value.numerator * 2 ** (scale - twos) * 5 ** (scale - fives)
            parts = Decimal(coefficient).as_tuple()
            return Decimal((parts.sign, parts.digits, -scale))
        with localcontext() as context:
            context.prec = 50
            return Decimal(value.numerator) / Decimal(value.denominator)
    if isinstance(value, dict):
        return {k: display_exact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [display_exact(v) for v in value]
    return value


def strict_references(value):
    """Do not accept a scalar or duplicate reference list as the documented schema."""
    if isinstance(value, dict):
        refs = value.get("source_refs")
        if refs is not None and (
            not isinstance(refs, list)
            or any(not isinstance(x, str) or not x.strip() for x in refs)
            or len(set(refs)) != len(refs)
        ):
            raise ValueError("source_refs must be an explicit array of unique nonblank strings or null")
        for child in value.values():
            strict_references(child)
    elif isinstance(value, list):
        for child in value:
            strict_references(child)


def evaluate(doc):
    strict_references(doc)
    r = PricingReview(doc, METHOD)
    d = r.data
    r.need(
        doc["context"].get("capacity") == "health-pricing-review"
        and doc["context"].get("line_of_business") == "health"
        and doc["context"].get("object_id") == d.get("cohort_id"),
        "professional-context",
        "Health pricing review capacity, health line and exact cohort object are required",
        d,
    )
    for source in doc["sources"]:
        r.fields(source, ("locator",))
    r.evidence(d)
    r.fields(d, ALIGN + ("inventory_statement", "reviewed_by", "source_locator"))
    r.flag(d, "inventory_complete")
    r.flag(d, "adjustments_complete")
    r.flag(d, "assumptions_reviewed")
    reviewed_on = r.date(d, "reviewed_on")
    valuation_day = r.date(d, "valuation_date")
    r.need(
        reviewed_on is not None and valuation_day is not None and reviewed_on >= valuation_day,
        "review-date",
        "Pricing review cannot predate the underlying claims valuation",
        d,
    )
    r.need(
        d.get("currency") in r.profile.get("currencies", []),
        "currency",
        "Currency must be explicitly included in reviewed profile",
        d,
    )
    for field in ("period_start", "period_end", "valuation_date"):
        r.date(d, field)
    base_start, base_end, valuation = [d.get(x) for x in ("period_start", "period_end", "valuation_date")]
    r.need(
        all(isinstance(x, str) for x in (base_start, base_end, valuation)) and base_start <= base_end <= valuation,
        "base-period",
        "Base experience start <= end <= valuation is required",
        d,
    )
    projection = d.get("projection")
    if not isinstance(projection, dict):
        raise ValueError("projection must be an object")
    r.evidence(projection)
    r.fields(
        projection,
        ALIGN + ("source_locator", "trend_basis", "projection_basis", "partial_month_method", "exposure_unit"),
    )
    r.need(
        projection.get("exposure_unit") == "member-months",
        "projection-exposure-unit",
        "Projection requires member months, never snapshot enrollment",
        projection,
    )
    r.flag(projection, "complete")
    r.flag(projection, "population_bridge_reviewed")
    for key in ("period_start", "period_end", "trend_from", "trend_to"):
        r.date(projection, key, future=True)
    r.need(
        all(projection.get(k) == d.get(k) for k in ALIGN),
        "projection-scope",
        "Projection scope must match the explicitly reviewed cohort and benefit basis",
        projection,
    )
    ps, pe, tf, tt = [projection.get(k) for k in ("period_start", "period_end", "trend_from", "trend_to")]
    r.need(
        all(isinstance(x, str) for x in (ps, pe, tf, tt, base_end)) and ps <= pe and ps > base_end and tf <= tt,
        "projection-period",
        "Explicit future projection and trend horizon are required; no midpoint or annualization inference",
        projection,
    )
    pmm = r.num(projection, "member_months")
    r.need(pmm is not None and pmm > 0, "projection-exposure", "Projected member months must be positive", projection)
    current = r.num(projection, "current_premium_pmpm")
    r.need(
        current is not None and current > 0,
        "premium-basis",
        "Current comparable premium PMPM must be positive",
        projection,
    )
    exposure = d.get("exposure")
    if not isinstance(exposure, dict):
        raise ValueError("exposure must be an object")
    r.evidence(exposure)
    r.fields(exposure, ("partial_month_method", "source_locator", "exposure_unit"))
    r.flag(exposure, "complete")
    r.need(
        exposure.get("exposure_unit") == "member-months",
        "exposure-unit",
        "Snapshot enrollment cannot substitute for member months",
        exposure,
    )
    r.need(
        all(exposure.get(k) == d.get(k) for k in BASE),
        "exposure-alignment",
        "Exposure and incurred claims require identical cohort, period, valuation, currency and benefit scope",
        exposure,
    )
    mm = r.num(exposure, "member_months")
    premium = r.num(exposure, "earned_premium")
    r.need(mm is not None and mm > 0, "base-exposure", "Base member months must be positive", exposure)
    r.need(
        premium is not None and premium > 0,
        "earned-premium",
        "Base earned premium must be positive for the descriptive claim/premium ratio",
        exposure,
    )
    expected = set(r.strings(d, "expected_category_ids", nonempty=True))
    categories = r.rows("categories", "category_id")
    r.need(
        {x["category_id"] for x in categories} == expected,
        "category-inventory",
        "Supplied categories must exactly match source-complete expected category inventory",
        d,
    )
    adjustments = r.rows("adjustments", "adjustment_id", nonempty=False)
    events = set()
    raw = {}
    rendered = []
    for row in categories:
        r.fields(row, ("source_locator", "incurred_convention", "recovery_basis", "trend_basis"))
        r.need(
            all(row.get(k) == d.get(k) for k in BASE),
            "claim-alignment",
            "Claim category basis does not exactly match base exposure",
            row,
        )
        r.need(
            row.get("incurred_convention") == "paid-plus-case-outstanding-plus-ibnr",
            "incurred-basis",
            "Explicit paid + unpaid case outstanding excluding IBNR + IBNR convention required",
            row,
        )
        r.flag(row, "case_excludes_ibnr")
        r.flag(row, "complete")
        ids = r.strings(row, "economic_event_ids", nonempty=True)
        r.need(
            not events.intersection(ids),
            "duplicate-event",
            "Economic events cannot be counted in multiple categories or adjustments",
            row,
        )
        events.update(ids)
        paid, case, ibnr, recovery = [r.num(row, k) for k in ("paid", "case_outstanding", "ibnr", "recoveries")]
        basis = row.get("recovery_basis")
        r.need(
            basis in {"gross-deduct-recoveries", "net-recoveries-already-included"},
            "recovery-basis",
            "Recovery accounting basis must be explicit",
            row,
        )
        r.need(
            basis != "net-recoveries-already-included" or recovery == 0,
            "double-recovery",
            "Already net claims require explicit zero separate recovery deduction",
            row,
        )
        net = total([paid, case, ibnr, -recovery if recovery is not None else None])
        r.need(
            net is not None and net >= 0,
            "incurred-total",
            "Supported net incurred total must be known and nonnegative",
            row,
        )
        cost, util = r.num(row, "cost_factor"), r.num(row, "utilization_factor")
        r.need(
            cost is not None and cost > 0 and util is not None and util > 0,
            "trend-factor",
            "Explicit positive cumulative cost and utilization factors required",
            row,
        )
        r.need(
            all(row.get(k) == projection.get(k) for k in ("trend_from", "trend_to", "trend_basis")),
            "trend-horizon",
            "Category factors must name the exact supplied cumulative trend horizon and basis",
            row,
        )
        raw[row["category_id"]] = {
            "net": net,
            "base_adjustments": [],
            "projection_adjustments": [],
            "cost": cost,
            "util": util,
            "row": row,
        }
    for row in adjustments:
        r.fields(row, ("category_id", "economic_event_id", "stage", "reason", "source_locator"))
        event = row.get("economic_event_id")
        r.need(event not in events, "duplicate-event", "Adjustment economic event already counted", row)
        events.add(event)
        key = row.get("category_id")
        r.need(key in raw, "adjustment-category", "Adjustment requires a known exact category", row)
        stage = row.get("stage")
        r.need(
            stage in {"base-incurred-amount", "projection-pmpm"},
            "adjustment-stage",
            "Adjustment stage must be base-incurred-amount or projection-pmpm",
            row,
        )
        scope = d if stage == "base-incurred-amount" else projection
        fields = BASE if stage == "base-incurred-amount" else ALIGN + ("period_start", "period_end")
        r.need(
            all(row.get(k) == scope.get(k) for k in fields),
            "adjustment-scope",
            "Adjustment basis must match its exact base or projection scope",
            row,
        )
        value = r.num(row, "amount", signed=True)
        if key in raw and stage in {"base-incurred-amount", "projection-pmpm"}:
            raw[key]["base_adjustments" if stage == "base-incurred-amount" else "projection_adjustments"].append(value)
    expense = d.get("expenses")
    if not isinstance(expense, dict):
        raise ValueError("expenses must be an object")
    r.evidence(expense)
    r.fields(expense, ("source_locator", "expense_basis"))
    r.flag(expense, "complete")
    r.need(
        all(expense.get(k) == projection.get(k) for k in ALIGN + ("period_start", "period_end")),
        "expense-scope",
        "Expenses must match projection population, currency, benefit and dates",
        expense,
    )
    fixed, pmpm, prop, margin = [
        r.num(expense, k, proportion=k in {"premium_proportion", "margin_proportion"})
        for k in ("fixed_total", "pmpm", "premium_proportion", "margin_proportion")
    ]
    r.need(
        prop is not None and margin is not None and prop + margin < 1,
        "premium-denominator",
        "Premium-proportional expense plus margin must be less than one",
        expense,
    )
    for key, item in raw.items():
        adjusted = total([item["net"], total(item["base_adjustments"])])
        base = ratio(adjusted, mm)
        projected = total(
            [
                base * item["cost"] * item["util"]
                if all(x is not None for x in (base, item["cost"], item["util"]))
                else None,
                total(item["projection_adjustments"]),
            ]
        )
        r.need(
            adjusted is not None and adjusted >= 0 and projected is not None and projected >= 0,
            "adjusted-cost",
            "Adjusted and projected costs must be known and nonnegative",
            item["row"],
        )
        rendered.append(
            {
                "category_id": key,
                "net_incurred": item["net"],
                "adjusted_incurred": adjusted,
                "base_pmpm": base,
                "projected_pmpm": projected,
                "source_refs": item["row"]["source_refs"],
            }
        )
    projected = total(x["projected_pmpm"] for x in rendered)
    expense_pmpm = total([ratio(fixed, pmm), pmpm])
    denominator = 1 - prop - margin if prop is not None and margin is not None else None
    indication = ratio(total([projected, expense_pmpm]), denominator)
    change = ratio(indication, current)
    metrics = {
        "base_member_months": mm,
        "projected_member_months": pmm,
        "net_incurred": total(x["net_incurred"] for x in rendered),
        "adjusted_incurred": total(x["adjusted_incurred"] for x in rendered),
        "projected_claim_pmpm": projected,
        "nonpremium_expense_pmpm": expense_pmpm,
        "conditional_premium_pmpm": indication,
        "renewal_change_fraction": change - 1 if change is not None else None,
        "descriptive_incurred_to_earned_premium": ratio(total(x["net_incurred"] for x in rendered), premium),
    }
    if not r.clear:
        metrics = {k: None for k in metrics}
        for row in rendered:
            for key in ("net_incurred", "adjusted_incurred", "base_pmpm", "projected_pmpm"):
                row[key] = None
    return r.finish(
        display_exact(
            {
                "metrics": metrics,
                "categories": rendered,
                "currency": d.get("currency"),
                "cohort_id": d.get("cohort_id"),
                "statutory_mlr_calculated": False,
                "premium_approved": False,
                "filing_prepared": False,
                "intermediate_arithmetic": "exact-rational",
                "recurring_ratio_significant_digits": 50,
            }
        )
    )


def validate(doc):
    return validate_with(evaluate, doc)
