"""R4 transition planning only. Reconcile quantity, cash and lot arithmetic; never execute."""
import math
from collections import defaultdict
from copy import deepcopy
from review_base import EPS, Review, numeric_fields, require_objects, rows, upstream_errors, validate_artifact
from wealth_contract import input_hash, iso_date, make_output, nonempty, validate_envelope

SKILL = "portfolio-rebalancing-assistant"
LIMITS = ("max_order_notional", "max_sell_turnover", "minimum_cash", "max_position_weight", "drift_tolerance_weight")


def validate_input(doc):
    errors = validate_envelope(doc)
    if not isinstance(doc, dict):
        return errors
    errors += upstream_errors(doc)
    require_objects(doc, ("account", "portfolio", "target", "policy", "intent"), errors)
    for field in ("approval", "execution", "authorization_tokens"):
        if field in doc:
            errors.append(f"{field}: legacy execution/approval inputs are not supported in this draft-only package")
    account, port, target, policy, intent = (doc.get(k) for k in ("account", "portfolio", "target", "policy", "intent"))
    if isinstance(account, dict):
        for field in ("account_id", "currency"):
            if not nonempty(account.get(field)):
                errors.append(f"account.{field} required")
        if account.get("taxable") is not None and not isinstance(account["taxable"], bool):
            errors.append("account.taxable must be boolean or null")
    if isinstance(port, dict):
        numeric_fields(port, ("cash", "reported_total_value"), errors, "portfolio")
        if port.get("positions_complete") is not None and not isinstance(port["positions_complete"], bool):
            errors.append("positions_complete must be boolean or null")
        lot_ids = set()
        for position in rows(port.get("positions"), "security_id", errors, "positions"):
            numeric_fields(position, ("quantity", "reported_market_value", "reported_cost_basis"), errors, "position")
            for lot in rows(position.get("lots"), "lot_id", errors, "lots"):
                if nonempty(lot.get("lot_id")) and lot["lot_id"] in lot_ids:
                    errors.append("lot_id must be unique across the account")
                if nonempty(lot.get("lot_id")):
                    lot_ids.add(lot["lot_id"])
                numeric_fields(lot, ("quantity", "cost_basis"), errors, "lot")
                if lot.get("acquired_on") is not None and not isinstance(lot["acquired_on"], str):
                    errors.append("lot.acquired_on must be an ISO date string or null")
    for security in rows(doc.get("universe"), "security_id", errors, "universe", 1):
        numeric_fields(security, ("price", "quantity_increment", "fee_bps", "fixed_fee"), errors, "universe")
        if security.get("tax_identity_group") is not None and not nonempty(security["tax_identity_group"]):
            errors.append("tax_identity_group must be a nonempty string or null")
    if isinstance(target, dict):
        numeric_fields(target, ("cash_weight",), errors, "target", 1)
        for row in rows(target.get("allocations"), "security_id", errors, "target allocations"):
            numeric_fields(row, ("weight",), errors, "target allocation", 1)
    if isinstance(policy, dict):
        numeric_fields(policy, LIMITS, errors, "policy")
        for restriction in rows(policy.get("restrictions"), "security_id", errors, "restrictions"):
            for key in ("buy_allowed", "sell_allowed"):
                if restriction.get(key) is not None and not isinstance(restriction[key], bool):
                    errors.append(f"restriction.{key} must be boolean or null")
    if isinstance(intent, dict):
        if intent.get("mode") not in ("generate", "validate"):
            errors.append("intent.mode must be generate or validate")
        if intent.get("lot_selection") not in ("oldest-first", "specified"):
            errors.append("intent.lot_selection must be explicitly oldest-first or specified")
        if intent.get("mode") == "generate" and intent.get("lot_selection") != "oldest-first":
            errors.append("generated plans require an explicit oldest-first lot selection convention")
        if intent.get("settlement_policy") not in ("same-day-netting", "prefund-buys"):
            errors.append("intent.settlement_policy must explicitly select same-day-netting or prefund-buys")
        numeric_fields(intent, ("transaction_cost_budget",), errors, "intent")
        if iso_date(intent.get("trade_date")) is None:
            errors.append("intent.trade_date must be an ISO date")
        if intent.get("mode") == "validate":
            for trade in rows(doc.get("trades"), "trade_id", errors, "trades"):
                if not nonempty(trade.get("security_id")) or trade.get("side") not in ("buy", "sell"):
                    errors.append("each trade requires security_id and buy/sell side")
                numeric_fields(trade, ("quantity", "fee_amount"), errors, "trade")
                for allocation in rows(trade.get("lot_allocations"), "lot_id", errors, "trade lot allocations"):
                    numeric_fields(allocation, ("quantity",), errors, "trade lot allocation")
                if intent.get("lot_selection") == "oldest-first" and trade.get("lot_allocations"):
                    errors.append("oldest-first mode requires empty caller lot allocations; use specified to preserve choices")
        elif doc.get("trades"):
            errors.append("generate mode does not accept a caller trade list; use validate mode")
    return errors


def compute(doc):
    errors = validate_input(doc)
    if errors:
        raise ValueError("; ".join(errors))
    r = Review(doc)
    account, port, target, policy, intent = (doc[k] for k in ("account", "portfolio", "target", "policy", "intent"))
    for obj, label in ((account, "account"), (port, "portfolio"), (target, "target"), (intent, "intent")):
        r.source(obj, label)
    r.policy(policy, "policy")
    for key in ("target_id", "version", "selection_reference"):
        r.text(target, key, "target")
    r.text(intent, "reason", "intent")
    limits = {key: r.num(policy, key, "policy") for key in LIMITS}
    for key in ("max_sell_turnover", "max_position_weight", "drift_tolerance_weight"):
        if limits[key] is not None and limits[key] > 1:
            r.gap("policy-range", f"{key}: use fractional weights between zero and one")
    budget = r.num(intent, "transaction_cost_budget", "intent")
    trade_date = iso_date(intent["trade_date"])
    if trade_date < iso_date(doc["as_of"]):
        r.gap("trade-date", "Proposed trade date precedes the request snapshot")
    cash = r.num(port, "cash", "portfolio")
    reported_total = r.num(port, "reported_total_value", "portfolio", True)
    if port.get("positions_complete") is not True:
        r.gap("positions-incomplete", "Complete positions snapshot is not recorded; absent securities cannot be treated as zero")
    taxable = account.get("taxable")
    if not isinstance(taxable, bool):
        r.gap("tax-context", "Account tax context is unknown")
    universe = {row["security_id"]: row for row in doc["universe"]}
    prices, increments, fees = {}, {}, {}
    for sid, security in universe.items():
        r.source(security, sid)
        prices[sid] = r.num(security, "price", sid, True)
        increments[sid] = r.num(security, "quantity_increment", sid, True)
        fees[sid] = (r.num(security, "fee_bps", sid), r.num(security, "fixed_fee", sid))
        if security.get("currency") != account["currency"]:
            r.gap("currency-mismatch", f"{sid}: quote currency differs from account; no FX conversion")
        quote_on = iso_date(security.get("quote_on"))
        if quote_on is None or quote_on > iso_date(doc["as_of"]):
            r.gap("quote-date", f"{sid}: quote date missing, invalid or future")
    positions = {row["security_id"]: row for row in port["positions"]}
    quantities, lot_map = {}, {}
    position_values, costs = {}, {}
    pre_evaluable = cash is not None and port.get("positions_complete") is True
    for sid, position in positions.items():
        r.source(position, f"position {sid}")
        quantity = r.num(position, "quantity", sid)
        quantities[sid] = quantity
        if sid not in universe:
            r.gap("unknown-security", f"{sid}: holding is missing from supplied pricing universe")
        price = prices.get(sid)
        market_value = quantity * price if quantity is not None and price is not None else None
        position_values[sid] = market_value
        reported_mv = r.num(position, "reported_market_value", sid)
        if market_value is None:
            pre_evaluable = False
        elif reported_mv is not None and abs(reported_mv - market_value) > 0.01:
            r.gap("position-reconciliation", f"{sid}: quantity times quote does not reconcile to recorded market value", position.get("source_ids"))
        lot_quantities, lot_costs = [], []
        for lot in position["lots"]:
            lid = lot["lot_id"]
            r.source(lot, f"lot {lid}")
            lq, lc = r.num(lot, "quantity", lid, True), r.num(lot, "cost_basis", lid)
            acquired = iso_date(lot.get("acquired_on"))
            if acquired is None or acquired > iso_date(doc["as_of"]):
                r.gap("lot-date", f"{lid}: acquired_on missing, invalid or future")
            lot_map[lid] = {**lot, "security_id": sid, "quantity": lq, "cost_basis": lc}
            lot_quantities.append(lq)
            lot_costs.append(lc)
        if taxable is True and not position["lots"] and quantity:
            r.gap("lot-gap", f"{sid}: taxable holding has no lot-level basis")
        if position["lots"] and quantity is not None and all(v is not None for v in lot_quantities):
            if abs(sum(lot_quantities) - quantity) > EPS:
                r.gap("lot-reconciliation", f"{sid}: lot quantities do not reconcile to the position")
        total_basis = sum(lot_costs) if position["lots"] and all(v is not None for v in lot_costs) else None
        costs[sid] = total_basis
        reported_basis = position.get("reported_cost_basis")
        if reported_basis is not None and total_basis is not None and abs(reported_basis - total_basis) > 0.01:
            r.gap("lot-reconciliation", f"{sid}: lot basis does not reconcile to recorded position basis")
    pre_nav = cash + sum(position_values.values()) if pre_evaluable else None
    if pre_nav is not None and pre_nav <= 0:
        r.gap("portfolio-value", "Portfolio net asset value must be positive")
        pre_nav = None
    if pre_nav is not None and reported_total is not None and abs(pre_nav - reported_total) > 0.01:
        r.gap("portfolio-reconciliation", "Cash plus position values do not reconcile to recorded total value")
    targets = {}
    for allocation in target["allocations"]:
        sid = allocation["security_id"]
        r.source(allocation, f"target {sid}")
        targets[sid] = r.num(allocation, "weight", f"target {sid}")
        if sid not in universe:
            r.gap("unknown-target-security", f"{sid}: target is not in the supplied universe")
    target_cash = r.num(target, "cash_weight", "target")
    target_evaluable = target_cash is not None and all(v is not None for v in targets.values())
    target_sum = target_cash + sum(targets.values()) if target_evaluable else None
    if target_sum is None or abs(target_sum - 1) > EPS:
        r.gap("target-reconciliation", "Target security weights plus cash must reconcile to one")
        target_evaluable = False
    if set(positions) - set(targets):
        r.gap("target-coverage", "Every existing position needs an explicit target, including zero for exits")
        target_evaluable = False
    restrictions = {row["security_id"]: row for row in policy["restrictions"]}
    for sid in sorted(set(positions) | set(targets)):
        restriction = restrictions.get(sid)
        if restriction is None:
            r.gap("restriction-gap", f"{sid}: explicit buy/sell restriction review missing")
        else:
            r.source(restriction, f"restrictions {sid}")
            for key in ("buy_allowed", "sell_allowed"):
                if not isinstance(restriction.get(key), bool):
                    r.gap("restriction-gap", f"{sid}: {key} unknown")
    def fee_for(sid, notional):
        bps, fixed = fees.get(sid, (None, None))
        return notional * bps / 10000 + fixed if bps is not None and fixed is not None else None

    trades = []
    if intent["mode"] == "generate":
        ready = pre_nav is not None and target_evaluable and budget is not None and budget < pre_nav
        ready = ready and all(sid in universe and prices[sid] is not None and increments[sid] is not None for sid in targets)
        if not ready:
            r.gap("generation-unavailable", "Target, prices, increments, portfolio or cost reserve incomplete; no trades generated")
        else:
            for sid in sorted(targets):
                current = quantities.get(sid, 0.0)
                if current is None:
                    continue
                desired = math.floor(((pre_nav - budget) * targets[sid] / prices[sid] + EPS) / increments[sid]) * increments[sid]
                delta = desired - current
                if abs(delta) <= EPS:
                    continue
                side, quantity = ("buy", delta) if delta > 0 else ("sell", -delta)
                trades.append({"trade_id": f"draft-{side}-{sid}", "security_id": sid, "side": side,
                               "quantity": round(quantity, 12), "fee_amount": fee_for(sid, quantity * prices[sid]),
                               "settles_on": universe[sid].get("settles_on"), "lot_allocations": [],
                               "source_ids": deepcopy(universe[sid].get("source_ids"))})
            trades.sort(key=lambda t: (0 if t["side"] == "sell" else 1, t["security_id"]))
    else:
        trades = deepcopy(doc["trades"])
    traded_ids = {trade["security_id"] for trade in trades}
    if traded_ids - set(targets):
        r.gap("target-coverage", f"Traded securities need explicit targets: {sorted(traded_ids - set(targets))}")
    allocated_lots = defaultdict(float)
    running_quantities = {sid: quantities.get(sid, 0.0) if port.get("positions_complete") is True else quantities.get(sid)
                          for sid in set(universe) | set(positions)}
    total_sells = total_buys = total_fees = 0.0
    trade_evaluable = pre_nav is not None
    ledger = defaultdict(lambda: {"buys": 0.0, "sells": 0.0, "fees": 0.0})
    trade_rows, gains = [], []
    for trade in trades:
        tid, sid, side = trade["trade_id"], trade["security_id"], trade["side"]
        r.source(trade, tid)
        quantity = r.num(trade, "quantity", tid, True)
        price = prices.get(sid)
        if sid not in universe:
            r.gap("unknown-trade-security", f"{tid}: security not in supplied universe")
        increment = increments.get(sid)
        if quantity is not None and increment is not None and abs(quantity / increment - round(quantity / increment)) > EPS:
            r.gap("quantity-increment", f"{tid}: quantity violates instrument increment")
        notional = quantity * price if quantity is not None and price is not None else None
        computed_fee = fee_for(sid, notional) if notional is not None else None
        supplied_fee = r.num(trade, "fee_amount", tid)
        if computed_fee is not None and supplied_fee is not None and abs(computed_fee - supplied_fee) > 0.01:
            r.gap("fee-reconciliation", f"{tid}: supplied fee differs from sourced bps and fixed components")
        settlement = iso_date(trade.get("settles_on"))
        if settlement is None or settlement < trade_date:
            r.gap("settlement-date", f"{tid}: settlement missing or before proposed trade")
            trade_evaluable = False
        if notional is not None and limits["max_order_notional"] is not None and notional > limits["max_order_notional"] + EPS:
            r.gap("order-limit", f"{tid}: notional exceeds supplied planning limit")
        restriction = restrictions.get(sid, {})
        if restriction.get(side + "_allowed") is not True:
            r.gap("restricted-transition", f"{tid}: {side} permission is false or unknown")
        available = running_quantities.get(sid)
        if quantity is None or available is None or notional is None or computed_fee is None:
            trade_evaluable = False
        else:
            if side == "sell" and quantity > available + EPS:
                r.gap("oversell", f"{tid}: cumulative sale exceeds available quantity")
                trade_evaluable = False
            running_quantities[sid] = available + (quantity if side == "buy" else -quantity)
            if side == "sell":
                total_sells += notional
            else:
                total_buys += notional
            total_fees += computed_fee
            if settlement is not None:
                bucket = ledger[settlement.isoformat()]
                bucket["buys" if side == "buy" else "sells"] += notional
                bucket["fees"] += computed_fee
        if side == "sell" and quantity is not None:
            if intent["lot_selection"] == "oldest-first":
                left = quantity
                trade["lot_allocations"] = []
                matching = sorted((l for l in lot_map.values() if l["security_id"] == sid),
                                  key=lambda l: (l.get("acquired_on") or "9999", l["lot_id"]))
                for lot in matching:
                    if lot["quantity"] is None:
                        continue
                    take = min(left, max(0, lot["quantity"] - allocated_lots[lot["lot_id"]]))
                    if take > EPS:
                        trade["lot_allocations"].append({"lot_id": lot["lot_id"], "quantity": take,
                                                          "source_ids": deepcopy(lot.get("source_ids"))})
                        left -= take
            lot_total, gain_total, gain_known = 0.0, 0.0, True
            for allocation in trade["lot_allocations"]:
                lid = allocation["lot_id"]
                r.source(allocation, f"{tid}/{lid}")
                aq = r.num(allocation, "quantity", f"{tid}/{lid}", True)
                lot = lot_map.get(lid)
                if aq is None or lot is None or lot["security_id"] != sid:
                    r.gap("lot-selection", f"{tid}/{lid}: selection does not resolve to this security")
                    gain_known = False
                    continue
                lot_total += aq
                allocated_lots[lid] += aq
                if lot["quantity"] is None or allocated_lots[lid] > lot["quantity"] + EPS:
                    r.gap("lot-overallocation", f"{tid}/{lid}: cumulative selected quantity exceeds available lot")
                    gain_known = False
                basis = aq / lot["quantity"] * lot["cost_basis"] if lot["quantity"] and lot["cost_basis"] is not None else None
                gain = aq * price - basis if price is not None and basis is not None else None
                if gain is None:
                    gain_known = False
                else:
                    gain_total += gain
                acquired = iso_date(lot.get("acquired_on"))
                gains.append({"trade_id": tid, "lot_id": lid, "security_id": sid, "quantity": aq,
                              "allocated_basis": basis, "gross_gain_loss": gain,
                              "holding_days_at_trade": (trade_date - acquired).days if acquired else None,
                              "source_ids": deepcopy(lot.get("source_ids"))})
            if abs(lot_total - quantity) > EPS and taxable is not False:
                r.gap("lot-selection", f"{tid}: selected lots do not cover the sale quantity")
                gain_known = False
            trade_gain = gain_total if gain_known and abs(lot_total - quantity) <= EPS else None
        else:
            trade_gain = None
            if trade.get("lot_allocations"):
                r.gap("lot-selection", f"{tid}: buy cannot consume existing tax lots")
        trade_rows.append({**trade, "price": price, "notional": notional, "calculated_fee": computed_fee,
                           "gross_gain_loss": trade_gain,
                           "intent_binding": input_hash({"request": doc, "trade_id": tid})})
    if budget is not None and total_fees > budget + EPS:
        r.gap("cost-budget", "Calculated transaction fees exceed the explicit cost reserve")
    ledger_rows, settled = [], cash if trade_evaluable else None
    for date, amounts in sorted(ledger.items()):
        before = settled
        if settled is not None:
            if intent["settlement_policy"] == "prefund-buys" and settled < amounts["buys"] + amounts["fees"] - EPS:
                r.gap("settlement-funding", f"{date}: buy debits/fees exceed cash before same-day sale credits")
            settled += amounts["sells"] - amounts["buys"] - amounts["fees"]
            if settled < -EPS:
                r.gap("settlement-funding", f"{date}: projected settled cash is negative")
        ledger_rows.append({"date": date, "opening_cash": before, **amounts, "closing_cash": settled})
    post_cash = cash + total_sells - total_buys - total_fees if trade_evaluable else None
    post_nav = pre_nav - total_fees if trade_evaluable else None
    turnover = total_sells / pre_nav if pre_nav and trade_evaluable else None
    if turnover is not None and limits["max_sell_turnover"] is not None and turnover > limits["max_sell_turnover"] + EPS:
        r.gap("turnover-limit", "Sell notional/pre-transition NAV exceeds supplied limit")
    if post_cash is not None and limits["minimum_cash"] is not None and post_cash < limits["minimum_cash"] - EPS:
        r.gap("minimum-cash", "Projected cash is below the supplied minimum")
    drift = []
    for sid in sorted(set(positions) | set(targets) | traded_ids):
        q = running_quantities.get(sid)
        mv = q * prices[sid] if q is not None and prices.get(sid) is not None and trade_evaluable else None
        weight = mv / post_nav if mv is not None and post_nav and post_nav > 0 else None
        tw = targets.get(sid)
        difference = weight - tw if weight is not None and tw is not None else None
        if difference is not None and limits["drift_tolerance_weight"] is not None and abs(difference) > limits["drift_tolerance_weight"] + EPS:
            r.gap("residual-drift", f"{sid}: projected weight remains outside target band")
        if weight is not None and limits["max_position_weight"] is not None and weight > limits["max_position_weight"] + EPS:
            r.gap("position-limit", f"{sid}: projected position exceeds supplied cap")
        drift.append({"security_id": sid, "before_quantity": quantities.get(sid, 0.0) if port.get("positions_complete") is True else quantities.get(sid),
                      "after_quantity": q if trade_evaluable else None, "after_market_value": mv,
                      "target_weight": tw, "after_weight": weight, "drift_weight": difference})
    projected_values = [row["after_market_value"] for row in drift]
    projected_total = post_cash + sum(projected_values) if post_cash is not None and all(v is not None for v in projected_values) else None
    if projected_total is not None and post_nav is not None and abs(projected_total - post_nav) > 0.01:
        r.gap("post-state-reconciliation", "Projected positions plus cash do not reconcile to post-fee NAV")
    cash_weight = post_cash / post_nav if post_cash is not None and post_nav and post_nav > 0 else None
    cash_drift = cash_weight - target_cash if cash_weight is not None and target_cash is not None else None
    if cash_drift is not None and limits["drift_tolerance_weight"] is not None and abs(cash_drift) > limits["drift_tolerance_weight"] + EPS:
        r.gap("residual-cash-drift", "Projected cash weight remains outside target band")
    loss_groups = {universe[g["security_id"]].get("tax_identity_group") for g in gains
                   if g["gross_gain_loss"] is not None and g["gross_gain_loss"] < 0 and g["security_id"] in universe}
    for trade in trade_rows:
        group = universe.get(trade["security_id"], {}).get("tax_identity_group")
        if trade["side"] == "buy" and group is not None and group in loss_groups:
            r.gap("same-plan-loss-repurchase", f"{trade['trade_id']}: buy shares a supplied tax-identity group with a loss sale; route for tax review")
    if None in loss_groups:
        r.gap("tax-identity-gap", "A loss sale lacks tax identity grouping; same-plan repurchase screen incomplete")
    result = {"input_snapshot": deepcopy(doc), **r.context(), "plan_hash": input_hash(doc), "trades": trade_rows,
              "pre_nav": pre_nav, "post_nav": post_nav, "post_cash": post_cash,
              "post_positions_plus_cash": projected_total,
              "total_sells": total_sells if trade_evaluable else None, "total_buys": total_buys if trade_evaluable else None,
              "transaction_fees": total_fees if trade_evaluable else None, "sell_turnover": turnover,
              "settlement_ledger": ledger_rows, "settlement_ledger_complete": trade_evaluable,
              "positions": drift, "cash_drift_weight": cash_drift,
              "lot_gain_loss": gains, "execution_status": "not-supported", "approval_status": "not-authenticated",
              "scope": "Draft transition estimates; gross lot arithmetic and supplied same-plan identity screen only. No orders, tax clearance, authenticated approvals, fill verification or guaranteed reversal."}
    return make_output(SKILL, doc, result, r.findings)


def validate_output(out):
    return validate_artifact(out, SKILL, compute)
