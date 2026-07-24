#!/usr/bin/env python3
"""Deterministic output validation for investment-source-ingester.

Validates the canonical source index + rejected queue before it is presented, delivered, or
written to a research library. Enforces the schema, lineage, rejected-record handling, the
entitlement boundary, and the R2/Utility tier boundary. Fails closed on any miss.

Checks:
  1. Schema/lineage — every index item has a durable source_id, source_ref, content_hash, a
     timestamp (published_at or effective_date), and ingested_at.
  2. Entitlement boundary — every index item is entitlement_status 'permitted' with a class in
     {public, licensed, internal}; a 'restricted' or otherwise non-permitted item is a hard
     failure; licensed/internal items must carry a grant_ref.
  3. Identity — source_ids are unique (identities are never merged); a duplicate_of must point
     at a canonical member present in the index and must not be self-referential.
  4. Counts tie-out — counts.{accepted,rejected,duplicates} match the arrays.
  5. Rejected-record handling — every rejected record carries a source_ref and a known reason.
  6. Tier boundary — no investment-advice/decision language and no inferred-permission language
     in the skill's free-text fields.
  7. The standing disclaimer is present.

Usage:
  python validate_output.py index.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ACCEPTED_CLASSES = {"public", "licensed", "internal"}
GRANT_REQUIRED = {"licensed", "internal"}
REJECT_REASONS = {
    "no_entitlement_declared", "unknown_entitlement_class", "restricted_content",
    "missing_grant_ref", "expired_entitlement",
}
DISCLAIMER = (
    "Source index only; entitlement is classified from explicitly declared grants and is never "
    "inferred. Restricted or undeclared sources are rejected, not ingested. No investment advice, "
    "valuation, rating, or trading decision is produced."
)
# R2 Utility must not produce an investment view or decision.
ADVICE_PATTERNS = [
    r"\bprice target\b", r"\b(buy|sell|hold|overweight|underweight)\s+(rating|recommendation)\b",
    r"\bwe recommend (buying|selling|shorting|holding)\b", r"\b(materially )?(under|over)valued\b",
    r"\btrade (recommendation|idea)\b", r"\binvestment recommendation\b",
    r"\binitiate coverage with\b", r"\b(sell|buy) the (stock|position|name)\b",
]
# Permission is declared, never inferred.
INFERENCE_PATTERNS = [
    r"\binferred (entitlement|permission|license|licence)\b",
    r"\bassumed (permitted|licensed|entitled)\b", r"\bpresumed (permitted|licensed)\b",
    r"\bpermission (was )?inferred\b", r"\btreat(ed)? as permitted\b",
]


def _txt(pack: dict) -> str:
    parts = [str(pack.get("summary", "")), str(pack.get("notes", ""))]
    for h in pack.get("handoff_hints") or []:
        parts.append(str(h.get("note", "")))
    return " ".join(parts)


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    index = pack.get("index")
    rejected = pack.get("rejected")
    if not isinstance(index, list):
        errors.append("missing 'index' array")
        index = []
    if not isinstance(rejected, list):
        errors.append("missing 'rejected' array")
        rejected = []

    seen_ids: set = set()
    for it in index:
        sid = it.get("source_id")
        tag = f"index item {sid or it.get('source_ref', '?')}"
        for k in ("source_id", "source_ref", "content_hash", "ingested_at"):
            if not it.get(k):
                errors.append(f"{tag}: missing '{k}' (lineage)")
        if not (it.get("published_at") or it.get("effective_date")):
            errors.append(f"{tag}: no timestamp (published_at or effective_date)")

        cls = str(it.get("entitlement_class", "")).strip().lower()
        if cls == "restricted":
            errors.append(f"{tag}: entitlement_class 'restricted' must never be ingested")
        elif cls not in ACCEPTED_CLASSES:
            errors.append(f"{tag}: entitlement_class {cls!r} not permitted (must be public/licensed/internal)")
        if it.get("entitlement_status") != "permitted":
            errors.append(f"{tag}: entitlement_status {it.get('entitlement_status')!r} != 'permitted'")
        if cls in GRANT_REQUIRED and not str(it.get("grant_ref") or "").strip():
            errors.append(f"{tag}: {cls} source missing grant_ref")

        if sid in seen_ids:
            errors.append(f"{tag}: duplicate source_id — identities must never be merged")
        seen_ids.add(sid)

    canon = {it.get("source_id") for it in index if it.get("canonical")}
    dup_items = [it for it in index if it.get("duplicate_of")]
    for it in dup_items:
        if it.get("canonical"):
            errors.append(f"index item {it.get('source_id')}: duplicate_of set but marked canonical")
        if it.get("duplicate_of") == it.get("source_id"):
            errors.append(f"index item {it.get('source_id')}: duplicate_of is self-referential")
        elif it.get("duplicate_of") not in canon:
            errors.append(f"index item {it.get('source_id')}: duplicate_of points at unknown canonical")

    counts = pack.get("counts") or {}
    if counts.get("accepted") != len(index):
        errors.append(f"counts.accepted {counts.get('accepted')} != len(index) {len(index)}")
    if counts.get("rejected") != len(rejected):
        errors.append(f"counts.rejected {counts.get('rejected')} != len(rejected) {len(rejected)}")
    if counts.get("duplicates") != len(dup_items):
        errors.append(f"counts.duplicates {counts.get('duplicates')} != duplicate index items {len(dup_items)}")

    for r in rejected:
        if not r.get("source_ref"):
            errors.append("rejected record missing source_ref")
        if r.get("reject_reason") not in REJECT_REASONS:
            errors.append(f"rejected record has unknown reject_reason {r.get('reject_reason')!r}")

    text = _txt(pack)
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"investment-advice/decision language detected: {m.group(0)!r} (R2 indexes, does not advise)")
    for pat in INFERENCE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"inferred-permission language detected: {m.group(0)!r} (entitlement is declared, never inferred)")

    if DISCLAIMER.lower() not in str(pack.get("disclaimer", "")).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "source_index.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
