"""Draft single-currency journal, accrual and supplied-valuation/class NAV workpapers."""
from decimal import Decimal
from foundation_contract import D, date_value, exact, ratio, validate_common, validate_referenced_sources, validate_actual_date, finish, cli_compute

SKILL = "fund-accounting-preparer"


@exact
def compute(doc):
    errors = validate_common(doc) + validate_referenced_sources(doc)
    if errors: raise ValueError("; ".join(errors))
    if any(date_value(source["as_of"]) > date_value(source["known_at"]) for source in doc["sources"]): raise ValueError("historical observation source cannot be known before its economic as_of")
    if doc["currency"] == "not-applicable": raise ValueError("supplied monetary/return currency required")
    mode, issues = doc.get("mode"), []
    if mode == "journal_trial_balance":
        accounts, journals = doc["accounts"], doc["journals"]
        if not isinstance(accounts, list) or not 1 <= len(accounts) <= 1000 or not isinstance(journals, list) or len(journals) > 1000: raise ValueError("bounded account and journal lists required")
        balances, movement, ids, rows = {}, {}, set(), []
        for account in accounts:
            aid = account["account_id"]
            if not isinstance(aid, str) or not aid or aid in balances: raise ValueError("unique nonempty account_id required")
            if account["type"] not in {"asset", "liability", "equity", "income", "expense"}: raise ValueError("unknown account type")
            if not account.get("source_ref"): raise ValueError("account source_ref required")
            balances[aid] = D(account["opening_debit_balance"]); movement[aid] = Decimal(0)
        if sum(balances.values()) != 0: raise ValueError("opening trial balance must balance; credits are negative signed balances")
        for journal in journals:
            if not journal["journal_id"] or journal["journal_id"] in ids: raise ValueError("unique journal_id required")
            ids.add(journal["journal_id"])
            if date_value(journal["date"]) > date_value(doc["as_of"]) or not journal.get("source_ref"): raise ValueError("journal date/source invalid")
            validate_actual_date(doc, journal["date"], journal["source_ref"])
            lines = journal["lines"]
            if not isinstance(lines, list) or not 2 <= len(lines) <= 1000: raise ValueError("journal requires2..1000 lines")
            debit, credit = Decimal(0), Decimal(0)
            for line in lines:
                aid, dr, cr = line["account_id"], D(line["debit"]), D(line["credit"])
                if aid not in balances or dr < 0 or cr < 0 or (dr > 0) == (cr > 0): raise ValueError("registered account and exactly one positive debit/credit required")
                movement[aid] += dr - cr; debit += dr; credit += cr
            if debit != credit: raise ValueError("unbalanced journal: " + journal["journal_id"])
            rows.append({"journal_id": journal["journal_id"], "debits": str(debit), "credits": str(credit), "balanced": True})
        result = {"journal_controls": rows, "accounts": [{"account_id": aid, "opening_debit_balance": str(value), "movement": str(movement[aid]), "closing_debit_balance": str(value + movement[aid])} for aid, value in balances.items()], "closing_trial_balance": str(sum(balances.values()) + sum(movement.values())), "posting_performed": False}
    elif mode == "accrual":
        rows = doc["accruals"]
        if not isinstance(rows, list) or not 1 <= len(rows) <= 1000: raise ValueError("1..1000 accrual rows required")
        ids, result_rows, total = set(), [], Decimal(0)
        for row in rows:
            if not row["accrual_id"] or row["accrual_id"] in ids: raise ValueError("unique accrual_id required")
            ids.add(row["accrual_id"])
            if row.get("day_count") != "ACT/365" or not row.get("source_ref"): raise ValueError("ACT/365 and source_ref required")
            start, end = date_value(row["start"]), date_value(row["end"])
            principal, rate = D(row["principal"]), D(row["annual_rate"])
            if not start < end <= date_value(doc["as_of"]) or principal < 0 or not 0 <= rate <= 1: raise ValueError("accrual date/principal/rate outside supported bounds")
            # This is a computed accrual horizon from fixed supplied terms, not
            # an observed terminal valuation. Terms may be known before end.
            if end > date_value(doc["knowledge_cutoff"]): raise ValueError("actual observation date exceeds knowledge cutoff for historical accrual horizon")
            amount = Decimal(ratio(principal * rate * Decimal((end - start).days), Decimal(365), 8)); total += amount
            result_rows.append({"accrual_id": row["accrual_id"], "days_excluding_start": (end - start).days, "expense_accrual": str(amount), "source_ref": row["source_ref"]})
        result = {"accrual_workpaper": result_rows, "total_expense_accrual": str(total), "rounding": "8 decimal places per accrual; no currency minor-unit booking implied", "posting_performed": False}
    elif mode == "nav_workpaper":
        assets, liabilities, classes = doc["assets"], doc["liabilities"], doc["classes"]
        if any(not isinstance(v, list) or len(v) > 1000 for v in (assets, liabilities, classes)) or not assets or not classes: raise ValueError("bounded assets/liabilities/classes lists required")
        ids = set()
        def total_rows(rows):
            total = Decimal(0)
            for row in rows:
                if not row["line_id"] or row["line_id"] in ids or not row.get("source_ref"): raise ValueError("unique cross-book line_id and source_ref required")
                validate_actual_date(doc, doc["as_of"], row["source_ref"])
                ids.add(row["line_id"]); amount = D(row["amount"])
                if amount < 0: raise ValueError("asset/liability amounts must be nonnegative; no sign inference")
                total += amount
            return total
        asset_total, liability_total = total_rows(assets), total_rows(liabilities)
        common_net = asset_total - liability_total
        if common_net <= 0: raise ValueError("nonpositive common net assets unsupported")
        weight_total, expense_total, class_rows, class_ids = Decimal(0), Decimal(0), [], set()
        for row in classes:
            if not row["class_id"] or row["class_id"] in class_ids or not row.get("source_ref"): raise ValueError("unique class_id and source_ref required")
            validate_actual_date(doc, doc["as_of"], row["source_ref"])
            class_ids.add(row["class_id"])
            weight, shares, expense = D(row["allocation_weight"]), D(row["shares_outstanding"]), D(row["class_specific_expense"])
            if not 0 <= weight <= 1 or shares <= 0 or expense < 0: raise ValueError("invalid class allocation/shares/expense")
            allocated = common_net * weight - expense
            if allocated <= 0: raise ValueError("nonpositive class net assets unsupported")
            weight_total += weight; expense_total += expense
            class_rows.append({"class_id": row["class_id"], "net_assets": str(allocated), "shares_outstanding": str(shares), "indicative_nav_per_share": ratio(allocated, shares, 8), "source_ref": row["source_ref"]})
        if weight_total != 1: raise ValueError("class allocation weights must sum exactly to1")
        fund_nav = common_net - expense_total
        benchmark = doc["system_of_record_benchmark"]
        for key in ("engine_id", "engine_version", "run_id", "source_ref", "engine_contract_source_ref", "acceptance_evidence_source_ref"):
            if not isinstance(benchmark.get(key), str) or not benchmark[key].strip(): raise ValueError("system-of-record benchmark identity/version/source required")
        if any(benchmark.get(k) != doc[k] for k in ("object_id", "as_of", "currency")): raise ValueError("benchmark object/date/currency mismatch")
        validate_actual_date(doc, benchmark["as_of"], benchmark["source_ref"])
        tolerance, benchmark_nav = D(doc["nav_tolerance"]), D(benchmark["nav"])
        if tolerance < 0 or benchmark_nav <= 0: raise ValueError("benchmark NAV/tolerance outside bounds")
        difference = fund_nav - benchmark_nav
        if abs(difference) > tolerance: issues.append("NAV workpaper differs from supplied system-of-record benchmark beyond tolerance")
        result = {"assets": str(asset_total), "common_liabilities": str(liability_total), "class_specific_expenses": str(expense_total), "indicative_fund_nav": str(fund_nav), "classes": class_rows, "benchmark_nav": str(benchmark_nav), "benchmark_difference": str(difference), "within_supplied_tolerance": abs(difference) <= tolerance, "benchmark_identity": {key: benchmark[key] for key in ("engine_id", "engine_version", "run_id", "engine_contract_source_ref", "acceptance_evidence_source_ref")}, "benchmark_acceptance_authenticated": False, "authoritative_nav_struck": False}
    else: raise ValueError("mode must be journal_trial_balance, accrual or nav_workpaper")
    return finish(doc, SKILL, "single-currency-workpaper-" + mode + "-v1", result, issues=issues,
                  limitations=["Draft workpaper only; enterprise accounting engine and administrator remain authoritative. No posting, striking or release.", "No trade capture, FX, tax, fair-value or ledger-to-NAV engine. Class allocation weights and values are supplied; class expenses must not duplicate common liabilities.", "Journal and cash sums are exact Decimal; accruals and NAV/share use explicitly rounded8-place ratios."], handoffs=["fund-nav-control-reviewer", "fund-valuation-oversight-reviewer", "investment-book-reconciler"])


if __name__ == "__main__": cli_compute(compute)
