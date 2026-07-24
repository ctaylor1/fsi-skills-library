#!/usr/bin/env python3
"""Deterministic readiness checks for payment-integration-readiness-pack.

Matches each required checklist item to its attestation, flags not-attested/missing items,
N/A without justification, and unattested gate items, and computes a readiness score by
category. Evidence + score only; never approves go-live.

Usage: python calculate_or_transform.py integration.json | --selftest
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path

DISCLAIMER = ("Readiness evidence only; not a go-live approval or a launch clearance. No "
              "integration has been approved for production.")


def compute(doc: dict) -> dict:
    integ = doc["integration"]
    ck = doc["checklist"]
    gate = set(ck.get("gate_items") or [])
    att_by_id = {a.get("item_id"): a for a in doc.get("attestations", [])}
    gaps = []
    cat_total = defaultdict(int)
    cat_ok = defaultdict(int)

    def gap(item, cat, expected, found, ref):
        gaps.append({"item_id": item, "category": cat, "expected": expected, "found": found,
                     "citation": f"attest:{ref}"})

    required = ck.get("required_items") or []
    for it in required:
        iid = it.get("item_id")
        cat = it.get("category", "uncategorized")
        cat_total[cat] += 1
        a = att_by_id.get(iid)
        ref = f"integration={integ.get('integration_id')};item={iid}"
        status = (a or {}).get("status")
        evidence = ((a or {}).get("evidence_ref") or "").strip()
        if a is None or status in (None, "not_attested"):
            gap(iid, cat, "attested + evidence", status or "missing", ref)
        elif status == "attested" and not evidence:
            gap(iid, cat, "attested + evidence", "attested without evidence", ref)
        elif status == "na":
            if iid in gate:
                gap(iid, cat, "attested (gate item)", "na (not allowed for gate item)", ref)
            elif not ((a.get("justification") or "").strip()):
                gap(iid, cat, "na + justification", "na without justification", ref)
            else:
                cat_ok[cat] += 1  # justified N/A counts as satisfied
        else:  # attested with evidence
            cat_ok[cat] += 1

    total = len(required)
    ok = sum(cat_ok.values())
    score = round(ok / total, 4) if total else 0.0
    disposition = "ready-for-review" if not gaps else "gaps-for-review"
    return {
        "packet_id": f"pirp-{integ.get('integration_id', 'UNKNOWN')}-0001",
        "integration_id": integ.get("integration_id"),
        "gateway": integ.get("gateway"),
        "checklist_version": ck.get("config_version"),
        "readiness_score": score,
        "items_required": total, "items_satisfied": ok,
        "by_category": {c: {"required": cat_total[c], "satisfied": cat_ok[c]} for c in sorted(cat_total)},
        "gaps": gaps,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "integration_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
