"""Tax-lot and transition illustrations with conservative household wash-sale screening."""
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal

from wealth_contract import make_output, nonempty
from wealth_analysis import (cited, common, dated, finding, input_findings, money,
                            number, output_errors, precise, records, require)

SKILL = "tax-aware-investment-reviewer"
TREATMENTS = ("taxable", "tax-deferred", "tax-exempt")


def check(doc):
    common(doc)
    require(doc.get("currency") == "USD", "only supplied USD tax basis and prices supported")
    accounts = records(doc.get("accounts"), "account_id", "household account scope")
    known = {a["account_id"] for a in accounts}
    as_of = dated(doc["as_of"], "as_of")
    for account in accounts:
        require(account.get("tax_treatment") in TREATMENTS, "explicit account tax treatment required")
        require(nonempty(account.get("owner_relationship")), "account owner relationship required; include applicable spouse/IRA scope")
        require(type(account.get("history_complete")) is bool and type(account.get("forward_orders_reviewed")) is bool, "account history/forward-order review must be explicit")
        start, end = dated(account.get("history_from"), "history_from"), dated(account.get("history_through"), "history_through")
        require(start <= end <= as_of, "account history coverage must be ordered and not future-dated")
    scope = doc.get("scope_review")
    require(isinstance(scope, dict) and type(scope.get("household_scope_complete")) is bool, "explicit household scope review required")
    lots = records(doc.get("lots"), "lot_id", "tax lots")
    lot_ids = {lot["lot_id"] for lot in lots}
    by_lot = {lot["lot_id"]: lot for lot in lots}
    for lot in lots:
        require(lot.get("account_id") in known, "lot outside declared account scope")
        for key in ("security_id", "asset_class"):
            require(nonempty(lot.get(key)), f"lot.{key} required")
        for key in ("quantity", "unit_cost_basis", "unit_price"):
            number(lot.get(key), key, 0)
        require(number(lot["quantity"]) > 0, "lot quantity must be positive")
        require(dated(lot.get("acquired_on"), "acquired_on") <= as_of, "lot acquisition is future-dated")
        require(dated(lot.get("price_as_of"), "price_as_of") <= as_of, "lot price is future-dated")
        require(lot.get("tax_term") in ("short", "long", "unknown"), "tax_term must be supplied short, long or unknown")
    requested = dict.fromkeys(lot_ids, Decimal(0))
    for sale in records(doc.get("proposed_sales"), "sale_id", "proposed_sales", empty=True):
        require(sale.get("lot_id") in lot_ids, "sale references unknown lot")
        require(number(sale.get("quantity"), "sale quantity", 0) > 0, "sale quantity must be positive")
        number(sale.get("estimated_fees"), "estimated_fees", 0, 2)
        when = dated(sale.get("trade_date"), "trade_date")
        lot = by_lot[sale["lot_id"]]
        require(when >= dated(lot["acquired_on"], "acquired_on"), "sale cannot precede acquisition")
        require(when >= dated(lot["price_as_of"], "price_as_of"), "historical sale cannot use a post-sale quote; supply the contemporaneous pre-sale snapshot")
        requested[lot["lot_id"]] += number(sale["quantity"])
        require(requested[lot["lot_id"]] <= number(lot["quantity"]), "aggregate proposed sales exceed available lot quantity")
    records(doc.get("equivalence_map"), "security_id", "equivalence_map", empty=True)
    for row in doc["equivalence_map"]:
        require(nonempty(row.get("group_id")), "human-sourced equivalence group required")
    for buy in records(doc.get("purchases"), "purchase_id", "household purchases", empty=True):
        require(buy.get("account_id") in known, "purchase outside declared account scope")
        require(nonempty(buy.get("security_id")) and nonempty(buy.get("acquisition_lot_id")), "purchase security and acquisition lot identifiers required")
        require(number(buy.get("quantity"), "purchase quantity", 0) > 0, "purchase quantity must be positive")
        when = dated(buy.get("trade_date"), "purchase trade date")
        require(buy.get("lifecycle") in ("executed", "proposed", "cancelled"), "explicit purchase lifecycle required")
        require(buy["lifecycle"] != "executed" or when <= as_of, "executed purchase cannot be future-dated")
    policy = doc.get("tax_profile")
    require(isinstance(policy, dict), "tax_profile required")
    for key in ("version", "owner"):
        require(nonempty(policy.get(key)), f"tax_profile.{key} required")
    for key in ("short_term_rate_pct", "long_term_rate_pct"):
        require(number(policy.get(key), key, 0) <= 100, "illustrative tax rates must be 0..100 percent")
    for key in ("max_positive_gain_amount", "max_tax_reserve"):
        number(policy.get(key), key, 0, 2)
    require(type(policy.get("max_price_age_days")) is int and 0 <= policy["max_price_age_days"] <= 366, "explicit price freshness policy required")
    location = doc.get("location_policy")
    require(isinstance(location, dict) and nonempty(location.get("version")), "location_policy version required")
    for row in records(location.get("preferences"), "asset_class", "location preferences", empty=True):
        choices = row.get("preferred_tax_treatments")
        require(isinstance(choices, list) and choices and all(x in TREATMENTS for x in choices), "location preferences must identify supported account treatments")
        require(nonempty(row.get("rationale")), "location preference rationale required")


def compute(doc):
    check(doc)
    findings = input_findings(doc)
    accounts = {a["account_id"]: a for a in doc["accounts"]}
    lots = {lot["lot_id"]: lot for lot in doc["lots"]}
    as_of = dated(doc["as_of"], "as_of")
    profile = doc["tax_profile"]
    for key in ("scope_review", "tax_profile", "location_policy"):
        cited(doc[key], doc, key, findings)
    if not doc["scope_review"]["household_scope_complete"]:
        finding(findings, "household-scope-gap", "Applicable household/spouse/retirement account scope is incomplete")
    for account in accounts.values():
        cited(account, doc, account["account_id"], findings)
    equivalence = {}
    for row in doc["equivalence_map"]:
        if cited(row, doc, row["security_id"], findings):
            equivalence[row["security_id"]] = row["group_id"]
    prefs = {p["asset_class"]: p for p in doc["location_policy"]["preferences"]}
    lot_rows, location_rows = [], []
    for lot in doc["lots"]:
        cited(lot, doc, lot["lot_id"], findings)
        stale = (as_of - dated(lot["price_as_of"], "price_as_of")).days > profile["max_price_age_days"]
        if stale:
            finding(findings, "stale-price", f"{lot['lot_id']}: price exceeds the supplied freshness policy")
        value = number(lot["quantity"]) * number(lot["unit_price"])
        basis = number(lot["quantity"]) * number(lot["unit_cost_basis"])
        treatment = accounts[lot["account_id"]]["tax_treatment"]
        lot_rows.append({"lot_id": lot["lot_id"], "account_id": lot["account_id"], "market_value": money(value),
                         "cost_basis": money(basis), "unrealized_gain_loss": money(value - basis),
                         "loss_candidate_for_review": treatment == "taxable" and value < basis and not stale,
                         "source_ids": lot.get("source_ids", [])})
        pref = prefs.get(lot["asset_class"])
        if pref is None:
            finding(findings, "location-unassessed", f"{lot['asset_class']}: no supplied asset-location policy")
            state = "unknown"
        else:
            cited(pref, doc, f"location/{lot['asset_class']}", findings)
            state = "aligned-to-supplied-policy" if treatment in pref["preferred_tax_treatments"] else "review-exception"
            if state == "review-exception":
                finding(findings, "location-exception", f"{lot['lot_id']}: account treatment differs from supplied preference; no transfer recommendation made")
        location_rows.append({"lot_id": lot["lot_id"], "account_tax_treatment": treatment, "status": state, "policy": deepcopy(pref)})
    sale_rows, remaining = [], {lot: number(row["quantity"]) for lot, row in lots.items()}
    purchase_available = {row["purchase_id"]: number(row["quantity"]) for row in doc["purchases"]}
    gains, losses, reserve = Decimal(0), Decimal(0), Decimal(0)
    reserve_complete = True
    for purchase in doc["purchases"]:
        cited(purchase, doc, purchase["purchase_id"], findings)
        if purchase["security_id"] not in equivalence and purchase["lifecycle"] != "cancelled":
            finding(findings, "equivalence-unknown", f"{purchase['purchase_id']}: tax equivalence is not established")
    for sale in sorted(doc["proposed_sales"], key=lambda r: (r["trade_date"], r["sale_id"])):
        cited(sale, doc, sale["sale_id"], findings)
        lot = lots[sale["lot_id"]]
        quantity = number(sale["quantity"])
        require(quantity <= remaining[lot["lot_id"]], "aggregate proposed sales exceed available lot quantity")
        remaining[lot["lot_id"]] -= quantity
        trade_date = dated(sale["trade_date"], "trade_date")
        require(trade_date >= dated(lot["acquired_on"], "acquired_on"), "sale predates acquisition")
        gross = quantity * number(lot["unit_price"])
        net = gross - number(sale["estimated_fees"])
        pnl = net - quantity * number(lot["unit_cost_basis"])
        taxable = accounts[lot["account_id"]]["tax_treatment"] == "taxable"
        estimate = None
        overlaps = []
        if taxable:
            gains += max(pnl, 0)
            losses += min(pnl, 0)
            if lot["tax_term"] == "unknown":
                finding(findings, "tax-term-unknown", f"{sale['sale_id']}: holding-period treatment not established")
                reserve_complete = False
            else:
                rate = number(profile["short_term_rate_pct" if lot["tax_term"] == "short" else "long_term_rate_pct"])
                estimate = max(pnl, 0) * rate / 100
                reserve += estimate
            if pnl < 0:
                lower, upper = trade_date - timedelta(days=30), trade_date + timedelta(days=30)
                if upper > as_of:
                    finding(findings, "forward-window-open", f"{sale['sale_id']}: replacement purchases through {upper} are not yet knowable")
                for account in accounts.values():
                    if (not account["history_complete"] or dated(account["history_from"], "history") > lower
                            or dated(account["history_through"], "history") < min(as_of, upper)
                            or not account["forward_orders_reviewed"]):
                        finding(findings, "wash-coverage-gap", f"{sale['sale_id']}/{account['account_id']}: historical or known-forward purchase coverage incomplete")
                group = equivalence.get(lot["security_id"])
                if group is None:
                    finding(findings, "equivalence-unknown", f"{sale['sale_id']}: sold security equivalence is not established")
                available_to_match = quantity
                for buy in sorted(doc["purchases"], key=lambda b: (b["trade_date"], b["purchase_id"])):
                    if (buy["lifecycle"] == "cancelled" or buy["acquisition_lot_id"] == lot["lot_id"]
                            or not lower <= dated(buy["trade_date"], "purchase date") <= upper
                            or group is None or equivalence.get(buy["security_id"]) != group):
                        continue
                    matched = min(available_to_match, purchase_available[buy["purchase_id"]])
                    if matched <= 0:
                        continue
                    available_to_match -= matched
                    purchase_available[buy["purchase_id"]] -= matched
                    overlaps.append({"purchase_id": buy["purchase_id"], "account_id": buy["account_id"],
                                     "tax_treatment": accounts[buy["account_id"]]["tax_treatment"], "lifecycle": buy["lifecycle"],
                                     "potential_overlap_quantity": precise(matched), "source_ids": buy.get("source_ids", [])})
                if overlaps:
                    finding(findings, "potential-wash-sale", f"{sale['sale_id']}: household replacement exposure requires tax-professional review; no deductible-loss determination")
        sale_rows.append({"sale_id": sale["sale_id"], "lot_id": lot["lot_id"], "quantity": precise(quantity),
                          "gross_proceeds": money(gross), "net_proceeds": money(net), "gain_loss": money(pnl),
                          "taxable_account": taxable, "tax_term": lot["tax_term"],
                          "positive_gain_tax_reserve": money(estimate) if estimate is not None else None,
                          "potential_replacements": overlaps, "source_ids": sale.get("source_ids", [])})
    if gains > number(profile["max_positive_gain_amount"]):
        finding(findings, "gain-budget", "Positive proposed gains exceed the supplied transition budget")
    if reserve_complete and reserve > number(profile["max_tax_reserve"]):
        finding(findings, "tax-reserve-budget", "Illustrative positive-gain tax reserve exceeds the supplied budget")
    result = {"input_snapshot": deepcopy(doc), "tax_lots": lot_rows, "proposed_sales": sale_rows,
              "transition": {"positive_taxable_gains": money(gains), "taxable_losses_before_wash_review": money(losses),
                             "net_taxable_gain_loss_before_wash_review": money(gains + losses),
                             "positive_gain_tax_reserve": money(reserve) if reserve_complete else None,
                             "loss_tax_benefit": "not-estimated", "deductible_loss": "not-determined"},
              "asset_location": location_rows, "execution_status": "not-executed", "basis_adjustments": "not-posted"}
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    return output_errors(out, SKILL, compute)
