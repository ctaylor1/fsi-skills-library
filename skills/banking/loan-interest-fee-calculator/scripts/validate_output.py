#!/usr/bin/env python3
"""Deterministic output validation for loan-interest-fee-calculator.

Validates the final recalculation workbook (the calculate_or_transform core + an author
narrative) before it is presented or delivered. Checks, in the order of the archetype's
validation focus (Model & calculate) and the R2 tier boundary:

  1. Formula tie-outs, re-derived INDEPENDENTLY (not trusted from the workbook):
       - interest        == principal * annual_rate * year_fraction(day_count)
       - fee             == amount (flat) or base * rate (percent)
       - amortization    == each interest = balance_start * periodic_rate; principal +
                            interest = payment (non-final periods); principal sums to the
                            original balance; ending balance == 0
       - settlement      == principal + accrued + per-diem + fees - unapplied
       - participation   == allocations sum EXACTLY to the shared total
  2. Variance report: variance == computed - book, and status/material flags are correct.
  3. Reconciliation: recomputed grand totals tie to any stated approved-engine totals, and
     every stated total is reconciled (variance = recomputed - approved; status correct).
  4. Assumption provenance: every assumptions_register entry carries provenance AND citation.
  5. Reproducibility: calc_id, inputs_hash, and config_version present.
  6. HARD BOUNDARY (R2): the workbook takes NO posting/approval action —
       - action_taken == 'none' and no truthy posting/approval flag is set; and
       - the author narrative contains no language claiming an adjustment was posted, booked,
         applied, waived, reversed, or approved, and no personalized financial/legal/tax
         advice (deterministic prohibited-action / prohibited-advice screen; fails closed).
  7. Standing disclaimer present.

Usage:
  python validate_output.py loan_calc_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json
import re
import sys
from datetime import date
from pathlib import Path

TOL = 0.01
DISCLAIMER = ("Illustrative loan-servicing recalculation for analytical review only; not a "
              "posting, adjustment, waiver, reversal, or approval, and not financial, legal, "
              "or tax advice. Every figure is conditional on the cited agreement terms, "
              "servicing data, and approved rate tables, and a qualified human must review "
              "and separately authorize any account change.")

# Affirmative claims that an account change WAS made or a decision WAS taken. Worded so the
# standing disclaimer (which uses the negated "not a posting, adjustment, waiver...") does not
# self-trip; the disclaimer is stripped before scanning as a second safeguard.
PROHIBITED_ACTION_PATTERNS = [
    r"\b(i|we) (have |'ve )?(posted|booked|applied|adjusted|waived|reversed|credited|refunded)\b",
    r"\b(the )?(adjustment|correction|fee reversal|waiver|refund|credit) (has been|was|is) "
    r"(posted|booked|applied|approved|processed|made)\b",
    r"\b(i|we) (approve|approved|authorize|authorized) the (adjustment|correction|waiver|reversal|payoff|write-off)\b",
    r"\bposting (this|the) (adjustment|correction|entry) to (the )?(system of record|servicing system|ledger|core)\b",
    r"\b(the )?account (has been|was) (adjusted|corrected|credited|updated)\b",
    r"\bwrite off the (balance|loan|fee)\b",
]
# Personalized financial/legal/tax advice an R2 recalculation must not give.
PROHIBITED_ADVICE_PATTERNS = [
    r"\byou should (refinance|pay off|default|dispute|stop paying|sue|litigate)\b",
    r"\b(we|i) recommend (that you |you )?(refinance|pay off|default|dispute|settle)\b",
    r"\bthis (is|constitutes) (legal|tax|financial) advice\b",
    r"\bfor tax purposes,? you (should|must|can) (deduct|claim|write off)\b",
]


def _num(v, default=None):
    try:
        return float(v.get("value") if isinstance(v, dict) else v)
    except (TypeError, ValueError, AttributeError):
        return default


def _pdate(s):
    y, m, d = str(s).split("-")[:3]
    return date(int(y), int(m), int(d))


def _year_fraction(start, end, convention):
    d1, d2 = _pdate(start), _pdate(end)
    actual = (d2 - d1).days
    conv = (convention or "30/360").lower().replace(" ", "")
    if conv in ("actual/360", "act/360", "a/360"):
        return actual / 360.0
    if conv in ("actual/365", "act/365", "a/365", "actual/365f", "actual/365fixed"):
        return actual / 365.0
    dd1, dd2 = d1.day, d2.day
    if conv in ("30e/360", "30e", "eurobond"):
        dd1 = 30 if dd1 == 31 else dd1
        dd2 = 30 if dd2 == 31 else dd2
    else:
        if dd1 == 31:
            dd1 = 30
        if dd2 == 31 and dd1 == 30:
            dd2 = 30
    return (360 * (d2.year - d1.year) + 30 * (d2.month - d1.month) + (dd2 - dd1)) / 360.0


def _check_interest(pack, errors):
    for ln in pack.get("interest") or []:
        p = _num(ln.get("principal")); r = _num(ln.get("annual_rate"))
        if None in (p, r) or not ln.get("start") or not ln.get("end"):
            errors.append(f"interest {ln.get('id')}: missing principal/rate/dates")
            continue
        yf = _year_fraction(ln["start"], ln["end"], ln.get("day_count"))
        expect = round(p * r * yf, 2)
        got = _num(ln.get("computed_amount"))
        if got is None or abs(expect - got) > TOL:
            errors.append(f"interest {ln.get('id')}: tie-out fails (expected {expect}, got {got})")


def _check_fees(pack, errors):
    for fee in pack.get("fees") or []:
        d = fee.get("detail") or {}
        basis = d.get("basis", "flat")
        if basis in ("pct_balance", "pct_payment", "percent"):
            expect = round(_num(d.get("base"), 0.0) * _num(d.get("rate"), 0.0), 2)
        else:
            expect = round(_num(d.get("amount"), 0.0), 2)
        got = _num(fee.get("computed_amount"))
        if got is None or abs(expect - got) > TOL:
            errors.append(f"fee {fee.get('id')}: tie-out fails (expected {expect}, got {got})")


def _check_amortization(pack, errors):
    am = pack.get("amortization")
    if not am:
        return
    principal = _num(am.get("principal"), 0.0)
    ppy = int(_num(am.get("periods_per_year"), 12))
    r = _num(am.get("annual_rate"), 0.0) / ppy
    rows = am.get("schedule") or []
    if not rows:
        errors.append("amortization: empty schedule")
        return
    method = (am.get("method") or "level_payment").lower()
    payment = _num(am.get("scheduled_payment"))
    principal_sum = 0.0
    for i, row in enumerate(rows):
        bstart = _num(row.get("balance_start")); it = _num(row.get("interest"))
        pt = _num(row.get("principal")); pay = _num(row.get("payment"))
        if None in (bstart, it, pt, pay):
            errors.append(f"amortization period {row.get('period')}: missing fields")
            continue
        if abs(round(bstart * r, 2) - it) > TOL:
            errors.append(f"amortization period {row.get('period')}: interest tie-out fails "
                          f"(expected {round(bstart * r, 2)}, got {it})")
        if abs(round(pt + it, 2) - pay) > TOL:
            errors.append(f"amortization period {row.get('period')}: payment != principal + interest")
        if method == "level_payment" and i < len(rows) - 1 and payment is not None \
                and abs(pay - payment) > TOL:
            errors.append(f"amortization period {row.get('period')}: payment {pay} != scheduled {payment}")
        principal_sum = round(principal_sum + pt, 2)
    if abs(principal_sum - round(principal, 2)) > TOL:
        errors.append(f"amortization: principal repaid {principal_sum} != original {round(principal, 2)}")
    if abs(_num(rows[-1].get("balance_end"), 1.0)) > TOL:
        errors.append(f"amortization: ending balance {rows[-1].get('balance_end')} != 0")


def _check_settlement(pack, errors):
    st = pack.get("settlement")
    if not st:
        return
    comps = st.get("components") or []
    expect = round(sum(_num(c.get("amount"), 0.0) for c in comps), 2)
    got = _num(st.get("computed_amount"))
    if got is None or abs(expect - got) > TOL:
        errors.append(f"settlement: payoff tie-out fails (component sum {expect}, got {got})")


def _check_participations(pack, errors):
    pa = pack.get("participations")
    if not pa:
        return
    total = _num(pa.get("total_amount"), 0.0)
    allocs = pa.get("allocations") or []
    s = round(sum(_num(a.get("allocated_amount"), 0.0) for a in allocs), 2)
    if abs(s - round(total, 2)) > TOL:
        errors.append(f"participations: allocations sum {s} != total {round(total, 2)} "
                      f"(pro-rata allocations must be exact)")
    share_sum = round(sum(_num(a.get("share_pct"), 0.0) for a in allocs), 8)
    if allocs and abs(share_sum - 1.0) > 1e-6:
        errors.append(f"participations: shares sum {share_sum} != 1.0")


def _check_variance_report(pack, errors):
    materiality = _num(pack.get("materiality_threshold"), 25.0)
    for row in pack.get("variance_report") or []:
        c = _num(row.get("computed")); b = _num(row.get("book")); v = _num(row.get("variance"))
        if None in (c, b, v):
            errors.append(f"variance {row.get('id')}: missing computed/book/variance")
            continue
        if abs(round(c - b, 2) - v) > TOL:
            errors.append(f"variance {row.get('id')}: variance {v} != computed-book {round(c - b, 2)}")
        expect_status = "match" if abs(v) <= TOL else "variance"
        if row.get("status") != expect_status:
            errors.append(f"variance {row.get('id')}: status {row.get('status')!r} should be {expect_status!r}")
        if bool(row.get("material")) != (abs(v) > materiality):
            errors.append(f"variance {row.get('id')}: material flag inconsistent with threshold {materiality}")


def _check_reconciliation(pack, errors):
    totals = pack.get("recomputed_totals") or {}
    recon = pack.get("reconciliation")
    if recon is None:
        errors.append("reconciliation missing (recomputed totals must be reconciled to approved-engine totals)")
        return
    for row in recon:
        key = row.get("total")
        rec = _num(row.get("recomputed")); appr = _num(row.get("approved_engine")); v = _num(row.get("variance"))
        if None in (rec, appr, v):
            errors.append(f"reconciliation {key}: missing recomputed/approved_engine/variance")
            continue
        if key in totals and abs(round(_num(totals[key], 0.0), 2) - rec) > TOL:
            errors.append(f"reconciliation {key}: recomputed {rec} disagrees with recomputed_totals {totals[key]}")
        if abs(round(rec - appr, 2) - v) > TOL:
            errors.append(f"reconciliation {key}: variance {v} != recomputed-approved {round(rec - appr, 2)}")
        expect_status = "reconciled" if abs(v) <= TOL else "out-of-balance"
        if row.get("status") != expect_status:
            errors.append(f"reconciliation {key}: status {row.get('status')!r} should be {expect_status!r}")


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    _check_interest(pack, errors)
    _check_fees(pack, errors)
    _check_amortization(pack, errors)
    _check_settlement(pack, errors)
    _check_participations(pack, errors)
    _check_variance_report(pack, errors)
    _check_reconciliation(pack, errors)

    # assumption provenance
    register = pack.get("assumptions_register") or []
    if not register:
        errors.append("assumptions_register missing (provenance must be recorded for every input)")
    for a in register:
        if not (a.get("provenance") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing provenance")
        if not (a.get("citation") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing citation")

    # reproducibility
    for k in ("calc_id", "inputs_hash", "config_version"):
        if not (str(pack.get(k) or "")).strip():
            errors.append(f"missing {k} (reproducibility)")

    # HARD BOUNDARY: no posting / approval action
    if str(pack.get("action_taken", "none")).strip().lower() != "none":
        errors.append(f"action_taken must be 'none' (R2 never posts or approves); got {pack.get('action_taken')!r}")
    for flag in ("posted", "adjustment_posted", "approved", "booked", "authorized"):
        if pack.get(flag):
            errors.append(f"prohibited: workbook sets {flag!r}=true (R2 never posts or approves an adjustment)")

    # prohibited-action / prohibited-advice screen over author free text (not the disclaimer)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))])
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in PROHIBITED_ACTION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited posting/approval language detected: {m.group(0)!r} "
                          f"(R2 recalculates and reports; it never posts or approves an adjustment)")
    for pat in PROHIBITED_ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited financial/legal/tax advice detected: {m.group(0)!r} "
                          f"(R2 recalculates and reports; it does not advise)")

    # standing disclaimer present
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "loan_calc_pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
