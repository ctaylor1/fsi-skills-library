#!/usr/bin/env python3
"""Deterministic output validation for bank-product-feature-comparator.

Screens the comparison pack (the calculate_or_transform core + any narrative) before it is
presented or delivered. This is the R2 prohibited-decision / fail-closed gate. Checks:
  1. No recommendation / suitability / ranking language (free text AND structural fields).
  2. No stale/unapproved product leaked into an "ok" comparison.
  3. Every present comparison cell carries a citation; every compared product is in the
     citation index; a comparison needs >= 2 approved products and >= 1 discovery question.
  4. A "fail_closed" pack emits block_reasons and NO comparison.
  5. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_KEY = "Factual comparison of approved products only"
# Structural fields that would encode a recommendation/ranking — never allowed.
PROHIBITED_KEYS = ("recommended_product", "best_product", "winner", "ranking",
                   "suitability", "top_pick", "preferred_product", "recommendation")
# Recommendation / suitability / needs-assessment phrasing an R2 comparator must not emit.
ADVICE_PATTERNS = [
    r"\bwe recommend\b", r"\bi recommend\b", r"\bour recommendation\b", r"\brecommended (product|option|choice)\b",
    r"\b(you|they|the customer) should (choose|open|pick|select|go with|get)\b",
    r"\bbest (option|choice|product|fit|account) for\b", r"\bbest (option|choice|product|fit|account)\b",
    r"\bbetter (option|choice|product|fit|account) for\b", r"\bmost suitable\b", r"\bmore suitable\b",
    r"\b(is|are|would be) suitable for\b", r"\bright (product|account|fit|choice) for\b",
    r"\bwould suit\b", r"\bideal for (you|them|the customer|this customer)\b",
    r"\bthe winner\b", r"\btop pick\b", r"\bpreferred product\b", r"\bmy suggestion is\b",
    r"\bwe suggest (choosing|opening|selecting|getting)\b", r"\bshould go with\b",
    r"\bbased on (your|the customer's) needs\b", r"\bmeets your needs best\b", r"\bfits (you|the customer) best\b",
]


def _texts(pack: dict) -> list[str]:
    """Free-text surfaces to scan — deliberately EXCLUDES the disclaimer field, which
    legitimately contains the words 'recommendation', 'suitability', and 'advice'."""
    out = [str(pack.get("narrative", "")), str(pack.get("summary_note", "")), str(pack.get("notes", ""))]
    out += [str(q) for q in pack.get("missing_discovery_questions", []) or []]
    out += [str(g) for g in pack.get("data_gaps", []) or []]
    out.append(str(pack.get("required_action", "")))
    for row in pack.get("comparison", []) or []:
        for cell in row.get("cells", []) or []:
            out.append(str(cell.get("note", "")))
    return out


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    status = pack.get("status")
    if status not in ("ok", "fail_closed"):
        errors.append(f"status must be 'ok' or 'fail_closed', got {status!r}")

    # Structural recommendation/ranking fields (any layer).
    for key in PROHIBITED_KEYS:
        if pack.get(key):
            errors.append(f"prohibited field present: {key!r} (R2 compares facts; it does not recommend/rank)")
    for row in pack.get("comparison", []) or []:
        for cell in row.get("cells", []) or []:
            for key in ("winner", "preferred", "recommended", "best"):
                if cell.get(key):
                    errors.append(f"prohibited cell flag {key!r} on attribute {row.get('attribute')!r}")

    # Free-text recommendation/suitability language.
    blob = " ".join(_texts(pack))
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            errors.append(f"recommendation/suitability language detected: {m.group(0)!r} "
                          "(R2 compares facts; it never assesses needs, suitability, or recommends)")

    if status == "ok":
        compared = pack.get("compared") or []
        if len(compared) < 2:
            errors.append(f"comparison requires >= 2 approved products (got {len(compared)})")
        if pack.get("excluded"):
            leaked = ", ".join(str(e.get("product_id")) for e in pack["excluded"])
            errors.append(f"status 'ok' but excluded/stale products present: {leaked} "
                          "(fail closed on stale/unapproved content)")
        comparison = pack.get("comparison") or []
        if not comparison:
            errors.append("status 'ok' but comparison is empty")
        cited_products = {c.get("product_id") for c in pack.get("citation_index") or []}
        for row in comparison:
            for cell in row.get("cells", []) or []:
                if cell.get("present") and not str(cell.get("citation", "")).strip():
                    errors.append(f"comparison cell for {cell.get('product_id')} attribute "
                                  f"{row.get('attribute')!r} missing citation")
        for pid in compared:
            if pid not in cited_products:
                errors.append(f"compared product {pid!r} absent from citation_index")
        if not (pack.get("missing_discovery_questions")):
            errors.append("no outstanding discovery questions surfaced (contract requires them)")

    elif status == "fail_closed":
        if not pack.get("block_reasons"):
            errors.append("fail_closed pack must list block_reasons")
        if pack.get("comparison"):
            errors.append("fail_closed pack must not emit a comparison")

    disclaimer_text = str(pack.get("disclaimer", "")) + " " + str(pack.get("narrative", ""))
    if DISCLAIMER_KEY.lower() not in disclaimer_text.lower():
        errors.append("missing standing disclaimer")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
