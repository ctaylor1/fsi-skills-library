#!/usr/bin/env python3
"""Deterministic entitlement classification, dedup, timestamping, and indexing for
investment-source-ingester.

Reads a source manifest (see validate_input.py), then for each source:
  1. classifies entitlement from the DECLARED grant only (never inferred);
  2. rejects — fail closed — any source that is restricted, undeclared, unknown-class,
     licensed/internal without a grant_ref, or past its entitlement expiry;
  3. assigns durable source_id (per source identity) and a durable job_id (per run);
  4. timestamps ingestion deterministically from as_of and records published/effective dates;
  5. deduplicates by content_hash WITHOUT merging identities — the highest-authority copy is
     marked canonical, the rest carry duplicate_of pointing at it (both keep their source_id).

Emits a canonical source index + a rejected-record queue. It NEVER parses financial content,
values a security, or produces any investment view — those belong to downstream skills.
The entitlement rules and source hierarchy are documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py manifest.json   # prints the index JSON to stdout
  python calculate_or_transform.py --selftest      # runs self-checks over the bundled fixture
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

# Source hierarchy (authority rank; lower = more authoritative). Drives dedup tie-break.
AUTHORITY = {
    "filing": 1, "press_release": 2, "presentation": 3,
    "transcript": 4, "market_data": 5, "internal_research": 6,
}
ACCEPTED_CLASSES = ("public", "licensed", "internal")
GRANT_REQUIRED = ("licensed", "internal")
REJECT_REASONS = (
    "no_entitlement_declared", "unknown_entitlement_class", "restricted_content",
    "missing_grant_ref", "expired_entitlement",
)
# Deterministic candidate-handoff map (a human routes; the ingester never executes a handoff).
HANDOFF_HINTS = {
    "filing": ("financials-normalizer", "candidate: filing may carry financial statements to normalize"),
    "press_release": ("financials-normalizer", "candidate: release may carry financial tables to normalize"),
    "presentation": ("financials-normalizer", "candidate: deck may carry financial schedules to normalize"),
    "market_data": ("security-master-enricher", "candidate: instrument records may need identifier enrichment"),
}
DISCLAIMER = (
    "Source index only; entitlement is classified from explicitly declared grants and is never "
    "inferred. Restricted or undeclared sources are rejected, not ingested. No investment advice, "
    "valuation, rating, or trading decision is produced."
)


def _sha1(s: str) -> str:
    return hashlib.sha1(str(s).encode("utf-8")).hexdigest()


def _source_id(source_ref: str) -> str:
    return "src-" + _sha1(source_ref)[:12]


def _job_id(job_ref: str, as_of: str) -> str:
    return f"isi-{as_of}-{_sha1(job_ref)[:8]}"


def _ts(s: dict) -> str:
    return str(s.get("published_at") or s.get("effective_date") or "")


def classify(src: dict, as_of: str) -> tuple[str, str | None, dict]:
    """Return (verdict, reject_reason, entitlement). verdict is 'accept' or 'reject'.

    Permission is only ever read from the declared entitlement block — never inferred from
    doc_type, issuer, or source. Any gap fails closed to a reject reason.
    """
    ent = src.get("entitlement") or {}
    cls = str(ent.get("class", "")).strip().lower()
    if not cls:
        return "reject", "no_entitlement_declared", ent
    if cls == "restricted":
        return "reject", "restricted_content", ent
    if cls not in ACCEPTED_CLASSES:
        return "reject", "unknown_entitlement_class", ent
    if cls in GRANT_REQUIRED and not str(ent.get("grant_ref", "")).strip():
        return "reject", "missing_grant_ref", ent
    expires = ent.get("expires")
    if expires and str(expires)[:10] < str(as_of)[:10]:
        return "reject", "expired_entitlement", ent
    return "accept", None, ent


def compute(doc: dict) -> dict:
    as_of = str(doc["as_of"])
    job_id = _job_id(str(doc["job_ref"]), as_of)
    accepted, rejected = [], []

    for s in doc.get("sources", []):
        verdict, reason, ent = classify(s, as_of)
        if verdict == "reject":
            rejected.append({
                "source_ref": s.get("source_ref"),
                "doc_type": s.get("doc_type"),
                "issuer": s.get("issuer"),
                "reject_reason": reason,
                "detail": f"declared class={str(ent.get('class', '')).strip().lower() or '(none)'}",
            })
            continue
        cls = str(ent.get("class", "")).strip().lower()
        accepted.append({
            "source_id": _source_id(str(s["source_ref"])),
            "source_ref": s.get("source_ref"),
            "issuer": s.get("issuer"),
            "doc_type": s.get("doc_type"),
            "title": s.get("title"),
            "entitlement_status": "permitted",
            "entitlement_class": cls,
            "grant_ref": str(ent.get("grant_ref", "")).strip() or None,
            "redistribution": ent.get("redistribution"),
            "published_at": s.get("published_at"),
            "effective_date": s.get("effective_date"),
            "ingested_at": as_of,
            "content_hash": s.get("content_hash"),
            "language": s.get("language"),
            "canonical": True,
            "duplicate_of": None,
        })

    # Deduplicate by content_hash without merging identities.
    by_hash: dict = {}
    for item in accepted:
        by_hash.setdefault(item["content_hash"], []).append(item)
    duplicates = 0
    for group in by_hash.values():
        if len(group) < 2:
            continue
        ordered = sorted(group, key=lambda it: (
            AUTHORITY.get(it["doc_type"], 99),
            _ts_of_item(it),
            str(it["source_ref"]),
        ))
        canonical = ordered[0]
        for dup in ordered[1:]:
            dup["canonical"] = False
            dup["duplicate_of"] = canonical["source_id"]
            duplicates += 1

    handoff_hints = []
    for item in accepted:
        if item["canonical"] and item["doc_type"] in HANDOFF_HINTS:
            skill, note = HANDOFF_HINTS[item["doc_type"]]
            handoff_hints.append({
                "source_id": item["source_id"],
                "doc_type": item["doc_type"],
                "candidate_skill": skill,
                "note": note + " — a human routes; the ingester does not parse content or execute the handoff",
            })

    return {
        "job_id": job_id,
        "as_of": as_of,
        "catalog_version": doc.get("catalog_version"),
        "requested_by": doc.get("requested_by"),
        "counts": {"accepted": len(accepted), "rejected": len(rejected), "duplicates": duplicates},
        "index": accepted,
        "rejected": rejected,
        "handoff_hints": handoff_hints,
        "summary": (
            f"Indexed {len(accepted)} permitted source(s) ({duplicates} duplicate(s) linked, not merged); "
            f"{len(rejected)} source(s) rejected to the queue by declared-entitlement rules."
        ),
        "disclaimer": DISCLAIMER,
    }


def _ts_of_item(item: dict) -> str:
    return str(item.get("published_at") or item.get("effective_date") or "")


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "source_manifest.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = compute(doc)
    errors: list[str] = []

    idx, rej = out["index"], out["rejected"]
    c = out["counts"]
    if c["accepted"] != len(idx):
        errors.append(f"counts.accepted {c['accepted']} != len(index) {len(idx)}")
    if c["rejected"] != len(rej):
        errors.append(f"counts.rejected {c['rejected']} != len(rejected) {len(rej)}")
    dup_items = [it for it in idx if it.get("duplicate_of")]
    if c["duplicates"] != len(dup_items):
        errors.append(f"counts.duplicates {c['duplicates']} != duplicate index items {len(dup_items)}")

    # No restricted/undeclared content ever reaches the index.
    for it in idx:
        if it["entitlement_class"] not in ACCEPTED_CLASSES:
            errors.append(f"index item {it['source_id']} has non-permitted class {it['entitlement_class']!r}")

    # Identity is preserved: source_ids are unique and deterministic.
    sids = [it["source_id"] for it in idx]
    if len(sids) != len(set(sids)):
        errors.append("duplicate source_id in index — identities must never be merged")
    for it in idx:
        if it["source_id"] != _source_id(str(it["source_ref"])):
            errors.append(f"source_id for {it['source_ref']} is not deterministic")

    # Every duplicate points at a canonical member that is itself in the index.
    canon = {it["source_id"] for it in idx if it["canonical"]}
    for it in dup_items:
        if it["duplicate_of"] not in canon:
            errors.append(f"duplicate {it['source_id']} points at non-canonical {it['duplicate_of']}")

    # Golden expectations over the bundled fixture (deterministic contract).
    if c["accepted"] != 6:
        errors.append(f"expected 6 accepted, got {c['accepted']}")
    if c["rejected"] != 4:
        errors.append(f"expected 4 rejected, got {c['rejected']}")
    if c["duplicates"] != 1:
        errors.append(f"expected 1 duplicate, got {c['duplicates']}")
    reasons = {r["reject_reason"] for r in rej}
    expected_reasons = {"restricted_content", "no_entitlement_declared", "missing_grant_ref", "expired_entitlement"}
    missing = expected_reasons - reasons
    if missing:
        errors.append(f"missing expected reject reasons: {sorted(missing)}")
    for r in rej:
        if r["reject_reason"] not in REJECT_REASONS:
            errors.append(f"unknown reject_reason {r['reject_reason']!r}")

    for e in errors:
        print("ERROR", e)
    print(f"ingest self-check: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
