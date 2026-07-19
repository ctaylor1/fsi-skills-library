#!/usr/bin/env python3
"""Deterministic SAR draft-package assembler for suspicious-activity-report-drafter.

Marshals an approved-investigation SAR case-intake file into a controlled, source-mapped
draft SAR package that maps to assets/output-template.md. It builds the subjects, accounts/
instruments, activity summary, dated chronology, amount + chronology tie-outs, typology
assessment (declared typologies vs. the approved typology library), the 5W+H narrative,
an evidence index, and the investigation rationale; it computes a packaging status, an
advisory recommended review path, and an approval ledger.

Hard boundaries (fail closed): if the case is NOT approved/adjudicated for SAR drafting
(`case_approved_for_sar` != true) the package is `blocked` and routed back to the
investigator — the suspicion determination is never made here. Any tie-out break, uncovered
party, unsupported typology, incomplete 5W+H, or uncited fact forces `needs-evidence`. The
assembler NEVER makes the file/no-file determination, files/e-files a SAR, submits anything
to FinCEN, closes or dispositions the case, writes a system of record, sends the package,
or adds speculation beyond the evidenced facts.

Usage: python calculate_or_transform.py case.json | --selftest
Prints the SAR draft-package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

WHO_WHAT = ("who", "what", "when", "where", "why", "how")
STANDING_NOTE = (
    "Draft SAR package for compliance quality review and human filing only. This package "
    "records fact-based narrative, source citations, tie-outs, and an advisory review path; "
    "it makes no suspicion or file/no-file determination, files nothing, e-files nothing, "
    "submits nothing to FinCEN, closes or dispositions no case, writes no system of record, "
    "adds no speculation beyond the evidence, and has not been sent. Every regulated decision "
    "and the filing itself remain with the authorized human (SAR quality reviewer / MLRO / "
    "BSA Officer)."
)


def _mask(ref: str) -> str:
    return ref or "****"


def _amount_tie_out(doc: dict) -> dict:
    txns = doc.get("transactions") or []
    act = doc.get("activity") or {}
    per = act.get("period") or {}
    computed_total = round(sum(float(t.get("amount") or 0) for t in txns), 2)
    declared_total = float(act.get("aggregate_amount") or 0)
    dates = sorted([t.get("date") for t in txns if t.get("date")])
    computed_period = {"from": dates[0] if dates else None, "to": dates[-1] if dates else None}
    declared_period = {"from": per.get("from"), "to": per.get("to")}
    computed_count = len(txns)
    declared_count = act.get("transaction_count")

    breaks = []
    if abs(computed_total - declared_total) > 0.005:
        breaks.append(f"amount: sum(transactions)={computed_total:g} != aggregate_amount={declared_total:g}")
    if computed_period != declared_period:
        breaks.append(f"period: transaction span {computed_period} != declared period {declared_period}")
    if declared_count is not None and declared_count != computed_count:
        breaks.append(f"count: transaction_count={declared_count} != actual={computed_count}")

    return {
        "title": "Amount & Chronology Tie-Out",
        "status": "pass" if not breaks else "break",
        "computed_total": computed_total,
        "declared_total": declared_total,
        "currency": act.get("currency"),
        "computed_period": computed_period,
        "declared_period": declared_period,
        "computed_count": computed_count,
        "declared_count": declared_count,
        "breaks": breaks,
    }


def _subjects(doc: dict) -> dict:
    subjects = doc.get("subjects") or []
    subj_refs = {s.get("subject_ref") for s in subjects}
    referenced = set()
    for t in doc.get("transactions") or []:
        if t.get("subject_ref"):
            referenced.add(t["subject_ref"])
        if t.get("counterparty_ref"):
            referenced.add(t["counterparty_ref"])
    uncovered = sorted(r for r in referenced if r not in subj_refs)
    items = [{
        "subject_ref": s.get("subject_ref"),
        "role": s.get("role"),
        "type": s.get("type"),
        "name_masked": _mask(s.get("name_masked")),
        "identifiers_masked": list(s.get("identifiers_masked") or []),
        "relationship": s.get("relationship"),
    } for s in subjects]
    citations = [f"casemgmt:{doc.get('case_id','?')};subjects@intake"]
    return {
        "title": "Subjects & Parties",
        "status": "gap" if uncovered else "present",
        "covered": not uncovered,
        "uncovered_parties": uncovered,
        "items": items,
        "citations": citations,
    }


def _chronology(doc: dict) -> dict:
    events = []
    uncited = []
    for t in sorted(doc.get("transactions") or [], key=lambda x: (x.get("date") or "", x.get("txn_id") or "")):
        cite = t.get("source_ref")
        if not cite:
            uncited.append(t.get("txn_id"))
        events.append({
            "date": t.get("date"),
            "txn_id": t.get("txn_id"),
            "amount": t.get("amount"),
            "instrument": t.get("instrument"),
            "subject_ref": t.get("subject_ref"),
            "counterparty_ref": t.get("counterparty_ref"),
            "citation": cite,
        })
    return {
        "title": "Chronology of Activity",
        "status": "gap" if uncited else "present",
        "events": events,
        "uncited_events": uncited,
    }


def _typology_assessment(doc: dict) -> dict:
    lib = doc.get("typology_library") or {}
    declared = doc.get("typologies") or []
    assessed = []
    all_supported = bool(declared) and bool(lib)
    for ty in declared:
        code = ty.get("code")
        observed = set(ty.get("observed_indicators") or [])
        entry = lib.get(code) or {}
        required = set(entry.get("required_indicators") or [])
        in_library = code in lib
        missing = sorted(required - observed)
        supported = in_library and not missing
        if not supported:
            all_supported = False
        assessed.append({
            "code": code,
            "label": entry.get("label") or code,
            "in_library": in_library,
            "observed_indicators": sorted(observed),
            "required_indicators": sorted(required),
            "missing_indicators": missing,
            "supported": supported,
            "citations": [f"config:typology-library={doc.get('config_version')}"] if in_library else [],
        })
    return {
        "title": "Typology Assessment",
        "status": "present" if all_supported else "gap",
        "typologies": assessed,
        "all_supported": all_supported,
    }


def _narrative(doc: dict) -> dict:
    ni = doc.get("narrative_inputs") or {}
    fields = {w: str(ni.get(w) or "").strip() for w in WHO_WHAT}
    missing = [w for w in WHO_WHAT if not fields[w]]
    ev = doc.get("evidence") or []
    citations = sorted({e.get("citation") for e in ev if e.get("citation")})
    return {
        "title": "SAR Narrative (5W + How)",
        "status": "present" if (not missing and citations) else "gap",
        "who": fields["who"],
        "what": fields["what"],
        "when": fields["when"],
        "where": fields["where"],
        "why": fields["why"],
        "how": fields["how"],
        "complete": not missing,
        "missing": missing,
        "citations": citations,
    }


def _evidence_index(doc: dict) -> dict:
    entries = []
    uncited = []
    for e in doc.get("evidence") or []:
        cite = e.get("citation")
        if not cite:
            uncited.append(e.get("fact"))
        entries.append({"fact": e.get("fact"), "citation": cite})
    return {
        "title": "Evidence Index",
        "status": "gap" if (uncited or not entries) else "present",
        "entries": entries,
        "uncited_facts": uncited,
    }


def _investigation_rationale(doc: dict) -> dict:
    r = doc.get("investigation_rationale") or {}
    cites = list(r.get("citations") or [])
    return {
        "title": "Investigation Rationale",
        "status": "present" if (r.get("summary") and cites) else "gap",
        "summary": r.get("summary"),
        "approving_investigation": doc.get("approving_investigation"),
        "citations": cites,
        "note": "Fact-based rationale for why the activity is suspicious; not a conclusion of guilt.",
    }


def _recommendation(status: str, hard: bool) -> dict:
    if hard:
        path = "hold-pending-investigation"
        note = ("Hard boundary: the case is not approved/adjudicated for SAR drafting. Recommend "
                "the package be held and routed to transaction-monitoring-alert-investigator to "
                "conclude the investigation. No suspicion or filing determination is made here.")
    elif status == "needs-evidence":
        path = "return-for-evidence"
        note = ("Gaps remain (tie-out break, uncovered party, unsupported typology, incomplete "
                "5W+H, or uncited fact). Recommend returning for the missing evidence before "
                "quality review; do not proceed on assumptions. No determination is made here.")
    else:
        path = "quality-review-and-compliance-approval"
        note = ("Draft is complete and tie-outs reconcile. Recommend SAR quality review and MLRO/"
                "BSA compliance approval, after which the authorized human decides whether to file "
                "and e-files via BSA E-Filing. Recommendation only — not a file/no-file decision.")
    return {"title": "Recommended Review Path", "recommended_review_path": path, "note": note}


def _approvals(required: list, recorded: list) -> dict:
    by_role = {r.get("role"): r for r in (recorded or []) if isinstance(r, dict)}
    ledger = []
    for role in required:
        rec = by_role.get(role)
        if rec and rec.get("approver") and rec.get("date"):
            ledger.append({"role": role, "status": "obtained",
                           "approver": rec.get("approver"), "date": rec.get("date")})
        else:
            ledger.append({"role": role, "status": "pending"})
    return {"title": "Approvals & Sign-off", "required": list(required), "ledger": ledger,
            "note": "Draft is queued for quality review and compliance approval; obtaining these "
                    "sign-offs and the filing decision are the human steps."}


def _routes(doc: dict, hard: bool) -> list[dict]:
    routes = []
    if hard:
        routes.append({"skill": "transaction-monitoring-alert-investigator",
                       "reason": "case not adjudicated for SAR — conclude the investigation first"})
    return routes


def _filing_header(doc: dict, status: str) -> dict:
    fc = doc.get("filing_context") or {}
    return {
        "title": "Filing Header (context only — no filing action)",
        "case_id": doc.get("case_id"),
        "approving_investigation": doc.get("approving_investigation"),
        "filing_type": fc.get("filing_type"),
        "prior_sar_ref": fc.get("prior_sar_ref"),
        "activity_detected_date": fc.get("activity_detected_date"),
        "regulatory_deadline_days": fc.get("regulatory_deadline_days"),
        "packaging_status": status,
        "note": "Filing type and deadline are carried for the human filer's context; this package "
                "does not file, e-file, or set a filing status of record.",
    }


def _accounts_instruments(doc: dict) -> dict:
    items = [{
        "account_ref": _mask(a.get("account_ref")),
        "type": a.get("type"),
        "instruments": list(a.get("instruments") or []),
    } for a in (doc.get("accounts_instruments") or [])]
    return {"title": "Accounts & Instruments", "status": "present" if items else "gap", "items": items}


def _activity_summary(doc: dict, tie: dict) -> dict:
    act = doc.get("activity") or {}
    return {
        "title": "Activity Summary",
        "period": act.get("period"),
        "aggregate_amount": act.get("aggregate_amount"),
        "currency": act.get("currency"),
        "transaction_count": act.get("transaction_count"),
        "tie_out_status": tie.get("status"),
    }


def package(doc: dict) -> dict:
    hard = doc.get("case_approved_for_sar") is not True

    sections: dict = {}
    tie = _amount_tie_out(doc)
    subjects = _subjects(doc)
    chronology = _chronology(doc)
    typ = _typology_assessment(doc)
    narrative = _narrative(doc)
    ev_index = _evidence_index(doc)
    rationale = _investigation_rationale(doc)

    # Determine status.
    gaps = []
    if tie["status"] != "pass":
        gaps.append("amount/chronology tie-out break")
    if not subjects["covered"]:
        gaps.append("uncovered party")
    if not typ["all_supported"]:
        gaps.append("unsupported typology")
    if not narrative["complete"] or not narrative["citations"]:
        gaps.append("incomplete or uncited 5W+H narrative")
    if chronology["uncited_events"]:
        gaps.append("uncited chronology event")
    if ev_index["status"] != "present":
        gaps.append("missing/uncited evidence index")
    if rationale["status"] != "present":
        gaps.append("uncited investigation rationale")

    if hard:
        status = "blocked"
    elif gaps:
        status = "needs-evidence"
    else:
        status = "ready-for-quality-review"

    sections["filing_header"] = _filing_header(doc, status)
    sections["subjects"] = subjects
    sections["accounts_instruments"] = _accounts_instruments(doc)
    sections["activity_summary"] = _activity_summary(doc, tie)
    sections["chronology"] = chronology
    sections["amount_tie_out"] = tie
    sections["typology_assessment"] = typ
    sections["narrative"] = narrative
    sections["evidence_index"] = ev_index
    sections["investigation_rationale"] = rationale
    sections["recommendation"] = _recommendation(status, hard)
    sections["approvals"] = _approvals(doc.get("required_approvals") or [], doc.get("recorded_approvals") or [])

    all_cites = sorted(set(
        subjects["citations"]
        + [e["citation"] for e in chronology["events"] if e.get("citation")]
        + narrative["citations"]
        + rationale["citations"]
        + [c for t in typ["typologies"] for c in t.get("citations", [])]
    ))
    sections["sources_citations"] = {
        "title": "Sources & Citations",
        "citations": all_cites,
        "note": "Every asserted fact is mapped to an approved source above.",
    }
    sections["standing_note_limitations"] = {"title": "Standing Note / Limitations", "text": STANDING_NOTE}

    return {
        "config_version": doc.get("config_version"),
        "template_version": doc.get("template_version") or "sar-package-v1",
        "case_id": doc.get("case_id"),
        "jurisdiction": doc.get("jurisdiction"),
        "packaging_status": status,
        "hard_boundary": hard,
        "gaps": gaps,
        "routes": _routes(doc, hard),
        "sections": sections,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "sar_case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(package(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
