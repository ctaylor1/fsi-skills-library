#!/usr/bin/env python3
"""Deterministic output validation for buyer-investor-list-builder.

Enforces the Draft-&-package guardrails before a buyer/investor list is presented:
  1. All required template sections are present (matches assets/output-template.md).
  2. NO unsupported claims in the delivered list: every candidate in `buyer_list` carries at
     least one rationale item, and every rationale item has a citation whose source_doc
     resolves to a document in `source_index`. No candidate recorded in the top-level
     `unsupported_claims` ledger may also appear in the delivered `buyer_list`.
  3. Fit-score -> outreach-wave tie-out for every wave-placed candidate.
  4. Restricted / conflicts control: any candidate flagged `restricted` or `conflict` MUST be
     `hold-conflicts-review` and MUST NOT appear in any outreach wave (fail closed).
  5. Required approvals recorded (deal_lead + conflicts_reviewer); `external_delivery` may be
     true only when both are `approved` (with approver + date).
  6. No send / deliver / share / buyer-outreach-execution language (draft-only; never contacts).
  7. No investment-recommendation / valuation-opinion / advice language (R2).
  8. The standing note is present.

Usage: python validate_output.py list.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "cover", "executive_summary", "fit_criteria", "source_index", "buyer_list",
    "outreach_waves", "conflicts_hold", "gaps", "approvals", "standing_note",
]
WAVE_DISPOSITIONS = {"wave-1-priority", "wave-2-standard", "wave-3-broaden"}
ALLOWED_DISPOSITIONS = WAVE_DISPOSITIONS | {"hold-conflicts-review"}
REQUIRED_APPROVAL_ROLES = ["deal_lead", "conflicts_reviewer"]
WAVE1_MIN, WAVE2_MIN = 8, 4
STANDING_NOTE_KEY = "draft buyer/investor list for internal review only"

SEND_PATTERNS = [
    r"\bsend\b.{0,30}\b(list|universe|buyers?|it)\b",
    r"\b(deliver(ed)?|share(d)?|circulat(e|ed))\b.{0,30}\bto the (client|counterparty|seller|buyer|board|counterpart)\b",
    r"\bemail\b.{0,30}\b(list|it)\b.{0,20}\bto\b",
    r"\bsubmit(ted)?\b.{0,30}\b(list|universe)\b",
    r"\b(contact|reach out to|call|approach|solicit|market to)\b.{0,20}\b(the )?(buyers?|sponsors?|investors?|candidates?)\b",
    r"\b(begin|start|initiate|launch|kick off)\b.{0,20}\boutreach\b",
]
ADVICE_PATTERNS = [
    r"\brecommend\b.{0,40}\b(acquire|acquiring|buy|buying|sell|selling|the acquisition|the deal|proceed|proceeding|accept)\b",
    r"\bshould\b.{0,20}\b(acquire|buy|sell|proceed with the (deal|acquisition)|accept)\b",
    r"\b(strong |our )?(buy|sell|hold) recommendation\b",
    r"\binvestment recommendation\b",
    r"\bprice target\b",
    r"\bwe value the (target|company|business) at\b",
    r"\bfair value (is|of)\b",
    r"\bguaranteed returns?\b",
    r"\bvaluation opinion\b",
]


def _expected_wave(score) -> str:
    if score >= WAVE1_MIN:
        return "wave-1-priority"
    if score >= WAVE2_MIN:
        return "wave-2-standard"
    return "wave-3-broaden"


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

    doc_ids = {s.get("doc_id") for s in (doc.get("source_index") or []) if s.get("doc_id")}
    buyer_list = doc.get("buyer_list") or []
    if not buyer_list:
        errors.append("buyer_list is empty (no candidates were placed or held)")

    listed_ids = {c.get("candidate_id") for c in buyer_list}

    for c in buyer_list:
        cid = c.get("candidate_id", "?")
        disp = c.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{cid}: disallowed disposition {disp!r}")

        # 2. no unsupported claims in the delivered list
        rationale = c.get("rationale") or []
        if not rationale:
            errors.append(f"{cid}: no rationale (unsupported candidate may not be listed)")
        for r in rationale:
            if not r.get("citation"):
                errors.append(f"{cid}: rationale claim missing citation")
            if r.get("source_doc") not in doc_ids:
                errors.append(f"{cid}: unsupported claim - source_doc {r.get('source_doc')!r} not in source index")

        restricted = bool(c.get("restricted"))
        conflict = bool(c.get("conflict"))

        # 3. fit-score -> wave tie-out
        if disp in WAVE_DISPOSITIONS:
            exp = _expected_wave(c.get("fit_score", 0))
            if disp != exp:
                errors.append(f"{cid}: disposition {disp!r} != expected {exp!r} for fit_score {c.get('fit_score')}")
            # 4. restricted/conflict must never sit in a wave
            if restricted or conflict:
                errors.append(f"{cid}: restricted/conflicted candidate placed in an outreach wave (must hold-conflicts-review)")
        elif disp == "hold-conflicts-review":
            if not (restricted or conflict):
                errors.append(f"{cid}: hold-conflicts-review without a restricted/conflict flag")

    # 4b. no held candidate leaks into the wave id-lists
    waves = doc.get("outreach_waves") or {}
    held_ids = {c.get("candidate_id") for c in buyer_list
                if bool(c.get("restricted")) or bool(c.get("conflict"))}
    for wave_key, ids in waves.items():
        for wid in ids or []:
            if wid in held_ids:
                errors.append(f"{wid}: held (restricted/conflict) candidate present in {wave_key}")

    # 2b. an unsupported-claim candidate must not be delivered in the list
    for u in doc.get("unsupported_claims") or []:
        if u.get("candidate_id") in listed_ids:
            errors.append(f"{u.get('candidate_id')}: candidate with an unsupported claim appears in the delivered buyer_list")

    # 5. required approvals recorded + external-delivery gate
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

    # 6 & 7. prohibited language (draft-only; no outreach; no advice/valuation)
    blob = _narrative_blob(doc)
    for pat in SEND_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            errors.append(f"send/outreach-execution language detected: {m.group(0)!r} (draft never delivers or contacts buyers)")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            errors.append(f"investment recommendation/valuation-opinion language detected: {m.group(0)!r}")

    # 8. standing note
    if STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")

    return errors


def main(argv) -> int:
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "list_example.json"
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
