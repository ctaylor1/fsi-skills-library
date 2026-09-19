"""Currency-separate corridor funding projection with conditional transfer legs."""
from datetime import datetime, timezone
from payment_foundation import dec, finding

SKILL = "payment-liquidity-and-funding-analyzer"
SUPPORTED_JURISDICTIONS = {"US", "EA", "UK", "BR", "IN", "CA"}
CURRENCIES = {"USD", "EUR", "GBP", "BRL", "INR", "CAD"}


def stamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return parsed.astimezone(timezone.utc)


def validate(data):
    errors = []
    try:
        start, end = stamp(data["window_start"]), stamp(data["window_end"])
        if start >= end:
            errors.append("window must increase")
    except (KeyError, TypeError, ValueError, AttributeError):
        return ["aware window_start and window_end required"]
    if not isinstance(data.get("history_complete"), bool):
        errors.append("history_complete boolean required")
    for key in ("accounts", "obligations", "funding_transfers", "stress_scenarios"):
        if not isinstance(data.get(key), list):
            errors.append(key + " must be a list")
    if errors:
        return errors
    accounts, economic_ids, transfer_ids, scenario_ids = {}, set(), set(), set()
    for account in data["accounts"]:
        aid = account.get("account_id")
        if not isinstance(aid, str) or not aid or aid in accounts:
            errors.append("unique account_id required")
        accounts[aid] = account
        for key in ("entity_id", "jurisdiction", "currency", "account_role"):
            if not isinstance(account.get(key), str) or not account[key]:
                errors.append("account requires " + key)
        if account.get("account_role") not in {"nostro", "local-payout", "source-funding", "settlement"}:
            errors.append("unsupported account_role")
        for key in ("opening_balance", "held"):
            if account.get(key) is not None:
                try:
                    if dec(account[key]) < 0:
                        errors.append("opening_balance and held cannot be negative")
                except (ValueError, TypeError, ArithmeticError):
                    errors.append("finite money or explicit null required")
        try:
            if stamp(account["snapshot_at"]) != start:
                errors.append("opening snapshot must equal window start")
        except (KeyError, TypeError, ValueError, AttributeError):
            errors.append("aware snapshot_at required")
    for obligation in data["obligations"]:
        eid = obligation.get("economic_id")
        if not isinstance(eid, str) or not eid or eid in economic_ids:
            errors.append("unique economic obligation identity required")
        economic_ids.add(eid)
        account = accounts.get(obligation.get("account_id"))
        if not account or any(obligation.get(k) != account.get(k) for k in ("entity_id", "currency")):
            errors.append("obligation account/entity/currency binding mismatch")
        if obligation.get("purpose") not in {"customer-payout", "nostro-obligation", "fee", "collateral"}:
            errors.append("unsupported obligation purpose")
        try:
            if dec(obligation.get("amount")) <= 0:
                errors.append("obligation amount must be positive")
            if not start <= stamp(obligation.get("due_at")) <= end:
                errors.append("obligation outside window")
        except (TypeError, ValueError, AttributeError, ArithmeticError):
            errors.append("positive amount and aware due_at required")
    for transfer in data["funding_transfers"]:
        tid = transfer.get("transfer_id")
        eid = transfer.get("economic_id")
        if not isinstance(tid, str) or not tid or tid in transfer_ids:
            errors.append("unique funding transfer identity required")
        transfer_ids.add(tid)
        if not isinstance(eid, str) or not eid or eid in economic_ids:
            errors.append("duplicate or absent economic funding identity")
        economic_ids.add(eid)
        source, destination = accounts.get(transfer.get("source_account")), accounts.get(transfer.get("destination_account"))
        if not source or not destination or source is destination:
            errors.append("funding requires distinct registered accounts")
        for side, account in (("source", source), ("destination", destination)):
            if account and any(transfer.get(side + "_" + key) != account.get(key) for key in ("entity_id", "currency")):
                errors.append("funding account/entity/currency binding mismatch")
            try:
                if dec(transfer.get(side + "_amount")) <= 0:
                    errors.append("funding amounts must be positive")
            except (ValueError, TypeError, ArithmeticError):
                errors.append("finite funding amount required")
        try:
            debit, credit = stamp(transfer["debit_at"]), stamp(transfer["credit_at"])
            if not start <= debit < credit <= end:
                errors.append("funding debit must precede credit inside window")
            for key in ("debit_window", "credit_window"):
                value = transfer.get(key)
                if value is not None and (not isinstance(value, dict) or stamp(value["opens_at"]) > stamp(value["closes_at"])):
                    errors.append("funding access window invalid")
            quote = transfer.get("fx_quote")
            if quote is not None:
                if dec(quote["rate"]) <= 0 or stamp(quote["quoted_at"]) > stamp(quote["expires_at"]):
                    errors.append("funding FX quote invalid")
        except (KeyError, TypeError, ValueError, AttributeError, ArithmeticError):
            errors.append("funding timestamps, windows and FX quote must be valid")
    for scenario in data["stress_scenarios"]:
        if not isinstance(scenario.get("scenario_id"), str) or not scenario["scenario_id"] or scenario["scenario_id"] in scenario_ids:
            errors.append("unique scenario identity required")
        scenario_ids.add(scenario.get("scenario_id"))
        if not isinstance(scenario.get("remove_transfer_ids"), list) or any(t not in transfer_ids for t in scenario.get("remove_transfer_ids", [])):
            errors.append("stress must reference registered transfers")
    for rows in (data["accounts"], data["obligations"], data["funding_transfers"]):
        if any(not isinstance(row.get("source_ids"), list) or not row["source_ids"] for row in rows):
            errors.append("each account, obligation and transfer requires source_ids")
    return errors


def transfer_gaps(transfer, accounts):
    gaps = []
    source, dest = accounts[transfer["source_account"]], accounts[transfer["destination_account"]]
    if transfer.get("certainty") != "firm" or not all(transfer.get(k) for k in ("funding_contract_ref", "access_review_ref", "limit_review_ref")):
        gaps.append("funding-not-firm-or-reviewed")
    if source["entity_id"] != dest["entity_id"] and not transfer.get("interentity_agreement_ref"):
        gaps.append("interentity-obligation-unresolved")
    for event in ("debit", "credit"):
        window = transfer.get(event + "_window")
        if not window or not window.get("availability_review_ref") or not stamp(window["opens_at"]) <= stamp(transfer[event + "_at"]) <= stamp(window["closes_at"]):
            gaps.append(event + "-access-window-unresolved")
    source_amount, dest_amount = dec(transfer["source_amount"]), dec(transfer["destination_amount"])
    if source["currency"] == dest["currency"]:
        if source_amount != dest_amount:
            gaps.append("same-currency-funding-not-conserved")
    else:
        quote = transfer.get("fx_quote")
        if not quote or not quote.get("quote_ref") or quote.get("kind") != "firm":
            gaps.append("funding-fx-not-firm-evidenced")
        elif not stamp(quote["quoted_at"]) <= stamp(transfer["debit_at"]) <= stamp(quote["expires_at"]):
            gaps.append("funding-fx-not-current-at-debit")
        else:
            orientation = quote.get("base_currency"), quote.get("quote_currency")
            if orientation == (source["currency"], dest["currency"]):
                expected = source_amount * dec(quote["rate"])
            elif orientation == (dest["currency"], source["currency"]):
                expected = source_amount / dec(quote["rate"])
            else:
                expected = None
            if expected is None or expected != dest_amount:
                gaps.append("funding-fx-amount-or-orientation-mismatch")
    return gaps


def project(data, removed):
    accounts = {a["account_id"]: a for a in data["accounts"]}
    balances = {aid: None if a.get("opening_balance") is None or a.get("held") is None else dec(a["opening_balance"]) - dec(a["held"]) for aid, a in accounts.items()}
    minimum, earliest = dict(balances), {aid: data["window_start"] if value is not None and value < 0 else None for aid, value in balances.items()}
    timeline, included, exclusions = [], set(), []
    events = [(stamp(o["due_at"]), 0, o["economic_id"], "obligation", o) for o in data["obligations"]]
    for transfer in data["funding_transfers"]:
        events.extend([(stamp(transfer["debit_at"]), 1, transfer["transfer_id"], "debit", transfer), (stamp(transfer["credit_at"]), 2, transfer["transfer_id"], "credit", transfer)])
    for when, _, identifier, kind, row in sorted(events):
        if kind == "obligation":
            aid, change = row["account_id"], -dec(row["amount"])
        elif kind == "debit":
            aid = row["source_account"]
            gaps = transfer_gaps(row, accounts)
            if row["transfer_id"] in removed:
                gaps.append("stress-funding-unavailable")
            if balances[aid] is None or balances[aid] < dec(row["source_amount"]):
                gaps.append("source-funds-unavailable-at-debit")
            if gaps:
                exclusions.append({"transfer_id": row["transfer_id"], "reasons": gaps, "source_ids": row["source_ids"]})
                continue
            included.add(identifier)
            change = -dec(row["source_amount"])
        else:
            if identifier not in included:
                continue
            aid, change = row["destination_account"], dec(row["destination_amount"])
        if balances[aid] is not None:
            balances[aid] += change
            minimum[aid] = min(minimum[aid], balances[aid])
            if balances[aid] < 0 and earliest[aid] is None:
                earliest[aid] = when.isoformat()
        timeline.append({"event_id": identifier, "kind": kind, "at": when.isoformat(), "account_id": aid, "entity_id": accounts[aid]["entity_id"], "currency": accounts[aid]["currency"], "change": str(change), "available_after": None if balances[aid] is None else str(balances[aid]), "source_ids": row["source_ids"]})
    return {"positions": [{"account_id": aid, "entity_id": a["entity_id"], "jurisdiction": a["jurisdiction"], "currency": a["currency"], "account_role": a["account_role"], "ending_available": None if balances[aid] is None else str(balances[aid]), "minimum_available": None if minimum[aid] is None else str(minimum[aid]), "peak_shortfall": None if minimum[aid] is None else str(max(dec("0"), -minimum[aid])), "first_shortfall_at": earliest[aid], "source_ids": a["source_ids"]} for aid, a in accounts.items()], "timeline": timeline, "excluded_funding_transfers": exclusions, "included_funding_transfer_ids": sorted(included)}


def analyze(request):
    data, findings = request["data"], []
    if not data["history_complete"]:
        findings.append(finding("incomplete-corridor-history", "Missing history can change every projected position."))
    if not data.get("accountable_reviewer"):
        findings.append(finding("corridor-treasury-owner-missing", "Name the accountable Treasury reviewer."))
    if not data["accounts"]:
        findings.append(finding("missing-corridor-accounts", "Supply separate nostro, source and payout positions."))
    for account in data["accounts"]:
        if account["jurisdiction"] not in SUPPORTED_JURISDICTIONS or account["currency"] not in CURRENCIES:
            findings.append(finding("unsupported-corridor-position", account["account_id"], account["source_ids"]))
        if account.get("opening_balance") is None or account.get("held") is None:
            findings.append(finding("unknown-opening-position", account["account_id"], account["source_ids"]))
        if not account.get("funding_model_review_ref") or not account.get("ownership_review_ref"):
            findings.append(finding("account-ownership-funding-review-missing", account["account_id"], account["source_ids"]))
    base = project(data, set())
    for position in base["positions"]:
        if position["peak_shortfall"] is not None and dec(position["peak_shortfall"]) > 0:
            findings.append(finding("corridor-funding-shortfall", position["account_id"] + " has a time-specific funding shortfall.", position["source_ids"]))
    for excluded in base["excluded_funding_transfers"]:
        findings.append(finding("funding-excluded", excluded["transfer_id"] + ": " + ", ".join(excluded["reasons"]), excluded["source_ids"]))
    stresses = [{"scenario_id": s["scenario_id"], "rationale": s.get("rationale"), **project(data, set(s["remove_transfer_ids"]))} for s in data["stress_scenarios"]]
    return {"result": {"module": "corridor-funding", "accountable_reviewer": data.get("accountable_reviewer"), "base": base, "stress_scenarios": stresses, "crosscurrency_or_interentity_netting": False, "funding_instructions_created": False}, "findings": findings, "handoffs": [{"target_skill": "payment-initiation-control-reviewer", "reason": "Review each distinct source debit and destination credit obligation with a supported local adapter; planning inclusion does not authorize funding.", "required_inputs": ["exact legal-entity account currency amounts and schedule", "firm funding and FX contracts plus access windows", "current liquidity and control evidence", "unresolved corridor findings"]}], "limitations": ["Declared firm funding is an offline scenario assumption; no access, quote, balance or counterparty identity is authenticated.", "Obligations are projected before funding debits and funding credits at equal timestamps; a later inflow never erases an earlier peak shortfall.", "Opening held funds remain restricted throughout this module; model releases as a separately reviewed snapshot rather than silently releasing them.", "FX transfers require strictly later credits and an exact supplied gross conversion; separate fees are explicit obligations. No FX rounding policy, credit line, unsecured overdraft, crosscurrency netting or interentity pooling is inferred."]}
