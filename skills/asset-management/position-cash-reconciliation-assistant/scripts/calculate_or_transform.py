#!/usr/bin/env python3
"""Deterministic position & cash reconciliation engine for position-cash-reconciliation-assistant.

Matches a fund's INTERNAL positions/cash (books / IBOR / accounting) to EXTERNAL records from a
custodian, prime broker, administrator, or counterparty, keyed by `match_key`. Classifies every
disagreement into a fixed break taxonomy, preserves lineage (source citations on every break),
computes a per-line tie-out, and emits PROPOSED-ONLY reconciling items.

HARD BOUNDARY: this engine never repairs a record, moves an asset, books a trade, or transfers
cash. Every reconciling item carries status "PROPOSED"; applying any change is a human/authorized
action in the book of record. Order/trade breaks are ROUTED to trade-break-resolver, not booked.

Break taxonomy (see references/domain-rules.md):
  quantity_break | cash_break | missing_internal | missing_external | pending_settlement | duplicate

Tie-out invariant (per reconciliation line / match_key): sum(break break_amount) ==
internal_total - external_total; residual == 0. Each ADJUSTING break's adjustment_amount ==
-break_amount. pending_settlement and routed (trade) breaks are documented, not adjusted.

Usage:
  python calculate_or_transform.py reconciliation.json    # prints the reconciliation pack JSON
  python calculate_or_transform.py --selftest             # runs bundled fixture + invariants
Prints the pack JSON to stdout (file/stdin mode). In --selftest mode prints self-check results
ending in a line "reconciliation self-test: N error(s)" (exit 0/1).
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "quantity_tolerance": 0.0,        # units; |internal_qty - external_qty| within this = matched
    "cash_tolerance": 0.01,           # native ccy; |internal - external| within this = matched
    "quantity_materiality": 100.0,    # units; position break material at/above this magnitude
    "cash_materiality_base": 1000.0,  # base ccy; cash break material at/above this base impact
    "pending_settlement_days": 3,     # settle_date within this many days after as_of = in-transit
    "fx_rates": {},                   # {CCY: rate_to_base}; base ccy is 1.0 implicitly
}
BREAK_TYPES = ("quantity_break", "cash_break", "missing_internal", "missing_external",
               "pending_settlement", "duplicate")
EXTERNAL_SYSTEMS = ("custodian", "prime_broker", "administrator", "counterparty")
TRADE_ROUTE = "trade-break-resolver"
DISCLAIMER = ("Reconciliation and proposed reconciling items only; no record has been repaired or "
              "adjusted and no asset, position, or cash has been moved. Breaks and proposed items "
              "require human review and authorized action in the book of record.")


def _round(x: float) -> float:
    return round(float(x) + 0.0, 2)


def _parse_dt(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _value(r: dict) -> float:
    """Native reconciliation value: signed quantity for positions, signed amount for cash."""
    if str(r.get("record_type")) == "position":
        return _round(r.get("quantity", 0))
    return _round(r.get("amount", 0))


def _unit(r: dict) -> str:
    """Reporting unit: 'units' for positions, the currency code for cash."""
    if str(r.get("record_type")) == "position":
        return "units"
    return str(r.get("currency") or "").upper()


def _cite(side: str, r: dict) -> str:
    return f"{side}:{r.get('source_ref', '?')}@{r.get('date', r.get('settle_date', '?'))}"


def _settle_dt(r: dict) -> datetime:
    return _parse_dt(r.get("settle_date") or r.get("date"))


def _is_pending(r: dict, as_of: datetime, days: int) -> bool:
    """True if r's settle_date lands after as_of but within the pending-settlement window."""
    try:
        delta = (_settle_dt(r) - as_of).days
    except (ValueError, TypeError):
        return False
    return 0 < delta <= days


def _fx_rate(cfg: dict, base_ccy: str, ccy: str):
    ccy = (ccy or "").upper()
    if not ccy or ccy == base_ccy.upper():
        return 1.0
    rates = {k.upper(): v for k, v in (cfg.get("fx_rates") or {}).items()}
    return rates.get(ccy)


def _base_impact(record_type: str, break_amount: float, unit: str, cfg: dict, base_ccy: str):
    """Base-currency impact for cash breaks (via versioned fx_rates). None for positions —
    this skill does not value positions (pricing is valuation-exception-packet's job)."""
    if record_type == "position":
        return None
    rate = _fx_rate(cfg, base_ccy, unit)
    if rate is None:
        return None
    return _round(break_amount * float(rate))


def _fingerprint(doc: dict, cfg: dict) -> str:
    """Stable content hash of the normalized inputs — the basis of an idempotent case id."""
    def norm(rows):
        return sorted(
            [{"record_id": r.get("record_id"), "match_key": r.get("match_key"),
              "account": r.get("account"), "source_system": r.get("source_system"),
              "record_type": r.get("record_type"), "date": str(r.get("date")),
              "settle_date": str(r.get("settle_date") or r.get("date")),
              "value": _value(r), "unit": _unit(r), "currency": (r.get("currency") or "").upper(),
              "route_hint": r.get("route_hint"), "source_ref": r.get("source_ref")} for r in rows],
            key=lambda r: (str(r["record_id"]),))
    payload = {
        "entity": doc.get("entity"), "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "base_currency": (doc.get("base_currency") or "").upper(),
        "config": {k: cfg[k] for k in sorted(cfg)},
        "internal": norm(doc.get("internal_records") or []),
        "external": norm(doc.get("external_records") or []),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _sort_key(r: dict):
    return (str(r.get("settle_date") or r.get("date")), str(r.get("record_id")))


def _proposed_item(pid: str, break_id: str, break_type: str, match_key: str, source_system: str,
                   break_amount: float, unit: str, currency) -> dict:
    """A PROPOSED (never applied) reconciling item that would bring the internal book to agree to
    the external record. The skill does not repair records, move assets, or decide which side is
    correct — an authorized human/system applies any change in the book of record."""
    adjustment = _round(-break_amount)
    return {
        "proposed_item_id": pid,
        "break_id": break_id,
        "status": "PROPOSED",
        "adjustment_amount": adjustment,
        "unit": unit,
        "currency": currency,
        "action": (f"Adjust the internal book by {adjustment:+.2f} {unit} to agree to the "
                   f"{source_system} record for {match_key} ({break_type}). PROPOSED - requires "
                   f"analyst review and authorized action in the book of record; not applied by "
                   f"this skill, which does not decide which side is correct."),
    }


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    qty_tol = float(cfg["quantity_tolerance"])
    cash_tol = float(cfg["cash_tolerance"])
    qty_mat = float(cfg["quantity_materiality"])
    cash_mat = float(cfg["cash_materiality_base"])
    pend_days = int(cfg["pending_settlement_days"])
    base_ccy = str(doc.get("base_currency") or "USD")
    as_of = _parse_dt(doc["as_of"])

    internal = list(doc.get("internal_records") or [])
    external = list(doc.get("external_records") or [])

    int_by_key: dict = {}
    ext_by_key: dict = {}
    for r in internal:
        int_by_key.setdefault(str(r.get("match_key")), []).append(r)
    for r in external:
        ext_by_key.setdefault(str(r.get("match_key")), []).append(r)

    breaks: list = []
    matched_count = 0
    seq = 0

    def _tol_for(rec_type: str) -> float:
        return qty_tol if rec_type == "position" else cash_tol

    def _material(rec_type: str, break_amount: float, base_impact) -> bool:
        if rec_type == "position":
            return abs(break_amount) >= qty_mat
        if base_impact is None:
            return False
        return abs(base_impact) >= cash_mat

    def new_break(btype, key, rec_type, account, source_system, unit, currency, break_amount,
                  int_row=None, ext_row=None, note=None, routed=False):
        nonlocal seq
        seq += 1
        break_amount = _round(break_amount)
        base_impact = _base_impact(rec_type, break_amount, unit, cfg, base_ccy)
        lineage = []
        b = {
            "break_id": f"BRK-{seq:04d}",
            "type": btype,
            "match_key": key,
            "record_type": rec_type,
            "account": account,
            "source_system": source_system,
            "unit": unit,
            "currency": currency,
            "break_amount": break_amount,
            "base_impact": base_impact,
            "material": _material(rec_type, break_amount, base_impact),
        }
        if int_row is not None:
            b["internal"] = {"record_id": int_row.get("record_id"), "value": _value(int_row),
                             "settle_date": int_row.get("settle_date") or int_row.get("date"),
                             "citation": _cite("internal", int_row)}
            lineage.append(_cite("internal", int_row))
        if ext_row is not None:
            b["external"] = {"record_id": ext_row.get("record_id"), "value": _value(ext_row),
                             "settle_date": ext_row.get("settle_date") or ext_row.get("date"),
                             "citation": _cite("external", ext_row)}
            lineage.append(_cite("external", ext_row))
        b["lineage"] = lineage
        if note:
            b["note"] = note
        # pending_settlement and routed (trade) breaks are documented, not adjusted here.
        if btype == "pending_settlement":
            b["requires_correction"] = False
            b["proposed_item"] = None
            b["routing"] = None
        elif routed:
            b["requires_correction"] = False
            b["proposed_item"] = None
            b["routing"] = {
                "route_to": TRADE_ROUTE,
                "reason": ("difference flagged as an order/trade discrepancy — resolving a trade "
                           "break is out of scope here; route to trade-break-resolver."),
            }
        else:
            b["requires_correction"] = True
            b["routing"] = None
            b["proposed_item"] = _proposed_item(f"PITM-{seq:04d}", b["break_id"], btype, key,
                                                source_system, break_amount, unit, currency)
        breaks.append(b)

    for key in sorted(set(int_by_key) | set(ext_by_key)):
        i_list = sorted(int_by_key.get(key, []), key=_sort_key)
        e_list = sorted(ext_by_key.get(key, []), key=_sort_key)
        npair = min(len(i_list), len(e_list))
        for idx in range(npair):
            g, s = i_list[idx], e_list[idx]
            rec_type = str(g.get("record_type") or s.get("record_type"))
            account = g.get("account") or s.get("account")
            source_system = s.get("source_system") or g.get("source_system")
            unit = _unit(g) if _unit(g) != "" else _unit(s)
            currency = (g.get("currency") or s.get("currency"))
            gv, sv = _value(g), _value(s)
            routed = str(g.get("route_hint") or s.get("route_hint")) == "trade_discrepancy"
            if abs(gv - sv) <= _tol_for(rec_type):
                matched_count += 1
                continue
            if _is_pending(g, as_of, pend_days) or _is_pending(s, as_of, pend_days):
                new_break("pending_settlement", key, rec_type, account, source_system, unit,
                          currency, gv - sv, int_row=g, ext_row=s,
                          note="matched line; difference attributable to an unsettled trade within "
                               "the settlement cutoff — expected to clear at settlement")
            else:
                btype = "quantity_break" if rec_type == "position" else "cash_break"
                new_break(btype, key, rec_type, account, source_system, unit, currency, gv - sv,
                          int_row=g, ext_row=s, routed=routed,
                          note=f"internal {gv:.2f} vs {source_system} {sv:.2f} ({unit})")
        # leftovers: duplicates (a pair existed) vs genuinely one-sided items
        for g in i_list[npair:]:
            rec_type = str(g.get("record_type"))
            unit, currency = _unit(g), g.get("currency")
            routed = str(g.get("route_hint")) == "trade_discrepancy"
            if npair >= 1:
                new_break("duplicate", key, rec_type, g.get("account"), g.get("source_system"),
                          unit, currency, _value(g), int_row=g, routed=routed,
                          note="extra internal record beyond the matched pair (duplicate booking)")
            elif _is_pending(g, as_of, pend_days):
                new_break("pending_settlement", key, rec_type, g.get("account"),
                          g.get("source_system"), unit, currency, _value(g), int_row=g,
                          note="internal record for an unsettled trade not yet reflected externally "
                               "— expected to clear at settlement")
            else:
                new_break("missing_external", key, rec_type, g.get("account"),
                          g.get("source_system"), unit, currency, _value(g), int_row=g,
                          routed=routed, note="on the internal book with no external confirmation")
        for s in e_list[npair:]:
            rec_type = str(s.get("record_type"))
            unit, currency = _unit(s), s.get("currency")
            routed = str(s.get("route_hint")) == "trade_discrepancy"
            src = s.get("source_system")
            if npair >= 1:
                new_break("duplicate", key, rec_type, s.get("account"), src, unit, currency,
                          -_value(s), ext_row=s, routed=routed,
                          note=f"extra {src} record beyond the matched pair (duplicate)")
            elif _is_pending(s, as_of, pend_days):
                new_break("pending_settlement", key, rec_type, s.get("account"), src, unit,
                          currency, -_value(s), ext_row=s,
                          note=f"{src} record for an unsettled trade not yet on the internal book "
                               "— expected to clear at settlement")
            else:
                new_break("missing_internal", key, rec_type, s.get("account"), src, unit,
                          currency, -_value(s), ext_row=s, routed=routed,
                          note=f"on the {src} record with no internal position/cash")

    groups = _build_groups(int_by_key, ext_by_key, breaks)
    all_ties_out = all(g["ties_out"] for g in groups)
    proposed = [b["proposed_item"] for b in breaks if b.get("proposed_item")]
    routed_breaks = [b["break_id"] for b in breaks if b.get("routing")]

    by_type = {t: sum(1 for b in breaks if b["type"] == t) for t in BREAK_TYPES}
    by_type = {t: n for t, n in by_type.items() if n}
    material_base = _round(sum(abs(b["base_impact"]) for b in breaks
                              if b.get("base_impact") is not None and b["material"]))

    fp = _fingerprint(doc, cfg)
    recon_id = f"pcr-{doc['entity']}-{doc['as_of']}-{fp[:8]}"

    pack = {
        "reconciliation_id": recon_id,
        "entity": doc["entity"],
        "as_of": doc["as_of"],
        "base_currency": base_ccy,
        "config_version": doc.get("config_version"),
        "input_fingerprint": fp,
        "tie_out": {
            "groups": groups,
            "all_ties_out": all_ties_out,
            "status": "clean_tie_out" if not breaks else "reconciled_with_breaks",
        },
        "matched_count": matched_count,
        "breaks": breaks,
        "proposed_items": proposed,
        "routed_breaks": routed_breaks,
        "summary": {
            "total_breaks": len(breaks),
            "by_type": by_type,
            "material_breaks": sum(1 for b in breaks if b["material"]),
            "proposed_items": len(proposed),
            "documented_pending": sum(1 for b in breaks if b["type"] == "pending_settlement"),
            "routed_to_trade_break_resolver": len(routed_breaks),
            "material_base_impact": material_base,
        },
        "disclaimer": DISCLAIMER,
    }
    pack["narrative"] = _narrative(pack)
    return pack


def _build_groups(int_by_key: dict, ext_by_key: dict, breaks: list) -> list:
    """Per-line (match_key) tie-out: breaks fully explain internal-vs-external difference."""
    groups = []
    for key in sorted(set(int_by_key) | set(ext_by_key)):
        i_rows = int_by_key.get(key, [])
        e_rows = ext_by_key.get(key, [])
        kbreaks = [b for b in breaks if b["match_key"] == key]
        internal_total = _round(sum(_value(r) for r in i_rows))
        external_total = _round(sum(_value(r) for r in e_rows))
        difference = _round(internal_total - external_total)
        breaks_total = _round(sum(b["break_amount"] for b in kbreaks))
        residual = _round(difference - breaks_total)
        # documented/routed items carry no adjustment and remain outstanding after corrections
        non_adjusting = _round(sum(b["break_amount"] for b in kbreaks
                                   if not b.get("requires_correction")))
        adjustments = _round(sum(b["proposed_item"]["adjustment_amount"] for b in kbreaks
                                 if b.get("proposed_item")))
        corrected_internal_total = _round(internal_total + adjustments)
        sample = (i_rows or e_rows)[0] if (i_rows or e_rows) else {}
        groups.append({
            "match_key": key,
            "record_type": sample.get("record_type"),
            "account": sample.get("account"),
            "source_system": (e_rows[0].get("source_system") if e_rows
                              else sample.get("source_system")),
            "unit": _unit(sample),
            "internal_total": internal_total,
            "external_total": external_total,
            "difference": difference,
            "breaks_total": breaks_total,
            "residual": residual,
            "corrected_internal_total": corrected_internal_total,
            "documented_or_routed_total": non_adjusting,
            "ties_out": residual == 0.0,
        })
    return groups


def _narrative(pack: dict) -> str:
    s = pack["summary"]
    g = pack["tie_out"]["groups"]
    tie = "all reconciliation lines tie out (residual 0)" if pack["tie_out"]["all_ties_out"] \
        else "one or more lines do NOT tie out"
    return (f"Position & cash reconciliation {pack['reconciliation_id']} for {pack['entity']} as of "
            f"{pack['as_of']} ({pack['base_currency']} base). {len(g)} reconciliation line(s); "
            f"{s['total_breaks']} break(s) classified {s['by_type']}; {s['material_breaks']} "
            f"material. {s['proposed_items']} PROPOSED reconciling item(s); {s['documented_pending']} "
            f"documented pending-settlement item(s); {s['routed_to_trade_break_resolver']} routed to "
            f"trade-break-resolver. {tie}. " + pack["disclaimer"])


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reconciliation_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = compute(doc)
    errors: list = []
    if not out["tie_out"]["all_ties_out"]:
        errors.append("tie-out: not all reconciliation lines tie (residual != 0 somewhere)")
    for grp in out["tie_out"]["groups"]:
        if grp["residual"] != 0.0:
            errors.append(f"{grp['match_key']}: residual {grp['residual']} != 0")
        if _round(grp["breaks_total"]) != _round(grp["difference"]):
            errors.append(f"{grp['match_key']}: breaks_total != internal-external difference")
        if _round(grp["corrected_internal_total"] - grp["external_total"]) != \
                _round(grp["documented_or_routed_total"]):
            errors.append(f"{grp['match_key']}: corrected internal does not agree to external "
                          "leaving only documented/routed items")
    for b in out["breaks"]:
        if b["type"] not in BREAK_TYPES:
            errors.append(f"{b['break_id']}: type {b['type']!r} not in taxonomy")
        if not b["lineage"]:
            errors.append(f"{b['break_id']}: no lineage citation")
        c = b.get("proposed_item")
        if b["type"] == "pending_settlement" or b.get("routing"):
            if c is not None:
                errors.append(f"{b['break_id']}: documented/routed break must carry no proposed item")
        else:
            if not c or c.get("status") != "PROPOSED":
                errors.append(f"{b['break_id']}: proposed item missing or not PROPOSED")
            elif _round(c["adjustment_amount"]) != _round(-b["break_amount"]):
                errors.append(f"{b['break_id']}: adjustment does not offset break_amount")
    # every expected break type is exercised by the bundled fixture
    for t in BREAK_TYPES:
        if not any(b["type"] == t for b in out["breaks"]):
            errors.append(f"fixture does not exercise break type {t!r}")
    if not out["routed_breaks"]:
        errors.append("fixture does not exercise trade-break routing")
    # idempotency: recompute must be byte-identical
    if json.dumps(compute(doc), sort_keys=True) != json.dumps(out, sort_keys=True):
        errors.append("non-idempotent: recompute produced a different result")
    for e in errors:
        print("ERROR", e)
    print(f"reconciliation self-test: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
