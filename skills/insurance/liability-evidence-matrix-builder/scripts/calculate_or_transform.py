#!/usr/bin/env python3
"""Deterministic evidence-matrix build for liability-evidence-matrix-builder.

For each alleged fact, collects supporting and contradicting evidence, assigns a coverage status
(supported / contested / unsupported), and flags unsupported facts and dangling evidence
references. Evidence mapping only; never determines liability, fault, or apportionment.

Usage: python calculate_or_transform.py claim.json | --selftest
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path

DISCLAIMER = ("Evidence mapping only; not a liability, fault, or negligence determination and not "
              "a claim decision. No responsibility has been apportioned.")


def compute(doc: dict) -> dict:
    claim = doc["claim"]
    facts = doc["facts"]
    evidence = doc.get("evidence", [])
    fact_ids = {f.get("fact_id") for f in facts}

    supports = defaultdict(list)
    contradicts = defaultdict(list)
    dangling = []
    for e in evidence:
        eid = e.get("evidence_id")
        ref = e.get("source_ref", eid)
        for fid in e.get("supports", []) or []:
            (supports[fid] if fid in fact_ids else dangling).append(
                {"evidence_id": eid, "fact_id": fid, "role": "supports", "citation": f"claim:{ref}"})
        for fid in e.get("contradicts", []) or []:
            (contradicts[fid] if fid in fact_ids else dangling).append(
                {"evidence_id": eid, "fact_id": fid, "role": "contradicts", "citation": f"claim:{ref}"})

    matrix, gaps = [], []
    status_counts = defaultdict(int)
    for f in facts:
        fid = f.get("fact_id")
        sup = supports.get(fid, [])
        con = contradicts.get(fid, [])
        if not sup:
            status = "unsupported"
            gaps.append({"type": "unsupported_fact", "fact_id": fid,
                         "citation": f"claim:claim={claim.get('claim_id')};fact={fid}"})
        elif con:
            status = "contested"
        else:
            status = "supported"
        status_counts[status] += 1
        matrix.append({"fact_id": fid, "statement": f.get("statement"), "party": f.get("party"),
                       "supporting": sup, "contradicting": con, "status": status})

    for d in dangling:
        gaps.append({"type": "dangling_evidence", "evidence_id": d["evidence_id"],
                     "fact_id": d["fact_id"], "citation": d["citation"]})

    disposition = "matrix-complete" if not gaps else "gaps-for-review"
    return {
        "matrix_id": f"lemb-{claim.get('claim_id', 'UNKNOWN')}-0001",
        "claim_id": claim.get("claim_id"), "claim_type": claim.get("claim_type"),
        "fact_count": len(facts),
        "status_counts": dict(status_counts),
        "matrix": matrix,
        "gaps": gaps,
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
