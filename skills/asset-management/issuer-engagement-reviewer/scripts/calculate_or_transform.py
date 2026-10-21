#!/usr/bin/env python3
"""Deterministic engagement-history assembly engine for issuer-engagement-reviewer.

Takes a de-identified issuer engagement log and assembles a cited, draft Engagement History
Brief: a reverse-chronological engagement timeline, each issuer commitment matched to the
progress the issuer has *disclosed* against it (with a factual, date-based status), a
role-level attendee roll-up, a deduplicated source-document list, and every still-open
follow-up. Assembly is normalization + matching only.

HARD BOUNDARY (fail closed downstream in validate_output): this engine NEVER chooses an
engagement objective, represents or states a firm position/view, casts or proposes a vote,
or writes a system of record. `engagement_objective.selected` is always null and
`firm_position.represented` is always false; those are human stewardship decisions.

Commitment status is factual and derived only from dates + disclosed progress:
  - "progress-disclosed"      : at least one disclosed-progress record references the commitment
  - "overdue-no-disclosure"   : due date has passed (< as_of_date) and no progress is disclosed
  - "no-progress-disclosed"   : no progress disclosed and the due date has not passed
It never judges whether a commitment was substantively met — that is the analyst's call.

Usage:
  python calculate_or_transform.py engagements.json   # prints the brief JSON to stdout
  python calculate_or_transform.py --selftest         # builds the brief from the bundled
                                                       # fixture, runs invariant checks, and
                                                       # prints a line ending "N error(s)"
Exit 0 unless --selftest finds an invariant violation (then 1).
"""
from __future__ import annotations
import json, sys, copy, hashlib
from datetime import date
from pathlib import Path
from native_integrity import attach_source, canonical_hash

FIXTURE = Path(__file__).resolve().parents[1] / "evals" / "files" / "engagements_example.json"

REQUIRED_APPROVALS = ["Stewardship analyst", "Stewardship lead"]
STANDING_NOTE = (
    "Draft engagement history only; this brief does not choose an engagement objective or "
    "represent a firm position, and casts or proposes no vote. A stewardship analyst must "
    "review, and a stewardship lead adjudicate, before use."
)
OBJECTIVE_NOTE = (
    "Not selected. Selecting an engagement objective is a human stewardship decision and is "
    "out of scope for this brief; route per handoffs."
)
POSITION_NOTE = "Not represented. This brief is evidence-only and states no view."

# Sections that must appear in every assembled brief (mirrors assets/output-template.md).
SECTION_KEYS = [
    "issuer_profile", "engagement_chronology", "commitments_and_progress",
    "attendees", "source_documents", "unresolved_follow_ups",
    "engagement_objective", "firm_position",
]


def _progress_index(engagements):
    """commitment_id -> list of disclosed-progress records (with engagement + citation)."""
    idx = {}
    for e in engagements:
        for p in e.get("disclosed_progress") or []:
            cid = p.get("commitment_id")
            idx.setdefault(cid, []).append({
                "engagement_id": e.get("engagement_id"),
                "text": p.get("text"),
                "disclosed_date": p.get("disclosed_date"),
                "citation": p.get("source_ref"),
            })
    return idx


def _commitment_status(due, has_progress, as_of):
    if has_progress:
        return "progress-disclosed"
    if due and as_of and str(due) < str(as_of):
        return "overdue-no-disclosure"
    return "no-progress-disclosed"


def _chronology(engagements):
    rows = []
    for e in engagements:
        rows.append({
            "engagement_id": e.get("engagement_id"),
            "date": e.get("date"),
            "type": e.get("type"),
            "channel": e.get("channel"),
            "topics": e.get("topics") or [],
            "firm_attendees": len(e.get("attendees_firm") or []),
            "issuer_attendees": len(e.get("attendees_issuer") or []),
            "citation": e.get("source_ref"),
        })
    rows.sort(key=lambda r: str(r.get("date") or ""), reverse=True)
    return rows


def _commitments(engagements, prog_idx, as_of):
    out = []
    for e in engagements:
        for c in e.get("commitments") or []:
            cid = c.get("commitment_id")
            progress = prog_idx.get(cid, [])
            citations = [e.get("source_ref")] + [p["citation"] for p in progress if p.get("citation")]
            out.append({
                "commitment_id": cid,
                "engagement_id": e.get("engagement_id"),
                "raised_date": e.get("date"),
                "text": c.get("text"),
                "due": c.get("due"),
                "status": _commitment_status(c.get("due"), bool(progress), as_of),
                "disclosed_progress": progress,
                "outcome_status": "not-assessed",
                "verification_status": "issuer-disclosed-not-independently-verified",
                "citations": [x for x in citations if x],
            })
    out.sort(key=lambda r: str(r.get("commitment_id") or ""))
    return out


def _attendees(engagements):
    firm, issuer = {}, {}
    for e in engagements:
        for p in e.get("attendees_firm") or []:
            firm.setdefault((p.get("role"), p.get("id")), []).append(e.get("engagement_id"))
        for p in e.get("attendees_issuer") or []:
            issuer.setdefault((p.get("role"), p.get("id")), []).append(e.get("engagement_id"))

    def _fmt(d):
        return sorted(
            ({"role": role, "id": pid, "engagements": sorted(engs)} for (role, pid), engs in d.items()),
            key=lambda r: (str(r["role"]), str(r["id"])),
        )
    return {"firm": _fmt(firm), "issuer": _fmt(issuer)}


def _source_documents(engagements):
    seen, out = set(), []
    for e in engagements:
        for d in e.get("source_docs") or []:
            did = d.get("doc_id")
            if did in seen:
                continue
            seen.add(did)
            out.append({
                "doc_id": did,
                "title": d.get("title"),
                "type": d.get("type"),
                "date": d.get("date"),
                "citation": d.get("source_ref"),
            })
    out.sort(key=lambda r: str(r.get("date") or ""), reverse=True)
    return out


def _unresolved_follow_ups(engagements):
    out = []
    for e in engagements:
        for f in e.get("follow_ups") or []:
            if str(f.get("status", "open")).lower() == "closed":
                continue
            out.append({
                "follow_up_id": f.get("follow_up_id"),
                "engagement_id": e.get("engagement_id"),
                "opened_date": e.get("date"),
                "text": f.get("text"),
                "owner_role": f.get("owner_role"),
                "citation": e.get("source_ref"),
            })
    out.sort(key=lambda r: str(r.get("opened_date") or ""), reverse=True)
    return out


def _native_build_brief(doc: dict) -> dict:
    as_of = doc.get("as_of_date")
    cutoff = date.fromisoformat(as_of)
    engagements, gaps = [], []
    for raw in doc.get("engagements") or []:
        e = copy.deepcopy(raw)
        try:
            if date.fromisoformat(e["date"]) > cutoff:
                raise ValueError("future engagement")
        except (KeyError, TypeError, ValueError):
            gaps.append({"engagement_id": e.get("engagement_id"), "reason": "future or invalid engagement date"})
            continue
        eligible = []
        for progress in e.get("disclosed_progress", []):
            try:
                if date.fromisoformat(progress["disclosed_date"]) > cutoff:
                    raise ValueError("future progress")
                eligible.append(progress)
            except (KeyError, TypeError, ValueError):
                gaps.append({"commitment_id": progress.get("commitment_id"), "reason": "future or invalid progress date"})
        e["disclosed_progress"] = eligible
        engagements.append(e)
    prog_idx = _progress_index(engagements)

    commitments = _commitments(engagements, prog_idx, as_of)
    follow_ups = _unresolved_follow_ups(engagements)

    sections = {
        "issuer_profile": {
            "issuer_id": (doc.get("issuer") or {}).get("issuer_id"),
            "name": (doc.get("issuer") or {}).get("name"),
            "sector": (doc.get("issuer") or {}).get("sector"),
            "ticker": (doc.get("issuer") or {}).get("ticker"),
            "as_of_date": as_of,
        },
        "engagement_chronology": _chronology(engagements),
        "commitments_and_progress": commitments,
        "attendees": _attendees(engagements),
        "source_documents": _source_documents(engagements),
        "unresolved_follow_ups": follow_ups,
        "engagement_objective": {"selected": None, "note": OBJECTIVE_NOTE},
        "firm_position": {"represented": False, "note": POSITION_NOTE},
    }

    summary = {
        "engagements": len(engagements),
        "commitments": len(commitments),
        "commitments_progress_disclosed": sum(1 for c in commitments if c["status"] == "progress-disclosed"),
        "commitments_overdue_no_disclosure": sum(1 for c in commitments if c["status"] == "overdue-no-disclosure"),
        "unresolved_follow_ups": len(follow_ups),
        "source_documents": len(sections["source_documents"]),
    }

    return {
        "brief_id": "eng-" + hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()[:20],
        "data_quality_gaps": gaps,
        "brief_version": doc.get("brief_version"),
        "draft": True,
        "status": "draft",
        "issuer_id": (doc.get("issuer") or {}).get("issuer_id"),
        "as_of_date": as_of,
        "sections": sections,
        "summary": summary,
        "handoffs": [
            {"when": "A vote decision needs an evidence packet (agenda, disclosures, policy, precedent)",
             "route_to": "proxy-voting-reviewer", "mode": "evidence"},
            {"when": "A human-proposed vote must be checked against voting policy and precedent",
             "route_to": "proxy-voting-reviewer", "mode": "policy"},
            {"when": "Choosing the engagement objective or setting/representing a firm position",
             "route_to": "human: stewardship analyst then stewardship lead / stewardship committee"},
        ],
        "human_review": {
            "status": "pending",
            "required_approvals": list(REQUIRED_APPROVALS),
            "recorded": [],
        },
        "provenance": {
            "brief_id": "eng-" + hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()[:20],
        "data_quality_gaps": gaps,
        "brief_version": doc.get("brief_version"),
            "source_hierarchy_version": doc.get("source_hierarchy_version"),
            "as_of_date": as_of,
        },
        "standing_note": STANDING_NOTE,
    }


def _selftest() -> int:
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    brief = build_brief(doc)
    errors = []

    for key in SECTION_KEYS:
        if key not in brief["sections"]:
            errors.append(f"missing section {key!r}")

    # HARD BOUNDARY invariants
    if brief["sections"]["engagement_objective"]["selected"] is not None:
        errors.append("engagement_objective.selected must be null (no objective chosen)")
    if brief["sections"]["firm_position"]["represented"] is not False:
        errors.append("firm_position.represented must be false (no firm position)")
    if brief.get("draft") is not True or brief.get("status") != "draft":
        errors.append("brief must be draft-only")

    # every assembled item must be cited (matches validate_output)
    for c in brief["sections"]["engagement_chronology"]:
        if not c.get("citation"):
            errors.append(f"uncited chronology row {c.get('engagement_id')}")
    for c in brief["sections"]["commitments_and_progress"]:
        if not c.get("citations"):
            errors.append(f"uncited commitment {c.get('commitment_id')}")
    for f in brief["sections"]["unresolved_follow_ups"]:
        if not f.get("citation"):
            errors.append(f"uncited follow-up {f.get('follow_up_id')}")

    # matching invariants against the known fixture
    statuses = {c["commitment_id"]: c["status"] for c in brief["sections"]["commitments_and_progress"]}
    expected = {
        "COM-1": "progress-disclosed",
        "COM-2": "progress-disclosed",
        "COM-3": "no-progress-disclosed",
        "COM-4": "overdue-no-disclosure",
    }
    for cid, exp in expected.items():
        if statuses.get(cid) != exp:
            errors.append(f"{cid}: status {statuses.get(cid)!r} != expected {exp!r}")
    if brief["summary"]["unresolved_follow_ups"] != 2:
        errors.append("expected 2 unresolved follow-ups (FU-1 is closed)")

    print(json.dumps(brief, indent=2))
    for e in errors:
        print("ERROR", e)
    print(f"transform selftest: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv) -> int:
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_brief(doc), indent=2))
    return 0




def build_brief(doc: dict) -> dict:
    # Reject non-JSON and non-finite input before any calculations.
    canonical_hash(doc)
    return attach_source(_native_build_brief(doc), doc)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
