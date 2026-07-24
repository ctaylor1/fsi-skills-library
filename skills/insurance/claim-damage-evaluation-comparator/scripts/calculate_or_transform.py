#!/usr/bin/env python3
"""Deterministic line-item comparison for claim-damage-evaluation-comparator.

Normalizes descriptions, groups by (category, normalized_description), and flags duplicates
(same amount across ≥2 documents), differences (≥2 distinct amounts), and unsupported items
(no linked supporting document). Evidence only; never values, settles, or approves.

Usage: python calculate_or_transform.py claim.json | --selftest
"""
from __future__ import annotations
import json, re, sys
from collections import defaultdict
from pathlib import Path

DISCLAIMER = ("Line-item comparison evidence only; not a damages, reserve, or settlement "
              "determination and not a coverage or liability decision. No amount has been set "
              "or approved.")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(s).lower())).strip()


def _num(v):
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


def compute(doc: dict) -> dict:
    cfg = doc.get("config") or {}
    require = cfg.get("categories_requiring_support")
    items = doc["line_items"]
    findings = []

    def cite(its):
        return "claims:" + ",".join(f"doc={i.get('doc_id')};item={i.get('item_id')}" for i in its)

    groups = defaultdict(list)
    for it in items:
        groups[(it.get("category"), _norm(it.get("description")))].append(it)

    for (cat, ndesc), its in sorted(groups.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        if len(its) < 2:
            continue
        amt_map = defaultdict(list)
        for it in its:
            amt_map[_num(it.get("amount"))].append(it)
        # duplicate: same amount on >= 2 distinct documents
        for amt, group in amt_map.items():
            if amt is None:
                continue
            docs = {i.get("doc_id") for i in group}
            if len(docs) >= 2:
                findings.append({"type": "duplicate", "category": cat,
                                 "description": its[0].get("description"), "amount": amt,
                                 "documents": sorted(docs), "citation": cite(group)})
        # difference: >= 2 distinct amounts in the group
        distinct = sorted(a for a in amt_map if a is not None)
        if len(distinct) >= 2:
            findings.append({"type": "difference", "category": cat,
                             "description": its[0].get("description"),
                             "amounts": distinct, "documents": sorted({i.get("doc_id") for i in its}),
                             "citation": cite(its)})

    # unsupported items
    for it in items:
        cat = it.get("category")
        if require is not None and cat not in require:
            continue
        if not (it.get("supported_by") or "").strip():
            findings.append({"type": "unsupported", "category": cat,
                             "description": it.get("description"), "amount": _num(it.get("amount")),
                             "documents": [it.get("doc_id")], "citation": cite([it])})

    counts = defaultdict(int)
    for f in findings:
        counts[f["type"]] += 1
    disposition = "clean" if not findings else "items-for-review"
    return {
        "comparison_id": f"cdec-{doc['claim'].get('claim_id', 'UNKNOWN')}-0001",
        "claim_id": doc["claim"].get("claim_id"),
        "claim_type": doc["claim"].get("claim_type"),
        "document_count": len(doc.get("documents", [])),
        "finding_counts": dict(counts),
        "findings": findings,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


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
