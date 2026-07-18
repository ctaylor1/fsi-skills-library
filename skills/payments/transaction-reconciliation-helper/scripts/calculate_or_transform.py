#!/usr/bin/env python3
"""Deterministic transaction-level reconciliation for transaction-reconciliation-helper.

Reads a reconciliation input file (see validate_input.py), groups records by shared
transaction reference, matches across sources, classifies mismatches into a documented
break taxonomy with lineage, computes control tie-outs against the cash position of record,
and emits PROPOSED resolution entries. Settlement-file / cash-ledger breaks are routed to
`settlement-break-reconciler`, not resolved here.

IMPORTANT: This produces matched records, a break classification, tie-out totals, and
PROPOSED entries only. It never posts a journal, writes a ledger, or closes a break. The
break taxonomy and tie-out identity are documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py input.json | --selftest
Prints the reconciliation JSON to stdout.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path

DEFAULT_CONFIG = {
    "amount_tolerance": 0.01,
    "expected_sources": ["gateway", "processor", "bank", "ledger"],
    "cash_rank": ["bank", "processor", "gateway"],
    "intransit_days": 2,
}
BREAK_TYPES = (
    "missing_record", "unmatched", "amount_mismatch", "duplicate",
    "status_mismatch", "currency_mismatch", "timing_difference", "fee_variance",
)
ROUTE_SKILL = "settlement-break-reconciler"
DISCLAIMER = ("Proposed entries only; not posted to any system of record. "
              "Human approval and posting required.")


def _cite(r: dict) -> str:
    return f"{r.get('source', '?')}:{r.get('source_ref', '?')}@{r.get('date', '?')}"


def _r2(x: float) -> float:
    return round(float(x), 2)


def _target_source(present: dict, cash_rank) -> str | None:
    """Highest-ranked cash source present in a group (position of record for cash)."""
    for s in cash_rank:
        if s in present:
            return s
    return None


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    tol = float(cfg["amount_tolerance"])
    expected = list(cfg["expected_sources"])
    cash_rank = list(cfg["cash_rank"])
    recs = doc["records"]

    groups: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        groups[r["txn_ref"]].append(r)

    matched, breaks, routed = [], [], []

    for ref in sorted(groups):
        rows = groups[ref]
        is_settlement = any(str(x.get("level", "transaction")) == "settlement" for x in rows)

        # index by source, detect duplicates within a source
        by_src: dict[str, list[dict]] = defaultdict(list)
        for x in rows:
            by_src[x["source"]].append(x)
        present = {s: v for s, v in by_src.items()}
        dup_sources = [s for s, v in by_src.items() if len(v) > 1]
        evidence = [{"record_id": x["record_id"], "source": x["source"],
                     "amount": _r2(x["amount"]), "citation": _cite(x)} for x in rows]

        # ---- settlement / cash-ledger level: route out, never resolve here ----
        if is_settlement:
            amts = {s: _r2(v[0]["amount"]) for s, v in by_src.items()}
            distinct = {round(a, 2) for a in amts.values()}
            if len(distinct) > 1 or set(present) != set(expected) & set(present):
                routed.append({
                    "txn_ref": ref, "break_type": "amount_mismatch",
                    "route_to": ROUTE_SKILL,
                    "reason": "settlement-file / cash-ledger break — out of scope for the "
                              "transaction-level helper; route to the settlement workflow",
                    "amounts": amts, "evidence": evidence})
            else:
                matched.append({"txn_ref": ref, "level": "settlement",
                                "amount": next(iter(distinct)), "sources": sorted(present),
                                "citation": _cite(rows[0])})
            continue

        # ---- transaction level ----
        missing = [s for s in expected if s not in present]
        src_amt = {s: _r2(v[0]["amount"]) for s, v in by_src.items()}
        currencies = {str(x.get("currency", "")).upper() for x in rows if x.get("currency")}
        tgt = _target_source(present, cash_rank)

        def add_break(bt, reason, proposed):
            breaks.append({
                "txn_ref": ref, "break_type": bt, "reason": reason,
                "present_sources": sorted(present), "missing_sources": missing,
                "amounts": src_amt, "evidence": evidence,
                "proposed_entry": proposed, "route_to": None})

        def ledger_entry(delta, note):
            return {"txn_ref": ref, "type": "ledger_adjustment", "status": "proposed",
                    "ledger_delta": _r2(delta), "requires_approval": True, "narrative": note}

        def investigate_entry(note):
            return {"txn_ref": ref, "type": "investigate", "status": "proposed",
                    "ledger_delta": 0.0, "requires_approval": True, "narrative": note}

        if dup_sources:
            add_break("duplicate",
                      f"duplicate record(s) for {ref} within source(s) {dup_sources}",
                      investigate_entry("Investigate and de-duplicate the repeated record before any entry."))
            continue

        if len(present) == 1:
            only = next(iter(present))
            if only == "ledger":
                add_break("unmatched",
                          f"ledger-only orphan for {ref}: recorded in the ledger with no "
                          f"gateway/processor/bank support",
                          ledger_entry(-src_amt["ledger"],
                                       "Propose reversing the unsupported ledger entry pending investigation."))
            else:
                amt = src_amt[only]
                add_break("unmatched",
                          f"{only}-only orphan for {ref}: present in {only} with no ledger record",
                          ledger_entry(amt, f"Propose recording the {only} transaction in the ledger."))
            continue

        if len(currencies) > 1:
            add_break("currency_mismatch",
                      f"records for {ref} span currencies {sorted(currencies)}",
                      investigate_entry("Resolve the currency/FX basis before proposing a ledger entry."))
            continue

        if "ledger" in missing:
            tgt_amt = src_amt.get(tgt)
            add_break("missing_record",
                      f"{ref} present in {sorted(present)} but missing from {missing}; "
                      f"unrecorded relative to the {tgt} cash position",
                      ledger_entry(tgt_amt, f"Propose recording {ref} in the ledger at the {tgt} amount {tgt_amt}."))
            continue

        if missing:
            # present in ledger but missing from a cash source (e.g. captured, not yet funded)
            add_break("missing_record",
                      f"{ref} recorded in ledger but missing from {missing} "
                      f"(possible in-transit / unsettled)",
                      investigate_entry(f"Confirm whether {ref} is in-transit within {cfg['intransit_days']}d "
                                        f"before proposing any adjustment."))
            continue

        # all expected sources present -> compare amounts against cash position of record
        ledger_amt = src_amt.get("ledger")
        tgt_amt = src_amt.get(tgt)
        distinct = {round(a, 2) for a in src_amt.values()}
        if len(distinct) == 1:
            matched.append({"txn_ref": ref, "amount": next(iter(distinct)),
                            "sources": sorted(present), "citation": _cite(rows[0])})
        elif ledger_amt is not None and tgt_amt is not None and abs(ledger_amt - tgt_amt) > tol:
            delta = _r2(tgt_amt - ledger_amt)
            add_break("amount_mismatch",
                      f"{ref} amounts differ across sources {src_amt}; ledger {ledger_amt} "
                      f"vs {tgt} position {tgt_amt}",
                      ledger_entry(delta, f"Propose a {delta:+.2f} ledger adjustment to tie {ref} to the {tgt} amount."))
        else:
            # amounts differ only within tolerance / only among non-ledger sources
            matched.append({"txn_ref": ref, "amount": tgt_amt if tgt_amt is not None else next(iter(distinct)),
                            "sources": sorted(present), "citation": _cite(rows[0]),
                            "note": "within tolerance"})

    proposed_entries = [b["proposed_entry"] for b in breaks if b.get("proposed_entry")]

    # ---- tie-out against the cash position of record (transaction level only) ----
    txn_rows = [r for r in recs if str(r.get("level", "transaction")) != "settlement"]
    source_totals: dict[str, float] = defaultdict(float)
    for r in txn_rows:
        source_totals[r["source"]] += float(r["amount"])
    source_totals = {s: _r2(v) for s, v in source_totals.items()}
    target_source = _target_source(source_totals, cash_rank)
    target_total = source_totals.get(target_source, 0.0) if target_source else 0.0
    ledger_total = source_totals.get("ledger", 0.0)
    net_proposed = _r2(sum(p["ledger_delta"] for p in proposed_entries
                           if p.get("type") == "ledger_adjustment"))
    residual_before = _r2(target_total - ledger_total)
    residual_after = _r2(residual_before - net_proposed)

    tie_out = {
        "source_totals": source_totals,
        "target_source": target_source,
        "target_total": _r2(target_total),
        "ledger_total": _r2(ledger_total),
        "net_proposed": net_proposed,
        "residual_before": residual_before,
        "residual_after": residual_after,
        "tolerance": tol,
        "tied_out": abs(residual_after) <= tol,
    }

    return {
        "recon_id": doc.get("recon_id", f"trx-{doc['as_of']}-0001"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "currency": doc.get("currency"),
        "summary": {
            "groups": len(groups),
            "matched": len(matched),
            "breaks": len(breaks),
            "routed": len(routed),
        },
        "matched": matched,
        "breaks": breaks,
        "routed_breaks": routed,
        "proposed_entries": proposed_entries,
        "tie_out": tie_out,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ledger_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
