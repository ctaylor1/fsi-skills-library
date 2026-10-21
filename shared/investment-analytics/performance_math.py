"""Bounded annual ACT/365 XIRR; shared K08/K11 method, not source authentication."""
from collections import defaultdict
from decimal import Decimal, localcontext


def conventional_xirr(cashflows):
    """One negative-to-positive sign change after same-day netting; no guessed root."""
    grouped = defaultdict(Decimal)
    for day, amount in cashflows:
        if not isinstance(amount, Decimal) or not amount.is_finite():
            raise ValueError("XIRR cash amounts must be finite Decimal values")
        grouped[day] += amount
    ordered = sorted((day, amount) for day, amount in grouped.items() if amount)
    metadata = {"day_count": "ACT/365", "rate_unit": "annual_decimal",
                "same_day_flows": "netted", "root_domain": "[-0.999999, 1000000]",
                "method": "conventional-sign-change bisection; numerical approximation"}
    def unavailable(reason):
        return {**metadata, "status": "unavailable", "annual_xirr": None, "reason": reason}
    if len(ordered) < 2 or ordered[0][1] >= 0 or ordered[-1][1] <= 0:
        return unavailable("requires negative investment followed by positive realization on a later date")
    signs = [amount > 0 for _, amount in ordered]
    if sum(a != b for a, b in zip(signs, signs[1:])) != 1:
        return unavailable("nonconventional signs: multiple or absent roots are possible; no root selected")
    if (ordered[-1][0] - ordered[0][0]).days > 36525:
        return unavailable("cash-flow horizon exceeds 100-year supported bound")
    # Fractional powers and roots are approximate; kept separate from exact cash arithmetic.
    with localcontext() as ctx:
        ctx.prec = 80
        from decimal import Inexact, Rounded
        ctx.traps[Inexact] = False
        ctx.traps[Rounded] = False
        times = [(Decimal((day - ordered[0][0]).days) / Decimal(365), amount)
                 for day, amount in ordered]
        def npv(rate):
            return sum((amount / ((1 + rate) ** years) for years, amount in times), Decimal(0))
        low, high = Decimal("-0.999999"), Decimal("1000000")
        f_low, f_high = npv(low), npv(high)
        if f_low < 0 or f_high > 0:
            return unavailable("unique conventional root is outside declared numerical search domain")
        tolerance = max(sum(abs(amount) for _, amount in times), Decimal(1)) * Decimal("1e-24")
        for iteration in range(1, 513):
            mid = (low + high) / 2
            value = npv(mid)
            if abs(value) <= tolerance and high - low <= Decimal("1e-24"):
                return {**metadata, "status": "calculated", "annual_xirr": format(mid, ".24f"),
                        "iterations": iteration, "unrounded_npv_residual": str(value),
                        "npv_absolute_tolerance": str(tolerance),
                        "uniqueness_basis": "one negative-to-positive sign change after date aggregation"}
            if value > 0:
                low = mid
            else:
                high = mid
        return unavailable("solver did not meet residual and interval tolerances")
