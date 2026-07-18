#!/usr/bin/env python3
"""Deterministic buyer/investor list builder for buyer-investor-list-builder.

Transforms a validated buyer-universe intake into a structured, source-mapped, tiered buyer
list draft. For each candidate it: binds every rationale claim to a citation and EXCLUDES any
claim whose source_doc is not in the source index (recorded as an unsupported claim); computes
a documented fit score and assigns an outreach wave; screens against the firm restricted /
conflicts list and holds any restricted or conflicted candidate OUT of every active wave; links
duplicates to the prior outreach list; and flags candidates missing key fields or all sourcing.

It never sends, delivers, or shares the list, never contacts a buyer, never files or writes a
system of record, and never makes a recommendation, valuation opinion, or investment advice. The
output is an internal draft keyed by a durable `list_id`.

Usage:
  python calculate_or_transform.py buyer_universe.json   # prints the list JSON to stdout
  python calculate_or_transform.py --selftest            # runs bundled self-check, prints N error(s)
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "cover", "executive_summary", "fit_criteria", "source_index", "buyer_list",
    "outreach_waves", "conflicts_hold", "gaps", "approvals", "standing_note",
]
BUYER_TYPES = {"strategic", "sponsor", "lender", "investor"}
SECTOR = {"strong": 3, "moderate": 1, "weak": 0}
SIZE = {"high": 3, "medium": 2, "low": 1}
REL = {"strong": 2, "some": 1, "none": 0}
GEO_PTS, MANDATE_PTS, PRECEDENT_PTS = 2, 2, 2
WAVE1_MIN, WAVE2_MIN = 8, 4
REQUIRED_APPROVAL_ROLES = ["deal_lead", "conflicts_reviewer"]
STANDING_NOTE = ("Draft buyer/investor list for internal review only; not approved for external "
                 "delivery; no buyer has been contacted and no investment recommendation is made.")


def _index(doc):
    return {s.get("doc_id"): s for s in (doc.get("sources") or []) if s.get("doc_id")}


def _citation(item, src):
    page = item.get("page")
    ver = (src or {}).get("version", "?")
    base = item.get("source_doc")
    return f"{base}:p{page}@{ver}" if page else f"{base}:@{ver}"


def _restricted(cand, restricted_ids):
    return bool(cand.get("restricted")) or cand.get("entity_id") in restricted_ids


def _fit_score(cand):
    """Documented, explainable fit score (see references/domain-rules.md)."""
    score, why = 0, []
    s = SECTOR.get(cand.get("sector_fit"), 0)
    if s:
        score += s; why.append(f"sector {cand.get('sector_fit')} +{s}")
    z = SIZE.get(cand.get("size_fit"), 0)
    if z:
        score += z; why.append(f"size {cand.get('size_fit')} +{z}")
    if cand.get("geo_fit"):
        score += GEO_PTS; why.append(f"geo +{GEO_PTS}")
    if cand.get("mandate_fit"):
        score += MANDATE_PTS; why.append(f"mandate +{MANDATE_PTS}")
    if cand.get("precedent_activity"):
        score += PRECEDENT_PTS; why.append(f"precedent +{PRECEDENT_PTS}")
    r = REL.get(cand.get("relationship"), 0)
    if r:
        score += r; why.append(f"relationship {cand.get('relationship')} +{r}")
    return score, why


def wave_for(score: int) -> str:
    if score >= WAVE1_MIN:
        return "wave-1-priority"
    if score >= WAVE2_MIN:
        return "wave-2-standard"
    return "wave-3-broaden"


def build_list(doc: dict) -> dict:
    mandate = doc.get("mandate") or {}
    list_id = f"BIL-{mandate.get('mandate_id', 'UNKNOWN')}"
    idx = _index(doc)
    restricted_ids = set(doc.get("restricted_list") or [])
    existing = {e.get("entity_id"): e for e in (doc.get("existing_list") or []) if e.get("entity_id")}

    source_index = [
        {"doc_id": s.get("doc_id"), "title": s.get("title"), "type": s.get("type"),
         "date": s.get("date"), "version": s.get("version"), "owner": s.get("owner"),
         "index_ref": s.get("index_ref")}
        for s in (doc.get("sources") or [])
    ]

    buyer_list: list[dict] = []       # placed (waves) + held (conflicts) candidates
    conflicts_hold: list[dict] = []
    needs_data: list[dict] = []
    needs_source: list[dict] = []
    duplicates: list[dict] = []
    unsupported_claims: list[dict] = []

    for cand in doc.get("candidates") or []:
        cid = cand.get("candidate_id")
        # 1. structural completeness -> needs-data (never guess to place a candidate)
        missing = []
        if cand.get("buyer_type") not in BUYER_TYPES:
            missing.append("buyer_type")
        if cand.get("sector_fit") not in SECTOR:
            missing.append("sector_fit")
        if cand.get("size_fit") not in SIZE:
            missing.append("size_fit")
        if missing:
            needs_data.append({"candidate_id": cid, "name_masked": cand.get("name_masked"),
                               "missing": missing})
            continue

        # 2. bind rationale citations; drop unsupported claims (source_doc not indexed)
        cited, dropped = [], []
        for claim in cand.get("rationale") or []:
            sd = claim.get("source_doc")
            if sd not in idx:
                unsupported_claims.append({"candidate_id": cid, "claim": claim.get("claim"),
                                           "source_doc": sd})
                dropped.append(sd)
                continue
            cited.append({"claim": claim.get("claim"), "source_doc": sd,
                          "citation": _citation(claim, idx.get(sd))})
        if not cited:
            needs_source.append({"candidate_id": cid, "name_masked": cand.get("name_masked"),
                                 "dropped_claims": dropped})
            continue

        score, why = _fit_score(cand)
        restricted = _restricted(cand, restricted_ids)
        conflict = bool(cand.get("conflict_flag"))

        # 3. restricted / conflict screen overrides wave placement (fail closed)
        if restricted or conflict:
            reason = "restricted-list" if restricted else "unresolved-conflict"
            rec = {"candidate_id": cid, "name_masked": cand.get("name_masked"),
                   "buyer_type": cand.get("buyer_type"), "fit_score": score,
                   "fit_reason": "; ".join(why), "disposition": "hold-conflicts-review",
                   "restricted": restricted, "conflict": conflict,
                   "relationship": cand.get("relationship"), "rationale": cited,
                   "route_handoff": "conflicts-of-interest-reviewer"}
            buyer_list.append(rec)
            conflicts_hold.append({"candidate_id": cid, "reason": reason})
            continue

        # 4. duplicate of a prior outreach-list entry -> link, do not re-list in a wave
        if cand.get("entity_id") in existing:
            duplicates.append({"candidate_id": cid, "name_masked": cand.get("name_masked"),
                               "linked_ref": existing[cand["entity_id"]].get("prior_ref")})
            continue

        # 5. place into a wave by documented score band
        wave = wave_for(score)
        buyer_list.append({
            "candidate_id": cid, "name_masked": cand.get("name_masked"),
            "buyer_type": cand.get("buyer_type"), "fit_score": score,
            "fit_reason": "; ".join(why), "disposition": wave,
            "restricted": False, "conflict": False,
            "relationship": cand.get("relationship"), "rationale": cited,
        })

    waves = {
        "wave-1-priority": [r["candidate_id"] for r in buyer_list if r["disposition"] == "wave-1-priority"],
        "wave-2-standard": [r["candidate_id"] for r in buyer_list if r["disposition"] == "wave-2-standard"],
        "wave-3-broaden": [r["candidate_id"] for r in buyer_list if r["disposition"] == "wave-3-broaden"],
    }

    ledger = [
        {"role": a.get("role"), "name_masked": a.get("name_masked"),
         "status": a.get("status", "pending"), "date": a.get("date")}
        for a in (doc.get("approvals") or [])
    ]
    by_role = {a["role"]: a for a in ledger}
    external_delivery = all(
        (by_role.get(r) or {}).get("status") == "approved" for r in REQUIRED_APPROVAL_ROLES
    )

    summary = {
        "total_candidates": len(doc.get("candidates") or []),
        "wave_1_priority": len(waves["wave-1-priority"]),
        "wave_2_standard": len(waves["wave-2-standard"]),
        "wave_3_broaden": len(waves["wave-3-broaden"]),
        "conflicts_hold": len(conflicts_hold),
        "needs_data": len(needs_data),
        "needs_source": len(needs_source),
        "duplicates": len(duplicates),
        "unsupported_claims": len(unsupported_claims),
    }

    return {
        "list_id": list_id,
        "mandate": {
            "mandate_id": mandate.get("mandate_id"),
            "project_codename": mandate.get("project_codename"),
            "target_name_masked": mandate.get("target_name_masked"),
            "process_type": mandate.get("process_type"),
            "as_of_date": mandate.get("as_of_date"),
            "deal_size_band": mandate.get("deal_size_band"),
        },
        "generated_as_of": mandate.get("as_of_date"),
        "sections": list(REQUIRED_SECTIONS),
        "source_index": source_index,
        "buyer_list": buyer_list,
        "outreach_waves": waves,
        "conflicts_hold": conflicts_hold,
        "needs_data": needs_data,
        "needs_source": needs_source,
        "duplicates": duplicates,
        "unsupported_claims": unsupported_claims,
        "summary": summary,
        "approvals": ledger,
        "external_delivery": external_delivery,
        "standing_note": STANDING_NOTE,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "buyer_universe_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = build_list(doc)
    errors: list[str] = []

    def check(cond, msg):
        if not cond:
            errors.append(msg)

    by_id = {r["candidate_id"]: r for r in out["buyer_list"]}
    check(out["list_id"] == "BIL-PROJ-HELIOS", f"unexpected list_id {out['list_id']!r}")
    check(out["outreach_waves"]["wave-1-priority"] == ["C-001"],
          f"unexpected wave-1 {out['outreach_waves']['wave-1-priority']}")
    check(out["outreach_waves"]["wave-2-standard"] == ["C-002"],
          f"unexpected wave-2 {out['outreach_waves']['wave-2-standard']}")
    check(out["outreach_waves"]["wave-3-broaden"] == ["C-003"],
          f"unexpected wave-3 {out['outreach_waves']['wave-3-broaden']}")
    check(by_id.get("C-001", {}).get("fit_score") == 12, "C-001 fit_score should be 12")
    check(by_id.get("C-002", {}).get("fit_score") == 7, "C-002 fit_score should be 7")
    check(by_id.get("C-003", {}).get("fit_score") == 1, "C-003 fit_score should be 1")
    check({h["candidate_id"] for h in out["conflicts_hold"]} == {"C-004", "C-005"},
          f"unexpected conflicts_hold {out['conflicts_hold']}")
    check(by_id.get("C-004", {}).get("restricted") is True, "C-004 must be flagged restricted")
    check(by_id.get("C-005", {}).get("conflict") is True, "C-005 must be flagged conflict")
    check(all(r["disposition"] == "hold-conflicts-review"
              for r in out["buyer_list"] if r["restricted"] or r["conflict"]),
          "a restricted/conflicted candidate leaked into an outreach wave")
    check([n["candidate_id"] for n in out["needs_data"]] == ["C-006"],
          f"unexpected needs_data {out['needs_data']}")
    check([n["candidate_id"] for n in out["needs_source"]] == ["C-007"],
          f"unexpected needs_source {out['needs_source']}")
    check([d["candidate_id"] for d in out["duplicates"]] == ["C-008"],
          f"unexpected duplicates {out['duplicates']}")
    check(len(out["unsupported_claims"]) == 1, "expected exactly one unsupported claim (C-007)")
    check(out["external_delivery"] is False, "draft fixture must not be external-delivery ready")
    check(out["sections"] == REQUIRED_SECTIONS, "sections do not match required template sections")

    print(f"list_id: {out['list_id']}")
    print("waves: wave-1={} wave-2={} wave-3={}".format(
        out["summary"]["wave_1_priority"], out["summary"]["wave_2_standard"],
        out["summary"]["wave_3_broaden"]))
    print("conflicts_hold: {}  needs_data: {}  needs_source: {}  duplicates: {}".format(
        out["summary"]["conflicts_hold"], out["summary"]["needs_data"],
        out["summary"]["needs_source"], out["summary"]["duplicates"]))
    print(f"unsupported_claims: {out['summary']['unsupported_claims']}")
    for e in errors:
        print("ERROR", e)
    print(f"buyer-list selftest: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv) -> int:
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_list(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
