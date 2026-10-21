"""Cash-dividend and stock-split entitlement workpaper from supplied eligible positions."""
from decimal import Decimal
from foundation_contract import D, date_value, exact, ratio, validate_common, validate_referenced_sources, validate_actual_date, finish, cli_compute

SKILL = "investment-asset-servicing-reviewer"


@exact
def compute(doc):
    errors = validate_common(doc) + validate_referenced_sources(doc)
    if errors: raise ValueError("; ".join(errors))
    if any(date_value(source["as_of"]) > date_value(source["known_at"]) for source in doc["sources"]): raise ValueError("historical observation source cannot be known before its economic as_of")
    if doc["currency"] == "not-applicable": raise ValueError("supplied monetary/return currency required")
    if doc.get("mode") != "entitlements": raise ValueError("only entitlements mode implemented")
    events, ids, rows, issues = doc["events"], set(), [], []
    if not isinstance(events, list) or not 1 <= len(events) <= 1000: raise ValueError("1..1000 events required")
    when = date_value(doc["as_of"])
    for event in events:
        eid = event["event_id"]
        if not isinstance(eid, str) or not eid or eid in ids: raise ValueError("unique event_id required")
        ids.add(eid)
        record, payable = date_value(event["record_date"]), date_value(event["payable_date"])
        if date_value(event["position_date"]) != record or not record <= when or payable < record: raise ValueError("eligible position date must equal known record date; payable precedes neither record nor entitlement")
        for ref in ("event_source_ref", "position_source_ref"):
            if not event.get(ref): raise ValueError(ref + " required")
        validate_actual_date(doc, event["position_date"], event["position_source_ref"])
        quantity, tolerance = D(event["eligible_quantity"]), D(event["tolerance"])
        if quantity < 0 or tolerance < 0: raise ValueError("negative quantities/tolerances unsupported")
        item = {"event_id": eid, "type": event["type"], "record_date": str(record), "payable_date": str(payable)}
        if event["type"] == "cash_dividend":
            rate, withholding = D(event["cash_per_share"]), D(event["withholding_rate"])
            if rate < 0 or not 0 <= withholding <= 1: raise ValueError("cash/withholding rate outside supported bounds")
            gross = quantity * rate; tax = gross * withholding; expected = gross - tax
            item.update(gross_cash=str(gross), supplied_rate_withholding=str(tax), expected_net_cash=str(expected), measurement_unit=doc["currency"])
        elif event["type"] == "stock_split":
            numerator, denominator = D(event["new_shares"]), D(event["old_shares"])
            if numerator <= 0 or denominator <= 0 or numerator != int(numerator) or denominator != int(denominator): raise ValueError("split ratio requires positive integer numerator/denominator")
            total = Decimal(ratio(quantity * numerator, denominator, 24))
            if event.get("fractional_policy") != "preserve-entitlement": raise ValueError("only preserve-entitlement implemented; no cash-in-lieu or rounding-election engine")
            expected = total - quantity
            item.update(post_split_total_units=str(total), expected_additional_units=str(expected), measurement_unit="security-units", fractional_entitlement=str(total - Decimal(int(total))))
        else: raise ValueError("unsupported corporate action; only cash_dividend and stock_split implemented")
        received = event.get("received_amount")
        if received is None:
            item.update(received=None, difference=None, reconciliation_status="due-unreceived" if when >= payable else "not-yet-due")
            if when >= payable: issues.append(eid + ": entitlement due but received evidence unavailable")
        else:
            if not event.get("receipt_source_ref") or not record <= date_value(event["received_date"]) <= when: raise ValueError("dated receipt source evidence required")
            validate_actual_date(doc, event["received_date"], event["receipt_source_ref"])
            received = D(received)
            if event["type"] == "cash_dividend" and received < 0: raise ValueError("negative cash receipt unsupported")
            difference = received - expected
            item.update(received=str(received), difference=str(difference), reconciliation_status="within-tolerance" if abs(difference) <= tolerance else "exception")
            if abs(difference) > tolerance: issues.append(eid + ": receipt differs from entitlement beyond supplied tolerance")
        rows.append(item)
    return finish(doc, SKILL, "supplied-record-date-entitlements-v1", {"events": rows}, issues=issues,
                  limitations=["Eligible quantities and event terms are supplied; trade/ex-date, market-claim and beneficial-owner entitlement are not inferred.", "Withholding rate is supplied arithmetic, not a tax/legal determination. No elections, custody instructions or payment execution.", "Split ratios rounded to24 decimal places; fractional cash-in-lieu and mandatory/voluntary reorganizations require specialist workflow."],
                  handoffs=["investment-book-reconciler", "fund-accounting-preparer"])


if __name__ == "__main__": cli_compute(compute)
