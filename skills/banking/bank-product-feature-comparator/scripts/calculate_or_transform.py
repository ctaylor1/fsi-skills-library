#!/usr/bin/env python3
"""Deterministic, factual product-feature comparison for bank-product-feature-comparator.

Reads a comparison request (see validate_input.py), gates every requested product on
approval status and freshness (effective/expiry/superseded), and — only if every requested
product is approved and current — emits a neutral side-by-side comparison across eligibility,
fees, and features with a citation index, a disclosures index, and the outstanding discovery
questions the banker still needs to confirm with the customer.

HARD BOUNDARY: this NEVER assesses needs or suitability and NEVER recommends, ranks, or
picks a "best" product. It presents cited facts side by side. If ANY requested product is
unapproved or stale, it FAILS CLOSED (status "fail_closed"): it emits no comparison and lists
the blocking reasons and the required content action. The mapping is documented in
references/domain-rules.md and re-checked by validate_output.py.

Usage:
  python calculate_or_transform.py request.json   # prints the comparison pack JSON
  python calculate_or_transform.py --selftest      # internal checks over bundled fixtures
Plain mode exits 0; --selftest exits 0 pass / 1 fail.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

FAMILIES = ("eligibility", "fees", "features")
DISCLAIMER = (
    "Factual comparison of approved products only. This is not advice, a suitability "
    "assessment, or a product recommendation. Confirm current product terms and the "
    "customer's eligibility before proceeding."
)


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _classify(p: dict, as_of: datetime) -> tuple[bool, str | None]:
    """Return (usable, block_reason). A product is usable only if approved and current."""
    status = str(p.get("approval_status", "")).strip().lower()
    if status != "approved":
        return False, f"unapproved_status:{p.get('approval_status')}"
    if p.get("superseded_by"):
        return False, f"superseded_by:{p['superseded_by']}"
    eff = p.get("effective_date")
    if eff and _parse_date(eff) > as_of:
        return False, "not_yet_effective"
    exp = p.get("expiry_date")
    if exp and _parse_date(exp) < as_of:
        return False, "expired_or_stale"
    return True, None


def _fmt_value(row: dict) -> str:
    val = row.get("value")
    unit = row.get("unit")
    return f"{val} {unit}".strip() if unit else str(val)


def compute(doc: dict) -> dict:
    as_of = _parse_date(doc["as_of"])
    by_id = {p.get("product_id"): p for p in doc.get("products", [])}
    requested = list(doc.get("requested_products", []))

    excluded: list[dict] = []
    compared: list[dict] = []
    for rid in requested:
        p = by_id.get(rid)
        if p is None:
            excluded.append({"product_id": rid, "name": None, "reason": "not_in_approved_catalog"})
            continue
        usable, reason = _classify(p, as_of)
        if usable:
            compared.append(p)
        else:
            excluded.append({"product_id": rid, "name": p.get("name"), "reason": reason})

    base = {
        "request_id": doc.get("request_id"),
        "as_of": doc.get("as_of"),
        "approved_catalog_version": doc.get("approved_catalog_version"),
        "compared": [p.get("product_id") for p in compared],
        "excluded": excluded,
        "disclaimer": DISCLAIMER,
    }

    # Fail closed on any stale/unapproved/unknown requested product.
    if excluded:
        reasons = "; ".join(f"{e['product_id']}={e['reason']}" for e in excluded)
        base.update({
            "status": "fail_closed",
            "comparison": [],
            "citation_index": [],
            "disclosures_index": [],
            "effective_dates": [],
            "missing_discovery_questions": [],
            "data_gaps": [],
            "block_reasons": [f"{e['product_id']}: {e['reason']}" for e in excluded],
            "required_action": (
                "Do not compare. Refresh the product content from the approved catalog "
                "(re-pull the current, effective, non-superseded version) or remove the "
                f"blocked product(s) from the request, then re-run. Blocked: {reasons}."
            ),
            "summary_note": (
                f"Comparison blocked: {len(excluded)} of {len(requested)} requested "
                "product(s) are unapproved, stale, or unknown."
            ),
        })
        return base

    # Build the neutral, cited side-by-side comparison.
    comparison: list[dict] = []
    citation_index: list[dict] = []
    data_gaps: list[str] = []
    for fam in FAMILIES:
        names: list[str] = []
        for p in compared:
            for row in p.get("attributes", {}).get(fam, []) or []:
                nm = row.get("name")
                if nm and nm not in names:
                    names.append(nm)
        for nm in names:
            cells = []
            for p in compared:
                match = next((r for r in p.get("attributes", {}).get(fam, []) or []
                              if r.get("name") == nm), None)
                if match is not None:
                    citation = str(match.get("citation", "")).strip()
                    cells.append({
                        "product_id": p["product_id"],
                        "value": _fmt_value(match),
                        "citation": citation,
                        "present": True,
                    })
                    citation_index.append({
                        "product_id": p["product_id"],
                        "family": fam,
                        "attribute": nm,
                        "citation": citation,
                        "version": p.get("version"),
                        "effective_date": p.get("effective_date"),
                    })
                else:
                    cells.append({
                        "product_id": p["product_id"],
                        "value": None,
                        "citation": None,
                        "present": False,
                        "note": "not specified on this product's approved sheet",
                    })
                    data_gaps.append(
                        f"{p['product_id']} does not specify {fam}.{nm}; confirm the current "
                        "term from the product sheet before comparing on this attribute."
                    )
            comparison.append({"family": fam, "attribute": nm, "cells": cells})

    disclosures_index = []
    effective_dates = []
    for p in compared:
        effective_dates.append({
            "product_id": p["product_id"],
            "version": p.get("version"),
            "effective_date": p.get("effective_date"),
            "expiry_date": p.get("expiry_date"),
        })
        for d in p.get("disclosures", []) or []:
            disclosures_index.append({
                "product_id": p["product_id"],
                "disclosure_id": d.get("id"),
                "title": d.get("title"),
                "effective_date": d.get("effective_date"),
                "citation": d.get("citation"),
            })

    # Outstanding discovery questions: union of each product's factual fact-gathering prompts.
    seen = set()
    missing_discovery_questions: list[str] = []
    for p in compared:
        for q in p.get("discovery_questions", []) or []:
            if q not in seen:
                seen.add(q)
                missing_discovery_questions.append(q)

    base.update({
        "status": "ok",
        "comparison": comparison,
        "citation_index": citation_index,
        "disclosures_index": disclosures_index,
        "effective_dates": effective_dates,
        "missing_discovery_questions": missing_discovery_questions,
        "data_gaps": data_gaps,
        "summary_note": (
            f"Side-by-side factual comparison of {len(compared)} approved product(s) across "
            f"{len({r['family'] for r in comparison})} attribute families, as of "
            f"{doc.get('as_of')}. Differences are shown with citations; no product is ranked "
            "or recommended."
        ),
    })
    return base


def _selftest() -> int:
    files = Path(__file__).resolve().parents[1] / "evals" / "files"
    errors: list[str] = []

    ok = compute(json.loads((files / "request_example.json").read_text(encoding="utf-8")))
    if ok.get("status") != "ok":
        errors.append(f"request_example expected status ok, got {ok.get('status')!r}")
    if len(ok.get("compared", [])) < 2:
        errors.append("request_example expected >= 2 compared products")
    if not ok.get("comparison"):
        errors.append("request_example expected a non-empty comparison")
    if not ok.get("citation_index"):
        errors.append("request_example expected a citation_index")
    if not ok.get("missing_discovery_questions"):
        errors.append("request_example expected outstanding discovery questions")
    for row in ok.get("comparison", []):
        for cell in row["cells"]:
            if cell.get("present") and not cell.get("citation"):
                errors.append(f"present cell {row['attribute']} for {cell['product_id']} lacks a citation")
    if any(k in ok for k in ("recommended_product", "best_product", "winner", "ranking")):
        errors.append("comparison must not contain a recommendation/ranking field")

    stale = compute(json.loads((files / "request_stale.json").read_text(encoding="utf-8")))
    if stale.get("status") != "fail_closed":
        errors.append(f"request_stale expected status fail_closed, got {stale.get('status')!r}")
    if not stale.get("block_reasons"):
        errors.append("request_stale expected block_reasons")
    if stale.get("comparison"):
        errors.append("fail_closed pack must not emit a comparison")

    for e in errors:
        print("ERROR", e)
    print(f"comparator self-test: {len(errors)} error(s)")
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
