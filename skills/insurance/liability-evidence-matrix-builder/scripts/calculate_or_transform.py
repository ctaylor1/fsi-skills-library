#!/usr/bin/env python3
"""Map supplied fact-specific source passages into supporting/contrary evidence. Legacy ID links are unverified hints. No fault, liability or credibility finding.

Usage: python calculate_or_transform.py input.json | --selftest
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from insurance_contract import build_artifact

DISCLAIMER = (
    "Evidence mapping only; not a liability, fault, or negligence determination and not "
    "a claim decision. No responsibility has been apportioned."
)


def _calculate(doc: dict) -> dict:
    claim, facts = doc["claim"], doc["facts"]
    ids = [f.get("fact_id") for f in facts]
    evidence = doc.get("evidence", [])
    eids = [e.get("evidence_id") for e in evidence]
    supports, contradicts, gaps = defaultdict(list), defaultdict(list), []
    if len(ids) != len(set(ids)) or len(eids) != len(set(eids)):
        gaps.append({"type": "duplicate_identifier", "citation": "input:identifiers"})
    for e in evidence:
        # Legacy lists are mapping hints, never proof of a source-backed relationship.
        for role in ("supports", "contradicts"):
            for fid in e.get(role, []) or []:
                gaps.append(
                    {
                        "type": "unverified_legacy_relation",
                        "fact_id": fid,
                        "evidence_id": e.get("evidence_id"),
                        "citation": e.get("source_ref") or "input:evidence",
                    }
                )
        for rel in e.get("relations", []) or []:
            fid, role = rel.get("fact_id"), rel.get("role")
            cell = {
                "fact_id": fid,
                "role": role,
                "evidence_id": e.get("evidence_id"),
                "citation": e.get("source_ref"),
                "source_version": e.get("version"),
                "source_quote": rel.get("source_quote"),
                "relation_basis": rel.get("relation_basis"),
                "assurance": "supplied_not_authenticated",
            }
            valid = (
                fid in ids
                and role in {"supports", "contradicts"}
                and all(
                    isinstance(cell.get(k), str) and cell[k].strip()
                    for k in ("citation", "source_version", "source_quote", "relation_basis")
                )
                and ids.count(fid) == 1
                and eids.count(e.get("evidence_id")) == 1
            )
            if not valid:
                gaps.append(
                    {
                        "type": "unresolved_evidence_relation",
                        "fact_id": fid,
                        "evidence_id": e.get("evidence_id"),
                        "citation": e.get("source_ref") or "input:evidence",
                    }
                )
            else:
                (supports if role == "supports" else contradicts)[fid].append(cell)
    matrix, counts = [], defaultdict(int)
    for f in facts:
        fid = f.get("fact_id")
        sup, con = supports[fid], contradicts[fid]
        status = "contested" if sup and con else "supported" if sup else "contradicted" if con else "unsupported"
        if status != "supported":
            gaps.append(
                {"type": status + "_fact", "fact_id": fid, "citation": f.get("source_ref") or f"input:fact={fid}"}
            )
        counts[status] += 1
        matrix.append(
            {
                "fact_id": fid,
                "statement": f.get("statement"),
                "party": f.get("party"),
                "supporting": sup,
                "contradicting": con,
                "status": status,
            }
        )
    return {
        "matrix_id": f"lemb-{claim.get('claim_id', 'UNKNOWN')}",
        "claim_id": claim.get("claim_id"),
        "claim_type": claim.get("claim_type"),
        "fact_count": len(facts),
        "status_counts": dict(counts),
        "matrix": matrix,
        "gaps": gaps,
        "suggested_disposition": "gaps-for-review" if gaps else "matrix-complete",
        "disclaimer": DISCLAIMER,
    }


def compute(doc: dict) -> dict:
    from validate_input import validate

    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    output = _calculate(doc)
    issues = [str(x) for x in output.get("gaps", [])]
    output["artifact"] = build_artifact(
        doc,
        output,
        producer="liability-evidence-matrix-builder",
        artifact_type="liability-evidence-matrix-builder-review",
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
