#!/usr/bin/env python3
"""Deterministic output validation for holdings-transaction-normalizer.

Validates a canonical pack (calculate_or_transform.py output + any narrative/notes) before it
is presented or delivered. This is the R2 / Utility fail-closed gate. It enforces:

  1. Reconciliation ties out: input == canonical + rejected, and each count equals the actual
     list length. No source record may be silently dropped.
  2. Every canonical record has a complete lineage envelope and a unique canonical_id, and the
     canonical body carries the required fields for its record_type.
  3. HARD BOUNDARY — no identity merge: each canonical record derives from exactly one
     source_record_id (a scalar). A list of ids, a merge separator, or a merged_from/
     merged_source_ids key fails closed.
  4. HARD BOUNDARY — no source overwrite: every canonical AND rejected record carries an
     immutable source_hash; any source-mutation flag fails closed.
  5. Every rejected record carries reason_code, reason, source_record_id, and source_hash.
  6. No prohibited normalization/advice language (chose the canonical value, resolved the
     conflict, merged identities, overwrote the source, buy/sell recommendation) in the
     free-text narrative/notes.
  7. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise (line ends "N error(s)").
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_FIELDS = {
    "position": ["account_id", "security_id", "quantity", "currency"],
    "cash": ["account_id", "currency", "amount"],
    "order": ["account_id", "order_ref", "side", "security_id", "quantity", "currency"],
    "transaction": ["account_id", "txn_ref", "txn_type", "amount", "currency", "trade_date"],
}
LINEAGE_KEYS = ("source_system", "source_record_id", "source_as_of", "ruleset_version", "source_hash")
DISCLAIMER_PHRASE = "no source record was merged or overwritten"
MERGE_SEPARATORS = (";", "+", ",", "|")
OVERWRITE_FLAGS = ("source_mutated", "overwrote_source", "source_modified", "source_overwritten")
# Positive assertions the normalizer must never make (screened in free text only, not in
# reject reasons or the disclaimer, which legitimately negate these terms).
PROHIBITED = [
    r"merged (the )?identit", r"merged (the )?records", r"deduplicated", r"overwrote (the )?source",
    r"overwrit\w* (the )?source", r"chose the canonical (value|price|record)", r"resolved the (identity|conflict|discrepanc)",
    r"corrected the source", r"the correct (price|value|identity) is", r"recommend (buy|sell|buying|selling|invest)",
    r"\bsuitab", r"picked the (right|correct) (price|value|record)",
]


def _bad_source_id(sid) -> bool:
    if isinstance(sid, (list, tuple, dict)):
        return True
    return any(sep in str(sid) for sep in MERGE_SEPARATORS)


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(pack, dict):
        return ["top-level pack must be a JSON object"]

    if not str(pack.get("job_id", "")).strip():
        errors.append("missing durable job_id")
    if not str(pack.get("ruleset_version", "")).strip():
        errors.append("missing ruleset_version (versioned mapping contract)")

    canon = pack.get("canonical_records")
    rej = pack.get("rejected_records")
    if not isinstance(canon, list) or not isinstance(rej, list):
        return errors + ["canonical_records and rejected_records must both be lists"]

    recon = pack.get("reconciliation") or {}
    n_in = recon.get("input")
    if n_in != len(canon) + len(rej) or recon.get("canonical") != len(canon) or recon.get("rejected") != len(rej):
        errors.append(f"reconciliation does not tie out (input={n_in}, canonical={len(canon)}, rejected={len(rej)}) "
                      "— records must not be silently dropped")
    if pack.get("input_record_count") not in (None, n_in):
        errors.append("input_record_count disagrees with reconciliation.input")

    seen_ids = set()
    for c in canon:
        cid = c.get("canonical_id")
        tag = f"canonical {cid!r}"
        if not str(cid or "").strip():
            errors.append("canonical record missing canonical_id")
        elif cid in seen_ids:
            errors.append(f"{tag}: duplicate canonical_id")
        seen_ids.add(cid)

        lin = c.get("lineage") or {}
        for k in LINEAGE_KEYS:
            if not str(lin.get(k, "") or "").strip():
                errors.append(f"{tag}: lineage missing {k}")
        if _bad_source_id(lin.get("source_record_id")):
            errors.append(f"{tag}: identity merge detected — lineage.source_record_id must map to exactly one source record")
        for flag in OVERWRITE_FLAGS:
            if c.get(flag) or lin.get(flag):
                errors.append(f"{tag}: source record not preserved (overwrite flag {flag!r} set)")
        if c.get("merged_from") or c.get("merged_source_ids"):
            errors.append(f"{tag}: identity merge detected — merged_from/merged_source_ids present")

        rt = c.get("record_type")
        body = c.get("canonical") or {}
        if rt not in REQUIRED_FIELDS:
            errors.append(f"{tag}: unknown record_type {rt!r}")
        else:
            miss = [f for f in REQUIRED_FIELDS[rt] if body.get(f) in (None, "")]
            if miss:
                errors.append(f"{tag}: canonical {rt} missing required fields {miss}")

    for r in rej:
        rid = r.get("source_record_id")
        rtag = f"rejected {r.get('source_system')}/{rid}"
        for k in ("reason_code", "reason", "source_record_id", "source_hash"):
            if not str(r.get(k, "") or "").strip():
                errors.append(f"{rtag}: missing {k}")

    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))])
    for pat in PROHIBITED:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited normalization/advice language detected: {m.group(0)!r}")

    disc = (str(pack.get("disclaimer", "")) + " " + str(pack.get("narrative", ""))).lower()
    if DISCLAIMER_PHRASE not in disc:
        errors.append("missing standing disclaimer")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "canonical_good.json"
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
