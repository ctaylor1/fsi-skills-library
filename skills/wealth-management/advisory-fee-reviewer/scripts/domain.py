"""Recalculate an explicitly scoped household advisory bill from supplied terms."""
from calendar import isleap
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal

from wealth_contract import make_output, nonempty
from wealth_analysis import (cited, common, dated, finding, input_findings, money,
                            number, output_errors, records, require)

SKILL = "advisory-fee-reviewer"


def check(doc):
    common(doc)
    require(doc.get("currency") == "USD", "only USD billing is supported; no FX inference")
    period = doc.get("billing_period")
    require(isinstance(period, dict), "billing_period required")
    start, end = dated(period.get("start"), "billing start"), dated(period.get("end"), "billing end")
    require(start <= end <= dated(doc["as_of"], "as_of"), "billing period must be closed and ordered")
    agreement = doc.get("agreement")
    require(isinstance(agreement, dict), "agreement required")
    for key in ("agreement_id", "version", "owner"):
        require(nonempty(agreement.get(key)), f"agreement.{key} required")
    require(agreement.get("schedule_type") in ("marginal", "cliff"), "explicit marginal or cliff schedule required")
    require(agreement.get("day_basis") in ("actual/365", "actual/actual"), "unsupported day basis")
    require(agreement.get("valuation_method") == "segment-constant", "only explicit segment-constant valuation is implemented")
    require(dated(agreement.get("effective_from"), "agreement start") <= start, "agreement not effective at period start")
    require(dated(agreement.get("effective_until"), "agreement end") >= end, "agreement does not cover entire billing period")
    number(agreement.get("minimum_period_fee"), "minimum_period_fee", 0, 2)
    require(type(agreement.get("minimum_applies_at_zero")) is bool, "minimum_applies_at_zero must be explicit")
    tiers = records(agreement.get("tiers"), "tier_id", "tiers")
    prior = Decimal(0)
    for i, tier in enumerate(tiers):
        number(tier.get("annual_rate_bps"), "annual_rate_bps", 0)
        upper = tier.get("up_to")
        if upper is None:
            require(i == len(tiers) - 1, "only final tier may be unbounded")
        else:
            upper = number(upper, "tier upper", 0, 2)
            require(upper > prior, "tier bounds must strictly increase")
            prior = upper
    require(tiers[-1].get("up_to") is None, "last tier must explicitly cover remaining assets")
    accounts = records(doc.get("accounts"), "account_id", "declared accounts")
    known = {a["account_id"] for a in accounts}
    for segment in records(doc.get("valuation_segments"), "segment_id", "valuation_segments", empty=True):
        a, b = dated(segment.get("start"), "segment start"), dated(segment.get("end"), "segment end")
        require(start <= a <= b <= end, "valuation segment outside billing period")
        for row in records(segment.get("accounts"), "account_id", "segment accounts", empty=True):
            require(row["account_id"] in known, "valuation account outside declared household billing group")
            number(row.get("reported_total"), "reported_total", 0, 2)
            for asset in records(row.get("assets"), "asset_id", "asset valuations", empty=True):
                number(asset.get("market_value"), "market_value", 0, 2)
                require("fee_eligible" in asset and (asset["fee_eligible"] is None or type(asset["fee_eligible"]) is bool), "fee_eligible must explicitly be true, false or null")
    for row in records(doc.get("assessed_charges"), "charge_id", "assessed_charges", empty=True):
        require(row.get("account_id") in known, "billed account outside declared household group")
        number(row.get("amount"), "assessed amount", places=2)
    require(type(doc.get("billing_records_complete")) is bool, "billing_records_complete must be explicit")
    for row in records(doc.get("adjustments"), "adjustment_id", "contract adjustments", empty=True):
        number(row.get("amount"), "adjustment", places=2)
        require(nonempty(row.get("reason")), "adjustment reason required")
    review = doc.get("conflict_review")
    require(isinstance(review, dict) and isinstance(review.get("items"), list), "explicit conflict_review required")
    if review.get("reviewed_on") is not None:
        dated(review["reviewed_on"], "conflict review")
    for row in records(review["items"], "conflict_id", "conflicts", empty=True):
        require(nonempty(row.get("description")), "conflict description required")
        require(row.get("status") in ("open", "addressed"), "conflict status must be open or addressed")


def annual_fee(assets, agreement):
    result, lower = Decimal(0), Decimal(0)
    for tier in agreement["tiers"]:
        upper = number(tier["up_to"]) if tier["up_to"] is not None else assets
        rate = number(tier["annual_rate_bps"]) / 10000
        if agreement["schedule_type"] == "cliff":
            if tier["up_to"] is None or assets <= upper:
                return assets * rate
        else:
            result += max(min(assets, upper) - lower, 0) * rate
        lower = upper
    return result


def year_fraction(start, end, basis):
    fraction = Decimal(0)
    while start <= end:
        stop = min(end, date(start.year, 12, 31))
        denominator = 366 if basis == "actual/actual" and isleap(start.year) else 365
        fraction += Decimal((stop - start).days + 1) / denominator
        start = stop + timedelta(days=1)
    return fraction


def compute(doc):
    check(doc)
    findings = input_findings(doc)
    agreement = doc["agreement"]
    cited(agreement, doc, "agreement", findings)
    known = {a["account_id"] for a in doc["accounts"]}
    for a in doc["accounts"]:
        cited(a, doc, f"scope/{a['account_id']}", findings)
    start, end = (dated(doc["billing_period"][k], k) for k in ("start", "end"))
    next_day, total, has_assets = start, Decimal(0), False
    segment_rows = []
    economic_complete = True
    for segment in sorted(doc["valuation_segments"], key=lambda s: (s["start"], s["segment_id"])):
        a, b = dated(segment["start"], "start"), dated(segment["end"], "end")
        if a != next_day:
            finding(findings, "segment-coverage", "Valuation intervals overlap or leave a gap; full fee suppressed.")
            economic_complete = False
        next_day = b + timedelta(days=1)
        rows = segment["accounts"]
        if {r["account_id"] for r in rows} != known:
            finding(findings, "account-coverage", f"{segment['segment_id']}: missing declared billing accounts")
            economic_complete = False
        billable = Decimal(0)
        details = []
        for row in rows:
            cited(row, doc, row["account_id"], findings)
            total_value = sum((number(x["market_value"]) for x in row["assets"]), Decimal(0))
            if total_value != number(row["reported_total"]):
                finding(findings, "valuation-tieout", f"{row['account_id']}: asset values do not tie to reported total")
                economic_complete = False
            eligible = Decimal(0)
            for asset in row["assets"]:
                cited(asset, doc, asset["asset_id"], findings)
                if asset["fee_eligible"] is None:
                    finding(findings, "eligibility-unknown", f"{asset['asset_id']}: billability not established")
                    economic_complete = False
                elif asset["fee_eligible"]:
                    eligible += number(asset["market_value"])
                elif not nonempty(asset.get("exclusion_reason")):
                    finding(findings, "exclusion-evidence", f"{asset['asset_id']}: excluded without a documented reason")
            billable += eligible
            details.append({"account_id": row["account_id"], "reported_total": money(total_value),
                            "billable_assets": money(eligible), "assets": deepcopy(row["assets"]), "source_ids": row.get("source_ids", [])})
        annual = annual_fee(billable, agreement)
        charge = annual * year_fraction(a, b, agreement["day_basis"])
        total += charge
        has_assets = has_assets or billable > 0
        segment_rows.append({"segment_id": segment["segment_id"], "start": segment["start"], "end": segment["end"],
                             "days": (b - a).days + 1, "accounts": details, "billable_assets": money(billable),
                             "annual_fee": money(annual), "illustrative_segment_fee": money(charge)})
    if next_day != end + timedelta(days=1):
        finding(findings, "segment-coverage", "Valuation segments do not cover the full billing period")
        economic_complete = False
    minimum = number(agreement["minimum_period_fee"]) if has_assets or agreement["minimum_applies_at_zero"] else Decimal(0)
    adjustments = Decimal(0)
    for row in doc["adjustments"]:
        cited(row, doc, row["adjustment_id"], findings)
        adjustments += number(row["amount"])
    expected = max(max(total, minimum) + adjustments, 0) if economic_complete else None
    # Match the rounded invoice amount; do not round every day or tier.
    expected = Decimal(money(expected)) if expected is not None else None
    assessed = sum((number(row["amount"]) for row in doc["assessed_charges"]), Decimal(0))
    for row in doc["assessed_charges"]:
        cited(row, doc, row["charge_id"], findings)
    if not doc["billing_records_complete"]:
        finding(findings, "billing-record-gap", "The assessed-charge inventory is incomplete; variance suppressed")
    variance = assessed - expected if expected is not None and doc["billing_records_complete"] else None
    if variance is not None and variance != 0:
        finding(findings, "fee-variance", f"Assessed less calculated fee is {money(variance)} USD; request source reconciliation.")
    review = doc["conflict_review"]
    cited(review, doc, "conflict review", findings)
    if not nonempty(review.get("reviewed_by")) or review.get("reviewed_on") is None:
        finding(findings, "conflict-review-gap", "Conflict inventory needs an attributed dated review")
    elif not dated(review["reviewed_on"], "conflict review") <= dated(doc["as_of"], "as_of"):
        finding(findings, "conflict-review-date", "Conflict review is future-dated")
    for row in review["items"]:
        cited(row, doc, row["conflict_id"], findings)
        if row["status"] == "open" or not nonempty(row.get("treatment")):
            finding(findings, "economic-conflict", f"{row['conflict_id']}: conflict treatment remains unresolved")
    result = {"input_snapshot": deepcopy(doc), "segments": segment_rows,
              "calculation": {"currency": "USD", "unadjusted_period_fee": money(total), "minimum_period_fee": money(minimum),
                              "adjustments": money(adjustments), "expected_fee": money(expected) if expected is not None else None,
                              "assessed_charges": money(assessed), "assessed_minus_expected": money(variance) if variance is not None else None,
                              "economic_coverage_complete": economic_complete},
              "conflict_review": deepcopy(review), "posting_status": "not-posted", "refund_decision": "not-made"}
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    return output_errors(out, SKILL, compute)
