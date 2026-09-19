from decimal import Decimal, InvalidOperation
from datetime import datetime
from payment_foundation import finding


def amount(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("amount must be a decimal string or integer")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid amount") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("amount must be finite and nonnegative")
    return result


def text(value):
    return isinstance(value, str) and bool(value.strip())


def stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp requires timezone")
    return result


def rows(data, key, fields, errors, nullable=()):
    items = data.get(key)
    if not isinstance(items, list):
        errors.append(key + " must be an explicit list")
        return []
    seen = set()
    for row in items:
        if not isinstance(row, dict):
            errors.append(key + " row must be an object")
            continue
        for field in fields:
            if not text(row.get(field)):
                errors.append(key + "." + field + " required")
        rid = row.get(fields[0])
        if rid in seen:
            errors.append(key + " duplicate " + fields[0])
        seen.add(rid)
        if not isinstance(row.get("source_ids"), list) or not row["source_ids"]:
            errors.append(key + " row needs source_ids")
        if "currency" in fields and (len(row.get("currency", "")) != 3 or not row.get("currency", "").isupper()):
            errors.append(key + " currency requires uppercase three-letter code")
        for field in nullable:
            if row.get(field) is not None:
                try:
                    amount(row[field])
                except ValueError as exc:
                    errors.append(key + "." + field + ": " + str(exc))
    return items


def handoff(target, reason, required):
    return {"target_skill": target, "reason": reason, "required_inputs": required}

from payment_foundation import load_rail_profile
SKILL = "payment-liquidity-and-funding-analyzer"


def validate(data):
    errors = []
    for field in ["window_start", "window_end"]:
        try:
            stamp(data[field])
        except (ValueError, KeyError, TypeError, AttributeError):
            errors.append(field + " requires timezone-aware ISO timestamp")
    if not errors and stamp(data["window_start"]) >= stamp(data["window_end"]):
        errors.append("window_start must precede window_end")
    accounts = rows(data, "accounts", ["account_id", "entity_id", "currency", "rail_profile_id", "funding_model", "snapshot_at"], errors, ["balance", "held"])
    for row in accounts:
        if not isinstance(row, dict):
            continue
        try:
            stamp(row["snapshot_at"])
        except (ValueError, KeyError, TypeError, AttributeError):
            errors.append("account snapshot_at needs timezone-aware timestamp")
    events = rows(data, "events", ["event_id", "economic_id", "account_id", "entity_id", "currency", "kind", "certainty", "due_at"], errors, ["amount"])
    for row in events:
        if not isinstance(row, dict):
            continue
        if row.get("kind") not in {"inflow", "outflow", "settlement-obligation"} or row.get("certainty") not in {"firm", "forecast"}:
            errors.append("event kind or certainty unsupported")
        try:
            stamp(row["due_at"])
        except (ValueError, KeyError, TypeError, AttributeError):
            errors.append("event due_at needs timezone-aware timestamp")
    rows(data, "reservations", ["reservation_id", "account_id", "event_id", "currency"], errors, ["amount"])
    windows = rows(data, "funding_windows", ["window_id", "account_id", "opens_at", "closes_at"], errors)
    for row in windows:
        if not isinstance(row, dict):
            continue
        try:
            if stamp(row["opens_at"]) > stamp(row["closes_at"]):
                errors.append("funding window order invalid")
        except (ValueError, KeyError, TypeError, AttributeError):
            errors.append("funding windows require timezone-aware timestamps")
    if type(data.get("history_complete")) is not bool:
        errors.append("history_complete boolean required")
    stresses = rows(data, "stress_scenarios", ["scenario_id", "rationale"], errors)
    for row in stresses:
        if not isinstance(row, dict):
            continue
        if not isinstance(row.get("remove_inflow_ids"), list) or any(not text(v) for v in row.get("remove_inflow_ids", [])):
            errors.append("stress requires remove_inflow_ids list")
        if type(row.get("outflow_multiplier_bps")) is not int or row["outflow_multiplier_bps"] < 10000:
            errors.append("stress outflow_multiplier_bps requires integer >= 10000")
    if not data.get("accounts"):
        errors.append("accounts requires at least one record")
    if any(isinstance(r, dict) and r.get("scenario_id") == "base" for r in data.get("stress_scenarios", [])):
        errors.append("base is a reserved scenario_id")
    return errors


def analyze(request):
    from datetime import date
    data = request["data"]
    findings = []
    start, end = stamp(data["window_start"]), stamp(data["window_end"])
    accounts = {r["account_id"]: r for r in data["accounts"]}
    events = {r["event_id"]: r for r in data["events"]}
    invalid_accounts = set()
    def gap(code, message, row=None):
        findings.append(finding(code, message, (row or {}).get("source_ids", [])))
    if start.date() < date.fromisoformat(request["as_of"]):
        gap("historical-window", "Analysis window starts before request as_of; confirm this is a retrospective case.")
    if not data["history_complete"]:
        gap("incomplete-history", "Unknown held/reserved resources or missing obligations prevent reliable projected positions.")
        invalid_accounts.update(accounts)
    seen_economic = {}
    for event in events.values():
        account = accounts.get(event["account_id"])
        if not account or account["entity_id"] != event["entity_id"] or account["currency"] != event["currency"]:
            invalid_accounts.add(event["account_id"])
            gap("event-owner-or-currency", event["event_id"], event)
        economic = event["economic_id"]
        if economic in seen_economic:
            invalid_accounts.update([event["account_id"], seen_economic[economic]])
            gap("double-counted-economic-event", economic + ": events must be disjoint; do not count the same obligation as outflow and settlement.", event)
        seen_economic[economic] = event["account_id"]
        if stamp(event["due_at"]) <= start:
            invalid_accounts.add(event["account_id"])
            gap("event-in-opening-snapshot", event["event_id"] + ": event at/before opening may already be in balance.", event)
        if event.get("amount") is None:
            invalid_accounts.add(event["account_id"])
            gap("unknown-event-amount", event["event_id"], event)
    reserved_events = set()
    for reservation in data["reservations"]:
        event = events.get(reservation["event_id"])
        account = accounts.get(reservation["account_id"])
        if not event or not account or event["kind"] == "inflow" or event["account_id"] != reservation["account_id"] or reservation["currency"] != account["currency"] or reservation["event_id"] in reserved_events or reservation.get("amount") is None or event.get("amount") is None or amount(reservation["amount"]) > amount(event["amount"]):
            invalid_accounts.add(reservation["account_id"])
            gap("invalid-or-overlapping-reservation", reservation["reservation_id"], reservation)
        reserved_events.add(reservation["event_id"])
    for window in data["funding_windows"]:
        if window["account_id"] not in accounts:
            gap("unknown-funding-window-account", window["window_id"], window)
    for scenario in data["stress_scenarios"]:
        for eid in scenario["remove_inflow_ids"]:
            if eid not in events or events[eid]["kind"] != "inflow":
                gap("invalid-stress-inflow", eid, scenario)
                invalid_accounts.update(accounts)
    result = []
    for account_id, account in accounts.items():
        profile = load_rail_profile(account["rail_profile_id"])
        if not profile or profile["jurisdiction"] != request["jurisdiction"] or account["currency"] not in profile["currencies"]:
            invalid_accounts.add(account_id)
            gap("unsupported-rail-or-currency", account_id, account)
        elif request["as_of"] < profile["reviewed_on"] or request["as_of"] > profile["review_due"] or end.date().isoformat() > profile["review_due"]:
            invalid_accounts.add(account_id)
            gap("stale-or-future-rail-profile", account_id, account)
        expected = {"US-FEDNOW": {"master-account", "correspondent-account"}, "US-RTP": {"prefunded-position", "funding-agent-prefunded-position"}}
        if account["rail_profile_id"] in expected and account["funding_model"] not in expected[account["rail_profile_id"]]:
            invalid_accounts.add(account_id)
            gap("funding-model-mismatch", account_id + ": FedNow master/correspondent settlement and RTP prefunded positions are distinct.", account)
        if account["rail_profile_id"] not in expected and not text(account.get("funding_model_evidence")):
            invalid_accounts.add(account_id)
            gap("funding-model-evidence-missing", account_id, account)
        if stamp(account["snapshot_at"]) != start or stamp(account["snapshot_at"]).date() > date.fromisoformat(request["as_of"]) or account.get("balance") is None or account.get("held") is None:
            invalid_accounts.add(account_id)
            gap("unknown-opening-position", account_id + ": balance and disjoint held amount require snapshot exactly at opening.", account)
        account_events = [e for e in events.values() if e["account_id"] == account_id and start < stamp(e["due_at"]) <= end]
        windows = [r for r in data["funding_windows"] if r["account_id"] == account_id]
        excluded = []
        eligible_inflows = set()
        for event in account_events:
            if event["kind"] != "inflow":
                continue
            open_window = any(stamp(w["opens_at"]) <= stamp(event["due_at"]) <= stamp(w["closes_at"]) for w in windows)
            if event["certainty"] == "firm" and open_window:
                eligible_inflows.add(event["event_id"])
            else:
                reason = "forecast-not-firm" if event["certainty"] != "firm" else "outside-evidenced-funding-window"
                excluded.append({"event_id": event["event_id"], "reason": reason})
                gap(reason, event["event_id"] + ": excluded from conservative available funding.", event)
        scenarios = [{"scenario_id": "base", "remove_inflow_ids": [], "outflow_multiplier_bps": 10000}] + data["stress_scenarios"]
        paths = []
        for scenario in scenarios:
            known = account_id not in invalid_accounts
            holds = amount(account["held"]) if known else None
            reservations = {r["event_id"]: amount(r["amount"]) for r in data["reservations"] if r["account_id"] == account_id} if known else {}
            available = amount(account["balance"]) - holds - sum(reservations.values(), Decimal(0)) if known else None
            minimum = available
            timeline = [{"at": data["window_start"], "event_ids": [], "available": str(available) if known else None}]
            # Conservative same-instant ordering: obligations precede incoming credits.
            ordered = sorted(account_events, key=lambda e: (stamp(e["due_at"]), e["kind"] == "inflow", e["event_id"]))
            for event in ordered:
                if known:
                    if event["kind"] == "inflow":
                        if event["event_id"] in eligible_inflows and event["event_id"] not in scenario["remove_inflow_ids"]:
                            available += amount(event["amount"])
                    else:
                        available -= amount(event["amount"]) * Decimal(scenario["outflow_multiplier_bps"]) / 10000
                        available += reservations.pop(event["event_id"], Decimal(0))
                    minimum = min(minimum, available)
                timeline.append({"at": event["due_at"], "event_ids": [event["event_id"]], "available": str(available) if known else None})
            shortage = max(-minimum, Decimal(0)) if known else None
            if shortage and shortage > 0:
                gap("funding-shortfall", account_id + "/" + scenario["scenario_id"] + " peak deficit " + str(shortage) + " " + account["currency"] + "; later receipts cannot cure earlier missed obligations.", account)
            paths.append({"scenario_id": scenario["scenario_id"], "timeline": timeline, "minimum_available": str(minimum) if known else None, "peak_shortfall": str(shortage) if known else None, "ending_available": str(available) if known else None})
        result.append({"account_id": account_id, "entity_id": account["entity_id"], "currency": account["currency"], "funding_model": account["funding_model"], "excluded_inflows": excluded, "scenario_paths": paths})
    return {"result": {"window_start": data["window_start"], "window_end": data["window_end"], "account_positions": result, "aggregation": "No cross-account, legal-entity or currency netting", "funding_options_for_owner_review": ["Confirm actual usable balance and disjoint holds/reservations", "Verify funding access and windows for the required settlement arrangement", "Stage evidenced resources before earliest obligation", "Review liquidity buffer and service limits under outage stress"], "transfers_created": False}, "findings": findings, "handoffs": [handoff("settlement-reconciliation-matcher", "Reconcile source balances and settlement obligations before funding decisions.", ["account statements", "settlement ledgers", "reservation identifiers"]), handoff("payment-initiation-control-reviewer", "Any funding movement requires a separately authorized exact instruction.", ["source and destination accounts", "amount and currency", "funding window", "approval and mandate"]), handoff("payment-platform-architecture-reviewer", "Review continuous funding monitoring, uncertain outcomes and recovery dependencies.", ["timed shortfalls", "failure assumptions", "system and operational dependencies"])]}
