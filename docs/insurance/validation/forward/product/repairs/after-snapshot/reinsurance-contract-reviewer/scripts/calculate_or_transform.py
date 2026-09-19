#!/usr/bin/env python3
"""Deterministic computation for reinsurance-contract-reviewer.

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
Supported reinstatement premium: restore erosion pro rata as to amount, up to the
explicit count of reinstatements, beginning with the first ceded loss. No time adjustment.
Other triggers remain not evaluable.

Usage:
  python calculate_or_transform.py treaty.json     # prints the interpretation JSON
  python calculate_or_transform.py --selftest       # tie out the bundled fixture
Exit 0 if the computation ties (0 errors), 1 otherwise.
"""
from __future__ import annotations
import json, sys, math
from datetime import date
from pathlib import Path

MONEY_TOL = 1.0  # one currency unit


def _num(v, default=None):
    try:
        return float(v) if not isinstance(v, bool) and math.isfinite(float(v)) else default
    except (TypeError, ValueError):
        return default


def _citation(src: dict, as_of: str) -> str:
    if not isinstance(src, dict) or not (src.get("system") and src.get("ref")):
        return ""
    return f"{src['system']}:{src['ref']}@{as_of}" if as_of else f"{src['system']}:{src['ref']}"


def _reinstatement_premium(prev_cum, new_cum, limit, reinstatements, terms, layer_premium):
    """Premium to restore limit for the band (prev_cum, new_cum], by reinstatement band."""
    # Restoration follows contractual erosion even when its premium charge is zero.
    if not reinstatements or limit <= 0:
        return 0.0, 0.0
    reinstated_amount = 0.0
    premium = 0.0
    for k in range(int(reinstatements)):
        band_lo, band_hi = limit * k, limit * (k + 1)
        lo = max(prev_cum, band_lo)
        hi = min(new_cum, band_hi)
        overlap = hi - lo
        if overlap <= 0:
            continue
        pct = 100.0
        if terms and k < len(terms):
            pct = _num((terms[k] or {}).get("premium_pct"), 100.0)
        reinstated_amount += overlap
        premium += overlap / limit * (pct / 100.0) * layer_premium
    return round(reinstated_amount, 2), round(premium, 2)


def transform(doc: dict) -> tuple[dict, list[str]]:
    from validate_input import validate
    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    layer = doc.get("layer") or {}
    attachment = _num(layer.get("attachment"))
    limit = _num(layer.get("limit"))
    reinstatements = layer.get("reinstatements") or 0
    layer_premium = _num(layer.get("layer_premium"), 0.0)
    terms = layer.get("reinstatement_terms")

    if str(doc.get("treaty_type", "")).lower() == "excess_of_loss":
        if attachment is None or limit is None or limit <= 0:
            errors.append("cannot illustrate: excess_of_loss layer needs numeric attachment and positive limit")

    aggregate_limit = _num(layer.get("aggregate_limit"))

    as_of = doc.get("inception_date", "")
    clauses_out = []
    for c in doc.get("clauses") or []:
        clauses_out.append({
            "clause_id": c.get("clause_id"),
            "clause_type": str(c.get("clause_type", "other")).lower(),
            "heading": c.get("heading"),
            "source_text": c.get("text"),
            "plain_summary": "",  # filled by the interpreting agent; schema slot only
            "citation": _citation(c.get("source") or {}, as_of),
        })

    occurrences = []
    total_ceded = 0.0
    total_reinst_premium = 0.0
    cumulative = 0.0
    losses = doc.get("losses") or []
    gaps = []
    if doc.get("treaty_type") != "excess_of_loss":
        gaps.append("numeric illustration supports excess_of_loss only; other contract types are explanation-only")
    if attachment is None or limit is None or limit <= 0 or aggregate_limit is None or aggregate_limit < 0:
        gaps.append("explicit attachment, positive limit and aggregate limit required")
    if doc.get("illustration_basis") != "losses_occurring" or not doc.get("illustration_basis_source"):
        gaps.append("reviewed losses-occurring basis and source required; other attachment bases unsupported")
    if reinstatements and (layer.get("reinstatement_basis") != "pro_rata_amount_on_erosion" or not terms or len(terms) != reinstatements or layer.get("layer_premium") is None):
        gaps.append("reinstatement illustration requires explicit pro-rata-on-erosion terms, count and premium")
    previous_date = None
    for ls in losses:
        if _num(ls.get("gross_loss")) is None:
            gaps.append("every loss needs a finite amount before aggregate allocation")
        if not isinstance(ls.get("eligible_for_illustration"), bool) or not ls.get("eligibility_source_ref"):
            gaps.append("reviewed eligibility and source required for every loss; no coverage inference")
        try:
            d = date.fromisoformat(ls["date"])
            if not date.fromisoformat(doc["inception_date"]) <= d <= date.fromisoformat(doc["expiry_date"]):
                gaps.append("loss date is outside the supplied treaty period")
            if previous_date and d < previous_date:
                gaps.append("loss chronology must be explicit and ascending")
            previous_date = d
        except (KeyError, ValueError, TypeError):
            gaps.append("valid treaty and loss dates required")
    can_illustrate = not gaps
    for ls in losses if can_illustrate else []:
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
        layer_loss = min(max(gross - attachment, 0.0), limit) if ls["eligible_for_illustration"] else 0.0
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
            "eligible_for_illustration": ls["eligible_for_illustration"],
            "eligibility_source_ref": ls["eligibility_source_ref"],
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
    if can_illustrate and exp_ceded is not None and abs(exp_ceded - total_ceded) > MONEY_TOL:
        errors.append(f"total_ceded {total_ceded} does not tie to expected_total_ceded {exp_ceded}")
    exp_rp = _num(doc.get("expected_total_reinstatement_premium"))
    if can_illustrate and exp_rp is not None and abs(exp_rp - total_reinst_premium) > MONEY_TOL:
        errors.append(
            f"total_reinstatement_premium {total_reinst_premium} does not tie to "
            f"expected_total_reinstatement_premium {exp_rp}")

    interpretation = {
        "calculation_inputs": doc,
        "illustration_status": "evaluable" if can_illustrate and losses else "not_evaluable",
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
            "reinstatement_basis": layer.get("reinstatement_basis"),
            "reinstatement_terms": terms,
        },
        "clauses": clauses_out,
        "clauses_interpreted_count": len(clauses_out),
        "recovery_illustration": {
            "aggregate_limit": aggregate_limit,
            "occurrences": occurrences,
            "total_ceded": total_ceded,
            "total_reinstatement_premium": total_reinst_premium,
        } if occurrences else None,
        "data_gaps": sorted(set(gaps)),
        "narrative": "",
        "disclaimer": "Informational interpretation only; not a coverage or recoverability "
                      "determination, reserving or accounting decision, or legal advice.",
    }
    return interpretation, errors



# Bind native result and source snapshot to the portable insurance evidence contract.
_native_transform = transform
def transform(doc):
    from insurance_contract import build_artifact, stable_hash
    result = _native_transform(doc)
    output = result[0] if isinstance(result, tuple) else result
    issues = []
    for field in ("not_evaluable", "data_gaps"):
        for item in output.get(field, []):
            issues.append(str(item))
    if output.get("cost_comparison_status") == "not_comparable":
        issues.append("quotes are not directly comparable; aggregate ranking suppressed")
    for item in output.get("segments", []):
        if not item.get("packageable"):
            issues.append(f"segment {item.get('segment_id')}: {item.get('status')}")
    for item in output.get("profiles", []):
        if item.get("recommended_disposition") == "needs-data":
            issues.append(f"submission {item.get('submission_id')} requires data")
    for item in output.get("reconciliation", []):
        if item.get("status") in {"mismatch", "unparseable"}:
            issues.append(f"unresolved source conflict: {item.get('field')}")
    for key in ("comparison_id", "analysis_id", "review_id", "packet_id", "worksheet_id", "triage_id", "interpretation_id"):
        if key in output:
            output[key] = "contract_interpretation-" + stable_hash(doc)[:24]
    output["artifact"] = build_artifact(doc, output, producer="reinsurance-contract-reviewer", artifact_type="contract_interpretation",
        completeness="partial" if issues else "complete", evaluability="partial" if issues else "evaluable", issues=issues)
    return result


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
