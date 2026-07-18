#!/usr/bin/env python3
"""Deterministic computation for reinsurance-treaty-interpreter.

Turns a validated treaty (plus optional occurrence losses) into a normalized interpretation
object with an ILLUSTRATIVE ceded-recovery calculation under the excess-of-loss layer terms.
This is descriptive arithmetic only — it reproduces what the treaty terms specify so the
plain-language interpretation is internally consistent. It never determines whether a real
claim is recoverable, nor what to bill, collect, reserve, or book.

Canonical layer arithmetic (documented in references/domain-rules.md), losses applied in order:
  aggregate_limit     = layer.aggregate_limit  (or limit * (1 + reinstatements))
  layer_loss          = min(max(gross - attachment, 0), limit)
  ceded_recovery      = min(layer_loss, aggregate_limit - cumulative_ceded_before)
  cumulative_ceded   += ceded_recovery
Reinstatement premium (band method): the first full `limit` is covered by the deposit
premium; each reinstatement k covers the cumulative band [limit*k, limit*(k+1)] at
reinstatement_terms[k-1]% of layer_premium, charged pro rata as to amount.

Usage:
  python calculate_or_transform.py treaty.json     # prints the interpretation JSON
  python calculate_or_transform.py --selftest       # tie out the bundled fixture
Exit 0 if the computation ties (0 errors), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

MONEY_TOL = 1.0  # one currency unit


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _citation(src: dict, as_of: str) -> str:
    if not isinstance(src, dict) or not (src.get("system") and src.get("ref")):
        return ""
    return f"{src['system']}:{src['ref']}@{as_of}" if as_of else f"{src['system']}:{src['ref']}"


def _reinstatement_premium(prev_cum, new_cum, limit, reinstatements, terms, layer_premium):
    """Premium to restore limit for the band (prev_cum, new_cum], by reinstatement band."""
    if not reinstatements or not layer_premium or limit <= 0:
        return 0.0, 0.0
    reinstated_amount = 0.0
    premium = 0.0
    for k in range(1, int(reinstatements) + 1):
        band_lo, band_hi = limit * k, limit * (k + 1)
        lo = max(prev_cum, band_lo)
        hi = min(new_cum, band_hi)
        overlap = hi - lo
        if overlap <= 0:
            continue
        pct = 100.0
        if terms and k - 1 < len(terms):
            pct = _num((terms[k - 1] or {}).get("premium_pct"), 100.0)
        reinstated_amount += overlap
        premium += overlap / limit * (pct / 100.0) * layer_premium
    return round(reinstated_amount, 2), round(premium, 2)


def transform(doc: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    layer = doc.get("layer") or {}
    attachment = _num(layer.get("attachment"))
    limit = _num(layer.get("limit"))
    reinstatements = layer.get("reinstatements") or 0
    layer_premium = _num(layer.get("layer_premium"), 0.0)
    terms = layer.get("reinstatement_terms")

    if str(doc.get("treaty_type", "")).lower() == "excess_of_loss":
        if attachment is None or limit is None or limit <= 0:
            errors.append("cannot illustrate: excess_of_loss layer needs numeric attachment and positive limit")

    if limit and limit > 0:
        default_agg = limit * (1 + int(reinstatements))
    else:
        default_agg = None
    aggregate_limit = _num(layer.get("aggregate_limit"), default_agg)

    as_of = doc.get("inception_date", "")
    clauses_out = []
    for c in doc.get("clauses") or []:
        clauses_out.append({
            "clause_id": c.get("clause_id"),
            "clause_type": str(c.get("clause_type", "other")).lower(),
            "heading": c.get("heading"),
            "plain_summary": "",  # filled by the interpreting agent; schema slot only
            "citation": _citation(c.get("source") or {}, as_of),
        })

    occurrences = []
    total_ceded = 0.0
    total_reinst_premium = 0.0
    cumulative = 0.0
    can_illustrate = (attachment is not None and limit and limit > 0 and aggregate_limit is not None)
    for ls in doc.get("losses") or []:
        gross = _num(ls.get("gross_loss"))
        cite = _citation(ls.get("source") or {}, ls.get("date", ""))
        if gross is None or not can_illustrate:
            occurrences.append({
                "occurrence_id": ls.get("occurrence_id"),
                "date": ls.get("date"),
                "gross_loss": gross,
                "layer_loss": None,
                "ceded_recovery": None,
                "cumulative_ceded": round(cumulative, 2),
                "remaining_aggregate": round(aggregate_limit - cumulative, 2) if aggregate_limit is not None else None,
                "reinstated_amount": None,
                "reinstatement_premium": None,
                "note": "excluded from illustration (non-numeric loss or incomplete layer)",
                "citation": cite,
            })
            continue
        layer_loss = min(max(gross - attachment, 0.0), limit)
        remaining_before = aggregate_limit - cumulative
        ceded = max(0.0, min(layer_loss, remaining_before))
        prev_cum = cumulative
        cumulative = round(cumulative + ceded, 2)
        reinstated_amount, reinst_premium = _reinstatement_premium(
            prev_cum, cumulative, limit, reinstatements, terms, layer_premium)
        total_ceded = round(total_ceded + ceded, 2)
        total_reinst_premium = round(total_reinst_premium + reinst_premium, 2)
        occurrences.append({
            "occurrence_id": ls.get("occurrence_id"),
            "date": ls.get("date"),
            "gross_loss": round(gross, 2),
            "layer_loss": round(layer_loss, 2),
            "ceded_recovery": round(ceded, 2),
            "cumulative_ceded": cumulative,
            "remaining_aggregate": round(aggregate_limit - cumulative, 2),
            "reinstated_amount": reinstated_amount,
            "reinstatement_premium": reinst_premium,
            "citation": cite,
        })

    # Optional tie-out targets in the input let the selftest verify the arithmetic.
    exp_ceded = _num(doc.get("expected_total_ceded"))
    if exp_ceded is not None and abs(exp_ceded - total_ceded) > MONEY_TOL:
        errors.append(f"total_ceded {total_ceded} does not tie to expected_total_ceded {exp_ceded}")
    exp_rp = _num(doc.get("expected_total_reinstatement_premium"))
    if exp_rp is not None and abs(exp_rp - total_reinst_premium) > MONEY_TOL:
        errors.append(
            f"total_reinstatement_premium {total_reinst_premium} does not tie to "
            f"expected_total_reinstatement_premium {exp_rp}")

    interpretation = {
        "interpretation_id": f"rti-{doc.get('uw_year','')}-{doc.get('treaty_id','')}-0001",
        "treaty_id": doc.get("treaty_id"),
        "cedent": doc.get("cedent"),
        "treaty_type": str(doc.get("treaty_type", "")).lower(),
        "uw_year": doc.get("uw_year"),
        "currency": doc.get("currency"),
        "inception_date": doc.get("inception_date"),
        "expiry_date": doc.get("expiry_date"),
        "layer": {
            "attachment": attachment,
            "limit": limit,
            "reinstatements": int(reinstatements) if reinstatements else 0,
            "aggregate_limit": aggregate_limit,
            "layer_premium": layer_premium,
        },
        "clauses": clauses_out,
        "clauses_interpreted_count": len(clauses_out),
        "recovery_illustration": {
            "aggregate_limit": aggregate_limit,
            "occurrences": occurrences,
            "total_ceded": total_ceded,
            "total_reinstatement_premium": total_reinst_premium,
        } if occurrences else None,
        "data_gaps": [],
        "narrative": "",
        "disclaimer": "Informational interpretation only; not a coverage or recoverability "
                      "determination, reserving or accounting decision, or legal advice.",
    }
    return interpretation, errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "treaty_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())

    interpretation, errors = transform(doc)
    if "--selftest" not in argv:
        print(json.dumps(interpretation, indent=2))
    for e in errors:
        print("ERROR", e)
    print(f"computation check: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
