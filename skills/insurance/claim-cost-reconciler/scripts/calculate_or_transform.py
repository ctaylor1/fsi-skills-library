#!/usr/bin/env python3
"""Compare source-versioned cost lines only within matching currency, service date, provider, unit and quantity. Superseded and unknown identities remain explicit. No valuation.

Usage: python calculate_or_transform.py input.json | --selftest
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from insurance_contract import amount, build_artifact, iso_date

DISCLAIMER = (
    "Line-item comparison evidence only; not a damages, reserve, or settlement "
    "determination and not a coverage or liability decision. No amount has been set "
    "or approved."
)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(s).lower())).strip()


def _num(v):
    try:
        return amount(v)
    except (TypeError, ValueError):
        return None


def _calculate(doc: dict) -> dict:
    import math

    cfg = doc.get("config") or {}
    require = cfg.get("categories_requiring_support")
    documents = doc.get("documents") or []
    docs = {d.get("doc_id"): d for d in documents}
    findings, gaps, comparable = [], [], []
    duplicates = len(docs) != len(documents)
    superseded = {d.get("supersedes") for d in documents if d.get("supersedes")}
    item_ids = [i.get("item_id") for i in doc.get("line_items", [])]
    for it in doc.get("line_items", []):
        d = docs.get(it.get("doc_id"), {})
        citation = f"claims:{d.get('source_ref', '')};item={it.get('item_id')}"
        missing = []
        for field in ("currency", "service_date", "provider_id", "unit", "quantity", "description"):
            if it.get(field) in (None, ""):
                missing.append(field)
        try:
            iso_date(it.get("service_date"))
            iso_date(d.get("document_date"))
            numeric = float(it["amount"])
            quantity = float(it["quantity"])
            if (
                isinstance(it["quantity"], bool)
                or isinstance(it["amount"], bool)
                or not math.isfinite(numeric)
                or numeric < 0
                or not math.isfinite(quantity)
                or quantity <= 0
            ):
                raise ValueError("amount or quantity")
        except (TypeError, ValueError, KeyError):
            missing.append("valid amount/quantity/service_date")
        if not d.get("source_ref") or not d.get("version") or not d.get("document_date"):
            missing.append("document source/version/date")
        if not isinstance(it.get("currency"), str) or len(it["currency"]) != 3 or not it["currency"].isupper():
            missing.append("three-letter uppercase currency")
        if duplicates or item_ids.count(it.get("item_id")) != 1:
            missing.append("unique document/item identity")
        if it.get("doc_id") in superseded:
            missing.append("superseded document; retained for history only")
        if missing:
            gaps.append({"item_id": it.get("item_id"), "reason": "; ".join(missing), "citation": citation})
        else:
            comparable.append(it)
        needs_support = require is None or it.get("category") in require
        support = docs.get(it.get("supported_by"), {})
        if needs_support and (not support.get("source_ref") or it.get("supported_by") in superseded):
            findings.append(
                {
                    "type": "unsupported",
                    "category": it.get("category"),
                    "description": it.get("description"),
                    "documents": [it.get("doc_id")],
                    "citation": citation,
                }
            )

    def cite(items):
        return ",".join(
            f"claims:{docs[i['doc_id']]['source_ref']};version={docs[i['doc_id']]['version']};item={i['item_id']}"
            for i in items
        )

    groups = defaultdict(list)
    for it in comparable:
        key = (
            it.get("category"),
            _norm(it["description"]),
            it["currency"],
            it["service_date"],
            it["provider_id"],
            it["unit"],
            float(it["quantity"]),
        )
        groups[key].append(it)
    for key, items in groups.items():
        amounts = defaultdict(list)
        for it in items:
            amounts[_num(it["amount"])].append(it)
        for amt, group in amounts.items():
            if len({i["doc_id"] for i in group}) > 1:
                findings.append(
                    {
                        "type": "duplicate",
                        "category": key[0],
                        "description": items[0]["description"],
                        "amount": float(amt),
                        "currency": key[2],
                        "documents": sorted({i["doc_id"] for i in group}),
                        "citation": cite(group),
                    }
                )
        if len(amounts) > 1 and len({i["doc_id"] for i in items}) > 1:
            findings.append(
                {
                    "type": "difference",
                    "category": key[0],
                    "description": items[0]["description"],
                    "amounts": [float(a) for a in sorted(amounts)],
                    "currency": key[2],
                    "documents": sorted({i["doc_id"] for i in items}),
                    "citation": cite(items),
                }
            )
    counts = defaultdict(int)
    for f in findings:
        counts[f["type"]] += 1
    return {
        "comparison_id": f"cdec-{doc['claim'].get('claim_id', 'UNKNOWN')}",
        "claim_id": doc["claim"].get("claim_id"),
        "claim_type": doc["claim"].get("claim_type"),
        "document_count": len(documents),
        "config_version": cfg.get("config_version"),
        "comparison_basis": "Exact supplied amounts; no currency conversion, rounding, valuation or price reasonableness opinion",
        "finding_counts": dict(counts),
        "findings": findings,
        "not_evaluable": gaps,
        "evaluated_item_count": len(comparable),
        "input_item_count": len(doc.get("line_items", [])),
        "suggested_disposition": "not-evaluable" if gaps else "items-for-review" if findings else "clean",
        "disclaimer": DISCLAIMER,
    }


def compute(doc: dict) -> dict:
    from validate_input import validate

    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    output = _calculate(doc)
    issues = [str(x) for x in output.get("not_evaluable", [])]
    output["artifact"] = build_artifact(
        doc,
        output,
        producer="claim-cost-reconciler",
        artifact_type="claim-damage-evaluation-comparator-review",
        completeness="partial" if issues else "complete",
        evaluability="partial" if issues else "evaluable",
        issues=issues,
    )
    return output


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claim_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
