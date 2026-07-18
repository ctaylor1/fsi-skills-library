#!/usr/bin/env python3
"""Deterministic due-diligence packaging engine for due-diligence-packager.

Transforms a validated data-room manifest into a structured, source-mapped diligence pack:
builds the source index, binds every extraction/issue to a citation, EXCLUDES any item whose
source_doc is not in the index (recorded as an unsupported claim -> needs-source), computes an
issue summary and workstream completeness, and assembles validated model-handoff bundles
(targets checked against known modeling skills). It never sends, submits, files, values, or
recommends; the pack is an internal draft with a `pack_id`.

Usage:
  python calculate_or_transform.py dataroom.json   # prints the pack JSON to stdout
  python calculate_or_transform.py --selftest      # runs bundled self-check, prints N error(s)
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "cover", "executive_summary", "source_index", "extracted_data", "issue_log",
    "open_questions", "completeness", "model_handoffs", "approvals", "standing_note",
]
REQUIRED_WORKSTREAMS = ["financial", "legal", "tax", "commercial", "operational", "hr"]
KNOWN_MODEL_TARGETS = {
    "three-statement-model-builder", "dcf-modeler", "lbo-model-builder",
    "merger-model-builder", "comps-analysis-builder", "scenario-sensitivity-generator",
}
REQUIRED_APPROVAL_ROLES = ["diligence_lead", "quality_reviewer"]
CONFIDENCE = {"high", "medium", "low"}
STANDING_NOTE = ("Draft diligence pack for internal review only; not approved for external "
                 "delivery; no valuation or investment recommendation is made.")


def _index(doc):
    return {s.get("doc_id"): s for s in (doc.get("sources") or []) if s.get("doc_id")}


def _citation(item, src):
    page = item.get("page")
    ver = (src or {}).get("version", "?")
    base = item.get("source_doc")
    return f"{base}:p{page}@{ver}" if page else f"{base}:@{ver}"


def _covered_workstreams(doc):
    covered = set()
    for s in doc.get("sources") or []:
        if s.get("type"):
            covered.add(s["type"])
    for e in doc.get("extractions") or []:
        if e.get("workstream"):
            covered.add(e["workstream"])
    for i in doc.get("issues") or []:
        if i.get("category"):
            covered.add(i["category"])
    return covered


def _payload_for(target, extractions):
    if target == "comps-analysis-builder":
        keep = {"financial", "commercial"}
    else:
        keep = {"financial"}
    return [e.get("field") for e in extractions if e.get("workstream") in keep]


def build_pack(doc: dict) -> dict:
    deal = doc.get("deal") or {}
    pack_id = f"DDP-{deal.get('deal_id','UNKNOWN')}"
    idx = _index(doc)
    unsupported: list[dict] = []

    # source index
    source_index = [
        {"doc_id": s.get("doc_id"), "title": s.get("title"), "type": s.get("type"),
         "date": s.get("date"), "version": s.get("version"), "owner": s.get("owner"),
         "index_ref": s.get("index_ref")}
        for s in (doc.get("sources") or [])
    ]

    # extracted data (exclude unsupported)
    extracted_data = []
    for e in doc.get("extractions") or []:
        sd = e.get("source_doc")
        if sd not in idx:
            unsupported.append({"kind": "extraction", "field": e.get("field"), "source_doc": sd})
            continue
        conf = e.get("confidence") if e.get("confidence") in CONFIDENCE else "low"
        extracted_data.append({
            "field": e.get("field"), "value": e.get("value"), "unit": e.get("unit"),
            "workstream": e.get("workstream"), "confidence": conf,
            "source_doc": sd, "citation": _citation(e, idx.get(sd)),
        })

    # issue log (exclude unsupported)
    issue_log = []
    counts = {"high": 0, "medium": 0, "low": 0}
    for i in doc.get("issues") or []:
        sd = i.get("source_doc")
        if sd not in idx:
            unsupported.append({"kind": "issue", "issue_id": i.get("issue_id"), "source_doc": sd})
            continue
        sev = i.get("severity")
        if sev in counts:
            counts[sev] += 1
        issue_log.append({
            "issue_id": i.get("issue_id"), "category": i.get("category"), "severity": sev,
            "description": i.get("description"), "status": i.get("status", "open"),
            "source_doc": sd, "citation": _citation(i, idx.get(sd)),
        })
    issue_summary = {**counts, "total": sum(counts.values())}

    # open questions (pass-through)
    open_questions = [
        {"q_id": q.get("q_id"), "topic": q.get("topic"), "question": q.get("question"),
         "owner": q.get("owner"), "priority": q.get("priority")}
        for q in (doc.get("open_questions") or [])
    ]

    # completeness
    covered = _covered_workstreams(doc)
    covered_req = [w for w in REQUIRED_WORKSTREAMS if w in covered]
    missing = [w for w in REQUIRED_WORKSTREAMS if w not in covered]
    completeness = {
        "workstreams_covered": len(covered_req),
        "workstreams_total": len(REQUIRED_WORKSTREAMS),
        "covered": covered_req,
        "missing": missing,
    }

    # model handoffs (targets validated)
    model_handoffs = []
    for t in doc.get("model_targets") or []:
        if t not in KNOWN_MODEL_TARGETS:
            unsupported.append({"kind": "handoff", "target_skill": t})
            continue
        model_handoffs.append({
            "target_skill": t,
            "payload_fields": _payload_for(t, extracted_data),
            "note": f"Cited extraction bundle from {pack_id}",
        })

    # approvals (draft: external_delivery only if all required roles approved)
    ledger = [
        {"role": a.get("role"), "name_masked": a.get("name_masked"),
         "status": a.get("status", "pending"), "date": a.get("date")}
        for a in (doc.get("approvals") or [])
    ]
    by_role = {a["role"]: a for a in ledger}
    external_delivery = all(
        (by_role.get(r) or {}).get("status") == "approved" for r in REQUIRED_APPROVAL_ROLES
    )

    return {
        "pack_id": pack_id,
        "deal": {
            "deal_id": deal.get("deal_id"),
            "project_codename": deal.get("project_codename"),
            "target_name_masked": deal.get("target_name_masked"),
            "as_of_date": deal.get("as_of_date"),
        },
        "generated_as_of": deal.get("as_of_date"),
        "sections": list(REQUIRED_SECTIONS),
        "source_index": source_index,
        "extracted_data": extracted_data,
        "issue_log": issue_log,
        "issue_summary": issue_summary,
        "open_questions": open_questions,
        "completeness": completeness,
        "model_handoffs": model_handoffs,
        "approvals": ledger,
        "external_delivery": external_delivery,
        "unsupported_claims": unsupported,
        "standing_note": STANDING_NOTE,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "dataroom_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    pack = build_pack(doc)
    errors: list[str] = []

    def check(cond, msg):
        if not cond:
            errors.append(msg)

    check(pack["pack_id"] == "DDP-PROJ-ATLAS", f"unexpected pack_id {pack['pack_id']!r}")
    check(pack["unsupported_claims"] == [], "expected no unsupported claims on clean fixture")
    check(len(pack["extracted_data"]) == 6, f"expected 6 extracted rows, got {len(pack['extracted_data'])}")
    check(pack["issue_summary"] == {"high": 1, "medium": 1, "low": 1, "total": 3},
          f"unexpected issue summary {pack['issue_summary']}")
    check([m["target_skill"] for m in pack["model_handoffs"]]
          == ["three-statement-model-builder", "dcf-modeler", "comps-analysis-builder"],
          "unexpected model-handoff targets")
    check(all(m["target_skill"] in KNOWN_MODEL_TARGETS for m in pack["model_handoffs"]),
          "a model-handoff target is not a known modeling skill")
    check(pack["completeness"]["missing"] == ["operational"],
          f"unexpected missing workstreams {pack['completeness']['missing']}")
    check(pack["external_delivery"] is False, "draft fixture must not be external-delivery ready")
    check(pack["sections"] == REQUIRED_SECTIONS, "sections do not match required template sections")

    print(f"pack_id: {pack['pack_id']}")
    print(f"issues: high={pack['issue_summary']['high']} medium={pack['issue_summary']['medium']} "
          f"low={pack['issue_summary']['low']} total={pack['issue_summary']['total']}")
    print("model_handoffs: " + ", ".join(m["target_skill"] for m in pack["model_handoffs"]))
    print(f"completeness: {pack['completeness']['workstreams_covered']}/"
          f"{pack['completeness']['workstreams_total']} covered; missing={pack['completeness']['missing']}")
    print(f"unsupported_claims: {len(pack['unsupported_claims'])}")
    for e in errors:
        print("ERROR", e)
    print(f"packaging selftest: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv) -> int:
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_pack(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
