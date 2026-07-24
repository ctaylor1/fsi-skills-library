#!/usr/bin/env python3
"""Deterministic loan interest, fee, amortization, settlement, and participation engine.

Reads a loan-recalculation input file (see validate_input.py) and rebuilds — from the cited
agreement terms, servicing transactions, and approved rate tables — the servicing analyst's
calculation workbook:

  * interest accruals per period (principal x rate x day-count year fraction),
  * fee recomputations (flat / percent-of-balance / percent-of-payment),
  * a level-payment or interest-only amortization schedule,
  * a settlement / payoff figure with an explicit component walk,
  * pro-rata participation allocations that sum exactly to the shared amount,
  * a variance report of every recomputed figure against the servicing-booked amount, and
  * a reconciliation of the recomputed grand totals to any stated approved-engine totals.

Every input carries a provenance tag and citation; the workbook is reproducible from a hash
of its numeric inputs and a durable calc_id.

IMPORTANT — HARD BOUNDARY (R2, Model & calculate): this engine RECALCULATES and REPORTS
only. It never posts, books, applies, waives, reverses, approves, or authorizes an
adjustment to any account or system of record, and it gives no financial, legal, or tax
advice. Rate tables, day-count conventions, tolerances, and materiality thresholds are
versioned configuration and cited inputs, not the skill's judgment. Any account change is a
separate, human-authorized step. See references/domain-rules.md and references/controls.md.

Usage:
  python calculate_or_transform.py loan_calc_input.json | --selftest
Prints the workbook JSON to stdout. Exit 0.
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

MONEY = 2            # currency precision
RATE_ROUND = 10      # year-fraction / factor precision
TOL = 0.01           # tie-out / match tolerance (currency)
DISCLAIMER = ("Illustrative loan-servicing recalculation for analytical review only; not a "
              "posting, adjustment, waiver, reversal, or approval, and not financial, legal, "
              "or tax advice. Every figure is conditional on the cited agreement terms, "
              "servicing data, and approved rate tables, and a qualified human must review "
              "and separately authorize any account change.")


def _v(node):
    """Numeric value from a bare scalar or a {value, provenance, citation} object."""
    if isinstance(node, dict):
        return float(node.get("value"))
    return float(node)


def _prov(node):
    return (node.get("provenance", "") if isinstance(node, dict) else "")


def _cite(node):
    return (node.get("citation", "") if isinstance(node, dict) else "")


def _pdate(s: str) -> date:
    y, m, d = str(s).split("-")[:3]
    return date(int(y), int(m), int(d))


def year_fraction(start: str, end: str, convention: str) -> tuple[float, int]:
    """Return (year_fraction, actual_days) for a day-count convention.

    Supported: 30/360 (US/NASD), 30E/360 (European), actual/360, actual/365 (fixed).
    Unknown conventions fall back to 30/360 (input validation warns separately).
    """
    d1, d2 = _pdate(start), _pdate(end)
    actual = (d2 - d1).days
    conv = (convention or "30/360").lower().replace(" ", "")
    if conv in ("actual/360", "act/360", "a/360"):
        return round(actual / 360.0, RATE_ROUND), actual
    if conv in ("actual/365", "act/365", "a/365", "actual/365f", "actual/365fixed"):
        return round(actual / 365.0, RATE_ROUND), actual
    # 30/360 family
    dd1, dd2 = d1.day, d2.day
    if conv in ("30e/360", "30e", "eurobond"):
        dd1 = 30 if dd1 == 31 else dd1
        dd2 = 30 if dd2 == 31 else dd2
    else:  # 30/360 US / NASD
        if dd1 == 31:
            dd1 = 30
        if dd2 == 31 and dd1 == 30:
            dd2 = 30
    days360 = 360 * (d2.year - d1.year) + 30 * (d2.month - d1.month) + (dd2 - dd1)
    return round(days360 / 360.0, RATE_ROUND), actual


# --------------------------------------------------------------------------- sections

def compute_interest(doc: dict, register: list) -> list:
    out = []
    for i, line in enumerate(doc.get("interest_accruals") or []):
        lid = line.get("id") or f"interest:{i + 1}"
        principal = _v(line["principal"])
        rate = _v(line["annual_rate"])
        conv = line.get("day_count") or doc.get("day_count_default") or "30/360"
        yf, actual = year_fraction(line["start"], line["end"], conv)
        interest = round(principal * rate * yf, MONEY)
        register.append({"id": f"{lid}:principal", "scope": "interest-accrual",
                         "value": principal, "provenance": _prov(line["principal"]),
                         "citation": _cite(line["principal"])})
        register.append({"id": f"{lid}:annual_rate", "scope": "rate-table",
                         "value": rate, "provenance": _prov(line["annual_rate"]),
                         "citation": _cite(line["annual_rate"])})
        rec = {
            "id": lid, "kind": "interest",
            "principal": round(principal, MONEY), "annual_rate": rate,
            "day_count": conv, "start": line["start"], "end": line["end"],
            "actual_days": actual, "year_fraction": yf,
            "computed_amount": interest,
        }
        if "book_amount" in line:
            rec["book_amount"] = round(_v(line["book_amount"]), MONEY)
        out.append(rec)
    return out


def compute_fees(doc: dict, register: list) -> list:
    out = []
    for i, fee in enumerate(doc.get("fees") or []):
        fid = fee.get("id") or f"fee:{i + 1}"
        basis = (fee.get("basis") or "flat").lower()
        if basis in ("pct_balance", "pct_payment", "percent"):
            base = _v(fee["base"])
            rate = _v(fee["rate"])
            amount = round(base * rate, MONEY)
            register.append({"id": f"{fid}:base", "scope": "fee", "value": base,
                             "provenance": _prov(fee["base"]), "citation": _cite(fee["base"])})
            register.append({"id": f"{fid}:rate", "scope": "rate-table", "value": rate,
                             "provenance": _prov(fee["rate"]), "citation": _cite(fee["rate"])})
            detail = {"basis": basis, "base": round(base, MONEY), "rate": rate}
        else:  # flat
            amount = round(_v(fee["amount"]), MONEY)
            register.append({"id": f"{fid}:amount", "scope": "fee", "value": amount,
                             "provenance": _prov(fee["amount"]), "citation": _cite(fee["amount"])})
            detail = {"basis": "flat", "amount": amount}
        rec = {"id": fid, "kind": "fee", "fee_type": fee.get("type", fid),
               "detail": detail, "computed_amount": amount}
        if "book_amount" in fee:
            rec["book_amount"] = round(_v(fee["book_amount"]), MONEY)
        out.append(rec)
    return out


def compute_amortization(doc: dict, register: list) -> dict | None:
    am = doc.get("amortization")
    if not am:
        return None
    principal = _v(am["principal"])
    annual_rate = _v(am["annual_rate"])
    n = int(_v(am["term_periods"]))
    ppy = int(_v(am.get("periods_per_year", 12)))
    method = (am.get("method") or "level_payment").lower()
    r = annual_rate / ppy
    register.append({"id": "amortization:principal", "scope": "amortization",
                     "value": principal, "provenance": _prov(am["principal"]),
                     "citation": _cite(am["principal"])})
    register.append({"id": "amortization:annual_rate", "scope": "rate-table",
                     "value": annual_rate, "provenance": _prov(am["annual_rate"]),
                     "citation": _cite(am["annual_rate"])})

    if method == "interest_only":
        payment = round(principal * r, MONEY)
    elif r == 0:
        payment = round(principal / n, MONEY)
    else:
        payment = round(principal * r / (1.0 - (1.0 + r) ** (-n)), MONEY)

    rows = []
    balance = round(principal, MONEY)
    for t in range(1, n + 1):
        interest_t = round(balance * r, MONEY)
        if method == "interest_only":
            principal_t = round(principal, MONEY) if t == n else 0.0
        elif t == n:
            principal_t = round(balance, MONEY)  # absorb rounding drift in the final period
        else:
            principal_t = round(payment - interest_t, MONEY)
        payment_t = round(principal_t + interest_t, MONEY)
        end_balance = round(balance - principal_t, MONEY)
        rows.append({"period": t, "balance_start": balance, "interest": interest_t,
                     "principal": principal_t, "payment": payment_t, "balance_end": end_balance})
        balance = end_balance

    return {
        "method": method, "principal": round(principal, MONEY), "annual_rate": annual_rate,
        "periods_per_year": ppy, "term_periods": n, "periodic_rate": round(r, RATE_ROUND),
        "scheduled_payment": payment,
        "total_interest": round(sum(x["interest"] for x in rows), MONEY),
        "total_principal": round(sum(x["principal"] for x in rows), MONEY),
        "ending_balance": rows[-1]["balance_end"] if rows else round(principal, MONEY),
        "schedule": rows,
    }


def compute_settlement(doc: dict, register: list) -> dict | None:
    st = doc.get("settlement")
    if not st:
        return None
    principal_out = _v(st["principal_outstanding"])
    accrued = _v(st.get("accrued_interest", 0.0))
    fees_due = _v(st.get("fees_due", 0.0))
    unapplied = _v(st.get("unapplied_funds", 0.0))
    per_diem = _v(st.get("per_diem", 0.0))
    per_diem_days = int(_v(st.get("per_diem_days", 0)))
    per_diem_interest = round(per_diem * per_diem_days, MONEY)
    for k in ("principal_outstanding", "accrued_interest", "fees_due", "unapplied_funds", "per_diem"):
        if k in st:
            register.append({"id": f"settlement:{k}", "scope": "settlement", "value": _v(st[k]),
                             "provenance": _prov(st[k]), "citation": _cite(st[k])})
    components = [
        {"item": "principal outstanding", "amount": round(principal_out, MONEY)},
        {"item": "plus: accrued interest", "amount": round(accrued, MONEY)},
        {"item": "plus: per-diem interest to payoff", "amount": per_diem_interest},
        {"item": "plus: fees due", "amount": round(fees_due, MONEY)},
        {"item": "less: unapplied funds", "amount": round(-unapplied, MONEY)},
    ]
    payoff = round(principal_out + accrued + per_diem_interest + fees_due - unapplied, MONEY)
    rec = {"payoff_date": st.get("payoff_date"), "components": components,
           "computed_amount": payoff}
    if "book_amount" in st:
        rec["book_amount"] = round(_v(st["book_amount"]), MONEY)
    return rec


def compute_participations(doc: dict, register: list) -> dict | None:
    pa = doc.get("participations")
    if not pa:
        return None
    total = round(_v(pa["total_amount"]), MONEY)
    register.append({"id": "participation:total_amount", "scope": "participation",
                     "value": total, "provenance": _prov(pa["total_amount"]),
                     "citation": _cite(pa["total_amount"])})
    parts = pa.get("participants") or []
    allocations = []
    running = 0.0
    for i, p in enumerate(parts):
        share = _v(p["share_pct"])
        register.append({"id": f"participation:{p.get('id', i + 1)}:share_pct",
                         "scope": "participation", "value": share,
                         "provenance": _prov(p["share_pct"]), "citation": _cite(p["share_pct"])})
        if i == len(parts) - 1:
            amount = round(total - running, MONEY)  # residual to the last party (exact sum)
        else:
            amount = round(total * share, MONEY)
            running = round(running + amount, MONEY)
        rec = {"id": p.get("id", f"participant-{i + 1}"), "share_pct": share, "allocated_amount": amount}
        if "book_amount" in p:
            rec["book_amount"] = round(_v(p["book_amount"]), MONEY)
        allocations.append(rec)
    return {"total_amount": total, "allocations": allocations,
            "allocated_sum": round(sum(a["allocated_amount"] for a in allocations), MONEY),
            "share_sum": round(sum(_v(p["share_pct"]) for p in parts), 10)}


# --------------------------------------------------------------------- variance + recon

def build_variance_report(sections: dict, materiality: float) -> list:
    report = []
    lines = list(sections.get("interest", [])) + list(sections.get("fees", []))
    st = sections.get("settlement")
    if st and "book_amount" in st:
        lines.append({"id": "settlement", "kind": "settlement",
                      "computed_amount": st["computed_amount"], "book_amount": st["book_amount"]})
    pa = sections.get("participations")
    for a in (pa.get("allocations", []) if pa else []):
        if "book_amount" in a:
            lines.append({"id": f"participation:{a['id']}", "kind": "participation",
                          "computed_amount": a["allocated_amount"], "book_amount": a["book_amount"]})
    for ln in lines:
        if "book_amount" not in ln:
            continue
        computed = round(float(ln["computed_amount"]), MONEY)
        book = round(float(ln["book_amount"]), MONEY)
        variance = round(computed - book, MONEY)
        report.append({
            "id": ln.get("id"), "kind": ln.get("kind"),
            "computed": computed, "book": book, "variance": variance,
            "status": "match" if abs(variance) <= TOL else "variance",
            "material": abs(variance) > materiality,
        })
    return report


def build_reconciliation(recomputed_totals: dict, doc: dict) -> list:
    stated = doc.get("approved_engine_totals") or {}
    recon = []
    for key, node in stated.items():
        stated_val = round(_v(node), MONEY)
        recomputed = round(float(recomputed_totals.get(key, 0.0)), MONEY)
        variance = round(recomputed - stated_val, MONEY)
        recon.append({"total": key, "recomputed": recomputed, "approved_engine": stated_val,
                      "variance": variance,
                      "status": "reconciled" if abs(variance) <= TOL else "out-of-balance"})
    return recon


# --------------------------------------------------------------------------- assemble

def compute(doc: dict) -> dict:
    register: list = []
    interest = compute_interest(doc, register)
    fees = compute_fees(doc, register)
    amortization = compute_amortization(doc, register)
    settlement = compute_settlement(doc, register)
    participations = compute_participations(doc, register)

    interest_total = round(sum(x["computed_amount"] for x in interest), MONEY)
    fee_total = round(sum(x["computed_amount"] for x in fees), MONEY)
    recomputed_totals = {
        "interest_total": interest_total,
        "fee_total": fee_total,
    }
    if amortization:
        recomputed_totals["amortization_interest_total"] = amortization["total_interest"]
    if settlement:
        recomputed_totals["settlement_payoff"] = settlement["computed_amount"]

    materiality = float(_v((doc.get("thresholds") or {}).get("materiality", 25.0)))
    sections = {"interest": interest, "fees": fees, "settlement": settlement,
                "participations": participations}
    variance_report = build_variance_report(sections, materiality)
    reconciliation = build_reconciliation(recomputed_totals, doc)

    # reproducibility hash over the numeric inputs
    hash_src = json.dumps({
        "loan_id": doc.get("loan_id"),
        "calc_date": doc.get("calc_date"),
        "interest": [[_v(x["principal"]), _v(x["annual_rate"]), x["start"], x["end"],
                      x.get("day_count") or doc.get("day_count_default")]
                     for x in (doc.get("interest_accruals") or [])],
        "fees": [[f.get("basis"), _v(f.get("amount", f.get("rate", 0))), _v(f.get("base", 0))]
                 for f in (doc.get("fees") or [])],
        "amortization": None if not doc.get("amortization") else [
            _v(doc["amortization"]["principal"]), _v(doc["amortization"]["annual_rate"]),
            _v(doc["amortization"]["term_periods"]),
            _v(doc["amortization"].get("periods_per_year", 12)),
            (doc["amortization"].get("method") or "level_payment")],
        "settlement": None if not doc.get("settlement") else [
            _v(doc["settlement"]["principal_outstanding"]),
            _v(doc["settlement"].get("accrued_interest", 0)),
            _v(doc["settlement"].get("fees_due", 0)),
            _v(doc["settlement"].get("unapplied_funds", 0)),
            _v(doc["settlement"].get("per_diem", 0)),
            _v(doc["settlement"].get("per_diem_days", 0))],
        "participations": None if not doc.get("participations") else [
            _v(doc["participations"]["total_amount"]),
            [_v(p["share_pct"]) for p in doc["participations"].get("participants", [])]],
    }, sort_keys=True)
    inputs_hash = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()[:16]
    loan_id = str(doc.get("loan_id", "LOAN"))
    calc_date = doc.get("calc_date", doc.get("as_of"))

    workbook = {
        "calc_id": f"licalc-{loan_id}-{calc_date}-{inputs_hash}",
        "case_id": doc.get("case_id"),
        "loan_id": loan_id,
        "as_of": doc.get("as_of"),
        "calc_date": calc_date,
        "currency": doc.get("currency"),
        "config_version": doc.get("config_version"),
        "rate_table_version": doc.get("rate_table_version"),
        "inputs_hash": inputs_hash,
        "action_taken": "none",  # HARD BOUNDARY: this engine never posts or approves
        "interest": interest,
        "fees": fees,
        "amortization": amortization,
        "settlement": settlement,
        "participations": participations,
        "recomputed_totals": recomputed_totals,
        "variance_report": variance_report,
        "reconciliation": reconciliation,
        "assumptions_register": register,
        "materiality_threshold": round(materiality, MONEY),
        "disclaimer": DISCLAIMER,
    }
    return workbook


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "loan_calc_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
