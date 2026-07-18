#!/usr/bin/env python3
"""Deterministic input validation for due-diligence-questionnaire-responder.

Validates a DDQ/RFP intake bundle before drafting. Fails closed on structural problems; warns
on data gaps that will surface as open items (questions with no approved answer, expired
content, missing required data points, unrecorded required approvals).

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, questionnaire_id, product, jurisdiction, as_of_date, template_version,
  client{client_id, name, type}, required_approvals[], required_disclosures[],
  content_library[{answer_id, topic, keywords[], text, owner, owner_role, effective_date,
                   expires, approval_status, source_ref, data_refs[]}],
  prior_answers[{answer_id, topic, text, owner, effective_date, approval_status, source_ref}],
  data_points[{data_id, label, value, as_of, expires, owner, source_ref}],
  approvals[{approval_id, type, approver_role, approver, status, date, source_ref}],
  questions[{question_id, section, text, topic, required, matched_answer_id, data_request}]

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "questionnaire_id", "as_of_date", "content_library", "questions")
REQUIRED_LIB = ("answer_id", "text", "source_ref")
REQUIRED_Q = ("question_id", "text")
APPROVAL_STATES = {"approved", "draft", "expired", "in-review"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    library = doc.get("content_library")
    if not isinstance(library, list) or not library:
        errors.append("content_library must be a non-empty list")
        return errors, warnings

    # index answers (library + prior) and check structure
    answer_ids = set()
    approved_topics: dict = {}
    for pool_name, key in (("content_library", "content_library"), ("prior_answers", "prior_answers")):
        for i, e in enumerate(doc.get(key) or []):
            tag = f"{key}[{i}] ({e.get('answer_id','?')})"
            for f in REQUIRED_LIB:
                if f not in e or e[f] in (None, ""):
                    errors.append(f"{tag}: missing '{f}'")
            aid = e.get("answer_id")
            if aid in answer_ids:
                warnings.append(f"{tag}: duplicate answer_id across pools -> library entry wins")
            answer_ids.add(aid)
            st = e.get("approval_status", "approved")
            if st not in APPROVAL_STATES:
                warnings.append(f"{tag}: approval_status {st!r} not recognized -> treated as non-approved")
            if not e.get("effective_date"):
                warnings.append(f"{tag}: no effective_date -> freshness cannot be evaluated")
            if st == "approved" and e.get("topic"):
                approved_topics.setdefault(e.get("topic"), []).append(aid)

    data_ids = {d.get("data_id") for d in (doc.get("data_points") or [])}

    questions = doc.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append("questions must be a non-empty list")
        return errors, warnings

    seen_q = set()
    for i, q in enumerate(questions):
        tag = f"questions[{i}] ({q.get('question_id','?')})"
        for f in REQUIRED_Q:
            if f not in q or q[f] in (None, ""):
                errors.append(f"{tag}: missing '{f}'")
        qid = q.get("question_id")
        if qid in seen_q:
            errors.append(f"{tag}: duplicate question_id")
        seen_q.add(qid)
        mid = q.get("matched_answer_id")
        if mid and mid not in answer_ids:
            warnings.append(f"{tag}: matched_answer_id {mid!r} not in content -> will be unsupported")
        if not mid:
            topic = q.get("topic")
            n = len(approved_topics.get(topic, []))
            if n == 0:
                warnings.append(f"{tag}: no approved answer for topic {topic!r} -> unsupported (route to owner)")
            elif n > 1:
                warnings.append(f"{tag}: {n} approved answers for topic {topic!r} -> ambiguous (route to owner)")
        if q.get("data_request") and q["data_request"] not in data_ids:
            warnings.append(f"{tag}: data_request {q['data_request']!r} not in data_points -> data-gap")

    for i, a in enumerate(doc.get("approvals") or []):
        if not a.get("type") or not a.get("status"):
            errors.append(f"approvals[{i}]: requires 'type' and 'status'")
        if a.get("status") == "recorded" and not a.get("source_ref"):
            errors.append(f"approvals[{i}] ({a.get('type','?')}): recorded approval missing 'source_ref'")

    if not doc.get("required_approvals"):
        warnings.append("no required_approvals configured -> approval capture limited")
    if doc.get("approvals") is None:
        warnings.append("no approvals provided -> all required approvals will be outstanding")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ddq_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
