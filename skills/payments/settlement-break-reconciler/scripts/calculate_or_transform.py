#!/usr/bin/env python3
"""Deterministic settlement reconciliation + break classification for settlement-break-reconciler.

Matches settlement records across network, acquirer/processor, bank cash, and internal
ledger sources by ``match_key``; ties out gross, fees, reserve, net, and cash; classifies
each discrepancy into a documented break taxonomy; quantifies impact; preserves lineage
(source citations); and drafts **proposed-only** corrections.

IMPORTANT: This produces a reconciliation, a classified break list, and *proposed*
corrections only. It NEVER posts a journal, changes a system of record, or executes a
correction. Every proposed correction carries ``status: "proposed"`` and
``requires_approval: true``. Break taxonomy and tie-out rules are documented in
references/domain-rules.md. The reconciliation is deterministic and reproducible: the same
inputs + config version reproduce the same breaks and the same correction identifiers
(idempotency).

Usage:
  python calculate_or_transform.py recon.json | --selftest
Prints the reconciliation JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "amount_tolerance_abs": 0.50,
    "fee_tolerance_abs": 0.50,
    "reserve_tolerance_abs": 0.50,
    "cash_tolerance_abs": 0.50,
    "net_calc_tolerance_abs": 0.50,
    "cash_settlement_lag_days": 2,
}

# Documented break taxonomy (see references/domain-rules.md). TIMING_DIFFERENCE is a
# reconciling item, not a hard break, and is reported separately.
BREAK_TYPES = {
    "AMOUNT_MISMATCH_GROSS", "FEE_VARIANCE", "RESERVE_VARIANCE", "NET_CALC_MISMATCH",
    "NET_CASH_MISMATCH", "LEDGER_POSTING_MISMATCH", "MISSING_IN_BANK",
    "MISSING_IN_LEDGER", "MISSING_IN_SETTLEMENT", "DUPLICATE", "CURRENCY_MISMATCH",
}
RECONCILING_ITEM_TYPES = {"TIMING_DIFFERENCE"}

DISCLAIMER = (
    "Reconciliation and proposed corrections only; no journal has been posted and no system "
    "of record has been changed. Every proposed correction requires human review and "
    "approval before posting."
)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _index(records: list) -> dict:
    """Group a source's records by match_key (list per key preserves duplicates)."""
    out: dict = {}
    for r in records or []:
        out.setdefault(str(r.get("match_key")), []).append(r)
    return out


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    period = doc.get("period") or {}
    period_end = _parse_date(period["end"]) if period.get("end") else None
    schedule = {str(s["scheme"]): s for s in (doc.get("fee_schedule") or [])}
    src = doc.get("sources") or {}
    net_i = _index(src.get("network"))
    prc_i = _index(src.get("processor"))
    bnk_i = _index(src.get("bank_cash"))
    led_i = _index(src.get("ledger"))

    all_keys = sorted(set(net_i) | set(prc_i) | set(bnk_i) | set(led_i))

    breaks: list = []
    reconciling_items: list = []
    not_evaluable: list = []
    seen_break_ids: set = set()

    def cite(system: str, rec: dict, date_field: str) -> str:
        return f"{system}:{rec.get('source_ref', '?')}@{rec.get(date_field, '?')}"

    def new_break_id(key: str, btype: str) -> str:
        base = f"BRK-{key}-{btype}"
        bid, n = base, 1
        while bid in seen_break_ids:
            n += 1
            bid = f"{base}-{n}"
        seen_break_ids.add(bid)
        return bid

    def add_break(key, btype, reason, impact, evidence):
        breaks.append({
            "break_id": new_break_id(key, btype),
            "match_key": key,
            "break_type": btype,
            "reason": reason,
            "impact": round(float(impact), 2),
            "currency": doc.get("settlement_currency"),
            "evidence": evidence,
        })

    for key in all_keys:
        n_list, p_list = net_i.get(key, []), prc_i.get(key, [])
        b_list, l_list = bnk_i.get(key, []), led_i.get(key, [])
        n0 = n_list[0] if n_list else None
        p0 = p_list[0] if p_list else None
        b0 = b_list[0] if b_list else None
        l0 = l_list[0] if l_list else None
        settled = bool(n0 or p0)

        # duplicates within a single source
        for lst, system, dfield in ((n_list, "network", "settlement_date"),
                                     (p_list, "processor", "settlement_date"),
                                     (b_list, "bank_cash", "value_date"),
                                     (l_list, "ledger", "post_date")):
            if len(lst) > 1:
                dup_amt = _num(lst[0].get("net", lst[0].get("amount", lst[0].get("gross", 0)))) or 0.0
                add_break(key, "DUPLICATE",
                          f"{len(lst)} {system} records share match_key {key}",
                          dup_amt,
                          [{"system": system, "citation": cite(system, r, dfield)} for r in lst])

        # currency consistency across present sources
        currencies = {str(r.get("currency")) for r in (n_list + p_list + b_list + l_list) if r and r.get("currency")}
        if len(currencies) > 1:
            add_break(key, "CURRENCY_MISMATCH",
                      f"conflicting settlement currencies {sorted(currencies)} on match_key {key}",
                      0.0,
                      [{"system": s, "citation": cite(s, r, d)}
                       for lst, s, d in ((n_list, "network", "settlement_date"),
                                         (p_list, "processor", "settlement_date"),
                                         (b_list, "bank_cash", "value_date"),
                                         (l_list, "ledger", "post_date")) for r in lst])

        # gross tie-out: network vs processor
        if n0 and p0 and _num(n0.get("gross")) is not None and _num(p0.get("gross")) is not None:
            diff = round(_num(p0["gross"]) - _num(n0["gross"]), 2)
            if abs(diff) > cfg["amount_tolerance_abs"]:
                add_break(key, "AMOUNT_MISMATCH_GROSS",
                          f"processor gross {p0['gross']} vs network gross {n0['gross']} (diff {diff:+.2f})",
                          diff,
                          [{"system": "network", "citation": cite("network", n0, "settlement_date")},
                           {"system": "processor", "citation": cite("processor", p0, "settlement_date")}])

        # fee / reserve tie-out vs schedule + processor net internal consistency
        if p0 and _num(p0.get("gross")) is not None:
            gross = _num(p0["gross"])
            sched = schedule.get(str(p0.get("scheme")))
            if sched is None:
                not_evaluable.append({"match_key": key, "check": "fee/reserve",
                                      "why": f"no fee_schedule row for scheme {p0.get('scheme')!r}"})
            else:
                exp_fee = round(gross * _num(sched.get("rate_bps") or 0) / 10000.0, 2)
                act_fee = _num(p0.get("fees"))
                if act_fee is not None and abs(act_fee - exp_fee) > cfg["fee_tolerance_abs"]:
                    add_break(key, "FEE_VARIANCE",
                              f"processor fee {act_fee} vs scheduled {exp_fee} ({sched.get('rate_bps')}bps) (diff {act_fee - exp_fee:+.2f})",
                              act_fee - exp_fee,
                              [{"system": "processor", "citation": cite("processor", p0, "settlement_date")},
                               {"system": "fee_schedule", "citation": f"fee_schedule:scheme={p0.get('scheme')};rate_bps={sched.get('rate_bps')}"}])
                exp_res = round(gross * _num(sched.get("reserve_bps") or 0) / 10000.0, 2)
                act_res = _num(p0.get("reserve"))
                if act_res is not None and abs(act_res - exp_res) > cfg["reserve_tolerance_abs"]:
                    add_break(key, "RESERVE_VARIANCE",
                              f"processor reserve {act_res} vs scheduled {exp_res} ({sched.get('reserve_bps')}bps) (diff {act_res - exp_res:+.2f})",
                              act_res - exp_res,
                              [{"system": "processor", "citation": cite("processor", p0, "settlement_date")},
                               {"system": "fee_schedule", "citation": f"fee_schedule:scheme={p0.get('scheme')};reserve_bps={sched.get('reserve_bps')}"}])
            # net internal consistency: net == gross - fees - reserve
            if all(_num(p0.get(k)) is not None for k in ("fees", "reserve", "net")):
                calc_net = round(gross - _num(p0["fees"]) - _num(p0["reserve"]), 2)
                if abs(_num(p0["net"]) - calc_net) > cfg["net_calc_tolerance_abs"]:
                    add_break(key, "NET_CALC_MISMATCH",
                              f"processor net {p0['net']} != gross-fees-reserve {calc_net}",
                              _num(p0["net"]) - calc_net,
                              [{"system": "processor", "citation": cite("processor", p0, "settlement_date")}])

        # settlement present but no bank cash -> timing (in lag window) or MISSING_IN_BANK
        if settled and not b0:
            ref = p0 or n0
            sdate = _parse_date(ref.get("settlement_date")) if ref.get("settlement_date") else None
            amt = _num((p0 or {}).get("net"))
            if amt is None:
                amt = _num((n0 or {}).get("gross")) or 0.0
            in_lag = (period_end is not None and sdate is not None
                      and (period_end - sdate).days < cfg["cash_settlement_lag_days"])
            ev = [{"system": "processor" if p0 else "network",
                   "citation": cite("processor" if p0 else "network", ref, "settlement_date")}]
            if in_lag:
                reconciling_items.append({
                    "reconciling_item_id": f"RI-{key}-TIMING_DIFFERENCE",
                    "match_key": key,
                    "type": "TIMING_DIFFERENCE",
                    "reason": f"settled {ref.get('settlement_date')} within {cfg['cash_settlement_lag_days']}d cash lag; cash expected next period",
                    "in_transit_amount": round(amt, 2),
                    "currency": doc.get("settlement_currency"),
                    "evidence": ev,
                })
            else:
                add_break(key, "MISSING_IN_BANK",
                          f"settled net {amt} has no matching bank cash receipt", amt, ev)

        # bank cash present but no settlement record
        if b0 and not settled:
            amt = _num(b0.get("amount")) or 0.0
            add_break(key, "MISSING_IN_SETTLEMENT",
                      f"bank cash {amt} has no matching network/processor settlement record",
                      amt,
                      [{"system": "bank_cash", "citation": cite("bank_cash", b0, "value_date")}])

        # settlement present but no ledger entry
        if settled and not l0:
            amt = _num((p0 or {}).get("net"))
            if amt is None:
                amt = _num((n0 or {}).get("gross")) or 0.0
            add_break(key, "MISSING_IN_LEDGER",
                      f"settled net {amt} is not booked in the internal ledger", amt,
                      [{"system": "processor" if p0 else "network",
                        "citation": cite("processor" if p0 else "network", p0 or n0, "settlement_date")}])

        # ledger entry with neither settlement nor bank support
        if l0 and not settled and not b0:
            amt = _num(l0.get("net")) or 0.0
            add_break(key, "MISSING_IN_SETTLEMENT",
                      f"ledger entry {amt} has no matching settlement or bank record", amt,
                      [{"system": "ledger", "citation": cite("ledger", l0, "post_date")}])

        # net vs cash tie-out
        if p0 and b0 and _num(p0.get("net")) is not None and _num(b0.get("amount")) is not None:
            diff = round(_num(b0["amount"]) - _num(p0["net"]), 2)
            if abs(diff) > cfg["cash_tolerance_abs"]:
                add_break(key, "NET_CASH_MISMATCH",
                          f"bank cash {b0['amount']} vs processor net {p0['net']} (diff {diff:+.2f})",
                          diff,
                          [{"system": "processor", "citation": cite("processor", p0, "settlement_date")},
                           {"system": "bank_cash", "citation": cite("bank_cash", b0, "value_date")}])

        # net vs ledger tie-out
        if p0 and l0 and _num(p0.get("net")) is not None and _num(l0.get("net")) is not None:
            diff = round(_num(l0["net"]) - _num(p0["net"]), 2)
            if abs(diff) > cfg["net_calc_tolerance_abs"]:
                add_break(key, "LEDGER_POSTING_MISMATCH",
                          f"ledger net {l0['net']} vs processor net {p0['net']} (diff {diff:+.2f})",
                          diff,
                          [{"system": "processor", "citation": cite("processor", p0, "settlement_date")},
                           {"system": "ledger", "citation": cite("ledger", l0, "post_date")}])

    # ---- portfolio tie-out summary ----
    def _sum(records, field):
        return round(sum(_num(r.get(field)) or 0.0 for r in records or []), 2)

    tie_out = {
        "network_gross_total": _sum(src.get("network"), "gross"),
        "processor_gross_total": _sum(src.get("processor"), "gross"),
        "processor_fees_total": _sum(src.get("processor"), "fees"),
        "processor_reserve_total": _sum(src.get("processor"), "reserve"),
        "processor_net_total": _sum(src.get("processor"), "net"),
        "bank_cash_total": _sum(src.get("bank_cash"), "amount"),
        "ledger_net_total": _sum(src.get("ledger"), "net"),
    }
    tie_out["gross_diff_processor_minus_network"] = round(
        tie_out["processor_gross_total"] - tie_out["network_gross_total"], 2)
    tie_out["net_diff_bank_minus_processor"] = round(
        tie_out["bank_cash_total"] - tie_out["processor_net_total"], 2)
    tie_out["net_diff_ledger_minus_processor"] = round(
        tie_out["ledger_net_total"] - tie_out["processor_net_total"], 2)

    total_impact = round(sum(abs(b["impact"]) for b in breaks), 2)
    by_type: dict = {}
    for b in breaks:
        by_type[b["break_type"]] = by_type.get(b["break_type"], 0) + 1

    corrections = [_propose_correction(b) for b in breaks]

    recon_id = f"sbr-{period.get('start', '?')}_{period.get('end', '?')}-{doc.get('config_version', 'nocfg')}"
    return {
        "reconciliation_id": recon_id,
        "as_of": doc.get("as_of"),
        "period": period,
        "config_version": doc.get("config_version"),
        "settlement_currency": doc.get("settlement_currency"),
        "tie_out": tie_out,
        "breaks": breaks,
        "reconciling_items": reconciling_items,
        "not_evaluable": not_evaluable,
        "corrections": corrections,
        "summary": {
            "keys_examined": len(all_keys),
            "break_count": len(breaks),
            "reconciling_item_count": len(reconciling_items),
            "breaks_by_type": by_type,
            "total_break_impact": total_impact,
            "clean": not breaks,
        },
        "disclaimer": DISCLAIMER,
    }


# proposed-correction templates by break type (draft-only; never posted)
_CORRECTION_TEMPLATE = {
    "MISSING_IN_LEDGER": ("journal", "Dr Settlement Clearing", "Cr Merchant Payable",
                          "Book settled net not yet reflected in the ledger"),
    "LEDGER_POSTING_MISMATCH": ("journal", "Dr/Cr Settlement Clearing", "Cr/Dr Merchant Payable",
                                "Adjust ledger net to agree to processor settled net"),
    "NET_CASH_MISMATCH": ("journal", "Dr/Cr Cash Suspense", "Cr/Dr Settlement Clearing",
                          "Record cash-vs-settlement difference to suspense pending investigation"),
    "FEE_VARIANCE": ("dispute", "Dr Fee Expense Adjustment", "Cr Fee Recoverable",
                     "Query processor fee vs contracted schedule; propose fee adjustment"),
    "RESERVE_VARIANCE": ("journal", "Dr/Cr Reserve Receivable", "Cr/Dr Settlement Clearing",
                         "Adjust reserve to contracted schedule"),
    "AMOUNT_MISMATCH_GROSS": ("investigation", None, None,
                              "Investigate network-vs-processor gross discrepancy before any posting"),
    "NET_CALC_MISMATCH": ("investigation", None, None,
                          "Processor net does not equal gross-fees-reserve; query processor file"),
    "MISSING_IN_BANK": ("investigation", None, None,
                        "Expected settlement cash not received; open funding follow-up with bank/processor"),
    "MISSING_IN_SETTLEMENT": ("investigation", None, None,
                              "Entry has no settlement support; review for reversal or missing file"),
    "DUPLICATE": ("investigation", None, None,
                  "Duplicate settlement record detected; review for de-duplication/reversal"),
    "CURRENCY_MISMATCH": ("investigation", None, None,
                          "Conflicting settlement currencies; resolve FX/currency mapping before posting"),
}


def _propose_correction(b: dict) -> dict:
    kind, dr, cr, memo = _CORRECTION_TEMPLATE.get(
        b["break_type"], ("investigation", None, None, "Investigate break before any posting"))
    corr = {
        "correction_id": f"COR-{b['break_id']}",
        "break_ref": b["break_id"],
        "match_key": b["match_key"],
        "break_type": b["break_type"],
        "correction_type": kind,
        "status": "proposed",
        "requires_approval": True,
        "impact": b["impact"],
        "currency": b.get("currency"),
        "memo": memo,
        "evidence": b["evidence"],
    }
    if kind in ("journal", "dispute") and dr and cr:
        corr["proposed_entry"] = {
            "debit_account": dr,
            "credit_account": cr,
            "amount": round(abs(b["impact"]), 2),
            "currency": b.get("currency"),
        }
    return corr


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "recon_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
