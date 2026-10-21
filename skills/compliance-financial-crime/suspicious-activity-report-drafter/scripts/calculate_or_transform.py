#!/usr/bin/env python3
"""Phase 1 assembles exact supplied evidence facts into six narrative fields. It does not verify that a cited source is true or that a paraphrase is entailed. Human reviewers must assess suspicion, narrative coherence, completeness, lawful disclosure and current entity-specific requirements. This implementation accepts transaction-based US intake; attempted-activity, STR and filing-lifecycle workflows require specialist preparation outside this calculator. Do not delay required reporting while awaiting case closure.

Offline Phase 1 calculation; see references/domain-rules.md.
"""
from __future__ import annotations
import json, sys, math
from datetime import date
from pathlib import Path
from native_integrity import attach_source
from native_integrity import canonical_hash

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


def _supplied_reference(ref: str) -> str:
    return ref or "****"


def _amount_tie_out(doc: dict) -> dict:
    txns = doc.get("transactions") or []
    act = doc.get("activity") or {}
    per = act.get("period") or {}
    amounts_valid = all(isinstance(t.get("amount"), (int, float)) and not isinstance(t.get("amount"), bool) and math.isfinite(t["amount"]) and t["amount"] >= 0 for t in txns)
    computed_total = round(sum(t["amount"] for t in txns), 2) if amounts_valid else 0
    declared_total = float(act.get("aggregate_amount") or 0)
    dates = sorted([t.get("date") for t in txns if t.get("date")])
    computed_period = {"from": dates[0] if dates else None, "to": dates[-1] if dates else None}
    declared_period = {"from": per.get("from"), "to": per.get("to")}
    computed_count = len(txns)
    declared_count = act.get("transaction_count")

    breaks = []
    if not amounts_valid:
        breaks.append("missing, invalid or negative transaction amount")
    try:
        assessed = date.fromisoformat(doc["as_of"])
        first, last = date.fromisoformat(per["from"]), date.fromisoformat(per["to"])
        if assessed.isoformat() != doc["as_of"] or first.isoformat() != per["from"] or last.isoformat() != per["to"]:
            raise ValueError("noncanonical assessment/activity date")
        if first > last: breaks.append("activity period starts after it ends")
        if first > assessed or last > assessed: breaks.append("activity period is after assessment as_of")
        for day in dates:
            parsed = date.fromisoformat(day)
            if parsed.isoformat() != day: raise ValueError("noncanonical transaction date")
            if parsed > assessed: breaks.append("transaction after assessment as_of: " + day)
    except (ValueError, TypeError, KeyError):
        breaks.append("real YYYY-MM-DD transaction, activity period and assessment dates required")
    if not txns or len({t.get("txn_id") for t in txns}) != len(txns):
        breaks.append("empty or duplicate transaction population")
    if not act.get("currency") or any(t.get("currency") != act.get("currency") for t in txns):
        breaks.append("mixed/missing transaction currency; FX conversion is not implemented")
    if act.get("amount_basis") != "gross-listed-transactions":
        breaks.append("amount basis must explicitly identify gross listed transaction legs, not unique proceeds")
    if not math.isfinite(computed_total) or not math.isfinite(declared_total):
        breaks.append("non-finite monetary value")
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
        "name_masked": _supplied_reference(s.get("name_masked")),
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
    all_supported = True
    ev_by_id = {e.get("evidence_id"): e for e in doc.get("evidence") or [] if e.get("evidence_id")}
    for ty in declared:
        code = ty.get("code")
        observed = set(ty.get("observed_indicators") or [])
        entry = lib.get(code) or {}
        required = set(entry.get("required_indicators") or [])
        in_library = code in lib
        missing = sorted(required - observed)
        support = ty.get("indicator_evidence") or {}
        unsupported_indicators = [i for i in observed if not support.get(i) or any(not ev_by_id.get(e, {}).get("citation") for e in support[i])]
        supported = in_library and not missing and not unsupported_indicators
        if not supported:
            all_supported = False
        assessed.append({
            "code": code,
            "label": entry.get("label") or code,
            "in_library": in_library,
            "observed_indicators": sorted(observed),
            "required_indicators": sorted(required),
            "missing_indicators": missing,
            "unsupported_indicators": unsupported_indicators,
            "supported": supported,
            "citations": sorted({ev_by_id[e]["citation"] for ids in support.values() for e in ids if ev_by_id.get(e, {}).get("citation")}),
        })
    return {
        "title": "Typology Assessment",
        "status": "present" if all_supported else "gap",
        "typologies": assessed,
        "all_supported": all_supported,
    }


def _narrative(doc: dict) -> dict:
    ni = doc.get("narrative_inputs") or {}
    evidence = {e.get("evidence_id"): e for e in doc.get("evidence") or [] if e.get("evidence_id")}
    mapping = doc.get("narrative_evidence_ids") or {}
    fields, citations, missing, claims = {}, set(), [], []
    for key in WHO_WHAT:
        ids = mapping.get(key) or []
        valid = bool(ids) and all(evidence.get(i, {}).get("fact") and evidence.get(i, {}).get("citation") for i in ids)
        text = " ".join(evidence[i]["fact"] for i in ids) if valid else ""
        # Phase 1 assembles exact supplied facts; it cannot verify freeform paraphrases.
        if not valid or (ni.get(key) and ni[key].strip() != text):
            missing.append(key)
            text = ""
        fields[key] = text
        if text:
            citations.update(evidence[i]["citation"] for i in ids)
            claims.append({"field": key, "evidence_ids": ids, "source_truth": "unverified"})
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
        "citations": sorted(citations),
        "claim_map": claims,
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
    evidence = {e.get("evidence_id"): e for e in doc.get("evidence") or [] if e.get("evidence_id")}
    ids = r.get("evidence_ids") or []
    valid = (isinstance(ids, list) and bool(ids) and all(isinstance(i, str) and evidence.get(i, {}).get("fact") and evidence.get(i, {}).get("citation") for i in ids))
    text = " ".join(evidence[i]["fact"] for i in ids) if valid else ""
    cites = sorted({evidence[i]["citation"] for i in ids}) if valid else []
    issues = []
    if not valid: issues.append("rationale requires evidence_ids resolving to cited facts")
    if not isinstance(r.get("summary"), str) or r["summary"].strip() != text:
        issues.append("rationale summary must exactly match its mapped supplied facts")
    declared = r.get("citations")
    if declared is not None and (not isinstance(declared, list) or any(not isinstance(c, str) for c in declared) or set(declared) != set(cites)):
        issues.append("rationale citations do not match mapped evidence")
    supported = not issues
    return {
        "title": "Investigation Rationale", "status": "present" if supported else "gap",
        "summary": text if supported else "", "evidence_ids": ids if valid else [],
        "approving_investigation": doc.get("approving_investigation"),
        "citations": cites if supported else [], "gaps": issues,
        "note": "Exact supplied evidence facts only; source truth and substantive suspicion rationale require human review. No conclusion of guilt is made.",
    }


def _recommendation(status: str, hard: bool) -> dict:
    if hard:
        path = "hold-pending-investigation"
        note = ("Required evidence for authorized SAR drafting is missing. Recommend FIU investigator "
                "review through the accountable human process; the financial-crime-case-investigator "
                "skill is planned, not installed. Do not delay required reporting while awaiting "
                "case closure. No suspicion or filing determination is made here.")
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


def approval_digest(doc):
    return canonical_hash({k: v for k, v in doc.items() if k not in {"recorded_approvals", "drafting_authorization"}})


def _approval_valid(rec, doc):
    try:
        dated = date.fromisoformat(rec["date"]) <= date.fromisoformat(doc["as_of"])
    except (TypeError, ValueError, KeyError):
        return False
    return bool(dated and rec.get("status") == "approved" and rec.get("approver")
                and rec.get("source_ref") and rec.get("role")
                and rec.get("case_id") == doc.get("case_id")
                and rec.get("input_sha256") == approval_digest(doc))


def _approvals(required: list, recorded: list, doc: dict) -> dict:
    by_role = {r.get("role"): r for r in (recorded or []) if isinstance(r, dict)}
    ledger = []
    for role in required:
        rec = by_role.get(role)
        if rec and _approval_valid(rec, doc):
            ledger.append({"role": role, "status": "obtained",
                           "approver": rec.get("approver"), "date": rec.get("date"),
                           "source_ref": rec.get("source_ref"), "input_sha256": rec.get("input_sha256"),
                           "authorization_truth": "unverified"})
        else:
            ledger.append({"role": role, "status": "pending"})
    return {"title": "Approvals & Sign-off", "required": list(required), "ledger": ledger,
            "note": "Draft is queued for quality review and compliance approval; obtaining these "
                    "sign-offs and the filing decision are the human steps."}


def _routes(doc: dict, hard: bool) -> list[dict]:
    routes = []
    if hard:
        routes.append({"skill": "financial-crime-case-investigator",
                       "support_status": "planned",
                       "fallback_owner": "accountable FIU investigator / BSA officer",
                       "reason": "missing drafting evidence needs human investigation review; no installed investigative skill or case-closure prerequisite is implied"})
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
        "account_ref": _supplied_reference(a.get("account_ref")),
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


def _compute_unbound(doc: dict) -> dict:
    hard = doc.get("case_approved_for_sar") is not True or not _approval_valid(doc.get("drafting_authorization") or {}, doc)

    sections: dict = {}
    tie = _amount_tie_out(doc)
    subjects = _subjects(doc)
    chronology = _chronology(doc)
    typ = _typology_assessment(doc)
    narrative = _narrative(doc) if not hard else {"title": "SAR Narrative (5W + How)", "status": "withheld", "complete": False, "missing": list(WHO_WHAT), "citations": [], "claim_map": [], **{w: "" for w in WHO_WHAT}}
    ev_index = _evidence_index(doc)
    rationale = _investigation_rationale(doc)

    # Determine status.
    gaps = []
    evidence_ids = [e.get("evidence_id") for e in doc.get("evidence") or []]
    if not all(evidence_ids) or len(set(evidence_ids)) != len(evidence_ids):
        gaps.append("missing or duplicate evidence identity")
    if not doc.get("required_approvals"):
        gaps.append("required review roles not configured")
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
    sections["approvals"] = _approvals(doc.get("required_approvals") or [], doc.get("recorded_approvals") or [], doc)

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
        "note": "Source references and exact supplied narrative facts are mapped; source truth, masking and issuer authority remain unverified.",
    }
    sections["standing_note_limitations"] = {"title": "Standing Note / Limitations", "text": STANDING_NOTE}

    return {
        "config_version": doc.get("config_version"),
        "as_of": doc.get("as_of"),
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


def package(doc):
    """Reject invalid intake before producing a native result; warnings remain partial."""
    from validate_input import validate as validate_input
    errors, _warnings = validate_input(doc)
    if errors:
        raise ValueError("invalid suspicious-activity-report-drafter input: " + "; ".join(errors))
    try:
        return attach_source(_compute_unbound(doc), doc)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, ArithmeticError) as exc:
        raise ValueError("invalid suspicious-activity-report-drafter input: " + str(exc)) from exc


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "sar_case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    try:
        result = package(doc)
    except ValueError as exc:
        print("ERROR " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
