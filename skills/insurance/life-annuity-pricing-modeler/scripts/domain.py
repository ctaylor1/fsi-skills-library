"""Annual mutually exclusive decrement cashflow model; not a reserve or approval engine."""

from native_support import (
    PROFILE,
    ROW_SCOPE,
    SCOPE,
    D,
    blocked,
    dec,
    finding,
    result,
    scoped,
    start,
    unique,
    validate_schema,
)

METHOD = "annual_mutually_exclusive_decrement_cashflow"
SCHEMA = {
    "scope": SCOPE,
    "profile": PROFILE,
    "initial_policies": "positive",
    "projection_end_year": "integer",
    "years": [
        {
            **ROW_SCOPE,
            "year": "integer",
            "mortality_probability": "probability",
            "lapse_probability": "probability",
            "premium": "nonnegative",
            "expense_boy": "nonnegative",
            "death_benefit": "nonnegative",
            "surrender_benefit": "nonnegative",
            "survival_benefit": "nonnegative",
            "discount_rate": "number",
        }
    ],
    "terminal_benefit_per_survivor": "nonnegative",
    "terminal_source_ref": "ref",
}


def validate(doc):
    return validate_schema(doc, SCHEMA)


def evaluate(doc):
    d, f = start(doc, SCHEMA, METHOD)
    empty = {
        "method": METHOD,
        "projection": None,
        "pv_premiums": None,
        "pv_expenses": None,
        "pv_benefits": None,
        "pv_net_cashflow": None,
        "net_cashflow_margin": None,
        "price_approved": False,
        "capital_tax_and_reserves_modeled": False,
    }
    if blocked(f):
        return result(f, empty)
    unique(d["years"], "year", f)
    rows = sorted(d["years"], key=lambda x: D(str(x["year"])))
    if [D(str(r["year"])) for r in rows] != [D(i) for i in range(1, int(D(str(d["projection_end_year"]))) + 1)]:
        f.append(finding("projection_gap", "Years must be contiguous from 1 through projection_end_year"))
    if d["scope"]["currency"] == "NONE":
        f.append(finding("monetary_currency", "Pricing requires a monetary currency"))
    for r in rows:
        scoped(r, d["scope"], f)
        q, lapse = D(str(r["mortality_probability"])), D(str(r["lapse_probability"]))
        if q + lapse > 1:
            f.append(
                finding(
                    "decrement_sum",
                    "Mortality and lapse are unconditional mutually exclusive annual probabilities; sum exceeds one",
                    [r["source_ref"]],
                )
            )
        if D(str(r["discount_rate"])) <= -1:
            f.append(finding("discount_domain", "Annual forward discount rates must exceed -1", [r["source_ref"]]))
    if blocked(f):
        return result(f, empty)
    lives, discount, pp, pe, pb = D(str(d["initial_policies"])), D(1), D(0), D(0), D(0)
    projection = []
    for r in rows:
        opening = lives
        deaths = opening * D(str(r["mortality_probability"]))
        lapses = opening * D(str(r["lapse_probability"]))
        lives = opening - deaths - lapses
        premium, expense = opening * D(str(r["premium"])), opening * D(str(r["expense_boy"]))
        benefit = (
            deaths * D(str(r["death_benefit"]))
            + lapses * D(str(r["surrender_benefit"]))
            + lives * D(str(r["survival_benefit"]))
        )
        terminal = lives * D(str(d["terminal_benefit_per_survivor"])) if r is rows[-1] else D(0)
        pv_premium, pv_expense = premium * discount, expense * discount
        end_discount = discount / (1 + D(str(r["discount_rate"])))
        pv_benefit = (benefit + terminal) * end_discount
        pp, pe, pb = pp + pv_premium, pe + pv_expense, pb + pv_benefit
        projection.append(
            {
                "year": r["year"],
                "opening_policies": dec(opening),
                "expected_deaths": dec(deaths),
                "expected_lapses": dec(lapses),
                "closing_policies": dec(lives),
                "boy_premium": dec(premium),
                "boy_expense": dec(expense),
                "eoy_benefits": dec(benefit),
                "eoy_terminal_benefit": dec(terminal),
                "discount_boy": dec(discount),
                "discount_eoy": dec(end_discount),
                "pv_net_cashflow": dec(pv_premium - pv_expense - pv_benefit),
                "source_refs": sorted({r["source_ref"], d["terminal_source_ref"]}),
            }
        )
        discount = end_discount
    net = pp - pe - pb
    if net < 0:
        f.append(
            finding(
                "negative_net_cashflow",
                "Supplied cashflows have negative discounted net cashflow before omitted capital, tax and reserve effects",
                [r["source_ref"] for r in rows],
                "review",
            )
        )
    if pp == 0:
        f.append(
            finding(
                "zero_premiums",
                "No premium PV; cashflow margin is undefined",
                [r["source_ref"] for r in rows],
                "review",
            )
        )
    return result(
        f,
        {
            **empty,
            "projection": projection,
            "pv_premiums": dec(pp),
            "pv_expenses": dec(pe),
            "pv_benefits": dec(pb),
            "pv_net_cashflow": dec(net),
            "net_cashflow_margin": dec(net / pp if pp else None),
        },
    )
