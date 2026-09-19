#!/usr/bin/env python3
"""Read-only settlement reconciliation and report-only payout explanation."""
from __future__ import annotations
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, localcontext, ROUND_HALF_UP
from pathlib import Path
from payment_contract import money, require_currency, stable_hash, VERSION

PARTITION = ("legal_entity_id", "account_id", "currency", "settlement_cycle")
SOURCES = ("network", "processor", "bank_cash", "ledger")
FIELDS = {"network": ("gross",), "processor": ("gross", "fees", "reserve", "refunds", "chargebacks", "adjustments", "net"),
          "bank_cash": ("amount",), "ledger": ("net",)}
DATES = {"network": "settlement_date", "processor": "settlement_date", "bank_cash": "value_date", "ledger": "post_date"}
FEES = {"interchange_fees", "scheme_fees", "processor_fees", "other_fees", "fees"}
DEDUCTIONS = FEES | {"refunds", "chargebacks", "reserve_held"}
CATEGORIES = FEES | {"gross_sales", "refunds", "chargebacks", "adjustments", "reserve_held", "reserve_released", "cash_advance", "net_settlement", "other"}
DISCLAIMER = "Read-only evidence comparison; no journal, payment repair, or system-of-record change is proposed or executed."
PAYOUT_DISCLAIMER = "Informational payout explanation only; not fee advice, bank-cash confirmation, or ledger reconciliation."


def amount(value):
    return None if value is None else money(value)


def serial(value):
    return None if value is None else format(value, "f")


def partition(record, defaults=None):
    defaults = defaults or {}
    return tuple(record.get(key, defaults.get(key)) for key in PARTITION)


def valid_date(value):
    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_input(doc):
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["input must be an object"], warnings
    mode = doc.get("mode", "reconcile-settlement")
    if mode not in ("reconcile-settlement", "explain-payout"):
        return ["mode must be reconcile-settlement or explain-payout"], warnings
    as_of = doc.get("as_of_date") if mode == "explain-payout" else doc.get("as_of")
    if not valid_date(as_of):
        errors.append("as_of/as_of_date must be a valid ISO date")
    if not isinstance(doc.get("config_version"), str) or not doc["config_version"].strip():
        errors.append("config_version required")
    config = doc.get("config", {})
    if not isinstance(config, dict):
        return errors + ["config must be an object"], warnings
    for field in ("amount_tolerance_abs", "fee_tolerance_abs", "reserve_tolerance_abs", "cash_tolerance_abs", "net_calc_tolerance_abs"):
        try:
            if money(config.get(field, "0.01")) < 0:
                errors.append(f"{field} cannot be negative")
        except (TypeError, ValueError, ArithmeticError):
            errors.append(f"{field} must be finite nonnegative money")
    units = config.get("currency_minor_units", {})
    if not isinstance(units, dict) or any(type(v) is not int or not 0 <= v <= 8 for v in units.values()):
        errors.append("currency_minor_units must map currencies to integer precision 0..8")
    if "cash_settlement_lag_days" in config:
        errors.append("cash_settlement_lag_days is unsupported; supply cited expected_funding_date")

    def row_check(row, label, defaults=None):
        if not isinstance(row, dict):
            errors.append(f"{label}: must be an object")
            return False
        key = partition(row, defaults)
        for field, value in zip(PARTITION, key):
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}: {field} required")
        try:
            require_currency(key[2])
        except ValueError:
            errors.append(f"{label}: invalid currency")
        return True

    def amounts_check(row, fields, label):
        for field in fields:
            try:
                amount(row.get(field))
            except (TypeError, ValueError, ArithmeticError):
                errors.append(f"{label}: {field} must be finite money or null")

    if mode == "explain-payout":
        for field in ("report_id", "merchant_id"):
            if not isinstance(doc.get(field), str) or not doc[field].strip():
                errors.append(f"{field} required")
        lines = doc.get("lines")
        if not isinstance(lines, list) or not lines:
            return errors + ["lines must be a nonempty list"], warnings
        for i, row in enumerate(lines):
            label = f"lines[{i}]"
            if not row_check(row, label, doc):
                continue
            for field in ("line_id", "category", "description"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    errors.append(f"{label}: {field} required")
            source = row.get("source")
            if not isinstance(source, dict) or not all(isinstance(source.get(k), str) and source[k].strip() for k in ("system", "ref")):
                errors.append(f"{label}: cited source.system/ref required")
            if row.get("settlement_date") is not None and not valid_date(row["settlement_date"]):
                errors.append(f"{label}: invalid settlement_date")
            amounts_check(row, ("gross_amount", "fee_amount", "net_amount"), label)
            if all(row.get(k) is None for k in ("gross_amount", "fee_amount", "net_amount")):
                warnings.append(f"{label}: unvalued line remains a data gap")
            if isinstance(row.get("category"), str) and row["category"] not in CATEGORIES:
                warnings.append(f"{label}: unmapped category retained as supplied")
        funding = doc.get("funding")
        if funding is not None:
            if row_check(funding, "funding", doc):
                amounts_check(funding, ("expected_net",), "funding")
                if not isinstance(funding.get("source_ref"), str) or not funding["source_ref"].strip():
                    errors.append("funding.source_ref required")
                if funding.get("funding_date") is not None and not valid_date(funding["funding_date"]):
                    errors.append("funding.funding_date invalid")
        return errors, warnings

    period = doc.get("period")
    if not isinstance(period, dict) or not all(valid_date(period.get(k)) for k in ("start", "end")):
        errors.append("period requires valid start and end dates")
    elif period["end"] < period["start"]:
        errors.append("period end precedes start")
    sources = doc.get("sources")
    if not isinstance(sources, dict) or not any(sources.get(k) for k in SOURCES):
        return errors + ["sources must contain at least one populated source list"], warnings
    for system, rows in sources.items():
        if system not in SOURCES or not isinstance(rows, list):
            errors.append(f"unsupported source or non-list: {system}")
            continue
        for i, row in enumerate(rows):
            label = f"{system}[{i}]"
            if not row_check(row, label):
                continue
            for field in ("record_id", "match_key", "source_ref"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    errors.append(f"{label}: {field} required")
            if not valid_date(row.get(DATES[system])):
                errors.append(f"{label}: invalid {DATES[system]}")
            amounts_check(row, FIELDS[system], label)
            if system == "processor":
                for field in ("fees", "reserve", "refunds", "chargebacks"):
                    try:
                        if row.get(field) is not None and money(row[field]) < 0:
                            errors.append(f"{label}: {field} is a positive deduction; use adjustments for signed changes")
                    except (ValueError, TypeError, ArithmeticError):
                        pass
            if row.get("expected_funding_date") is not None:
                if not valid_date(row["expected_funding_date"]) or not row.get("funding_due_source_ref"):
                    errors.append(f"{label}: expected_funding_date requires valid date and funding_due_source_ref")
    schedules = doc.get("fee_schedule", [])
    if not isinstance(schedules, list):
        return errors + ["fee_schedule must be a list"], warnings
    for i, row in enumerate(schedules):
        label = f"fee_schedule[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{label}: must be an object")
            continue
        for field in ("legal_entity_id", "account_id", "currency", "scheme", "version", "source_ref"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{label}: {field} required")
        try:
            require_currency(row.get("currency"))
        except ValueError:
            errors.append(f"{label}: invalid currency")
        if not valid_date(row.get("effective_from")) or (row.get("effective_to") is not None and not valid_date(row["effective_to"])):
            errors.append(f"{label}: valid effective interval required")
        elif row.get("effective_to") and row["effective_to"] < row["effective_from"]:
            errors.append(f"{label}: effective interval reversed")
        amounts_check(row, ("rate_bps", "reserve_bps"), label)
        for field in ("rate_bps", "reserve_bps"):
            try:
                if row.get(field) is not None and money(row[field]) < 0:
                    errors.append(f"{label}: {field} cannot be negative")
            except (ValueError, TypeError, ArithmeticError):
                pass
    return errors, warnings


def compute(doc):
    errors, warnings = validate_input(doc)
    if errors:
        raise ValueError("; ".join(errors))
    with localcontext() as ctx:
        ctx.prec = 60
        result = explain(doc) if doc.get("mode") == "explain-payout" else reconcile(doc)
    return {"schema_version": "1.0", "skill": "payment-settlement-reconciler",
            "input_hash": stable_hash(doc), "source_snapshot": doc, "config_version": doc["config_version"],
            "warnings": warnings, **result}


def reconcile(doc):
    cfg = doc.get("config", {})
    indexed = defaultdict(lambda: defaultdict(list))
    identity_uses = defaultdict(set)
    for source, rows in doc["sources"].items():
        for row in rows:
            key = partition(row) + (row["match_key"],)
            indexed[key][source].append(row)
            namespace = (row["legal_entity_id"], row["account_id"])
            identity_uses[("record_id", source, namespace, row["record_id"])].add(key)
            identity_uses[("source_ref", source, (), row["source_ref"])].add(key)
    identity_conflicts = defaultdict(list)
    for identity, uses in sorted(identity_uses.items()):
        if len(uses) > 1:
            conflict = {"source": identity[1], "identity_field": identity[0], "identity_value": identity[3],
                        "source_namespace": list(identity[2]),
                        "references": [{"partition": dict(zip(PARTITION, key[:4])), "match_key": key[4]} for key in sorted(uses)]}
            for key in uses:
                identity_conflicts[key].append(conflict)
    groups, by_partition = [], defaultdict(list)
    for key, sources in sorted(indexed.items()):
        scope = dict(zip(PARTITION, key[:4]))
        identity = {"partition": scope, "match_key": key[4]}
        evidence = [{"evidence_id": r["record_id"], "status": "supplied", "source": source,
                     "source_ref": f"{source}:{r['source_ref']}@{r[DATES[source]]}"}
                    for source, rows in sorted(sources.items()) for r in sorted(rows, key=lambda r: (r["record_id"], r["source_ref"]))]
        duplicated = sorted(source for source, rows in sources.items() if len(rows) > 1)
        duplicate_ids = sorted({record_id for (_, record_id), n in Counter((e["source"], e["evidence_id"]) for e in evidence).items() if n > 1})
        quarantine = bool(duplicated or duplicate_ids or identity_conflicts[key])
        values = {source: {field: None if quarantine or source not in sources else amount(sources[source][0].get(field))
                           for field in FIELDS[source]} for source in SOURCES}
        checks, issues, pending = [], [], []
        if quarantine:
            issues.append({"type": "AMBIGUOUS_DUPLICATE", "sources": duplicated, "record_ids": duplicate_ids, "difference": None})
            if identity_conflicts[key]:
                issues[-1]["reused_source_identities"] = identity_conflicts[key]
        else:
            def compare(kind, left, right, tolerance_field, extra_evidence=None):
                diff = right - left if left is not None and right is not None else None
                tol = money(cfg.get(tolerance_field, "0.01"))
                status = "not_evaluable" if diff is None else "within_tolerance" if abs(diff) <= tol else "mismatch"
                check = {"type": kind, "expected": serial(left), "observed": serial(right),
                         "observed_minus_expected": serial(diff), "tolerance": serial(tol), "status": status}
                if extra_evidence:
                    check["additional_source_refs"] = extra_evidence
                checks.append(check)
                if status == "mismatch":
                    issues.append({"type": kind, "difference": serial(diff)})
            n, p, b, l = (values[s] for s in SOURCES)
            compare("GROSS_MISMATCH", n["gross"], p["gross"], "amount_tolerance_abs")
            waterfall = [p[k] for k in ("gross", "fees", "reserve", "refunds", "chargebacks", "adjustments")]
            net = waterfall[0] - sum(waterfall[1:5], Decimal(0)) + waterfall[5] if all(v is not None for v in waterfall) else None
            compare("NET_CALC_MISMATCH", net, p["net"], "net_calc_tolerance_abs")
            compare("NET_CASH_MISMATCH", p["net"], b["amount"], "cash_tolerance_abs")
            compare("LEDGER_SETTLEMENT_MISMATCH", p["net"], l["net"], "net_calc_tolerance_abs")
            compare("LEDGER_CASH_MISMATCH", b["amount"], l["net"], "cash_tolerance_abs")
            processor = sources.get("processor", [None])[0]
            schedules = []
            if processor:
                schedules = [s for s in doc.get("fee_schedule", [])
                             if all(s[k] == processor[k] for k in PARTITION[:3])
                             and s["scheme"] == processor.get("scheme")
                             and s["effective_from"] <= processor["settlement_date"]
                             and (not s.get("effective_to") or processor["settlement_date"] <= s["effective_to"])]
            units = cfg.get("currency_minor_units", {}).get(scope["currency"])
            schedule = schedules[0] if len(schedules) == 1 else None
            for kind, rate_field, actual_field, tol_field in (("FEE_VARIANCE", "rate_bps", "fees", "fee_tolerance_abs"),
                                                            ("RESERVE_VARIANCE", "reserve_bps", "reserve", "reserve_tolerance_abs")):
                rate = amount(schedule.get(rate_field)) if schedule else None
                expected = (p["gross"] * rate / Decimal(10000)).quantize(Decimal(1).scaleb(-units), rounding=ROUND_HALF_UP) if p["gross"] is not None and rate is not None and units is not None else None
                compare(kind, expected, p[actual_field], tol_field, [schedule["source_ref"]] if schedule else None)
                if expected is None:
                    checks[-1]["reason"] = "ambiguous schedule" if len(schedules) > 1 else "missing scoped effective schedule, rate, gross, or currency precision"
            settled = bool(sources.get("network") or sources.get("processor"))
            if settled and "bank_cash" not in sources:
                due_rows = [r for source in ("processor", "network") for r in sources.get(source, []) if r.get("expected_funding_date")]
                dues = {r["expected_funding_date"] for r in due_rows}
                if len(dues) == 1 and doc["as_of"] < next(iter(dues)):
                    pending.append({"type": "PENDING_FUNDING", "due_date": next(iter(dues)), "expected_net": serial(p["net"]),
                                    "source_refs": [r["funding_due_source_ref"] for r in due_rows]})
                else:
                    issues.append({"type": "MISSING_IN_BANK", "difference": None,
                                   "reason": "conflicting funding dates" if len(dues) > 1 else "no bank evidence; due date absent or reached"})
            if settled and "ledger" not in sources:
                issues.append({"type": "MISSING_IN_LEDGER", "difference": None})
            if not settled:
                issues.append({"type": "MISSING_IN_SETTLEMENT", "difference": None})
            if "network" not in sources:
                issues.append({"type": "MISSING_NETWORK", "difference": None})
            if "processor" not in sources:
                issues.append({"type": "MISSING_PROCESSOR", "difference": None})
            for source, rows in sorted(sources.items()):
                for field, value in values[source].items():
                    if value is None:
                        issues.append({"type": "UNVALUED_FIELD", "source": source, "field": field, "difference": None})
        for issue in issues:
            issue["issue_id"] = stable_hash({**identity, **issue})
        complete = not quarantine and not issues and not pending and all(c["status"] == "within_tolerance" for c in checks)
        group = {**identity, "group_id": stable_hash(identity), "status": "quarantined" if quarantine else "matched" if complete else "needs_review" if issues else "incomplete",
                 "source_values": {s: {f: serial(v) for f, v in fields.items()} for s, fields in values.items()},
                 "checks": checks, "issues": issues, "pending_items": pending, "evidence": evidence}
        groups.append(group)
        by_partition[key[:4]].append(group)
    totals = []
    for key, members in sorted(by_partition.items()):
        scoped = {}
        for source in SOURCES:
            for field in FIELDS[source]:
                known = [amount(g["source_values"][source][field]) for g in members]
                count = sum(v is not None for v in known)
                subtotal = sum((v for v in known if v is not None), Decimal(0)) if count else None
                scoped[f"{source}.{field}"] = {"total": serial(subtotal) if count == len(members) else None,
                                             "known_subtotal": serial(subtotal), "known_groups": count,
                                             "missing_or_quarantined_groups": len(members) - count}
        totals.append({"partition": dict(zip(PARTITION, key)), "source_totals": scoped})
    handoffs = []
    for group in groups:
        if group["status"] == "matched":
            continue
        identity = {"partition": group["partition"], "match_key": group["match_key"]}
        handoffs.append({"contract_version": VERSION, "handoff_id": stable_hash({"identity": identity, "issues": group["issues"], "checks": group["checks"]}),
                         "source_skill": "payment-settlement-reconciler", "target_skill": "bank-payment-exception-investigator",
                         "case_id": group["group_id"], "lead_owner": "settlement-operations",
                         "requested_output": "Investigate evidence gaps and differences; no accounting instruction",
                         "action_mode": "read-only", "source_refs": [e["source_ref"] for e in group["evidence"]],
                         "unresolved_issues": group["issues"] + group["pending_items"] + [c for c in group["checks"] if c["status"] == "not_evaluable"],
                         "target_input": identity, "target_validation": "required", "authority_granted": False})
    return {"mode": "reconcile-settlement", "as_of": doc["as_of"], "period": doc["period"], "groups": groups,
            "partition_totals": totals, "investigation_handoffs": handoffs,
            "summary": {"group_count": len(groups), "issue_count": sum(len(g["issues"]) for g in groups),
                        "fully_evaluated_and_matched": bool(groups) and all(g["status"] == "matched" for g in groups)},
            "disclaimer": DISCLAIMER}


def line_value(row):
    if row.get("net_amount") is not None:
        return money(row["net_amount"]), "net_amount"
    if row.get("fee_amount") is not None and row["category"] in FEES:
        return -abs(money(row["fee_amount"])), "negative fee_amount"
    if row.get("gross_amount") is not None:
        return money(row["gross_amount"]), "signed gross_amount"
    return None, "unvalued"


def explain(doc):
    indexed = defaultdict(list)
    line_id_counts = Counter(row["line_id"] for row in doc["lines"])
    citation_counts = Counter((row["source"]["system"], row["source"]["ref"]) for row in doc["lines"])
    for row in doc["lines"]:
        indexed[partition(row, doc)].append(row)
    funding = doc.get("funding")
    if funding is not None:
        indexed.setdefault(partition(funding, doc), [])
    outputs = []
    tol = money(doc.get("config", {}).get("amount_tolerance_abs", "0.01"))
    for key, rows in sorted(indexed.items()):
        categories, controls, gaps, issues = [], [], [], []
        for row in sorted(rows, key=lambda r: (r["line_id"], r["source"]["ref"])):
            value, basis = line_value(row)
            citation = f"{row['source']['system']}:{row['source']['ref']}@{row.get('settlement_date', doc['as_of_date'])}"
            line = {"line_id": row["line_id"], "category": row["category"], "amount": serial(value),
                    "basis": basis, "source_ref": citation, "evidence_status": "supplied"}
            source_identity = (row["source"]["system"], row["source"]["ref"])
            if line_id_counts[row["line_id"]] > 1 or citation_counts[source_identity] > 1:
                gaps.append({"type": "AMBIGUOUS_DUPLICATE", "line_id": row["line_id"], "source_ref": citation})
                line["amount"], line["basis"] = None, "quarantined duplicate"
                value = None
            if row["category"] == "gross_sales" and row.get("gross_amount") is not None and row.get("net_amount") is not None and money(row["gross_amount"]) != money(row["net_amount"]):
                gaps.append({"type": "COMPOSITE_SALES_LINE", "line_id": row["line_id"], "source_ref": citation})
                line["amount"], line["basis"] = None, "requires component normalization"
                value = None
            if row["category"] == "net_settlement":
                controls.append(line)
                continue
            if value is None:
                gaps.append({"type": "UNVALUED_LINE", "line_id": row["line_id"], "source_ref": citation})
            if value is not None and row["category"] in DEDUCTIONS and value > 0:
                issues.append({"type": "SIGN_CONVENTION_CONFLICT", "line_id": row["line_id"], "source_ref": citation})
            if row.get("net_amount") is not None and row.get("fee_amount") is not None and row["category"] in FEES:
                if money(row["net_amount"]) != -abs(money(row["fee_amount"])):
                    issues.append({"type": "FEE_LINE_CONFLICT", "line_id": row["line_id"], "source_ref": citation})
            categories.append(line)
        known = [money(c["amount"]) for c in categories if c["amount"] is not None]
        subtotal = sum(known, Decimal(0)) if known else None
        complete = bool(categories) and all(c["amount"] is not None for c in categories)
        calculated = subtotal if complete else None
        reported = amount(controls[0]["amount"]) if len(controls) == 1 else None
        if len(controls) > 1:
            issues.append({"type": "AMBIGUOUS_REPORTED_NET", "line_ids": [c["line_id"] for c in controls]})
        scoped_funding = funding is not None and partition(funding, doc) == key
        expected = amount(funding.get("expected_net")) if scoped_funding else None
        checks = []
        for kind, left, right in (("calculated_vs_reported", calculated, reported),
                                  ("calculated_vs_funding", calculated, expected),
                                  ("reported_vs_funding", reported, expected)):
            diff = right - left if left is not None and right is not None else None
            checks.append({"type": kind, "right_minus_left": serial(diff),
                           "status": "not_evaluable" if diff is None else "within_tolerance" if abs(diff) <= tol else "mismatch"})
        fee_lines = [c for c in categories if c["category"] in FEES]
        fee_total = sum((abs(money(c["amount"])) for c in fee_lines), Decimal(0)) if fee_lines and all(c["amount"] is not None for c in fee_lines) else None
        sales_lines = [c for c in categories if c["category"] == "gross_sales"]
        gross = sum((money(c["amount"]) for c in sales_lines), Decimal(0)) if sales_lines and all(c["amount"] is not None for c in sales_lines) else None
        rate = (fee_total / gross * 100).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP) if gross is not None and gross > 0 and fee_total is not None else None
        outputs.append({"partition": dict(zip(PARTITION, key)), "categories": categories, "reported_net_lines": controls,
                        "known_line_subtotal": serial(subtotal), "calculated_net": serial(calculated), "reported_net": serial(reported),
                        "funding_expected_net": serial(expected), "funding_source_ref": funding["source_ref"] if scoped_funding else None,
                        "gross_sales": serial(gross), "total_fees": serial(fee_total), "effective_fee_rate_pct": serial(rate),
                        "checks": checks, "data_gaps": gaps, "issues": issues,
                        "status": "discrepancy" if issues or any(c["status"] == "mismatch" for c in checks) else "incomplete" if gaps or not complete else "explained"})
    return {"mode": "explain-payout", "as_of_date": doc["as_of_date"], "report_id": doc["report_id"],
            "merchant_id": doc["merchant_id"], "partitions": outputs,
            "summary": {"partition_count": len(outputs), "bank_cash_confirmed": False, "ledger_reconciled": False,
                        "discrepancy_count": sum(len(p["issues"]) + sum(c["status"] == "mismatch" for c in p["checks"]) for p in outputs)},
            "disclaimer": PAYOUT_DISCLAIMER}


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/recon_example.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    try:
        doc = json.loads(path.read_text() if path else sys.stdin.read(), parse_float=str)
        print(json.dumps(compute(doc), indent=2))
        return 0
    except (ValueError, TypeError, ArithmeticError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
