#!/usr/bin/env python3
"""Deterministic security-master enrichment engine for security-master-enricher.

For each candidate security, joins candidate identifier and attribute values gathered from
multiple APPROVED sources, applies a ranked source hierarchy to PROPOSE one enriched value
per attribute, preserves provenance (source citations on every proposal), classifies every
disagreement / data-quality issue into a fixed conflict taxonomy, and emits a steward
conflict queue.

IMPORTANT: This engine PROPOSES enrichment only. It never creates a production security,
never resolves or merges conflicting identities, and never writes to the security master.
Every proposal carries status "PROPOSED"; identity conflicts (identifier_conflict,
identifier_invalid) are NEVER auto-resolved — they carry no proposed value and always
require security-steward review.

Conflict taxonomy (see references/domain-rules.md):
  identifier_conflict | identifier_invalid | attribute_conflict | stale_value |
  missing_required | unpermitted_source

Tie-out invariants (enforced by scripts/validate_output.py):
  - every enrichment field maps to exactly one disposition (agreed | conflicted | missing |
    absent); sum of dispositions == securities * len(ENRICH_FIELDS);
  - attribute proposals == agreed + conflicted fields;
  - conflict-queue length == sum of counts by conflict type;
  - every proposal cites >= 1 approved source (provenance);
  - no identity is resolved (identifier conflicts carry no proposal).

Usage:
  python calculate_or_transform.py enrichment.json    # prints enrichment pack JSON
  python calculate_or_transform.py --selftest         # runs bundled fixture + invariants
In --selftest mode prints checks ending in "enrichment self-test: N error(s)" (exit 0/1).
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Fixed enrichment field registry — every security is evaluated against exactly these fields.
ENRICH_FIELDS = ("currency", "exchange", "asset_class", "maturity", "coupon", "rating",
                 "benchmark", "issuer")
NUMERIC_FIELDS = {"coupon"}
CONFLICT_TYPES = ("identifier_conflict", "identifier_invalid", "attribute_conflict",
                  "stale_value", "missing_required", "unpermitted_source")
IDENTITY_CONFLICTS = {"identifier_conflict", "identifier_invalid"}

DEFAULT_CONFIG = {
    "required_fields": ["currency", "asset_class", "issuer"],
    "material_fields": ["asset_class", "maturity", "coupon", "rating"],
    "numeric_tolerance": 0.0001,
    "freshness_days": 30,
}

DISCLAIMER = ("Enrichment proposals and conflict queue only; no security has been created, "
              "no identity has been resolved or merged, and nothing has been written to the "
              "security master. All proposals and identity conflicts require security-steward "
              "review and authorized posting.")


def _parse_dt(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _norm_str(v) -> str:
    return str(v).strip().casefold()


def _cite(source: str, ref: dict) -> str:
    return f"{source}:{ref.get('field') or ref.get('scheme') or '?'}@{ref.get('as_of', '?')}"


# --- identifier structural validation (deterministic; no network) ---

def _isin_valid(code: str) -> bool:
    """ISIN = 2-letter country + 9 alphanumeric + 1 Luhn check digit (12 chars)."""
    code = str(code).strip().upper()
    if len(code) != 12 or not code[:2].isalpha() or not code.isalnum():
        return False
    digits = ""
    for ch in code:
        digits += str(ord(ch) - 55) if ch.isalpha() else ch
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2 == 1:  # validate full string: check digit (i==0) is not doubled
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _cusip_valid(code: str) -> bool:
    """CUSIP = 8 base chars + 1 mod-10 check digit (9 chars)."""
    code = str(code).strip().upper()
    if len(code) != 9 or not code.isalnum():
        return False
    total = 0
    for i, ch in enumerate(code[:8]):
        if ch.isdigit():
            v = int(ch)
        else:
            v = ord(ch) - 55  # A=10 .. Z=35
        if i % 2 == 1:  # 1-indexed even position doubled
            v *= 2
        total += v // 10 + v % 10
    check = (10 - (total % 10)) % 10
    return str(check) == code[8]


def _identifier_structurally_valid(scheme: str, value: str) -> bool:
    s = str(scheme).strip().upper()
    if s == "ISIN":
        return _isin_valid(value)
    if s == "CUSIP":
        return _cusip_valid(value)
    return True  # schemes without a bundled check are treated as structurally acceptable


def _fingerprint(doc: dict, cfg: dict) -> str:
    """Stable content hash of the normalized inputs — the basis of an idempotent id."""
    def norm_sec(sec):
        ids = sorted(
            [{"scheme": str(i.get("scheme")).upper(), "value": str(i.get("value")),
              "source": i.get("source"), "as_of": str(i.get("as_of"))}
             for i in (sec.get("identifiers") or [])],
            key=lambda r: (r["scheme"], r["value"], str(r["source"])))
        attrs = sorted(
            [{"field": i.get("field"), "value": str(i.get("value")), "source": i.get("source"),
              "as_of": str(i.get("as_of")), "effective_date": str(i.get("effective_date") or "")}
             for i in (sec.get("attributes") or [])],
            key=lambda r: (str(r["field"]), str(r["source"]), str(r["value"])))
        return {"security_key": sec.get("security_key"), "identifiers": ids, "attributes": attrs}

    payload = {
        "entity": doc.get("entity"), "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "source_hierarchy": list(doc.get("source_hierarchy") or []),
        "config": {k: cfg[k] for k in sorted(cfg)},
        "securities": sorted([norm_sec(s) for s in (doc.get("securities") or [])],
                             key=lambda s: str(s["security_key"])),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    required = set(cfg["required_fields"])
    material = set(cfg["material_fields"])
    tol = float(cfg["numeric_tolerance"])
    freshness_days = int(cfg["freshness_days"])
    hierarchy = list(doc.get("source_hierarchy") or [])
    rank = {src: i for i, src in enumerate(hierarchy)}
    as_of = doc.get("as_of")
    cutoff = _parse_dt(as_of) - timedelta(days=freshness_days) if as_of else None

    proposals: list = []
    conflicts: list = []
    pseq = 0
    cseq = 0
    disp = {"agreed": 0, "conflicted": 0, "missing": 0, "absent": 0}
    id_disp = {"agreed_id": 0, "conflicted_id": 0, "invalid_id": 0}

    def new_proposal(sec_key, field, value, source, as_of_v, effective, confidence,
                     provenance, steward, conflict_id=None, kind="attribute"):
        nonlocal pseq
        pseq += 1
        p = {
            "proposal_id": f"ENR-{pseq:04d}",
            "security_key": sec_key,
            "kind": kind,
            "field": field,
            "status": "PROPOSED",
            "proposed_value": value,
            "selected_source": source,
            "selected_source_rank": rank.get(source),
            "as_of": as_of_v,
            "effective_date": effective,
            "confidence": confidence,
            "provenance": provenance,
            "requires_steward_review": steward,
            "conflict_id": conflict_id,
        }
        proposals.append(p)
        return p["proposal_id"]

    def new_conflict(sec_key, ctype, field, candidates, severity, note):
        nonlocal cseq
        cseq += 1
        c = {
            "conflict_id": f"CFL-{cseq:04d}",
            "security_key": sec_key,
            "type": ctype,
            "field": field,
            "candidates": candidates,
            "severity": severity,
            "requires_steward_review": True,
            "note": note,
        }
        conflicts.append(c)
        return c["conflict_id"]

    for sec in sorted(doc.get("securities") or [], key=lambda s: str(s.get("security_key"))):
        sec_key = sec.get("security_key")

        # ---- identifiers: agree / conflict / invalid (identity is never resolved) ----
        by_scheme: dict = {}
        for i in sec.get("identifiers") or []:
            src = i.get("source")
            if src not in rank:  # unpermitted source on an identifier is queued, not used
                new_conflict(sec_key, "unpermitted_source",
                             str(i.get("scheme")).upper(),
                             [{"value": i.get("value"), "source": src, "as_of": i.get("as_of")}],
                             "minor", f"identifier from source {src!r} not in approved hierarchy — excluded")
                continue
            by_scheme.setdefault(str(i.get("scheme")).upper(), []).append(i)

        for scheme in sorted(by_scheme):
            rows = sorted(by_scheme[scheme], key=lambda r: (rank.get(r.get("source"), 1e9),
                                                            str(r.get("value"))))
            distinct = sorted({str(r.get("value")) for r in rows})
            cands = [{"value": r.get("value"), "source": r.get("source"),
                      "source_rank": rank.get(r.get("source")), "as_of": r.get("as_of"),
                      "citation": _cite(r.get("source"), {"scheme": scheme, "as_of": r.get("as_of")})}
                     for r in rows]
            if len(distinct) > 1:
                id_disp["conflicted_id"] += 1
                new_conflict(sec_key, "identifier_conflict", scheme, cands, "identity",
                             f"{len(distinct)} different {scheme} values for one security_key — "
                             "identity conflict; not resolved by this skill (steward review required)")
                continue
            top = rows[0]
            if not _identifier_structurally_valid(scheme, top.get("value")):
                id_disp["invalid_id"] += 1
                new_conflict(sec_key, "identifier_invalid", scheme, cands, "identity",
                             f"{scheme} {top.get('value')!r} fails its structural/check-digit "
                             "validation — not proposed; steward review required")
                continue
            id_disp["agreed_id"] += 1
            prov = [c["citation"] for c in cands]
            conf = "agreed" if len(rows) > 1 else "single_source"
            new_proposal(sec_key, scheme, top.get("value"), top.get("source"),
                         top.get("as_of"), top.get("effective_date"), conf, prov,
                         steward=False, kind="identifier")

        # ---- attributes: one disposition per enrichment field ----
        attrs_by_field: dict = {}
        for a in sec.get("attributes") or []:
            attrs_by_field.setdefault(a.get("field"), []).append(a)

        for field in ENRICH_FIELDS:
            rows_all = attrs_by_field.get(field, [])
            approved = [a for a in rows_all if a.get("source") in rank]
            unpermitted = [a for a in rows_all if a.get("source") not in rank]
            if unpermitted:
                new_conflict(sec_key, "unpermitted_source", field,
                             [{"value": a.get("value"), "source": a.get("source"),
                               "as_of": a.get("as_of")} for a in unpermitted], "minor",
                             f"{len(unpermitted)} {field} value(s) from unapproved source(s) — excluded")

            if not approved:
                if field in required:
                    disp["missing"] += 1
                    new_conflict(sec_key, "missing_required", field, [], "material",
                                 f"required field {field!r} has no value from any approved source")
                else:
                    disp["absent"] += 1
                continue

            approved = sorted(approved, key=lambda a: (rank.get(a.get("source"), 1e9),
                                                       str(a.get("as_of"))))
            top = approved[0]
            cands = [{"value": a.get("value"), "source": a.get("source"),
                      "source_rank": rank.get(a.get("source")), "as_of": a.get("as_of"),
                      "citation": _cite(a.get("source"), {"field": field, "as_of": a.get("as_of")})}
                     for a in approved]
            prov = [c["citation"] for c in cands]

            # agreement test across approved candidates
            if field in NUMERIC_FIELDS:
                nums = [_num(a.get("value")) for a in approved]
                agree = all(n is not None for n in nums) and (max(nums) - min(nums) <= tol)
            else:
                agree = len({_norm_str(a.get("value")) for a in approved}) == 1

            # freshness of the selected candidate
            stale = False
            if cutoff is not None and top.get("as_of"):
                try:
                    stale = _parse_dt(top.get("as_of")) < cutoff
                except ValueError:
                    stale = False

            if agree:
                disp["agreed"] += 1
                conf = "agreed" if len(approved) > 1 else "single_source"
                conflict_id = None
                if stale:
                    conflict_id = new_conflict(
                        sec_key, "stale_value", field, cands,
                        "material" if field in material else "minor",
                        f"selected {field} from {top.get('source')} as_of {top.get('as_of')} is "
                        f"older than the {freshness_days}-day freshness window")
                new_proposal(sec_key, field, top.get("value"), top.get("source"),
                             top.get("as_of"), top.get("effective_date"), conf, prov,
                             steward=bool(stale), conflict_id=conflict_id)
            else:
                disp["conflicted"] += 1
                conflict_id = new_conflict(
                    sec_key, "attribute_conflict", field, cands,
                    "material" if field in material else "minor",
                    f"approved sources disagree on {field}; selected top-ranked "
                    f"{top.get('source')} value pending steward review")
                new_proposal(sec_key, field, top.get("value"), top.get("source"),
                             top.get("as_of"), top.get("effective_date"), "conflict", prov,
                             steward=True, conflict_id=conflict_id)

    # ---- roll-ups & tie-out ----
    securities_in = len(doc.get("securities") or [])
    fields_considered = securities_in * len(ENRICH_FIELDS)
    disp_total = disp["agreed"] + disp["conflicted"] + disp["missing"] + disp["absent"]
    attr_proposals = sum(1 for p in proposals if p["kind"] == "attribute")
    id_proposals = sum(1 for p in proposals if p["kind"] == "identifier")
    by_conflict = {t: sum(1 for c in conflicts if c["type"] == t) for t in CONFLICT_TYPES}
    by_conflict = {t: n for t, n in by_conflict.items() if n}

    fp = _fingerprint(doc, cfg)
    enrichment_id = f"sme-{doc.get('entity')}-{doc.get('as_of')}-{fp[:8]}"

    return {
        "enrichment_id": enrichment_id,
        "entity": doc.get("entity"),
        "as_of": as_of,
        "config_version": doc.get("config_version"),
        "source_hierarchy": hierarchy,
        "input_fingerprint": fp,
        "tie_out": {
            "securities_in": securities_in,
            "fields_considered": fields_considered,
            "dispositions": disp,
            "disposition_total": disp_total,
            "residual": fields_considered - disp_total,
            "attribute_proposals": attr_proposals,
            "identifier_proposals": id_proposals,
            "proposals_total": len(proposals),
            "conflicts_total": len(conflicts),
            "identity_conflicts": sum(1 for c in conflicts if c["type"] in IDENTITY_CONFLICTS),
            "reconciled": (disp_total == fields_considered
                           and attr_proposals == disp["agreed"] + disp["conflicted"]
                           and len(conflicts) == sum(by_conflict.values())),
        },
        "enrichment_proposals": proposals,
        "conflict_queue": conflicts,
        "summary": {
            "securities": securities_in,
            "proposals": len(proposals),
            "conflicts": len(conflicts),
            "by_conflict_type": by_conflict,
            "steward_review_required": sum(1 for p in proposals if p["requires_steward_review"])
            + len(conflicts),
        },
        "disclaimer": DISCLAIMER,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "enrichment_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = compute(doc)
    errors: list = []
    t = out["tie_out"]

    if t["residual"] != 0:
        errors.append(f"tie-out residual {t['residual']} != 0 (field dispositions do not account)")
    if t["disposition_total"] != t["fields_considered"]:
        errors.append("disposition_total != fields_considered")
    if t["attribute_proposals"] != t["dispositions"]["agreed"] + t["dispositions"]["conflicted"]:
        errors.append("attribute proposals != agreed + conflicted fields")
    if t["conflicts_total"] != len(out["conflict_queue"]):
        errors.append("conflicts_total != conflict_queue length")
    if not t["reconciled"]:
        errors.append("tie_out.reconciled is false")

    # taxonomy coverage: the fixture is designed to exercise every conflict type
    seen = {c["type"] for c in out["conflict_queue"]}
    for ct in CONFLICT_TYPES:
        if ct not in seen:
            errors.append(f"fixture missing conflict type {ct}")

    for p in out["enrichment_proposals"]:
        if p["status"] != "PROPOSED":
            errors.append(f"{p['proposal_id']}: status {p['status']!r} != PROPOSED")
        if not p["provenance"]:
            errors.append(f"{p['proposal_id']}: no provenance citation")

    # identity is never resolved: no proposal exists for a conflicted/invalid identifier scheme
    id_conf = {(c["security_key"], c["field"]) for c in out["conflict_queue"]
               if c["type"] in IDENTITY_CONFLICTS}
    for p in out["enrichment_proposals"]:
        if p["kind"] == "identifier" and (p["security_key"], p["field"]) in id_conf:
            errors.append(f"{p['proposal_id']}: identity {p['field']} was resolved despite a conflict")
    for c in out["conflict_queue"]:
        if c["type"] in IDENTITY_CONFLICTS and not c["requires_steward_review"]:
            errors.append(f"{c['conflict_id']}: identity conflict not flagged for steward review")

    # idempotency: recompute must be byte-identical
    if json.dumps(compute(doc), sort_keys=True) != json.dumps(out, sort_keys=True):
        errors.append("non-idempotent: recompute produced a different result")

    for e in errors:
        print("ERROR", e)
    print(f"enrichment self-test: {len(errors)} error(s)")
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
