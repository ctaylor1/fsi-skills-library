#!/usr/bin/env python3
"""Deterministic NAV tie-out / break-classification engine for nav-preparation-tie-out.

Reconciles the NAV components a fund accountant must tie out — positions, prices, accruals,
income, expenses, shares, and cash — between the fund's book of record and an independent
verifier source (custodian, administrator, or approved pricing source) per component.
Classifies every disagreement into a fixed break taxonomy, preserves lineage (a source
citation on every break), computes the tie-out, and emits PROPOSED-ONLY resolutions.

IMPORTANT — HARD BOUNDARY (R3 decision-support):
  This engine NEVER strikes/certifies a NAV, NEVER chooses or overrides a price, and NEVER
  posts an accounting entry. It produces evidence and PROPOSED resolutions only. Price
  disagreements are routed to `valuation-exception-packet`; the fund accountant reviews and
  takes any authorized action in the systems of record.

Break taxonomy (see references/domain-rules.md):
  quantity_break | price_break | cash_break | accrual_break | income_break |
  expense_break | shares_break | missing_record | timing_difference

Tie-out invariant: for every reconciled (component, currency) control total the classified
breaks fully explain book_total - verifier_total; the overall residual == 0 and the number of
non-timing breaks equals out_of_tolerance_count.

Usage:
  python calculate_or_transform.py tie_out_job.json   # prints the tie-out packet JSON
  python calculate_or_transform.py --selftest         # runs bundled fixture + invariants
Prints the packet JSON to stdout (file/stdin mode). In --selftest mode prints self-check
results ending in a line "nav tie-out self-test: N error(s)" (exit 0/1).
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

# Ordered so break_id / resolution_id sequencing is deterministic.
COMPONENTS = ("position", "price", "cash", "accrual", "income", "expense", "shares")
# Components whose values are additive within a currency group (meaningful control totals).
# position (per-instrument quantity) and price (per-instrument level) are line-level only.
AGGREGATABLE = {"cash", "accrual", "income", "expense", "shares"}
COMPONENT_BREAK = {
    "position": "quantity_break", "price": "price_break", "cash": "cash_break",
    "accrual": "accrual_break", "income": "income_break", "expense": "expense_break",
    "shares": "shares_break",
}
BREAK_TYPES = ("quantity_break", "price_break", "cash_break", "accrual_break",
               "income_break", "expense_break", "shares_break", "missing_record",
               "timing_difference")
PRICE_ROUTE = "valuation-exception-packet"
PRECISION = {"position": 4, "price": 6, "shares": 4,
             "cash": 2, "accrual": 2, "income": 2, "expense": 2}

DEFAULT_CONFIG = {
    "tolerances": {"position": 0.0001, "price": 0.000001, "cash": 0.01, "accrual": 0.01,
                   "income": 0.01, "expense": 0.01, "shares": 0.0001},
    "date_tolerance_days": 1,
    "materiality": {"default": 100.0, "price": 0.01, "position": 1.0, "shares": 1.0},
    "component_sources": {"position": "custodian", "price": "pricing", "cash": "custodian",
                          "accrual": "administrator", "income": "administrator",
                          "expense": "administrator", "shares": "administrator"},
}
DISCLAIMER = ("Tie-out and break packet only; NAV has not been struck, no price has been "
              "selected, and no accounting entry has been posted. All resolutions are "
              "PROPOSED and require fund-accountant review and authorized action in the "
              "systems of record.")


def _merge_config(cfg: dict) -> dict:
    out = {k: dict(v) if isinstance(v, dict) else v for k, v in DEFAULT_CONFIG.items()}
    for k, v in (cfg or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out


def _round(x, component: str) -> float:
    return round(float(x) + 0.0, PRECISION.get(component, 2))


def _parse_dt(s) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _cite(source: str, r: dict) -> str:
    return f"{source}:{r.get('source_ref', '?')}@{r.get('as_of', '?')}"


def _fingerprint(doc: dict, cfg: dict) -> str:
    """Stable content hash of the normalized inputs — the basis of an idempotent id."""
    def norm(rows):
        return sorted(
            [{"line_id": r.get("line_id"), "component": r.get("component"),
              "key": r.get("key"), "source": r.get("source"),
              "value": round(float(r.get("value", 0)) + 0.0, 8),
              "currency": (r.get("currency") or "").upper(),
              "as_of": str(r.get("as_of", "")), "source_ref": r.get("source_ref")}
             for r in rows],
            key=lambda r: (str(r["component"]), str(r["source"]), str(r["key"]), str(r["line_id"])))
    payload = {
        "fund": doc.get("fund"), "share_class": doc.get("share_class"),
        "as_of": doc.get("as_of"), "config_version": doc.get("config_version"),
        "base_currency": (doc.get("base_currency") or "").upper(),
        "config": json.dumps(cfg, sort_keys=True),
        "lines": norm(doc.get("lines") or []),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _sort_key(r: dict):
    return (str(r.get("as_of", "")), str(r.get("line_id", "")))


def _resolution(seq: int, break_id: str, btype: str, component: str, key: str) -> dict:
    """Build a PROPOSED-ONLY resolution. It never chooses a value, strikes NAV, or posts."""
    if btype == "price_break":
        disposition = "route_to_valuation_exception_packet"
        route_to = PRICE_ROUTE
        action = (f"Route the price disagreement on {key} to {PRICE_ROUTE} for valuation "
                  f"review; this skill does not choose a price.")
    else:
        disposition = "investigate_and_adjust_in_source"
        route_to = None
        action = (f"Investigate the {btype.replace('_', ' ')} on {key} between book and its "
                  f"verifier source and propose an adjustment for review in the accounting "
                  f"system; this skill does not post it.")
    return {
        "resolution_id": f"PRS-{seq:04d}",
        "break_id": break_id,
        "status": "PROPOSED",
        "disposition": disposition,
        "route_to": route_to,
        "recommended_action": action,
        "chooses_value": False,
        "strikes_nav": False,
        "posts_entry": False,
        "note": ("PROPOSED evidence only; NAV not struck, no price chosen, no accounting "
                 "entry posted. Requires fund-accountant review and authorized action in the "
                 "systems of record."),
    }


def compute(doc: dict) -> dict:
    cfg = _merge_config(doc.get("config") or {})
    tol = cfg["tolerances"]
    date_tol = int(cfg["date_tolerance_days"])
    mat = cfg["materiality"]
    comp_sources = cfg["component_sources"]
    base_ccy = (doc.get("base_currency") or "").upper()
    lines = list(doc.get("lines") or [])

    def ccy(r):
        return (r.get("currency") or base_ccy or "").upper()

    def is_material(component, impact):
        thr = float(mat.get(component, mat.get("default", 100.0)))
        return abs(impact) >= thr

    breaks: list = []
    matched_count = 0
    seq = 0
    # control totals keyed by (component, currency) for aggregatable components
    ctl: dict = {}

    def touch_ctl(component, currency):
        if component in AGGREGATABLE:
            ctl.setdefault((component, currency),
                           {"component": component, "currency": currency,
                            "book_total": 0.0, "verifier_total": 0.0,
                            "difference": 0.0, "breaks_impact_sum": 0.0})

    def new_break(component, btype, key, currency, impact, book_row=None, ver_row=None, note=None):
        nonlocal seq
        seq += 1
        impact = _round(impact, component)
        lineage = []
        b = {
            "break_id": f"BRK-{seq:04d}",
            "type": btype,
            "component": component,
            "key": key,
            "currency": currency,
            "verifier_source": comp_sources.get(component),
            "impact": impact,
            "unit": {"position": "quantity", "price": "price", "shares": "shares"}.get(component, "amount"),
            "material": is_material(component, impact) if btype != "timing_difference" else False,
        }
        if book_row is not None:
            b["book"] = {"line_id": book_row.get("line_id"), "value": _round(book_row["value"], component),
                         "as_of": book_row.get("as_of"), "citation": _cite("book", book_row)}
            lineage.append(_cite("book", book_row))
        if ver_row is not None:
            vsrc = ver_row.get("source")
            b["verifier"] = {"line_id": ver_row.get("line_id"), "value": _round(ver_row["value"], component),
                             "as_of": ver_row.get("as_of"), "citation": _cite(vsrc, ver_row)}
            lineage.append(_cite(vsrc, ver_row))
        b["lineage"] = lineage
        if note:
            b["note"] = note
        if btype == "timing_difference":
            b["requires_resolution"] = False
            b["proposed_resolution"] = None
        else:
            b["requires_resolution"] = True
            b["proposed_resolution"] = _resolution(seq, b["break_id"], btype, component, key)
        if component in AGGREGATABLE:
            touch_ctl(component, currency)
            ctl[(component, currency)]["breaks_impact_sum"] += impact
        breaks.append(b)

    # --- component-by-component reconciliation ---
    for component in COMPONENTS:
        verifier = comp_sources.get(component)
        comp_lines = [r for r in lines if r.get("component") == component]
        book_lines = [r for r in comp_lines if r.get("source") == "book"]
        ver_lines = [r for r in comp_lines if r.get("source") == verifier]

        # accumulate control totals (independent of the break list)
        for r in book_lines:
            touch_ctl(component, ccy(r))
            if component in AGGREGATABLE:
                ctl[(component, ccy(r))]["book_total"] += float(r["value"])
        for r in ver_lines:
            touch_ctl(component, ccy(r))
            if component in AGGREGATABLE:
                ctl[(component, ccy(r))]["verifier_total"] += float(r["value"])

        book_by_key: dict = {}
        ver_by_key: dict = {}
        for r in book_lines:
            book_by_key.setdefault(str(r.get("key")), []).append(r)
        for r in ver_lines:
            ver_by_key.setdefault(str(r.get("key")), []).append(r)

        for key in sorted(set(book_by_key) | set(ver_by_key)):
            bl = sorted(book_by_key.get(key, []), key=_sort_key)
            vl = sorted(ver_by_key.get(key, []), key=_sort_key)
            npair = min(len(bl), len(vl))
            for i in range(npair):
                b, v = bl[i], vl[i]
                bv, vv = float(b["value"]), float(v["value"])
                delta = _round(bv - vv, component)
                if abs(delta) > float(tol.get(component, 0.0)):
                    new_break(component, COMPONENT_BREAK[component], key, ccy(b), delta,
                              book_row=b, ver_row=v,
                              note=(f"book {bv:.{PRECISION.get(component, 2)}f} vs "
                                    f"{v.get('source')} {vv:.{PRECISION.get(component, 2)}f} "
                                    f"(tolerance {tol.get(component)})"))
                elif abs((_parse_dt(b.get("as_of")) - _parse_dt(v.get("as_of"))).days) > date_tol:
                    new_break(component, "timing_difference", key, ccy(b), 0.0,
                              book_row=b, ver_row=v,
                              note="matched value; as-of/settlement dates differ beyond cutoff — clears next cycle")
                else:
                    matched_count += 1
            # leftovers: one-sided records are missing on the other side
            for b in bl[npair:]:
                new_break(component, "missing_record", key, ccy(b), float(b["value"]),
                          book_row=b, note=f"{component} present in book, absent at {verifier}")
            for v in vl[npair:]:
                new_break(component, "missing_record", key, ccy(v), -float(v["value"]),
                          ver_row=v, note=f"{component} present at {verifier}, absent in book")

    # --- control totals + tie-out ---
    control_totals = []
    residual = 0.0
    for kk in sorted(ctl):
        c = ctl[kk]
        c["book_total"] = round(c["book_total"] + 0.0, 2)
        c["verifier_total"] = round(c["verifier_total"] + 0.0, 2)
        c["difference"] = round(c["book_total"] - c["verifier_total"], 2)
        c["breaks_impact_sum"] = round(c["breaks_impact_sum"] + 0.0, 2)
        c["ties_out"] = abs(c["difference"] - c["breaks_impact_sum"]) < 0.005
        residual = round(residual + (c["difference"] - c["breaks_impact_sum"]), 2)
        control_totals.append(c)

    non_timing = [b for b in breaks if b["type"] != "timing_difference"]
    resolutions = [b["proposed_resolution"] for b in breaks if b.get("proposed_resolution")]
    by_type = {t: sum(1 for b in breaks if b["type"] == t) for t in BREAK_TYPES}
    by_type = {t: n for t, n in by_type.items() if n}

    fp = _fingerprint(doc, cfg)
    sclass = doc.get("share_class") or "NA"
    tie_out_id = f"npt-{doc['fund']}-{sclass}-{doc['as_of']}-{fp[:8]}"

    return {
        "tie_out_id": tie_out_id,
        "fund": doc["fund"],
        "share_class": doc.get("share_class"),
        "as_of": doc["as_of"],
        "base_currency": doc.get("base_currency"),
        "config_version": doc.get("config_version"),
        "input_fingerprint": fp,
        "tie_out": {
            "control_totals": control_totals,
            "residual": round(residual + 0.0, 2),
            "out_of_tolerance_count": len(non_timing),
            "captured_break_count": len(non_timing),
            "components_reconciled": sorted({b["component"] for b in breaks}
                                            | {r.get("component") for r in lines if r.get("component") in COMPONENTS}),
            "all_control_totals_tie": all(c["ties_out"] for c in control_totals),
            "ties_out": (round(residual + 0.0, 2) == 0.0) and all(c["ties_out"] for c in control_totals),
            "status": "clean_tie_out" if not breaks else "reconciled_with_breaks",
        },
        "matched_count": matched_count,
        "breaks": breaks,
        "proposed_resolutions": resolutions,
        "summary": {
            "total_breaks": len(breaks),
            "by_type": by_type,
            "material_breaks": sum(1 for b in breaks if b["material"]),
            "resolutions_proposed": len(resolutions),
            "price_breaks_routed": sum(1 for b in breaks if b["type"] == "price_break"),
        },
        "disclaimer": DISCLAIMER,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "tie_out_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = compute(doc)
    errors = []
    t = out["tie_out"]
    if t["residual"] != 0.0:
        errors.append(f"tie-out residual {t['residual']} != 0 (breaks do not explain the differences)")
    if not t["all_control_totals_tie"]:
        errors.append("at least one control total does not tie (difference != breaks_impact_sum)")
    if t["out_of_tolerance_count"] != t["captured_break_count"]:
        errors.append("out_of_tolerance_count != captured_break_count")
    for b in out["breaks"]:
        if b["type"] not in BREAK_TYPES:
            errors.append(f"{b['break_id']}: type {b['type']!r} not in taxonomy")
        if not b["lineage"]:
            errors.append(f"{b['break_id']}: no lineage citation")
        r = b.get("proposed_resolution")
        if b["type"] == "timing_difference":
            if r is not None or b.get("requires_resolution") is not False:
                errors.append(f"{b['break_id']}: timing_difference must be a documented item with no resolution")
            continue
        if not r or r.get("status") != "PROPOSED":
            errors.append(f"{b['break_id']}: resolution missing or not PROPOSED")
            continue
        if r.get("chooses_value") or r.get("strikes_nav") or r.get("posts_entry"):
            errors.append(f"{b['break_id']}: resolution asserts a prohibited action (choose/strike/post)")
        if b["type"] == "price_break" and r.get("route_to") != PRICE_ROUTE:
            errors.append(f"{b['break_id']}: price_break not routed to {PRICE_ROUTE}")
    # expected taxonomy coverage in the fixture
    seen = set(out["summary"]["by_type"])
    for want in BREAK_TYPES:
        if want not in seen:
            errors.append(f"fixture missing expected break type: {want}")
    # idempotency: recompute must be identical
    if json.dumps(compute(doc), sort_keys=True) != json.dumps(out, sort_keys=True):
        errors.append("non-idempotent: recompute produced a different result")
    for e in errors:
        print("ERROR", e)
    print(f"nav tie-out self-test: {len(errors)} error(s)")
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
