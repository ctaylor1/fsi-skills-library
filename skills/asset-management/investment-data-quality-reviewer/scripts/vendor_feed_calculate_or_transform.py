#!/usr/bin/env python3
"""Deterministic internal-vs-vendor market-data reconciliation for investment-data-quality-reviewer.

Matches a firm's internal book-of-record observations to one vendor feed's observations cell by
cell, where a cell is one (instrument_id, domain, field) triple across five domains - price,
rating, index_constituent, corporate_action, instrument_attribute. It classifies every
disagreement into a fixed break taxonomy, preserves lineage (per-source citation + as-of time on
every break), computes a completeness tie-out, and routes each break to its owner.

HARD BOUNDARY: this engine NEVER chooses the canonical value, overrides a source, or repairs a
record. Every break carries canonical_value == null and disposition == "UNRESOLVED". Price-domain
breaks are routed to the fund-valuation-oversight-reviewer process; the skill does not adjudicate which
source is correct.

Break taxonomy (see references/vendor_feed-domain-rules.md):
  value_mismatch | missing_in_internal | missing_in_vendor | stale_as_of

Tie-out invariant (completeness): matched_cells + break_cells == total_cells (the union of cells
present on either side); residual_cells == 0. No cell is dropped or double-counted.

Usage:
  python calculate_or_transform.py feed_reconciliation.json   # prints reconciliation JSON
  python calculate_or_transform.py --selftest                 # runs bundled fixture + invariants
Prints the reconciliation JSON to stdout (file/stdin mode). In --selftest mode prints self-check
results ending in a line "reconciliation self-test: N error(s)" (exit 0/1).
"""
from __future__ import annotations
import hashlib
import json
import sys
import math
from decimal import Decimal
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "numeric_tolerance_abs": 0.0001,
    "numeric_tolerance_pct": 0.001,
    "materiality_pct": 0.005,
    "materiality_abs": 0.5,
    "staleness_max_age_days": 3,
}
BREAK_TYPES = ("value_mismatch", "missing_in_internal", "missing_in_vendor", "stale_as_of", "not_comparable")

# Where each domain's discrepancies are routed. The mandated price route is the
# fund-valuation-oversight-reviewer process; other domains route to the reference-data owner. Routing
# only forwards evidence - it never resolves the disagreement here.
ROUTE_BY_DOMAIN = {
    "price": "fund-valuation-oversight-reviewer",
    "rating": "investment-reference-data-reviewer",
    "instrument_attribute": "investment-reference-data-reviewer",
    "corporate_action": "corporate-action-interpreter",
    "index_constituent": "index/benchmark data owner (human review)",
}
PRICE_ROUTE = "fund-valuation-oversight-reviewer"

DISCLAIMER = ("Field-level discrepancy report only; this skill does not choose the canonical "
              "value, override a source, or repair any record. Price exceptions are routed to "
              "the valuation-exception process. All discrepancies require human review before "
              "any system-of-record change.")


def _num(v):
    try:
        value = float(v)
        return value if not isinstance(v,bool) and math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def _round(x, nd=6):
    return round(float(x) + 0.0, nd)


def _norm_cat(v) -> str:
    return str(v).strip().upper()


def _parse_dt(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _cite(side: str, r: dict) -> str:
    return f"{side}:{r.get('source_ref', '?')}@{r.get('as_of', '?')}"


def _side_view(side: str, r: dict) -> dict:
    return {
        "value": r.get("value"),
        "as_of": r.get("as_of"),
        "currency": r.get("currency"),
        "source_ref": r.get("source_ref"),
        "citation": _cite(side, r),
    }


def _is_numeric(iv: dict, vv: dict) -> bool:
    """Numeric only when both values parse as numbers and neither declares itself categorical."""
    if iv.get("data_type") == "categorical" or vv.get("data_type") == "categorical":
        return False
    return _num(iv.get("value")) is not None and _num(vv.get("value")) is not None


def _fingerprint(doc: dict, cfg: dict) -> str:
    """Stable content hash of the normalized inputs - the basis of an idempotent id."""
    def norm(rows):
        out = []
        for r in rows:
            n = _num(r.get("value"))
            val = r.get("value")
            out.append({
                "instrument_id": r.get("instrument_id"),
                "domain": r.get("domain"),
                "field": r.get("field"),
                "value": val,
                "as_of": str(r.get("as_of")),
                "source_ref": r.get("source_ref"),
                "currency": (r.get("currency") or "").upper(),
                "data_type": r.get("data_type"),
                "unit": r.get("unit"),
                "valuation_date": r.get("valuation_date"),
            })
        return sorted(out, key=lambda r: (str(r["instrument_id"]), str(r["domain"]), str(r["field"])))
    payload = {
        "entity": doc.get("entity"),
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "internal_source": doc.get("internal_source"),
        "vendor_source": doc.get("vendor_source"),
        "currency": (doc.get("currency") or "").upper(),
        "config": {k: cfg[k] for k in sorted(cfg)},
        "internal": norm(doc.get("internal_observations") or []),
        "vendor": norm(doc.get("vendor_observations") or []),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _age_days(cutoff: datetime, obs_as_of: str) -> int:
    return (cutoff - _parse_dt(obs_as_of)).days


def _compute_native(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    tol_abs = float(cfg["numeric_tolerance_abs"])
    tol_pct = float(cfg["numeric_tolerance_pct"])
    mat_pct = float(cfg["materiality_pct"])
    mat_abs = float(cfg["materiality_abs"])
    stale_days = int(cfg["staleness_max_age_days"])
    cutoff = _parse_dt(doc["as_of"])

    internal = list(doc.get("internal_observations") or [])
    vendor = list(doc.get("vendor_observations") or [])

    def index(rows):
        result = {}
        for r in rows:
            key = (str(r.get("instrument_id")), str(r.get("domain")), str(r.get("field")))
            if key in result: raise ValueError("Duplicate source cell requires explicit upstream consolidation")
            result[key] = r
        return result

    iv_by_cell = index(internal)
    vv_by_cell = index(vendor)
    all_cells = sorted(set(iv_by_cell) | set(vv_by_cell))

    breaks: list = []
    matched_count = 0
    seq = 0

    def add_break(btype, cell, iv=None, vv=None, difference=None, as_of_gap_days=None,
                  material=False, data_type=None, note=""):
        nonlocal seq
        seq += 1
        instrument_id, domain, field = cell
        lineage = []
        b = {
            "break_id": f"BRK-{seq:04d}",
            "instrument_id": instrument_id,
            "domain": domain,
            "field": field,
            "type": btype,
            "data_type": data_type,
            "internal": _side_view("internal", iv) if iv is not None else None,
            "vendor": _side_view("vendor", vv) if vv is not None else None,
            "difference": difference,
            "as_of_gap_days": as_of_gap_days,
            "material": material,
            "route": ROUTE_BY_DOMAIN.get(domain, "reference-data owner (human review)"),
            "disposition": "UNRESOLVED",   # skill never resolves a discrepancy
            "canonical_value": None,       # HARD BOUNDARY: the canonical value is never chosen
            "note": note,
        }
        if iv is not None:
            lineage.append(_cite("internal", iv))
        if vv is not None:
            lineage.append(_cite("vendor", vv))
        b["lineage"] = lineage
        breaks.append(b)

    for cell in all_cells:
        instrument_id, domain, field = cell
        iv = iv_by_cell.get(cell)
        vv = vv_by_cell.get(cell)

        if iv is not None and vv is None:
            add_break("missing_in_vendor", cell, iv=iv, material=True,
                      note="present in internal book-of-record; absent from vendor feed")
            continue
        if iv is None and vv is not None:
            add_break("missing_in_internal", cell, vv=vv, material=True,
                      note="present in vendor feed; absent from internal book-of-record")
            continue

        before = len(breaks)
        try:
            iv_age = _age_days(cutoff, iv.get("as_of"))
            vv_age = _age_days(cutoff, vv.get("as_of"))
            dates_valid = iv_age >= 0 and vv_age >= 0
        except (ValueError, TypeError): dates_valid = False
        if not dates_valid:
            add_break("not_comparable", cell, iv, vv, material=None, note="Observation date invalid or future; comparison withheld")
            continue
        stale = iv_age > stale_days or vv_age > stale_days
        if stale:
            add_break("stale_as_of", cell, iv, vv, as_of_gap_days=max(iv_age,vv_age), material=None,
                      note="Stale evidence is an additional finding, independent of value disagreement")
        numeric = _is_numeric(iv,vv)
        reasons = []
        if (domain == 'price' or iv.get('data_type') == 'numeric' or vv.get('data_type') == 'numeric') and not numeric:
            reasons.append('required finite numeric observation unavailable')
        if numeric and (not iv.get('unit') or iv.get('unit') != vv.get('unit')):
            reasons.append('numeric unit missing or mismatched')
        if domain == 'price' and (not iv.get('currency') or iv.get('currency') != vv.get('currency')):
            reasons.append('price currencies missing or mismatched')
        if str(iv.get('valuation_date') or iv['as_of'][:10]) != str(vv.get('valuation_date') or vv['as_of'][:10]):
            reasons.append('economic valuation dates differ')
        if reasons:
            add_break('not_comparable',cell,iv,vv,material=None,note='; '.join(reasons))
            continue
        if numeric:
            a,b_ = Decimal(str(iv['value'])),Decimal(str(vv['value']))
            diff=a-b_;base=max(abs(a),abs(b_))
            tol=max(Decimal(str(tol_abs)),Decimal(str(tol_pct))*base)
            if abs(diff)>tol:
                material=abs(diff)>=Decimal(str(mat_abs)) or (base!=0 and abs(diff)/base>=Decimal(str(mat_pct)))
                add_break('value_mismatch',cell,iv,vv,difference=str(diff),data_type='numeric',material=material,
                          note='Comparable supplied numeric values disagree outside the configured tolerance')
        elif _norm_cat(iv.get('value')) != _norm_cat(vv.get('value')):
            add_break('value_mismatch',cell,iv,vv,data_type='categorical',material=True,note='Comparable categorical values disagree')
        if len(breaks)==before: matched_count+=1

    total_cells = len(all_cells)
    break_cells = len({(b["instrument_id"], b["domain"], b["field"]) for b in breaks})
    cells_accounted = matched_count + break_cells
    residual_cells = total_cells - cells_accounted

    by_type = {t: sum(1 for b in breaks if b["type"] == t) for t in BREAK_TYPES}
    by_type = {t: n for t, n in by_type.items() if n}
    by_domain: dict = {}
    for b in breaks:
        by_domain[b["domain"]] = by_domain.get(b["domain"], 0) + 1

    routing: dict = {}
    for b in breaks:
        routing.setdefault(b["route"], []).append(b["break_id"])

    price_routed = [b["break_id"] for b in breaks if b["domain"] == "price"]

    fp = _fingerprint(doc, cfg)
    recon_id = f"ivfr-{doc['entity']}-{doc['as_of']}-{fp[:8]}"

    return {
        "reconciliation_id": recon_id,
        "entity": doc["entity"],
        "as_of": doc["as_of"],
        "internal_source": doc.get("internal_source"),
        "vendor_source": doc.get("vendor_source"),
        "currency": doc.get("currency"),
        "config_version": doc.get("config_version"),
        "input_fingerprint": fp,
        "tie_out": {
            "internal_cells": len(iv_by_cell),
            "vendor_cells": len(vv_by_cell),
            "total_cells": total_cells,
            "matched_cells": matched_count,
            "break_cells": break_cells,
            "cells_accounted": cells_accounted,
            "residual_cells": residual_cells,
            "ties_out": residual_cells == 0 and cells_accounted == total_cells,
            "status": "clean_tie_out" if not breaks else "reconciled_with_discrepancies",
        },
        "breaks": breaks,
        "summary": {
            "total_breaks": len(breaks),
            "by_type": by_type,
            "by_domain": by_domain,
            "material_breaks": sum(1 for b in breaks if b["material"]),
            "price_breaks_routed": len(price_routed),
        },
        "routing": routing,
        "disclaimer": DISCLAIMER,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "feed_reconciliation_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = compute(doc)
    errors = []
    t = out["tie_out"]
    if not t["ties_out"] or t["residual_cells"] != 0:
        errors.append(f"tie-out does not complete: residual_cells {t['residual_cells']}")
    if t["matched_cells"] + t["break_cells"] != t["total_cells"]:
        errors.append("matched + breaks != total cells (cells dropped or double-counted)")
    for b in out["breaks"]:
        if b["type"] not in BREAK_TYPES:
            errors.append(f"{b['break_id']}: type {b['type']!r} not in taxonomy")
        if not b["lineage"]:
            errors.append(f"{b['break_id']}: no lineage citation")
        for cit in b["lineage"]:
            if not (cit.startswith("internal:") or cit.startswith("vendor:")):
                errors.append(f"{b['break_id']}: lineage {cit!r} lacks internal:/vendor: prefix")
        if b["canonical_value"] is not None:
            errors.append(f"{b['break_id']}: canonical_value set - skill must never choose it")
        if b["disposition"] != "UNRESOLVED":
            errors.append(f"{b['break_id']}: disposition {b['disposition']!r} != UNRESOLVED")
        if b["domain"] == "price" and b["route"] != PRICE_ROUTE:
            errors.append(f"{b['break_id']}: price break not routed to {PRICE_ROUTE}")
    # the golden fixture must exhibit every break type at least once
    seen = {b["type"] for b in out["breaks"]}
    for expected in set(BREAK_TYPES) - {"not_comparable"}:
        if expected not in seen:
            errors.append(f"fixture missing expected break type {expected}")
    # idempotency: recompute must be byte-identical
    if json.dumps(compute(doc), sort_keys=True) != json.dumps(out, sort_keys=True):
        errors.append("non-idempotent: recompute produced a different result")
    for e in errors:
        print("ERROR", e)
    print(f"reconciliation self-test: {len(errors)} error(s)")
    return 1 if errors else 0


from native_integrity import attach_source, canonical_hash

def compute(doc):
    canonical_hash(doc)
    return attach_source(_compute_native(doc), doc)


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
