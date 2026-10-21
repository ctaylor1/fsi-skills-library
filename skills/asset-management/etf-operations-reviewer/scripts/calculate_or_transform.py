"""Supplied ETF creation/redemption basket control; never order or settlement execution."""
from datetime import datetime
from decimal import Decimal
from foundation_contract import D, date_value, exact, ratio, validate_common, validate_referenced_sources, validate_actual_date, finish, cli_compute

SKILL = "etf-operations-reviewer"


def timestamp(value):
    if not isinstance(value, str): raise ValueError("timezone-aware ISO timestamp required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None: raise ValueError("timezone-aware ISO timestamp required")
    return result


@exact
def compute(doc):
    if isinstance(doc,dict) and "extension" in doc:
        from specialized_basket import compute as compute_extension
        return compute_extension(doc)
    errors = validate_common(doc) + validate_referenced_sources(doc)
    if errors: raise ValueError("; ".join(errors))
    if any(date_value(source["as_of"]) > date_value(source["known_at"]) for source in doc["sources"]): raise ValueError("historical observation source cannot be known before its economic as_of")
    if doc["currency"] == "not-applicable": raise ValueError("supplied monetary/return currency required")
    issues = []
    if doc.get("mode") == "basket_control":
        if doc["direction"] not in {"creation", "redemption"}: raise ValueError("creation/redemption direction required")
        size, units = D(doc["creation_unit_size"]), D(doc["creation_units"])
        if size <= 0 or units <= 0 or size != int(size) or units != int(units): raise ValueError("positive integral creation unit size/count required")
        cash, fee, tolerance = D(doc["cash_per_creation_unit"]), D(doc["transaction_fee"]), D(doc["value_tolerance"])
        if fee < 0 or tolerance < 0: raise ValueError("negative fee/tolerance unsupported")
        for ref in ("basket_source_ref", "nav_source_ref", "ap_source_ref", "dealing_terms_source_ref"):
            if not doc.get(ref): raise ValueError(ref + " required")
        received, cutoff = timestamp(doc["order_received_at"]), timestamp(doc["cutoff_at"])
        if received.astimezone(cutoff.tzinfo).date() > date_value(doc["as_of"]): raise ValueError("order receipt occurs after as_of")
        validate_actual_date(doc, received.astimezone(cutoff.tzinfo).date().isoformat(), doc["basket_source_ref"])
        if received > cutoff: issues.append("Order is late for the supplied ETF cutoff; no acceptance")
        if doc["ap_status"] not in {"supplied-active", "unknown", "expired"}: raise ValueError("unsupported AP agreement evidence status")
        if doc["ap_status"] != "supplied-active" or date_value(doc["ap_valid_until"]) < received.astimezone(cutoff.tzinfo).date(): issues.append("AP agreement status is unresolved or expired")
        if doc["basket_type"] not in {"standard", "custom"}: raise ValueError("explicit standard/custom basket required")
        if doc["basket_type"] == "custom":
            if doc.get("custom_review_status") not in {"supplied-approved", "pending", "unknown"} or not doc.get("custom_review_source_ref"): raise ValueError("custom basket requires explicit review evidence/source")
            if doc["custom_review_status"] != "supplied-approved": issues.append("Custom basket review remains unresolved")
        components = doc["components"]
        if not isinstance(components, list) or len(components) > 1000: raise ValueError("0..1000 basket components required; empty is cash-only")
        total, ids, rows, missing = Decimal(0), set(), [], []
        for row in components:
            if not row["instrument_id"] or row["instrument_id"] in ids or not row.get("source_ref"): raise ValueError("unique instrument and source required")
            ids.add(row["instrument_id"]); quantity = D(row["quantity_per_creation_unit"])
            if quantity < 0: raise ValueError("short/signed basket constituents unsupported")
            if row.get("price") is None:
                value = None; missing.append(row["instrument_id"])
            else:
                price = D(row["price"])
                if price <= 0: raise ValueError("positive same-currency component price required")
                validate_actual_date(doc, doc["as_of"], row["source_ref"])
                value = quantity * price; total += value
            rows.append({"instrument_id": row["instrument_id"], "total_quantity": str(quantity * units), "value_per_creation_unit": str(value) if value is not None else None})
        nav = D(doc["nav_per_share"]) if doc.get("nav_per_share") is not None else None
        if nav is not None: validate_actual_date(doc, doc["as_of"], doc["nav_source_ref"])
        if nav is not None and nav <= 0: raise ValueError("positive supplied NAV/share required")
        if missing: issues.append("Unpriced basket constituents: " + ", ".join(missing))
        if nav is None: issues.append("NAV unavailable; basket control unavailable")
        difference = total + cash - size * nav if not missing and nav is not None else None
        if difference is not None and abs(difference) > tolerance: issues.append("Basket/cash versus NAV value exceeds supplied per-creation-unit tolerance")
        ap_cash = cash * units + fee if doc["direction"] == "creation" else cash * units - fee
        result = {"direction": doc["direction"], "total_etf_shares": str(size * units), "component_transfers": rows,
                  "basket_securities_per_creation_unit": str(total) if not missing else None,
                  "cash_per_creation_unit": str(cash), "nav_value_per_creation_unit": str(size * nav) if nav is not None else None,
                  "value_difference_per_creation_unit": str(difference) if difference is not None else None,
                  "within_supplied_tolerance": abs(difference) <= tolerance if difference is not None else None,
                  "indicative_ap_cash": str(ap_cash), "ap_cash_convention": "AP pays on creation; AP receives on redemption; negative reverses direction; fee is outside NAV basket tie-out",
                  "ap_agreement_status": doc["ap_status"], "accepted": False, "settlement_performed": False}
    elif doc.get("mode") == "secondary_market":
        nav, market, bid, ask = (D(doc[k]) for k in ("nav_per_share", "market_price", "bid", "ask"))
        if min(nav, market, bid, ask) <= 0 or bid > ask: raise ValueError("positive prices and noncrossed quote required")
        for ref in ("nav_source_ref", "quote_source_ref"):
            if not doc.get(ref): raise ValueError(ref + " required")
        if date_value(doc["nav_date"]) != date_value(doc["quote_date"]) or doc["nav_date"] != doc["as_of"]: raise ValueError("same-as_of NAV and quote dates required")
        validate_actual_date(doc, doc["nav_date"], doc["nav_source_ref"])
        validate_actual_date(doc, doc["quote_date"], doc["quote_source_ref"])
        result = {"premium_discount": ratio(market - nav, nav, 12), "quoted_spread_to_midpoint": ratio(2 * (ask - bid), ask + bid, 12), "ratio_unit": "decimal", "execution_performed": False}
    else: raise ValueError("mode must be basket_control or secondary_market")
    return finish(doc, SKILL, "supplied-etf-control-" + doc["mode"] + "-v1", result, issues=issues,
                  limitations=["Same-currency supplied cash/securities and NAV only; no FX, derivative valuation, authorized-participant authentication or settlement engine.", "Basket/timing/custom-review assertions do not determine Rule6c-11 or UCITS applicability or grant acceptance/execution.", "Secondary-market ratios rounded to12 places; no historical premium/disclosure or trading-cost certification."], handoffs=["index-portfolio-reviewer", "fund-accounting-preparer", "fund-investor-operations-reviewer"])


if __name__ == "__main__": cli_compute(compute)
