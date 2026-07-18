#!/usr/bin/env python3
"""Deterministic output validation for due-diligence-packager.

Enforces the Draft-&-package guardrails before a diligence pack is presented:
  1. All required template sections are present (matches assets/output-template.md).
  2. NO unsupported claims: `unsupported_claims` is empty AND every extracted-data / issue
     item carries a citation whose source_doc resolves to a document in `source_index`.
  3. Model-handoff targets are known modeling skills (no invented downstream skill).
  4. Required approvals are recorded (diligence_lead + quality_reviewer); `external_delivery`
     may be true only when both are `approved` (with approver + date).
  5. No send / submit / external-delivery language (draft-only; the skill never delivers).
  6. No valuation-opinion / investment-recommendation / advice language (R2).
  7. The standing note is present.

Usage: python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "cover", "executive_summary", "source_index", "extracted_data", "issue_log",
    "open_questions", "completeness", "model_handoffs", "approvals", "standing_note",
]
KNOWN_MODEL_TARGETS = {
    "three-statement-model-builder", "dcf-modeler", "lbo-model-builder",
    "merger-model-builder", "comps-analysis-builder", "scenario-sensitivity-generator",
}
REQUIRED_APPROVAL_ROLES = ["diligence_lead", "quality_reviewer"]
STANDING_NOTE_KEY = "draft diligence pack for internal review only"

SEND_PATTERNS = [
    r"\bsend\b.{0,30}\b(pack|report|memo|it)\b.{0,30}\bto the (buyer|seller|counterparty|client|counterpart)\b",
    r"\bsubmit(ted)?\b.{0,30}\b(pack|report|memo)\b",
    r"\bemail\b.{0,30}\b(pack|report|memo|it)\b.{0,20}\bto\b",
    r"\b(deliver(ed)?|sent|share(d)?)\b.{0,30}\bto the (buyer|seller|counterparty|client)\b",
    r"\bsend it to the (buyer|seller|counterparty|client)\b",
]
ADVICE_PATTERNS = [
    r"\brecommend\b.{0,40}\b(acquire|acquiring|buy|buying|sell|selling|the acquisition|the deal|proceed|proceeding)\b",
    r"\bshould\b.{0,20}\b(acquire|buy|sell|proceed with the acquisition)\b",
    r"\b(strong |our )?(buy|sell|hold) recommendation\b",
    r"\binvestment recommendation\b",
    r"\bprice target\b",
    r"\bwe value the (target|company|business) at\b",
    r"\bfair value (is|of)\b",
    r"\bguaranteed returns?\b",
    r"\bvaluation opinion\b",
]


def _narrative_blob(doc: dict) -> str:
    parts = []
    for k in ("executive_summary", "narrative", "notes", "cover_note", "summary"):
        v = doc.get(k)
        if isinstance(v, str):
            parts.append(v)
    return " ".join(parts)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    # 1. required sections
    sections = doc.get("sections") or []
    for s in REQUIRED_SECTIONS:
        if s not in sections:
            errors.append(f"missing required section: {s}")

    # 2. no unsupported claims
    doc_ids = {s.get("doc_id") for s in (doc.get("source_index") or []) if s.get("doc_id")}
    if doc.get("unsupported_claims"):
        errors.append(f"unsupported claims present: {len(doc['unsupported_claims'])} (every data point must cite an indexed source)")
    for e in doc.get("extracted_data") or []:
        field = e.get("field", "?")
        if not e.get("citation"):
            errors.append(f"extracted_data '{field}': missing citation")
        if e.get("source_doc") not in doc_ids:
            errors.append(f"unsupported claim (extraction) '{field}': source_doc {e.get('source_doc')!r} not in source index")
    for i in doc.get("issue_log") or []:
        iid = i.get("issue_id", "?")
        if not i.get("citation"):
            errors.append(f"issue_log '{iid}': missing citation")
        if i.get("source_doc") not in doc_ids:
            errors.append(f"unsupported claim (issue) '{iid}': source_doc {i.get('source_doc')!r} not in source index")

    # 3. model-handoff targets known
    for m in doc.get("model_handoffs") or []:
        t = m.get("target_skill")
        if t not in KNOWN_MODEL_TARGETS:
            errors.append(f"model-handoff target {t!r} is not a known modeling skill (invalid handoff)")

    # 4. required approvals recorded + external-delivery gate
    ledger = {a.get("role"): a for a in (doc.get("approvals") or []) if isinstance(a, dict)}
    for role in REQUIRED_APPROVAL_ROLES:
        a = ledger.get(role)
        if not a:
            errors.append(f"missing required approval: {role}")
        elif a.get("status") not in ("pending", "approved"):
            errors.append(f"approval {role}: invalid/unrecorded status {a.get('status')!r}")
    if doc.get("external_delivery") is True:
        for role in REQUIRED_APPROVAL_ROLES:
            a = ledger.get(role) or {}
            if a.get("status") != "approved":
                errors.append(f"external_delivery=true but approval {role} not approved (draft may not be marked deliverable)")
            elif not a.get("date"):
                errors.append(f"external_delivery=true but approval {role} missing approval date")

    # 5 & 6. prohibited language (draft-only; no advice/recommendation)
    blob = _narrative_blob(doc)
    for pat in SEND_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            errors.append(f"send/submit/external-delivery language detected: {m.group(0)!r} (draft never delivers)")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            errors.append(f"investment recommendation/valuation-opinion language detected: {m.group(0)!r}")

    # 7. standing note
    if STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")

    return errors


def main(argv) -> int:
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
