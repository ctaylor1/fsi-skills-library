#!/usr/bin/env python3
"""Deterministic DDQ/RFP response assembler for due-diligence-questionnaire-responder.

For each questionnaire question, match it to an APPROVED content-library or prior answer,
assign a response status (drafted | stale | unapproved-source | data-gap | unsupported),
attach source citations (content owner, effective date, and any data-point citation), inject
required disclosures, capture recorded approvals plus outstanding required approvals, and
route every unsupported / stale / data-gap / unapproved question to a content owner as an open
item. It NEVER fabricates an answer, never uses non-approved content, never adds a
performance/return guarantee, and never sends or submits the response. The output is a DRAFT
manifest (`draft_status: draft-assembled`) for owner + compliance review.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the response manifest JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Canonical response sections (versioned contract; mirrors assets/output-template.md and the
# REQUIRED_SECTIONS enforced by scripts/validate_output.py).
TEMPLATE_VERSION = "ddq-response-template@0.1.0"

# Statuses whose answer text is asserted to the reader and therefore MUST cite an approved
# source. Only these two carry drafted answer text.
ASSERTED = {"drafted", "stale"}

# Standard performance disclosure, injected whenever any drafted answer cites performance /
# data. validate_output requires this exact statement when data is cited.
STANDARD_PERF_DISCLOSURE = ("Past performance is not indicative of future results. Figures are "
                            "as of the stated date, may be gross of fees, and are subject to "
                            "change and to verification by the content owner.")

STANDING_NOTE = ("Draft DDQ/RFP response for human review only. Every answer is drawn from "
                 "approved content and cited; no answer is fabricated. Content owners and "
                 "compliance must review and approve before any answer is sent or submitted to "
                 "a client, investor, or consultant.")


def _mask_id(s):
    if not s:
        return s
    s = str(s)
    return s if len(s) <= 3 else f"{s[:2]}…{s[-2:]}"


def _is_stale(entry, as_of):
    exp = entry.get("expires")
    return bool(exp and as_of and str(exp) < str(as_of))


def _candidate_pool(doc):
    """Combined answer pool: content library first, then prior answers (both keyed by id)."""
    pool = {}
    for e in doc.get("content_library") or []:
        pool[e.get("answer_id")] = {**e, "pool": "library"}
    for e in doc.get("prior_answers") or []:
        # do not overwrite a library entry with a prior of the same id
        pool.setdefault(e.get("answer_id"), {**e, "pool": "prior"})
    return pool


def _match_by_topic(q, doc):
    """Return (approved_matches, any_matches) for a question with no explicit matched_answer_id."""
    topic = q.get("topic")
    approved, any_match = [], []
    for e in (doc.get("content_library") or []) + (doc.get("prior_answers") or []):
        if topic and e.get("topic") == topic:
            any_match.append(e)
            if e.get("approval_status", "approved") == "approved":
                approved.append(e)
    return approved, any_match


def _route_owner(entry, q):
    if entry:
        return entry.get("owner") or q.get("owner") or "Unassigned content owner", \
               entry.get("owner_role") or q.get("owner_role") or "content owner"
    return q.get("owner") or "Unassigned content owner", q.get("owner_role") or "content owner"


def respond_question(q, doc, pool, data_index, as_of):
    qid = q.get("question_id")
    rec = {"question_id": qid, "section": q.get("section"), "topic": q.get("topic"),
           "answer_id": None, "text": None, "owner": None, "owner_role": None,
           "effective_date": None, "expires": None, "source_approved": False,
           "data_cited": False, "data_id": None, "citations": [], "reason": None}

    # 1. resolve a single candidate answer
    entry = None
    if q.get("matched_answer_id"):
        entry = pool.get(q["matched_answer_id"])
        if entry is None:
            rec.update(status="unsupported",
                       reason=f"matched answer id {q['matched_answer_id']!r} not found in approved content")
            rec["owner"], rec["owner_role"] = _route_owner(None, q)
            return rec
    else:
        approved, any_match = _match_by_topic(q, doc)
        if len(approved) == 1:
            entry = approved[0]
        elif len(approved) > 1:
            rec.update(status="unsupported",
                       reason=f"ambiguous match: {len(approved)} approved answers for topic "
                              f"{q.get('topic')!r}; content owner must select one")
            rec["owner"], rec["owner_role"] = _route_owner(approved[0], q)
            return rec
        elif any_match:
            entry = any_match[0]  # only non-approved candidates exist -> handled below
        else:
            rec.update(status="unsupported",
                       reason=f"no approved content for topic {q.get('topic')!r}")
            rec["owner"], rec["owner_role"] = _route_owner(None, q)
            return rec

    rec["answer_id"] = entry.get("answer_id")
    rec["owner"], rec["owner_role"] = _route_owner(entry, q)
    rec["effective_date"], rec["expires"] = entry.get("effective_date"), entry.get("expires")

    # 2. approved-source gate (never draft from non-approved content)
    if entry.get("approval_status", "approved") != "approved":
        rec.update(status="unapproved-source", source_approved=False,
                   reason=f"content {entry.get('answer_id')!r} is {entry.get('approval_status')!r}, "
                          f"not approved; route to owner for approval before use",
                   citations=[entry.get("source_ref")])
        return rec

    rec["source_approved"] = True

    # 3. data requirement (a required data point must exist and be fresh)
    if q.get("data_request"):
        dp = data_index.get(q["data_request"])
        if dp is None:
            rec.update(status="data-gap",
                       reason=f"required data point {q['data_request']!r} not provided; route to data owner")
            return rec
        if _is_stale(dp, as_of):
            rec.update(status="data-gap",
                       reason=f"data point {q['data_request']!r} is stale (expires {dp.get('expires')} "
                              f"before as_of {as_of}); route to data owner",
                       citations=[dp.get("source_ref")])
            return rec
        rec["data_cited"] = True
        rec["data_id"] = dp.get("data_id")
        rec["citations"].append(dp.get("source_ref"))

    # 4. freshness of the content entry itself (stale-language detection)
    rec["text"] = entry.get("text")
    rec["citations"].insert(0, entry.get("source_ref"))
    if _is_stale(entry, as_of):
        rec.update(status="stale",
                   reason=f"content effective {entry.get('effective_date')} expired {entry.get('expires')} "
                          f"before as_of {as_of}; drafted but must be refreshed by the owner")
    else:
        rec["status"] = "drafted"
    return rec


def assemble(doc: dict) -> dict:
    as_of = doc.get("as_of_date")
    pool = _candidate_pool(doc)
    data_index = {d.get("data_id"): d for d in (doc.get("data_points") or [])}
    client = doc.get("client") or {}

    responses = [respond_question(q, doc, pool, data_index, as_of) for q in doc.get("questions") or []]

    open_items: list = []
    citations: list = []
    data_appendix: list = []
    used_data = set()

    for r in responses:
        for c in r.get("citations") or []:
            if c:
                citations.append(c)
        if r["status"] == "stale":
            open_items.append({"item": r["question_id"], "type": "stale-answer", "owner": r["owner"],
                               "citation": (r["citations"] or [None])[0],
                               "action": "refresh the answer with current approved content"})
        elif r["status"] == "unapproved-source":
            open_items.append({"item": r["question_id"], "type": "unapproved-source", "owner": r["owner"],
                               "citation": (r["citations"] or [None])[0],
                               "action": "obtain content-owner approval before this answer may be used"})
        elif r["status"] == "data-gap":
            open_items.append({"item": r["question_id"], "type": "data-gap", "owner": r["owner"],
                               "citation": (r["citations"] or [None])[0],
                               "action": "provide the required, in-date data point"})
        elif r["status"] == "unsupported":
            open_items.append({"item": r["question_id"], "type": "unsupported-question", "owner": r["owner"],
                               "action": "route to the content owner to author an approved answer"})
        # build data appendix for cited, fresh data
        if r["data_cited"] and r.get("data_id") and r["data_id"] not in used_data:
            dp = data_index.get(r["data_id"])
            if dp:
                used_data.add(r["data_id"])
                data_appendix.append({"data_id": dp.get("data_id"), "label": dp.get("label"),
                                      "value": dp.get("value"), "as_of": dp.get("as_of"),
                                      "citation": dp.get("source_ref")})

    # disclosures: carry over the input's required disclosures, then inject the standard
    # performance disclosure whenever any answer cites performance/data.
    disclosures = [dict(d) for d in (doc.get("required_disclosures") or []) if d.get("trigger") in (None, "always")]
    data_cited_any = any(r["data_cited"] for r in responses)
    if data_cited_any and not any(STANDARD_PERF_DISCLOSURE in (d.get("text") or "") for d in disclosures):
        disclosures.append({"id": "perf-standard", "text": STANDARD_PERF_DISCLOSURE,
                            "trigger": "performance-data", "source_ref": "policy:disclosure-standard"})
    for d in disclosures:
        if d.get("source_ref"):
            citations.append(d["source_ref"])

    # approvals: capture recorded, then mark required-but-missing as outstanding
    recorded_types = set()
    approvals = {"recorded": [], "outstanding": []}
    for a in doc.get("approvals") or []:
        if a.get("status") == "recorded":
            rec = {"type": a.get("type"), "approver_role": a.get("approver_role"),
                   "approver": _mask_id(a.get("approver")), "date": a.get("date"),
                   "citation": a.get("source_ref")}
            approvals["recorded"].append(rec)
            recorded_types.add(a.get("type"))
            if rec["citation"]:
                citations.append(rec["citation"])
        else:
            approvals["outstanding"].append({"type": a.get("type"), "status": a.get("status") or "outstanding"})
    for req_ap in doc.get("required_approvals") or []:
        if req_ap not in recorded_types:
            if not any(o.get("type") == req_ap for o in approvals["outstanding"]):
                approvals["outstanding"].append({"type": req_ap, "status": "outstanding"})
            open_items.append({"item": req_ap, "type": "outstanding-approval",
                               "owner": "Compliance / Product",
                               "action": "obtain the required approval before delivery"})

    # dedup source index preserving order
    seen, source_index = set(), []
    for c in citations:
        if c and c not in seen:
            seen.add(c)
            source_index.append(c)

    counts = {s: sum(1 for r in responses if r["status"] == s)
              for s in ("drafted", "stale", "unapproved-source", "data-gap", "unsupported")}

    sections = {
        "response_summary": {
            "questionnaire_id": doc.get("questionnaire_id"),
            "product": doc.get("product"),
            "strategy": doc.get("strategy"),
            "jurisdiction": doc.get("jurisdiction"),
            "as_of_date": as_of,
            "client_masked": _mask_id(client.get("client_id")),
            "counts": {**counts, "questions_total": len(responses),
                       "open_items_total": len(open_items),
                       "approvals_recorded": len(approvals["recorded"]),
                       "approvals_outstanding": len(approvals["outstanding"])},
        },
        "respondent_profile": {
            "product": doc.get("product"), "strategy": doc.get("strategy"),
            "jurisdiction": doc.get("jurisdiction"),
            "client_type": client.get("type"), "client_masked": _mask_id(client.get("client_id")),
        },
        "responses": responses,
        "data_appendix": data_appendix,
        "disclosures": disclosures,
        "approvals": approvals,
        "open_items": open_items,
        "source_index": source_index,
    }

    return {
        "config_version": doc.get("config_version"),
        "questionnaire_id": doc.get("questionnaire_id"),
        "product": doc.get("product"),
        "jurisdiction": doc.get("jurisdiction"),
        "as_of_date": as_of,
        "template_version": doc.get("template_version", TEMPLATE_VERSION),
        "draft_status": "draft-assembled",
        "human_approval_required_before_delivery": True,
        "question_count": len(responses),
        "sections": sections,
        "open_items": open_items,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ddq_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
