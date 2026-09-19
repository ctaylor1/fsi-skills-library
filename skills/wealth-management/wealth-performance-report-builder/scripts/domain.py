"""Flow-boundary time-weighted return reporting; no annualization or GIPS assertion."""
from copy import deepcopy
from decimal import Decimal

from wealth_contract import make_output, nonempty
from wealth_analysis import (cited, common, dated, finding, input_findings, money,
                            number, output_errors, precise, records, require)

SKILL = "wealth-performance-report-builder"
FIELDS = ("opening_value", "ending_value", "external_flow_start", "external_flow_end",
          "internal_flow_start", "internal_flow_end", "fees_end")


def check(doc):
    common(doc)
    require(doc.get("currency") == "USD", "only USD values supported; no inferred currency conversion")
    accounts = records(doc.get("accounts"), "account_id", "account scope")
    known = {r["account_id"] for r in accounts}
    report = doc.get("report_period")
    require(isinstance(report, dict), "report_period required")
    start, end = dated(report.get("start"), "report start"), dated(report.get("end"), "report end")
    require(start < end <= dated(doc["as_of"], "as_of"), "closed ordered report period required")
    policy = doc.get("methodology")
    require(isinstance(policy, dict), "methodology required")
    for key in ("version", "owner"):
        require(nonempty(policy.get(key)), f"methodology.{key} required")
    require(policy.get("method") == "flow-boundary-twr", "method must be flow-boundary-twr")
    require(policy.get("fee_timing") == "end-of-subperiod", "explicit end-of-subperiod fee convention required")
    require(type(policy.get("all_flows_at_boundaries")) is bool, "all_flows_at_boundaries must be explicit")
    number(policy.get("return_tolerance_bps"), "return tolerance", 0)
    for period in records(doc.get("subperiods"), "period_id", "subperiods", empty=True):
        a, b = dated(period.get("start"), "subperiod start"), dated(period.get("end"), "subperiod end")
        require(start <= a < b <= end, "subperiod outside report interval")
        for row in records(period.get("accounts"), "account_id", "subperiod accounts", empty=True):
            require(row["account_id"] in known, "performance account outside declared scope")
            for field in FIELDS:
                if row.get(field) is not None:
                    number(row[field], field, 0 if field in ("opening_value", "ending_value", "fees_end") else None, 2)
    official = doc.get("official_reference")
    require(isinstance(official, dict), "official_reference required (values may be null)")
    for key in ("household_end_value", "household_net_return_pct"):
        if official.get(key) is not None:
            number(official[key], key, 0 if key == "household_end_value" else None)
    benchmark = doc.get("benchmark")
    require(isinstance(benchmark, dict), "benchmark must be supplied or explicitly not applicable")
    require(type(benchmark.get("applicable")) is bool, "benchmark applicability must be explicit")
    if benchmark["applicable"]:
        for key in ("benchmark_id", "version", "rationale"):
            require(nonempty(benchmark.get(key)), f"benchmark.{key} required")
        for row in records(benchmark.get("returns"), "period_id", "benchmark returns", empty=True):
            number(row.get("return_pct"), "benchmark return", -100)
    else:
        require(nonempty(benchmark.get("reason")), "benchmark not-applicable reason required")


def returns(values):
    start_flow = values["external_flow_start"] + values["internal_flow_start"]
    end_flow = values["external_flow_end"] + values["internal_flow_end"]
    capital = values["opening_value"] + start_flow
    require(capital > 0, "positive invested capital required for subperiod return")
    net_factor = (values["ending_value"] - end_flow) / capital
    gross_factor = (values["ending_value"] - end_flow + values["fees_end"]) / capital
    require(net_factor >= 0, "negative post-flow residual is inconsistent with this long-only valuation model")
    return net_factor, gross_factor


def compute(doc):
    check(doc)
    findings = input_findings(doc)
    policy = doc["methodology"]
    cited(policy, doc, "methodology", findings)
    method_ok = policy["all_flows_at_boundaries"]
    if not method_ok:
        finding(findings, "flow-timing", "Intermediate flows require additional valuations; TWR suppressed")
    accounts = {r["account_id"]: r for r in doc["accounts"]}
    for row in accounts.values():
        cited(row, doc, row["account_id"], findings)
    factors = {aid: [Decimal(1), Decimal(1)] for aid in accounts}
    valid = {aid: method_ok for aid in accounts}
    active_seen = dict.fromkeys(accounts, False)
    prior_end = {}
    household_factors = [Decimal(1), Decimal(1)]
    household_valid = method_ok
    next_start = doc["report_period"]["start"]
    rows, fees, external_net = [], Decimal(0), Decimal(0)
    last_household_end = None
    for period in sorted(doc["subperiods"], key=lambda p: (p["start"], p["period_id"])):
        if period["start"] != next_start:
            finding(findings, "period-coverage", "Subperiods overlap or leave gaps; cumulative returns suppressed")
            valid = dict.fromkeys(accounts, False)
            household_valid = False
        next_start = period["end"]
        data = {r["account_id"]: r for r in period["accounts"]}
        totals = dict.fromkeys(FIELDS, Decimal(0))
        period_valid = method_ok
        details = []
        for aid in accounts:
            row = data.get(aid)
            if row is None or any(row.get(field) is None for field in FIELDS):
                finding(findings, "account-data-gap", f"{period['period_id']}/{aid}: missing valuation, fee or flow fields")
                valid[aid], period_valid = False, False
                details.append({"account_id": aid, "net_return_pct": None, "gross_return_pct": None, "status": "missing-data"})
                continue
            cited(row, doc, f"{period['period_id']}/{aid}", findings)
            values = {field: number(row[field]) for field in FIELDS}
            for field in FIELDS:
                totals[field] += values[field]
            if aid in prior_end and values["opening_value"] != prior_end[aid]:
                finding(findings, "valuation-continuity", f"{aid}: opening value differs from previous ending value")
                valid[aid], period_valid = False, False
            prior_end[aid] = values["ending_value"]
            if all(value == 0 for value in values.values()):
                details.append({"account_id": aid, "values": {k: money(v) for k, v in values.items()},
                                "net_return_pct": None, "gross_return_pct": None,
                                "status": "not-applicable-no-invested-capital", "source_ids": row.get("source_ids", [])})
                continue
            active_seen[aid] = True
            net, gross = None, None
            if method_ok:
                try:
                    net, gross = returns(values)
                    factors[aid][0] *= net
                    factors[aid][1] *= gross
                except ValueError as exc:
                    finding(findings, "return-not-evaluable", f"{period['period_id']}/{aid}: {exc}")
                    valid[aid], period_valid = False, False
            details.append({"account_id": aid, "values": {k: money(v) for k, v in values.items()},
                            "net_return_pct": precise((net - 1) * 100) if net is not None else None,
                            "gross_return_pct": precise((gross - 1) * 100) if gross is not None else None,
                            "source_ids": row.get("source_ids", [])})
        for field in ("internal_flow_start", "internal_flow_end"):
            # Missing fees or valuations must not erase a known offsetting transfer.
            # Assert a break only when this particular flow is known for every account.
            if len(data) == len(accounts) and all(row.get(field) is not None for row in data.values()):
                internal_total = sum((number(row[field]) for row in data.values()), Decimal(0))
                if internal_total != 0:
                    finding(findings, "internal-transfer-break", f"{period['period_id']}/{field}: household internal transfers do not offset")
                    period_valid = False
        fees += totals["fees_end"]
        external_net += totals["external_flow_start"] + totals["external_flow_end"]
        net, gross = None, None
        if period_valid:
            try:
                net, gross = returns(totals)
                household_factors[0] *= net
                household_factors[1] *= gross
            except ValueError as exc:
                finding(findings, "household-return-not-evaluable", str(exc))
                period_valid = False
        household_valid = household_valid and period_valid
        last_household_end = sum((number(row["ending_value"]) for row in data.values()), Decimal(0)) if len(data) == len(accounts) and all(
            row.get("ending_value") is not None for row in data.values()) else None
        rows.append({"period_id": period["period_id"], "start": period["start"], "end": period["end"], "accounts": details,
                     "household_net_return_pct": precise((net - 1) * 100) if net is not None else None,
                     "household_gross_return_pct": precise((gross - 1) * 100) if gross is not None else None})
    if next_start != doc["report_period"]["end"]:
        finding(findings, "period-coverage", "Subperiods do not cover entire report interval")
        valid = dict.fromkeys(accounts, False)
        household_valid = False
    net = (household_factors[0] - 1) * 100 if household_valid else None
    gross = (household_factors[1] - 1) * 100 if household_valid else None
    official = doc["official_reference"]
    cited(official, doc, "official performance reference", findings)
    for key in ("household_end_value", "household_net_return_pct"):
        if official.get(key) is None:
            finding(findings, "official-reference-gap", f"{key}: no independent reference supplied")
    if official.get("household_end_value") is not None and last_household_end is not None:
        if number(official["household_end_value"]) != last_household_end:
            finding(findings, "closing-value-tieout", "Calculated household ending value differs from the reference")
    if official.get("household_net_return_pct") is not None and net is not None:
        if abs(number(official["household_net_return_pct"]) - net) * 100 > number(policy["return_tolerance_bps"]):
            finding(findings, "official-return-tieout", "Computed net return differs from the reference beyond the supplied tolerance")
    benchmark = doc["benchmark"]
    cited(benchmark, doc, "benchmark applicability", findings)
    benchmark_return = None
    if benchmark["applicable"]:
        ids = {row["period_id"] for row in doc["subperiods"]}
        given = {r["period_id"]: r for r in benchmark["returns"]}
        if benchmark.get("currency") != "USD" or set(given) != ids or not household_valid:
            finding(findings, "benchmark-comparability", "Benchmark currency, subperiod coverage or portfolio return is not comparable")
        else:
            factor = Decimal(1)
            for row in benchmark["returns"]:
                cited(row, doc, f"benchmark/{row['period_id']}", findings)
                factor *= 1 + number(row["return_pct"]) / 100
            benchmark_return = (factor - 1) * 100
    result = {"input_snapshot": deepcopy(doc), "subperiods": rows,
              "account_returns": [{"account_id": aid, "net_return_pct": precise((factors[aid][0] - 1) * 100) if valid[aid] and active_seen[aid] else None,
                                   "gross_return_pct": precise((factors[aid][1] - 1) * 100) if valid[aid] and active_seen[aid] else None,
                                   "status": "not-evaluable" if not valid[aid] else "calculated" if active_seen[aid] else "not-applicable-no-invested-capital"} for aid in accounts],
              "household": {"net_return_pct": precise(net) if net is not None else None,
                            "gross_return_pct": precise(gross) if gross is not None else None,
                            "ending_value": money(last_household_end) if last_household_end is not None else None,
                            "observed_fees": money(fees), "observed_net_external_flows": money(external_net),
                            "coverage_complete": household_valid},
              "benchmark_return_pct": precise(benchmark_return) if benchmark_return is not None else None,
              "net_less_benchmark_percentage_points": precise(net - benchmark_return) if net is not None and benchmark_return is not None else None,
              "annualized": False, "gips_compliance_asserted": False}
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    return output_errors(out, SKILL, compute)
