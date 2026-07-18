#!/usr/bin/env python3
"""Deterministic, explainable statement extraction for bank-statement-analyzer.

Reads a statement file (see validate_input.py), extracts income, recurring obligations,
cash-flow trends, and fees, and flags factual anomalies with evidence + citations. Emits a
machine-readable core the SKILL wraps in a plain-language pack.

IMPORTANT: This produces *extracted figures and factual flags* only. It never produces a
lending/credit/affordability decision, an eligibility determination, personalized financial
advice, or a fraud finding. All thresholds are documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py statement.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, re, statistics, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "recurring_min_occurrences": 2,
    "recurring_amount_tol_pct": 0.15,
    "large_debit_k": 3.0,
    "min_baseline_n": 10,
    "duplicate_window_hours": 24,
    "low_balance_threshold": 0.0,
    "income_categories": ["payroll", "salary", "direct-deposit", "direct deposit",
                          "pension", "benefit", "income"],
    "fee_keywords": ["fee", "nsf", "overdraft", "service charge", "maintenance",
                     "returned item", "insufficient funds", "atm fee"],
    "nsf_keywords": ["nsf", "returned item", "insufficient funds"],
}
DISCLAIMER = ("Analysis and extracted figures only; not a lending decision, eligibility "
              "determination, or financial advice.")


def _parse_dt(s: str) -> datetime:
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.strptime(s[:10], "%Y-%m-%d")


def _norm(s) -> str:
    return " ".join(str(s or "").lower().split())


def _cite(t: dict) -> str:
    return f"stmt:{t.get('source_ref','?')}@{t.get('date','?')}"


def _months_in_period(period: dict) -> int:
    a, b = _parse_dt(period["start"]), _parse_dt(period["end"])
    return max(1, (b.year - a.year) * 12 + (b.month - a.month) + 1)


def _matches(text: str, keywords) -> bool:
    """Word-boundary keyword match (so 'coffee' does not match the fee keyword 'fee')."""
    t = _norm(text)
    return any(re.search(r"\b" + re.escape(k) + r"\b", t) for k in keywords)


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    income_cats = [c.lower() for c in cfg["income_categories"]]
    txns = sorted(doc["transactions"], key=lambda t: str(t["date"]))
    credits = [t for t in txns if t["direction"] == "credit"]
    debits = [t for t in txns if t["direction"] == "debit"]
    period = doc["statement_period"]
    months = _months_in_period(period)

    # --- recurrence detection (by normalized counterparty) ---
    def group(rows):
        g: dict[str, list] = {}
        for t in rows:
            g.setdefault(_norm(t.get("counterparty")), []).append(t)
        return g

    credit_groups = group(credits)
    debit_groups = group(debits)

    recurring_credit_payees = {
        k for k, rows in credit_groups.items()
        if k and len(rows) >= cfg["recurring_min_occurrences"]}

    def _stable(rows) -> bool:
        amts = [float(r["amount"]) for r in rows]
        m = statistics.mean(amts)
        if m == 0:
            return False
        return all(abs(a - m) <= cfg["recurring_amount_tol_pct"] * m for a in amts)

    recurring_debit_keys = {
        k for k, rows in debit_groups.items()
        if k and len(rows) >= cfg["recurring_min_occurrences"] and _stable(rows)}

    # --- income_summary ---
    income_rows = [t for t in credits
                   if _norm(t.get("category")) in income_cats
                   or _matches(t.get("category"), income_cats)
                   or _norm(t.get("counterparty")) in recurring_credit_payees]
    income_total = round(sum(float(t["amount"]) for t in income_rows), 2)
    income = {
        "total": income_total,
        "count": len(income_rows),
        "monthly_average": round(income_total / months, 2),
        "months_in_period": months,
        "evidence": [{"txn_id": t["txn_id"], "amount": t["amount"],
                      "counterparty": t.get("counterparty"), "citation": _cite(t)}
                     for t in income_rows],
    }

    # --- recurring_obligations ---
    obligations = []
    for k in sorted(recurring_debit_keys):
        rows = debit_groups[k]
        amts = [float(r["amount"]) for r in rows]
        obligations.append({
            "counterparty": rows[0].get("counterparty"),
            "occurrences": len(rows),
            "mean_amount": round(statistics.mean(amts), 2),
            "total": round(sum(amts), 2),
            "evidence": [{"txn_id": r["txn_id"], "amount": r["amount"], "citation": _cite(r)}
                         for r in rows],
        })
    obligations_total = round(sum(o["total"] for o in obligations), 2)

    # --- fees ---
    fee_rows = [t for t in debits
                if _norm(t.get("category")) == "fee"
                or _matches(t.get("counterparty"), cfg["fee_keywords"])
                or _matches(t.get("category"), cfg["fee_keywords"])]
    fees = {
        "total": round(sum(float(t["amount"]) for t in fee_rows), 2),
        "count": len(fee_rows),
        "evidence": [{"txn_id": t["txn_id"], "amount": t["amount"],
                      "counterparty": t.get("counterparty"), "citation": _cite(t)}
                     for t in fee_rows],
    }

    # --- cash_flow ---
    total_credits = round(sum(float(t["amount"]) for t in credits), 2)
    total_debits = round(sum(float(t["amount"]) for t in debits), 2)
    net = round(total_credits - total_debits, 2)
    monthly: dict[str, dict] = {}
    for t in txns:
        mk = str(t["date"])[:7]
        b = monthly.setdefault(mk, {"credits": 0.0, "debits": 0.0})
        b["credits" if t["direction"] == "credit" else "debits"] += float(t["amount"])
    monthly_net = [{"month": mk, "credits": round(v["credits"], 2),
                    "debits": round(v["debits"], 2),
                    "net": round(v["credits"] - v["debits"], 2)}
                   for mk, v in sorted(monthly.items())]
    cash_flow = {"total_credits": total_credits, "total_debits": total_debits,
                 "net_cash_flow": net, "monthly_net": monthly_net}
    if "opening_balance" in doc and "closing_balance" in doc:
        expected = round(float(doc["opening_balance"]) + net, 2)
        cash_flow["balance_tie_out"] = {
            "opening_balance": round(float(doc["opening_balance"]), 2),
            "closing_balance": round(float(doc["closing_balance"]), 2),
            "expected_closing": expected,
            "reconciles": abs(expected - round(float(doc["closing_balance"]), 2)) < 0.01,
        }

    # --- anomalies (factual, evidenced) ---
    anomalies = []

    def add_anom(name, fired, reason, evidence, confidence):
        anomalies.append({"anomaly": name, "fired": fired, "reason": reason,
                          "evidence": evidence, "confidence": confidence})

    # negative_balance_day
    with_bal = [t for t in txns if t.get("balance") is not None]
    neg = [t for t in with_bal if float(t["balance"]) < cfg["low_balance_threshold"]]
    if with_bal:
        add_anom("negative_balance_day", bool(neg),
                 f"{len(neg)} row(s) with balance below {cfg['low_balance_threshold']}"
                 if neg else "no negative-balance rows",
                 [{"txn_id": t["txn_id"], "balance": t["balance"], "citation": _cite(t)} for t in neg],
                 "high" if neg else "high")

    # nsf_returned_item
    nsf = [t for t in txns
           if _matches(t.get("counterparty"), cfg["nsf_keywords"])
           or _matches(t.get("category"), cfg["nsf_keywords"])]
    add_anom("nsf_returned_item", bool(nsf),
             f"{len(nsf)} NSF/returned-item event(s)" if nsf else "no NSF/returned items",
             [{"txn_id": t["txn_id"], "amount": t["amount"], "citation": _cite(t)} for t in nsf],
             "high")

    # large_one_off_debit (non-recurring, non-fee)
    fee_ids = {t["txn_id"] for t in fee_rows}
    var_debits = [t for t in debits
                  if _norm(t.get("counterparty")) not in recurring_debit_keys
                  and t["txn_id"] not in fee_ids]
    if len(var_debits) >= cfg["min_baseline_n"]:
        amts = [float(t["amount"]) for t in var_debits]
        mean = statistics.mean(amts)
        stdev = statistics.pstdev(amts) or 0.0
        thr = mean + cfg["large_debit_k"] * stdev
        hits = [t for t in var_debits if float(t["amount"]) > thr]
        add_anom("large_one_off_debit", bool(hits),
                 f"debit(s) exceed baseline mean {mean:.2f} + {cfg['large_debit_k']}*stdev "
                 f"{stdev:.2f} = {thr:.2f}" if hits else f"no debit exceeds {thr:.2f}",
                 [{"txn_id": t["txn_id"], "amount": t["amount"], "citation": _cite(t)} for t in hits],
                 "medium")
    else:
        add_anom("large_one_off_debit", False,
                 f"baseline debits {len(var_debits)} < {cfg['min_baseline_n']}; low-confidence",
                 [], "low")

    # duplicate_transaction
    seen: dict[tuple, dict] = {}
    dups = []
    for t in debits:
        key = (round(float(t["amount"]), 2), _norm(t.get("counterparty")))
        prev = seen.get(key)
        if prev is not None:
            gap = abs((_parse_dt(t["date"]) - _parse_dt(prev["date"])).total_seconds()) / 3600.0
            if gap <= cfg["duplicate_window_hours"]:
                dups.append({"txn_id": t["txn_id"], "duplicate_of": prev["txn_id"],
                             "amount": t["amount"], "citation": _cite(t)})
        seen[key] = t
    add_anom("duplicate_transaction", bool(dups),
             f"{len(dups)} possible duplicate debit(s) within {cfg['duplicate_window_hours']}h"
             if dups else "no duplicate debits detected", dups, "medium")

    # --- confidence flags ---
    n = len(txns)
    uncategorized = sum(1 for t in txns if not t.get("category"))
    flags = []
    if uncategorized:
        flags.append(f"{uncategorized}/{n} transactions lacked a category; "
                     f"income/fee classification used keyword heuristics")
    if not with_bal:
        flags.append("no running balances supplied; balance-based anomalies not evaluable")
    elif len(with_bal) < n:
        flags.append(f"only {len(with_bal)}/{n} rows carried a balance; balance checks partial")
    if len(var_debits) < cfg["min_baseline_n"]:
        flags.append("thin baseline; large_one_off_debit is low-confidence")
    if "opening_balance" not in doc or "closing_balance" not in doc:
        flags.append("no opening/closing balance; cash-flow tie-out not evaluable")

    fired_anoms = [a["anomaly"] for a in anomalies if a["fired"]]

    return {
        "analysis_id": f"bsa-{str(doc['account_id']).replace('*','')}-{period['start']}_{period['end']}-0001",
        "account_id": doc["account_id"],
        "statement_period": period,
        "currency": doc.get("currency"),
        "config_version": doc.get("config_version"),
        "income_summary": income,
        "recurring_obligations": obligations,
        "recurring_obligations_total": obligations_total,
        "cash_flow": cash_flow,
        "fees": fees,
        "anomalies": anomalies,
        "fired_anomalies": fired_anoms,
        "confidence_flags": flags,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "statement_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
