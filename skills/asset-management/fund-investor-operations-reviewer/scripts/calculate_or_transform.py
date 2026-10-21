"""Supplied dealing timetable and eligibility evidence; indicative units, never acceptance."""
from datetime import datetime
from decimal import Decimal
from foundation_contract import D, date_value, exact, ratio, validate_common, validate_referenced_sources, validate_actual_date, finish, cli_compute

SKILL = "fund-investor-operations-reviewer"


def timestamp(value):
    if not isinstance(value, str): raise ValueError("timezone-aware ISO timestamp required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None: raise ValueError("timezone-aware ISO timestamp required")
    return result


@exact
def compute(doc):
    errors = validate_common(doc) + validate_referenced_sources(doc)
    if errors: raise ValueError("; ".join(errors))
    if any(date_value(source["as_of"]) > date_value(source["known_at"]) for source in doc["sources"]): raise ValueError("historical observation source cannot be known before its economic as_of")
    if doc["currency"] == "not-applicable": raise ValueError("supplied monetary/return currency required")
    if doc.get("mode") != "dealing_review": raise ValueError("only dealing_review mode implemented")
    cutoff, valuation = timestamp(doc["cutoff_at"]), timestamp(doc["valuation_at"])
    if cutoff > valuation or valuation.date() > date_value(doc["as_of"]) or not doc.get("dealing_terms_source_ref"): raise ValueError("invalid supplied cutoff/valuation timetable or missing source")
    orders, ids, rows, issues = doc["orders"], set(), [], []
    if not isinstance(orders, list) or not 1 <= len(orders) <= 1000: raise ValueError("1..1000 orders required")
    for order in orders:
        oid = order["order_id"]
        if not isinstance(oid, str) or not oid or oid in ids: raise ValueError("unique order_id required")
        ids.add(oid)
        received = timestamp(order["received_at"])
        if received.astimezone(valuation.tzinfo).date() > date_value(doc["as_of"]) or not order.get("source_ref"): raise ValueError("invalid receipt date/source")
        validate_actual_date(doc, received.astimezone(valuation.tzinfo).date().isoformat(), order["source_ref"])
        if order["type"] not in {"subscription", "redemption"}: raise ValueError("unsupported dealing type")
        eligibility = order.get("aml_evidence_status")
        if eligibility not in {"supplied-cleared", "pending", "blocked", "unknown"}: raise ValueError("explicit AML evidence status required")
        if not order.get("aml_source_ref") or not order.get("share_class_id"): raise ValueError("AML source and share class required")
        fee = D(order["fee_amount"])
        if fee < 0: raise ValueError("negative dealing fee unsupported")
        item = {"order_id": oid, "share_class_id": order["share_class_id"], "type": order["type"], "on_time": received <= cutoff,
                "supplied_aml_evidence_status": eligibility, "accepted": False, "indicative_units": None, "indicative_net_cash": None}
        reasons = []
        if received > cutoff: reasons.append("late-for-supplied-cutoff; next-dealing-date review required")
        if eligibility != "supplied-cleared": reasons.append("eligibility evidence unresolved; no subscription/redemption acceptance")
        if date_value(order["aml_valid_until"]) < valuation.date(): reasons.append("AML evidence expired before dealing valuation")
        if order.get("nav_per_unit") is None: reasons.append("NAV unavailable; indicative amount not calculated")
        else:
            nav = D(order["nav_per_unit"])
            if nav <= 0 or not order.get("nav_source_ref") or timestamp(order["nav_valuation_at"]) != valuation: raise ValueError("positive NAV bound to exact supplied valuation timestamp/source required")
            validate_actual_date(doc, valuation.date().isoformat(), order["nav_source_ref"])
        amount = D(order["subscription_cash"] if order["type"] == "subscription" else order["redemption_units"])
        if amount <= 0: raise ValueError("positive order cash/units required")
        if not reasons:
            if order["type"] == "subscription":
                cash = amount - fee
                if cash <= 0: raise ValueError("subscription fee consumes supplied cash")
                units = Decimal(ratio(cash, nav, 8))
                item.update(indicative_units=str(units), indicative_net_cash=str(cash), unit_rounding_cash_residual=str(cash - units * nav))
            else:
                cash = amount * nav - fee
                if cash < 0: raise ValueError("redemption fee exceeds proceeds")
                item.update(indicative_units=str(amount), indicative_net_cash=str(cash))
        item["review_status"] = "exceptions" if reasons else "indicative-calculation-only"
        item["exceptions"] = reasons; issues += [oid + ": " + reason for reason in reasons]; rows.append(item)
    return finish(doc, SKILL, "supplied-dealing-timetable-v1", {"orders": rows, "cutoff_at": doc["cutoff_at"], "valuation_at": doc["valuation_at"]}, issues=issues,
                  limitations=["Supplied fund/class timetable and eligibility assertions only; no jurisdictional cutoff, business-day calendar or AML determination.", "Late/unresolved orders have no indicative pricing; no backdating, acceptance, units issuance/cancellation or cash transfer.", "Subscription units rounded to8 decimal places; residual cash disclosed. Swing pricing, dilution adjustments, gates and tax require separate methods."],
                  handoffs=["fund-accounting-preparer", "fund-liquidity-assessor"])


if __name__ == "__main__": cli_compute(compute)
