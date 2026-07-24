#!/usr/bin/env python3
"""Deterministic input validation for loan-interest-fee-calculator.

Validates a loan-recalculation input file before the workbook is built. Fails closed on
structural problems (no calculation section present, non-numeric principal/rate, malformed
dates, participation shares that cannot sum to 1, unsupported amortization method); warns on
data-quality gaps that weaken the workbook (missing provenance/citation on a cited amount,
unrecognized day-count convention, missing rate-table/config version, end-before-start
accrual windows).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  case_id, loan_id, as_of (YYYY-MM-DD), calc_date (YYYY-MM-DD), config_version,
  rate_table_version, currency, day_count_default,
  interest_accruals[]{id,principal,annual_rate,start,end,day_count,book_amount?},
  fees[]{id,type,basis(flat|pct_balance|pct_payment),amount|rate+base,book_amount?},
  amortization{principal,annual_rate,term_periods,periods_per_year,method},
  settlement{payoff_date,principal_outstanding,accrued_interest,fees_due,unapplied_funds,
             per_diem,per_diem_days,book_amount?},
  participations{total_amount,participants[]{id,share_pct,book_amount?}},
  approved_engine_totals{...}, thresholds{materiality}
Each cited amount is an object {value, provenance, citation}.

Usage:
  python validate_input.py loan_calc_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
KNOWN_DAY_COUNTS = {"30/360", "30e/360", "actual/360", "actual/365", "actual/365f",
                    "act/360", "act/365", "actual/365fixed"}
CALC_SECTIONS = ("interest_accruals", "fees", "amortization", "settlement", "participations")


def _v(node):
    try:
        return float(node.get("value") if isinstance(node, dict) else node)
    except (TypeError, ValueError, AttributeError):
        return None


def _prov_cite(node):
    if isinstance(node, dict):
        return (node.get("provenance") or "").strip(), (node.get("citation") or "").strip()
    return "", ""


def _check_amount(node, label, errors, warnings, *, require=True):
    if node is None:
        if require:
            errors.append(f"{label} is required")
        return
    if _v(node) is None:
        errors.append(f"{label} value is not numeric")
    prov, cite = _prov_cite(node)
    if not prov:
        warnings.append(f"{label} has no provenance — validate_output will reject the workbook")
    if not cite:
        warnings.append(f"{label} has no citation — validate_output will reject the workbook")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not doc.get("loan_id"):
        errors.append("missing 'loan_id'")
    for k in ("as_of", "calc_date"):
        if k not in doc:
            errors.append(f"missing '{k}'")
        elif not DATE_RE.match(str(doc[k])):
            errors.append(f"{k} must start YYYY-MM-DD, got {doc[k]!r}")
    if not doc.get("config_version"):
        warnings.append("no config_version — the workbook will not be reproducible against a config contract")
    if not doc.get("rate_table_version"):
        warnings.append("no rate_table_version — rates cannot be tied to an approved rate-table version")
    if not doc.get("case_id"):
        warnings.append("no case_id — a durable servicing case id should carry through the workbook")

    if not any(doc.get(s) for s in CALC_SECTIONS):
        errors.append(f"no calculation section present — supply at least one of {', '.join(CALC_SECTIONS)}")

    # interest accruals
    for i, line in enumerate(doc.get("interest_accruals") or []):
        lid = line.get("id", f"interest[{i}]")
        _check_amount(line.get("principal"), f"interest {lid}: principal", errors, warnings)
        _check_amount(line.get("annual_rate"), f"interest {lid}: annual_rate", errors, warnings)
        for dk in ("start", "end"):
            if not DATE_RE.match(str(line.get(dk, ""))):
                errors.append(f"interest {lid}: {dk} must be YYYY-MM-DD, got {line.get(dk)!r}")
        if DATE_RE.match(str(line.get("start", ""))) and DATE_RE.match(str(line.get("end", ""))):
            if str(line["end"]) < str(line["start"]):
                errors.append(f"interest {lid}: end {line['end']} is before start {line['start']}")
        conv = (line.get("day_count") or doc.get("day_count_default") or "30/360").lower().replace(" ", "")
        if conv not in KNOWN_DAY_COUNTS:
            warnings.append(f"interest {lid}: unrecognized day_count {conv!r} — engine defaults to 30/360")

    # fees
    for i, fee in enumerate(doc.get("fees") or []):
        fid = fee.get("id", f"fee[{i}]")
        basis = (fee.get("basis") or "flat").lower()
        if basis in ("pct_balance", "pct_payment", "percent"):
            _check_amount(fee.get("base"), f"fee {fid}: base", errors, warnings)
            _check_amount(fee.get("rate"), f"fee {fid}: rate", errors, warnings)
        elif basis == "flat":
            _check_amount(fee.get("amount"), f"fee {fid}: amount", errors, warnings)
        else:
            errors.append(f"fee {fid}: basis {basis!r} must be flat, pct_balance, or pct_payment")

    # amortization
    am = doc.get("amortization")
    if am:
        _check_amount(am.get("principal"), "amortization: principal", errors, warnings)
        _check_amount(am.get("annual_rate"), "amortization: annual_rate", errors, warnings)
        n = _v(am.get("term_periods"))
        if n is None or n <= 0 or n != int(n):
            errors.append(f"amortization: term_periods must be a positive integer, got {am.get('term_periods')!r}")
        method = (am.get("method") or "level_payment").lower()
        if method not in ("level_payment", "interest_only"):
            errors.append(f"amortization: method {method!r} must be level_payment or interest_only")

    # settlement
    st = doc.get("settlement")
    if st:
        _check_amount(st.get("principal_outstanding"), "settlement: principal_outstanding", errors, warnings)
        for opt in ("accrued_interest", "fees_due", "unapplied_funds", "per_diem"):
            if opt in st:
                _check_amount(st.get(opt), f"settlement: {opt}", errors, warnings, require=False)

    # participations
    pa = doc.get("participations")
    if pa:
        _check_amount(pa.get("total_amount"), "participations: total_amount", errors, warnings)
        parts = pa.get("participants") or []
        if len(parts) < 2:
            warnings.append("participations: fewer than 2 participants — allocation is trivial")
        share_sum = 0.0
        ok = True
        for i, p in enumerate(parts):
            s = _v(p.get("share_pct"))
            if s is None:
                errors.append(f"participations: participant[{i}] share_pct is not numeric")
                ok = False
            else:
                share_sum += s
            prov, cite = _prov_cite(p.get("share_pct"))
            if not prov or not cite:
                warnings.append(f"participations: participant {p.get('id', i)} share_pct missing provenance/citation")
        if ok and parts and abs(share_sum - 1.0) > 1e-6:
            errors.append(f"participations: shares must sum to 1.0, got {round(share_sum, 8)}")

    # thresholds
    thr = doc.get("thresholds") or {}
    if "materiality" in thr and _v(thr["materiality"]) is None:
        errors.append("thresholds.materiality is not numeric")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "loan_calc_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
