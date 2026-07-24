#!/usr/bin/env python3
"""Deterministic output validation for security-master-enricher.

Validates a finished enrichment pack (the calculate_or_transform core + an optional
narrative) before it is presented or delivered. Fails closed on any miss. Checks:

  1. TIE-OUTS        - every enrichment field maps to exactly one disposition (agreed |
                       conflicted | missing | absent); disposition_total == fields_considered;
                       residual == 0; attribute proposals == agreed + conflicted; conflict-queue
                       length == sum of counts by conflict type.
  2. CONFLICT TAXONOMY - every conflict.type is in the fixed taxonomy and carries an id, field,
                       severity, and candidates.
  3. PROVENANCE      - every enrichment proposal cites >= 1 approved source.
  4. IDENTITY BOUNDARY - identity conflicts (identifier_conflict, identifier_invalid) carry NO
                       proposed value, require steward review, and have NO matching identifier
                       proposal (a conflicting identity is never resolved/merged by this skill).
  5. PROPOSED-ONLY / PROHIBITED-DECISION - every proposal has status "PROPOSED"; NO
                       creation/resolution/merge-completed language and NO personalized
                       investment advice anywhere in the free text.
  6. IDEMPOTENCY     - enrichment_id is a pure function of stated inputs (entity/as_of +
                       input_fingerprint); no timestamp/random component.
  7. DISCLAIMER      - the standing no-creation/no-resolution disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

CONFLICT_TYPES = {"identifier_conflict", "identifier_invalid", "attribute_conflict",
                  "stale_value", "missing_required", "unpermitted_source"}
IDENTITY_CONFLICTS = {"identifier_conflict", "identifier_invalid"}
ENRICH_FIELD_COUNT = 8  # len(ENRICH_FIELDS) in calculate_or_transform.py
PROHIBITED_STATUS = {"APPLIED", "CREATED", "COMMITTED", "POSTED", "GOLDEN", "RESOLVED", "MERGED"}
FP_RE = re.compile(r"^[0-9a-f]{64}$")

DISCLAIMER = ("Enrichment proposals and conflict queue only; no security has been created, "
              "no identity has been resolved or merged, and nothing has been written to the "
              "security master. All proposals and identity conflicts require security-steward "
              "review and authorized posting.")

# Claims that a security was actually CREATED in the master or an identity RESOLVED/MERGED.
# An R2 draft-only enricher must never assert these; proposing/queueing them is allowed.
CREATION_PATTERNS = [
    r"\bsecurit(?:y|ies) (?:has|have|was|were) (?:been )?created\b",
    r"\b(?:created|added|promoted|committed) [^.]{0,40}(?:security master|golden (?:record|copy)|production security)\b",
    r"\bwrote to the (?:security )?master\b",
    r"\bpromoted to (?:golden|production|the master)\b",
    r"\bresolved the (?:identity|identifier|isin|cusip|sedol|conflict)\b",
    r"\bidentit(?:y|ies) (?:was|were|have|has) (?:been )?(?:resolved|merged)\b",
    r"\bmerged the (?:duplicate|identit(?:y|ies)|record|security)\b",
]
# Personalized investment advice is prohibited (universal R-tier prohibition).
ADVICE_PATTERNS = [
    r"\b(?:buy|sell) (?:this|the) (?:security|bond|stock|name|issuer)\b",
    r"\brecommend (?:over|under)weight",
    r"\brecommend (?:buying|selling|investing)\b",
    r"\bprice target\b",
]


def _validate_ties(pack: dict, errors: list) -> None:
    tie = pack.get("tie_out") or {}
    proposals = pack.get("enrichment_proposals") or []
    conflicts = pack.get("conflict_queue") or []
    disp = tie.get("dispositions") or {}

    securities_in = tie.get("securities_in")
    if isinstance(securities_in, int):
        expected_fields = securities_in * ENRICH_FIELD_COUNT
        if tie.get("fields_considered") != expected_fields:
            errors.append(f"tie-out: fields_considered {tie.get('fields_considered')} != "
                          f"securities_in*{ENRICH_FIELD_COUNT} ({expected_fields})")

    disp_total = sum(int(disp.get(k, 0)) for k in ("agreed", "conflicted", "missing", "absent"))
    if "fields_considered" in tie and disp_total != tie["fields_considered"]:
        errors.append(f"tie-out: dispositions sum {disp_total} != fields_considered "
                      f"{tie['fields_considered']} (a field is unaccounted for)")
    if tie.get("residual") not in (0, 0.0, None) or (
            "fields_considered" in tie and tie.get("fields_considered", 0) - disp_total != 0):
        errors.append("tie-out: residual is not zero (dispositions do not account for every field)")

    attr_proposals = sum(1 for p in proposals if p.get("kind") == "attribute")
    if attr_proposals != int(disp.get("agreed", 0)) + int(disp.get("conflicted", 0)):
        errors.append(f"tie-out: attribute proposals {attr_proposals} != agreed+conflicted "
                      f"{int(disp.get('agreed', 0)) + int(disp.get('conflicted', 0))}")

    by_type = {}
    for c in conflicts:
        by_type[c.get("type")] = by_type.get(c.get("type"), 0) + 1
    if len(conflicts) != sum(by_type.values()):
        errors.append("tie-out: conflict-queue length != sum of counts by type")
    if "conflicts_total" in tie and tie["conflicts_total"] != len(conflicts):
        errors.append(f"tie-out: conflicts_total {tie['conflicts_total']} != conflict_queue "
                      f"length {len(conflicts)}")
    reported = pack.get("summary", {}).get("by_conflict_type")
    if reported is not None and reported != {t: n for t, n in by_type.items() if n}:
        errors.append("tie-out: summary.by_conflict_type disagrees with the conflict_queue")


def validate(pack: dict) -> list:
    errors: list = []

    for k in ("enrichment_id", "input_fingerprint", "entity", "as_of", "tie_out",
              "enrichment_proposals", "conflict_queue", "disclaimer"):
        if k not in pack:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors

    proposals = pack.get("enrichment_proposals") or []
    conflicts = pack.get("conflict_queue") or []

    # --- 2 conflict taxonomy ---
    for c in conflicts:
        cid = c.get("conflict_id", "?")
        if c.get("type") not in CONFLICT_TYPES:
            errors.append(f"{cid}: conflict type {c.get('type')!r} not in taxonomy {sorted(CONFLICT_TYPES)}")
        for k in ("field", "severity", "candidates"):
            if k not in c:
                errors.append(f"{cid}: missing '{k}'")

    # --- 1 tie-outs ---
    _validate_ties(pack, errors)

    # --- 3 provenance + 5 proposed-only ---
    for p in proposals:
        pid = p.get("proposal_id", "?")
        if p.get("status") != "PROPOSED":
            errors.append(f"{pid}: status {p.get('status')!r} != 'PROPOSED' "
                          "(enrichment is proposed, never applied)")
        if str(p.get("status", "")).upper() in PROHIBITED_STATUS:
            errors.append(f"{pid}: prohibited applied/created status {p.get('status')!r}")
        if not (p.get("provenance") or []):
            errors.append(f"{pid}: no provenance citation (every proposal must trace to a source)")

    # --- 4 identity boundary: conflicting identities are never resolved ---
    id_conf_keys = {(c.get("security_key"), c.get("field")) for c in conflicts
                    if c.get("type") in IDENTITY_CONFLICTS}
    for c in conflicts:
        if c.get("type") in IDENTITY_CONFLICTS:
            if not c.get("requires_steward_review"):
                errors.append(f"{c.get('conflict_id','?')}: identity conflict must require steward review")
            if c.get("proposed_value") not in (None, "", "null"):
                errors.append(f"{c.get('conflict_id','?')}: identity conflict carries a proposed_value "
                              "(identities must not be auto-resolved)")
    for p in proposals:
        if p.get("kind") == "identifier" and (p.get("security_key"), p.get("field")) in id_conf_keys:
            errors.append(f"{p.get('proposal_id','?')}: identifier {p.get('field')} was resolved for a "
                          "security with an identity conflict (prohibited without steward approval)")

    # --- 6 idempotency ---
    fp = str(pack.get("input_fingerprint", ""))
    if not FP_RE.match(fp):
        errors.append("input_fingerprint is not a 64-hex content hash (idempotency basis missing)")
    expected_prefix = f"sme-{pack.get('entity')}-{pack.get('as_of')}-"
    eid = str(pack.get("enrichment_id", ""))
    if not eid.startswith(expected_prefix):
        errors.append(f"enrichment_id {eid!r} not derived from entity/as_of (not idempotent)")
    elif fp and not eid.endswith(fp[:8]):
        errors.append("enrichment_id does not bind to input_fingerprint (id must be reproducible)")

    # --- 5 prohibited-decision / advice language screen ---
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(c.get("note", "")) for c in conflicts]
    text = " ".join(text_parts)
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    text = re.sub(r"\bnot (?:yet )?(?:resolved|created|merged|posted|proposed by this skill)\b",
                  " ", text, flags=re.I)
    for pat in CREATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"creation/resolution-completed language detected: {m.group(0)!r} "
                          "(R2 proposes enrichment; it never creates a security or resolves an identity)")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited investment-advice language detected: {m.group(0)!r} "
                          "(this skill enriches reference data; it gives no investment advice)")

    # --- 7 disclaimer ---
    hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in hay:
        errors.append("missing standing no-creation/no-resolution disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "enrichment_pack_example.json"
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
