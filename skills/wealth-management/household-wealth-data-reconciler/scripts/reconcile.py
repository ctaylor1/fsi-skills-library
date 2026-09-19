"""Reconcile cited account-level snapshots without guessing identity, ownership or FX."""
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN

from wealth_contract import (iso_date, make_output, nonempty, source_errors,
                            validate_envelope, validate_output_envelope)

SKILL = "household-wealth-data-reconciler"


def amount(value, share=False):
    # JSON bool is an int in Python; floating-point money is intentionally unsupported.
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("use a decimal string or integer, never bool/float")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid decimal") from exc
    places = 6 if share else 2
    if (not result.is_finite() or result < 0 or result > Decimal("1e15")
            or result.as_tuple().exponent < -places or (share and result > 1)):
        raise ValueError("invalid amount, precision or household share")
    return result


def money(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))


def validate_input(doc):
    errors = validate_envelope(doc)
    if errors:
        return errors
    if doc.get("base_currency") != "USD":
        errors.append("base_currency must be USD; no FX conversion is implemented")
    parties = doc.get("household_party_ids")
    if (not isinstance(parties, list) or not parties or not all(nonempty(x) for x in parties)
            or len(parties) != len(set(parties))):
        errors.append("household_party_ids must be unique nonempty strings")
    expected = doc.get("expected_accounts")
    if not isinstance(expected, list) or not expected:
        errors.append("expected_accounts must declare nonempty reconciliation scope")
    else:
        ids = []
        for row in expected:
            if not isinstance(row, dict) or not nonempty(row.get("account_id")):
                errors.append("expected account requires account_id")
                continue
            ids.append(row["account_id"])
            if row.get("kind") not in ("asset", "liability"):
                errors.append("expected account kind must be asset or liability")
            errors.extend(source_errors(row.get("source_ids"), doc))
        if len(ids) != len(set(ids)):
            errors.append("duplicate expected account_id")
    policy = doc.get("valuation_policy")
    if not isinstance(policy, dict):
        errors.append("valuation_policy required")
    else:
        if not nonempty(policy.get("version")):
            errors.append("valuation_policy.version required")
        days = policy.get("max_age_days")
        if type(days) is not int or not 0 <= days <= 366:
            errors.append("valuation_policy.max_age_days must be integer 0..366")
        errors.extend(source_errors(policy.get("source_ids"), doc))
    records = doc.get("records")
    if not isinstance(records, list):
        errors.append("records must be a list (empty means no statements supplied)")
    else:
        ids = []
        for row in records:
            if not isinstance(row, dict) or not nonempty(row.get("record_id")) or not nonempty(row.get("account_id")):
                errors.append("each record requires record_id and account_id")
                continue
            ids.append(row["record_id"])
            if row.get("kind") not in ("asset", "liability"):
                errors.append("record kind must be asset or liability")
            for key in ("currency", "valuation_date"):
                if row.get(key) is not None and not isinstance(row[key], str):
                    errors.append(f"{key} must be a string or null")
            # Missing economic fields remain explicit findings; malformed supplied amounts fail.
            for key in ("value", "household_share"):
                if row.get(key) is not None:
                    try:
                        amount(row[key], key == "household_share")
                    except ValueError as exc:
                        errors.append(f"{row['record_id']}.{key}: {exc}")
            if not isinstance(row.get("owner_party_ids"), list) or not all(nonempty(x) for x in row.get("owner_party_ids", [])):
                errors.append("owner_party_ids must be a list of strings (empty is unknown)")
            elif len(row["owner_party_ids"]) != len(set(row["owner_party_ids"])):
                errors.append("duplicate owner_party_ids")
            for key in ("identity_verified", "is_held_away"):
                if row.get(key) is not None and type(row[key]) is not bool:
                    errors.append(f"{key} must be boolean or null")
        if len(ids) != len(set(ids)):
            errors.append("duplicate record_id")
    reference = doc.get("reference_totals")
    if reference is not None:
        if not isinstance(reference, dict):
            errors.append("reference_totals must be an object")
        else:
            errors.extend(source_errors(reference.get("source_ids"), doc))
            for key in ("assets", "liabilities"):
                try:
                    amount(reference.get(key))
                except ValueError as exc:
                    errors.append(f"reference_totals.{key}: {exc}")
            if reference.get("basis") != "household-share" or reference.get("currency") != "USD":
                errors.append("reference_totals must use household-share basis in USD")
    return errors


def reconcile(doc):
    errors = validate_input(doc)
    if errors:
        raise ValueError("; ".join(errors))
    findings, included, excluded = [], [], []
    expected = {row["account_id"]: row for row in doc["expected_accounts"]}
    grouped = defaultdict(list)
    for row in doc["records"]:
        grouped[row["account_id"]].append(row)
    as_of = iso_date(doc["as_of"])
    for account_id in sorted(set(expected) | set(grouped)):
        rows = grouped[account_id]
        reasons = []
        if account_id not in expected:
            reasons.append("outside declared account scope")
        if not rows:
            reasons.append("no account snapshot supplied")
        signatures = set()
        for row in rows:
            prefix = row["record_id"] + ": "
            reasons.extend(prefix + e for e in source_errors(row.get("source_ids"), doc))
            if row.get("identity_verified") is not True:
                reasons.append(prefix + "account mapping has not been confirmed")
            owners = row["owner_party_ids"]
            if not owners or not set(owners).intersection(doc["household_party_ids"]):
                reasons.append(prefix + "household ownership is unresolved")
            if row.get("household_share") is None:
                reasons.append(prefix + "explicit household share required")
            if row.get("value") is None:
                reasons.append(prefix + "account value missing")
            if row.get("currency") != doc["base_currency"]:
                reasons.append(prefix + "unsupported currency; no FX assumption permitted")
            if type(row.get("is_held_away")) is not bool:
                reasons.append(prefix + "held-away classification unknown")
            when = iso_date(row.get("valuation_date"))
            if when is None or not 0 <= (as_of - when).days <= doc["valuation_policy"]["max_age_days"]:
                reasons.append(prefix + "valuation date missing, stale or future-dated")
            if account_id in expected and row["kind"] != expected[account_id]["kind"]:
                reasons.append(prefix + "asset/liability type conflicts with declared scope")
            signatures.add((row["kind"], str(amount(row["value"]).normalize()) if row.get("value") is not None else None,
                            str(amount(row["household_share"], True).normalize()) if row.get("household_share") is not None else None,
                            row.get("currency"), row.get("valuation_date"), tuple(sorted(owners)), row.get("is_held_away")))
        if len(signatures) > 1:
            reasons.append("conflicting account snapshots; no winner selected")
        if reasons:
            excluded.append({"account_id": account_id, "record_ids": [r["record_id"] for r in rows], "reasons": reasons})
            findings.append({"code": "account-unreconciled", "account_id": account_id, "message": "; ".join(reasons)})
            continue
        row = rows[0]
        included.append({"account_id": account_id, "kind": row["kind"], "value": money(amount(row["value"])),
                         "household_share": str(amount(row["household_share"], True)),
                         "household_value": money(amount(row["value"]) * amount(row["household_share"], True)),
                         "currency": row["currency"], "valuation_date": row["valuation_date"],
                         "owner_party_ids": sorted(row["owner_party_ids"]), "is_held_away": row["is_held_away"],
                         "record_ids": [r["record_id"] for r in rows],
                         "source_ids": sorted(set(s for r in rows for s in r["source_ids"]))})
    assets = sum((Decimal(r["household_value"]) for r in included if r["kind"] == "asset"), Decimal(0))
    liabilities = sum((Decimal(r["household_value"]) for r in included if r["kind"] == "liability"), Decimal(0))
    tie_out = {"status": "not-performed", "reason": "no independent reference totals supplied"}
    if doc.get("reference_totals") is not None:
        ref = doc["reference_totals"]
        av, lv = assets - amount(ref["assets"]), liabilities - amount(ref["liabilities"])
        tie_out = {"status": "matched" if not excluded and av == lv == 0 else "break",
                   "asset_variance": money(av), "liability_variance": money(lv), "source_ids": ref["source_ids"]}
        if tie_out["status"] == "break":
            findings.append({"code": "reference-tieout-break", "message": "Included household-share totals do not fully reconcile to the reference."})
    result = {"input_snapshot": deepcopy(doc), "included_accounts": included, "excluded_accounts": excluded,
              "coverage": {"expected": len(expected), "included": len(included), "excluded": len(excluded),
                           "complete_for_declared_scope": not excluded},
              "totals": {"currency": "USD", "basis": "household-share", "assets": money(assets),
                         "liabilities": money(liabilities), "net_worth": money(assets - liabilities),
                         "partial": bool(excluded)}, "reference_tie_out": tie_out}
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    errors = validate_output_envelope(out, SKILL)
    if errors:
        return errors
    snapshot = out["result"].get("input_snapshot")
    errors = validate_input(snapshot)
    if errors:
        return ["invalid input snapshot: " + e for e in errors]
    if out != reconcile(snapshot):
        errors.append("artifact differs from reconciliation of its bound input")
    # Independent conservation check protects arithmetic rather than only text/shape.
    try:
        totals = out["result"]["totals"]
        rows = out["result"]["included_accounts"]
        for kind, field in (("asset", "assets"), ("liability", "liabilities")):
            total = sum((Decimal(r["household_value"]) for r in rows if r["kind"] == kind), Decimal(0))
            if total != Decimal(totals[field]):
                errors.append("account totals do not conserve household values")
        if Decimal(totals["assets"]) - Decimal(totals["liabilities"]) != Decimal(totals["net_worth"]):
            errors.append("net worth arithmetic mismatch")
    except (KeyError, TypeError, InvalidOperation):
        errors.append("invalid totals or included account values")
    return errors
