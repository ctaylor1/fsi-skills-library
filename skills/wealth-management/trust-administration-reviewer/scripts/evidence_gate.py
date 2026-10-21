#!/usr/bin/env python3
"""Detached field-to-source review preflight. Stdlib only; no semantic classifier.

Hashes and spans establish bindings, not entailment or reviewer authority. See
EVIDENCE-GATE.md. Nothing here authenticates a person or approves a transaction.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, Inexact, InvalidOperation, Overflow, Rounded, ROUND_HALF_UP, Underflow, localcontext
import hashlib
import json
from pathlib import Path
import sys

PACKET = "wealth-source-packet-v1"
INVENTORY = "wealth-evidence-inventory-v1"
REVIEW = "wealth-evidence-review-v1"
RECEIPT = "wealth-evidence-receipt-v1"
CLASSES = {"supported", "derived", "unknown", "local-label"}
LOCAL_KEYS = {"schema_version", "request_id", "mode", "goal_id", "objective_id",
              "item_id", "row_id", "draft_id", "label"}
ORIGIN_KEYS = {"artifact_id", "origin_artifact_id", "upstream_artifact_id", "input_hash"}
LIMITATIONS = [
    "Exact hashes, spans and values establish binding, not semantic entailment.",
    "Entailment and subject/field alignment are separately recorded reviewer judgments.",
    "Reviewer identity and independence are declared, not authenticated or certified.",
    "Source truth, completeness, freshness, legal applicability and access require separate review.",
    "This receipt is private review evidence, not professional approval or permission to act.",
    "Native package validation and audience release checks remain required.",
]


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _json(value, depth=0):
    if depth > 40:
        raise ValueError("JSON nesting exceeds 40 levels")
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise ValueError("JSON object keys must be strings")
        for v in value.values():
            _json(v, depth + 1)
    elif isinstance(value, list):
        for v in value:
            _json(v, depth + 1)
    elif value is not None and type(value) not in (str, int, float, bool):
        raise ValueError("unsupported JSON value")
    if type(value) is float and not Decimal(str(value)).is_finite():
        raise ValueError("nonfinite number")


def hash_object(value):
    _json(value)
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid JSON encoding") from exc
    if len(raw) > 8_000_000:
        raise ValueError("JSON document exceeds 8 MB")
    return hashlib.sha256(raw).hexdigest()


def _escape(token):
    return token.replace("~", "~0").replace("/", "~1")


def _tokens(pointer):
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise ValueError("invalid JSON Pointer")
    if pointer == "":
        return []
    tokens = pointer[1:].split("/")
    for token in tokens:
        if "~" in token.replace("~0", "").replace("~1", ""):
            raise ValueError("invalid JSON Pointer escape")
    return [t.replace("~1", "/").replace("~0", "~") for t in tokens]


def value_at(doc, pointer):
    value = doc
    for token in _tokens(pointer):
        if isinstance(value, dict):
            if token not in value:
                raise ValueError("source/claim pointer does not exist")
            value = value[token]
        elif isinstance(value, list) and token.isascii() and token.isdigit() and str(int(token)) == token:
            index = int(token)
            if index >= len(value):
                raise ValueError("source/claim array index out of bounds")
            value = value[index]
        else:
            raise ValueError("source/claim pointer does not resolve")
    return value


def _leaves(doc, pointer=""):
    if isinstance(doc, dict) and doc:
        out = {}
        for key in sorted(doc):
            out.update(_leaves(doc[key], pointer + "/" + _escape(key)))
        return out
    if isinstance(doc, list) and doc:
        out = {}
        for index, value in enumerate(doc):
            out.update(_leaves(value, pointer + "/" + str(index)))
        return out
    return {pointer: doc}


def _packet(packet):
    hash_object(packet)
    if not isinstance(packet, dict) or packet.get("schema_version") != PACKET or not _text(packet.get("packet_id")):
        raise ValueError("detached packet requires wealth-source-packet-v1 and packet_id")
    rows = packet.get("sources")
    if not isinstance(rows, list) or not rows or len(rows) > 2000:
        raise ValueError("packet sources must contain 1..2000 records")
    sources = {}
    for row in rows:
        if not isinstance(row, dict) or any(not _text(row.get(k)) for k in ("source_id", "reference", "content")):
            raise ValueError("each raw source requires source_id, reference and content strings")
        sid = row["source_id"]
        if sid in sources:
            raise ValueError("duplicate raw source_id")
        sources[sid] = row
    return sources


def make_inventory(candidate, packet, producer_id):
    """Enumerate all fields; no materiality inference or field exemptions."""
    digest = hash_object(candidate)
    _packet(packet)
    if not isinstance(candidate, dict) or not candidate:
        raise ValueError("candidate must be a nonempty JSON object")
    if not _text(producer_id):
        raise ValueError("producer_id is required as a declared identity")
    leaves = _leaves(candidate)
    if len(leaves) > 20000:
        raise ValueError("candidate exceeds 20000 field claims")
    inventory = {
        "schema_version": INVENTORY, "producer_id": producer_id,
        "candidate_sha256": digest, "source_packet_sha256": hash_object(packet),
        "fields": [{"claim_id": p, "value_sha256": hash_object(v)} for p, v in leaves.items()],
    }
    inventory["inventory_sha256"] = hash_object(inventory)
    return inventory


def _date(value):
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is not None
    except (ValueError, OverflowError):
        return False


def _evidence(evidence, sources):
    if not isinstance(evidence, list) or len(evidence) > 100:
        raise ValueError("evidence must be a list of at most 100 exact spans")
    ids, quotes = set(), []
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {"source_id", "field", "start", "end", "quote"}:
            raise ValueError("citation requires exactly source_id, field, start, end, quote")
        sid, field = item["source_id"], item["field"]
        if not isinstance(sid, str) or sid not in sources or field not in ("content", "reference"):
            raise ValueError("citation source or raw text field is unknown")
        start, end, quote = item["start"], item["end"], item["quote"]
        raw = sources[sid][field]
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw):
            raise ValueError("citation span is out of bounds")
        if not _text(quote) or raw[start:end] != quote:
            raise ValueError("citation quote differs from detached source span")
        ids.add(sid); quotes.append(quote)
    return ids, quotes


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("derivation requires numeric operands and result")
    try:
        number = Decimal(str(value))
        if (not number.is_finite() or number.copy_abs() > Decimal("1e30")
                or len(number.as_tuple().digits) > 60
                or not -30 <= number.as_tuple().exponent <= 30):
            raise ValueError("derivation number out of bounds")
        return number
    except InvalidOperation as exc:
        raise ValueError("derivation requires finite decimals") from exc


def _calculate(spec, values):
    if not isinstance(spec, dict) or not isinstance(spec.get("operands"), list):
        raise ValueError("derivation requires operation, operand claim_ids and unit")
    if set(spec) - {"operation", "operands", "unit", "places"} or not _text(spec.get("unit")):
        raise ValueError("derivation has unsupported fields or lacks unit")
    nums = [_number(values[p]) for p in spec["operands"]]
    op = spec.get("operation")
    if not nums or len(nums) > 100:
        raise ValueError("derivation requires 1..100 reviewed operands")
    if "places" in spec and op != "round":
        raise ValueError("places is only permitted for explicit round")
    with localcontext() as ctx:
        ctx.prec = 60
        # Arithmetic must be exactly representable within the declared bounds.
        # Only the explicit round operation may discard precision. In particular,
        # a nonterminating ratio cannot silently become a claimed exact fact.
        for signal in (Inexact, Rounded, Underflow, Overflow):
            ctx.traps[signal] = True
        if op == "sum":
            return sum(nums, Decimal(0))
        if op == "difference" and len(nums) == 2:
            return nums[0] - nums[1]
        if op == "product":
            value = Decimal(1)
            for n in nums:
                value *= n
            return value
        if op == "ratio" and len(nums) == 2 and nums[1] != 0:
            return nums[0] / nums[1]
        if op == "round" and len(nums) == 1 and type(spec.get("places")) is int and 0 <= spec["places"] <= 8:
            ctx.traps[Inexact] = False
            ctx.traps[Rounded] = False
            return nums[0].quantize(Decimal(1).scaleb(-spec["places"]), rounding=ROUND_HALF_UP)
    raise ValueError("unsupported derivation, arity, rounding or zero denominator")


def check(candidate, packet, inventory, review):
    """Check exact bindings plus detached reviewer decisions; never infer entailment."""
    hash_object(inventory)
    bindings = {"candidate_sha256": hash_object(candidate), "source_packet_sha256": hash_object(packet),
                "inventory_sha256": inventory.get("inventory_sha256") if isinstance(inventory, dict) else None,
                "review_sha256": hash_object(review)}
    findings = []
    def add(code, message):
        findings.append({"code": code, "message": message})
    try:
        sources = _packet(packet)
        expected = make_inventory(candidate, packet, inventory.get("producer_id") if isinstance(inventory, dict) else None)
        if inventory != expected:
            raise ValueError("inventory differs from complete detached candidate/source enumeration")
        if not isinstance(review, dict) or review.get("schema_version") != REVIEW:
            raise ValueError("review requires wealth-evidence-review-v1")
        for key in ("candidate_sha256", "source_packet_sha256", "inventory_sha256"):
            if review.get(key) != expected[key]:
                raise ValueError("review does not bind current " + key)
        reviewer = review.get("reviewer")
        if not isinstance(reviewer, dict) or not _text(reviewer.get("reviewer_id")) or reviewer.get("kind") not in ("human", "model"):
            raise ValueError("reviewer requires declared reviewer_id and human/model kind")
        if reviewer.get("independent_from_producer") is not True or reviewer["reviewer_id"].strip().casefold() == inventory["producer_id"].strip().casefold():
            raise ValueError("self-review or undeclared independence cannot clear preflight")
        if not _date(review.get("reviewed_at")) or not _text(review.get("review_reference")):
            raise ValueError("review requires dated, referenced decision record")
        decisions = review.get("decisions")
        if not isinstance(decisions, list) or any(not isinstance(d, dict) for d in decisions):
            raise ValueError("review decisions must be a list of field records")
        leaves = _leaves(candidate)
        ids = [d.get("claim_id") for d in decisions]
        if any(not isinstance(p, str) for p in ids) or len(set(ids)) != len(ids) or set(ids) != set(leaves):
            raise ValueError("review must cover every field exactly once, with no extra claims")
    except (ValueError, TypeError, KeyError) as exc:
        add("invalid-review-binding", str(exc))
        sources, leaves, decisions = {}, _leaves(candidate), []
    decision_map = {d["claim_id"]: d for d in decisions}
    checked, active = {}, set()

    def inspect(pointer):
        if pointer in checked:
            return checked[pointer]
        if pointer in active:
            raise ValueError("cyclic derivation")
        if len(active) >= 60:
            raise ValueError("derivation dependency depth exceeds 60")
        active.add(pointer)
        d = decision_map.get(pointer, {})
        value = leaves[pointer]
        row = {"claim_id": pointer, "classification": d.get("classification"),
               "status": "blocked", "source_ids": [], "findings": []}
        try:
            if findings:
                raise ValueError("detached binding/inventory/reviewer check failed")
            if d.get("classification") not in CLASSES:
                raise ValueError("unknown field classification")
            if d.get("verdict") != "supported":
                raise ValueError("reviewer marked field unsupported or unreviewed")
            if not _text(d.get("rationale")):
                raise ValueError("field requires substantive recorded reviewer rationale")
            if d.get("field_check") != "matched" or d.get("subject_check") not in ("matched", "not-applicable"):
                raise ValueError("source field/subject mismatch or unreviewed alignment")
            source_ids, quotes = _evidence(d.get("evidence"), sources)
            row["source_ids"] = sorted(source_ids)
            classification = d["classification"]
            if classification in ("supported", "derived") and d["subject_check"] != "matched":
                raise ValueError("factual and derived claims require reviewed subject alignment")
            name = _tokens(pointer)[-1] if pointer else ""
            binding = d.get("value_binding")
            if binding is not None:
                if not isinstance(binding, dict) or set(binding) != {"source_id", "pointer"} or binding.get("source_id") not in sources:
                    raise ValueError("value_binding requires an existing raw source and JSON Pointer")
                raw_value = value_at(sources[binding["source_id"]], binding["pointer"])
                if hash_object(raw_value) != hash_object(value):
                    raise ValueError("candidate differs from exact typed raw source value")
                source_ids.add(binding["source_id"])
            if classification == "unknown":
                if value is not None or binding is not None or "derivation" in d:
                    raise ValueError("unknown must preserve explicit null, without fabricated replacement")
            elif classification == "local-label":
                if name not in LOCAL_KEYS or not _text(value) or binding is not None or "derivation" in d:
                    raise ValueError("local label cannot encode provenance, identity, authority, preference or financial fact")
            elif classification == "supported":
                if value is None:
                    raise ValueError("null must be classified unknown")
                if not source_ids:
                    raise ValueError("supported field requires raw-source evidence")
                if "derivation" in d:
                    raise ValueError("supported facts cannot conceal a derivation")
                if name in ORIGIN_KEYS and binding is None and value not in quotes:
                    raise ValueError("upstream provenance requires exact identifier span or typed raw-source binding")
            elif classification == "derived":
                if name == "priority" or name in ORIGIN_KEYS or binding is not None:
                    raise ValueError("preferences and provenance cannot be derived")
                spec = d.get("derivation")
                operands = spec.get("operands") if isinstance(spec, dict) else None
                if not isinstance(operands, list) or any(not isinstance(p, str) or p not in leaves for p in operands):
                    raise ValueError("derivation must use existing claim pointers")
                for parent in operands:
                    prior = inspect(parent)
                    if prior["status"] != "reviewed" or prior["classification"] not in ("supported", "derived"):
                        raise ValueError("derivation depends on unknown, local or blocked operand")
                    source_ids.update(prior["source_ids"])
                if _number(value) != _calculate(spec, leaves):
                    raise ValueError("derived value does not match explicit operation")
                row["derivation"] = deepcopy(spec)
            row["source_ids"] = sorted(source_ids)
            row["status"] = "reviewed"
        except (ValueError, TypeError, KeyError, InvalidOperation, ArithmeticError) as exc:
            row["findings"].append({"code": "field-blocked", "message": str(exc)})
        finally:
            active.discard(pointer)
        checked[pointer] = row
        return row

    claim_reviews = [inspect(p) for p in leaves]
    blocked = [r["claim_id"] for r in claim_reviews if r["status"] != "reviewed"]
    ok = not findings and not blocked
    receipt = {
        "schema_version": RECEIPT, "status": "reviewed-for-draft" if ok else "blocked",
        "bindings": bindings, "findings": findings, "claim_reviews": claim_reviews,
        "reviewed_fields": [{"claim_id": r["claim_id"], "value": deepcopy(leaves[r["claim_id"]]),
                             "classification": r["classification"], "source_ids": r["source_ids"]}
                            for r in claim_reviews if r["status"] == "reviewed"],
        "withheld_claim_ids": blocked, "projected_input": deepcopy(candidate) if ok else None,
        "reviewer": deepcopy(review.get("reviewer")) if isinstance(review, dict) else None,
        "reviewed_at": review.get("reviewed_at") if isinstance(review, dict) else None,
        "review_reference": review.get("review_reference") if isinstance(review, dict) else None,
        "semantic_assurance": "recorded-reviewer-judgment-only",
        "identity_authenticated": False, "professional_approval": False,
        "human_review_required": True, "action_taken": False, "delivery_status": "not-delivered",
        "limitations": LIMITATIONS,
    }
    receipt["receipt_sha256"] = hash_object(receipt)
    return receipt


def validate_receipt(receipt, candidate, packet, inventory, review):
    try:
        expected = check(candidate, packet, inventory, review)
        return [] if hash_object(receipt) == hash_object(expected) else ["receipt differs from detached reconstruction"]
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        return ["invalid detached evidence: " + str(exc)]


def example():
    """Return synthetic (candidate, packet, inventory, review), never actual approval.

    Explicit decisions below are a worked schema example. Do not use this routine
    to manufacture decisions for other candidates or replace independent review.
    """
    candidate = {"request_id": "draft-DEMO", "account_id": "ACCT-DEMO",
                 "value": "500.00", "tax_treatment": None}
    packet = {"schema_version": PACKET, "packet_id": "synthetic-DEMO",
              "recipients": [{"recipient_id": "advisor-DEMO", "kind": "person"}],
              "sources": [{"source_id": "DEMO-1", "reference": "Synthetic custody extract, 2026-10-04",
                           "content": "ACCT-DEMO has value USD 500.00. Tax treatment is not supplied.",
                           "data": {"account_id": "ACCT-DEMO", "value": "500.00"},
                           "access": {"allowed_recipient_ids": ["advisor-DEMO"],
                                      "effective_date": "2026-10-04", "valid_until": "2026-10-31"}}]}
    inventory = make_inventory(candidate, packet, "synthetic-extractor")
    review = {"schema_version": REVIEW,
              **{k: inventory[k] for k in ("candidate_sha256", "source_packet_sha256", "inventory_sha256")},
              "reviewer": {"reviewer_id": "synthetic-peer", "kind": "model", "independent_from_producer": True},
              "reviewed_at": "2026-10-04T12:00:00Z", "review_reference": "worked-example-only-not-real-review",
              "decisions": []}
    for claim in inventory["fields"]:
        pointer = claim["claim_id"]
        row = {"claim_id": pointer, "classification": "supported", "verdict": "supported",
               "subject_check": "matched", "field_check": "matched", "evidence": [],
               "rationale": "Synthetic independent review of this exact subject and field in the supplied extract."}
        if pointer == "/request_id":
            row.update(classification="local-label", subject_check="not-applicable",
                       rationale="Local draft tracking label; no source authority is claimed.")
        elif pointer == "/tax_treatment":
            quote = "Tax treatment is not supplied."
            start = packet["sources"][0]["content"].index(quote)
            row.update(classification="unknown", rationale="Missing treatment remains null; no IRA classification inferred.",
                       evidence=[{"source_id": "DEMO-1", "field": "content", "start": start,
                                  "end": start + len(quote), "quote": quote}])
        else:
            row["value_binding"] = {"source_id": "DEMO-1", "pointer": "/data" + pointer}
        review["decisions"].append(row)
    return candidate, packet, inventory, review


def _load(path):
    if Path(path).stat().st_size > 8_000_000:
        raise ValueError("file exceeds 8 MB")
    def pairs(items):
        out = {}
        for key, val in items:
            if key in out:
                raise ValueError("duplicate JSON object key")
            out[key] = val
        return out
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON constant")))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog="Examples and exact decision schema: EVIDENCE-GATE.md")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("inventory", "check", "validate"):
        p = sub.add_parser(command)
        p.add_argument("--candidate", required=True); p.add_argument("--sources", required=True)
        if command == "inventory":
            p.add_argument("--producer", required=True)
        else:
            p.add_argument("--inventory", required=True); p.add_argument("--review", required=True)
        if command == "validate":
            p.add_argument("--receipt", required=True)
    args = parser.parse_args(argv)
    try:
        candidate, packet = _load(args.candidate), _load(args.sources)
        if args.command == "inventory":
            output = make_inventory(candidate, packet, args.producer); status = 0
        else:
            inventory, review = _load(args.inventory), _load(args.review)
            if args.command == "check":
                output = check(candidate, packet, inventory, review)
                status = 0 if output["status"] == "reviewed-for-draft" else 1
            else:
                errors = validate_receipt(_load(args.receipt), candidate, packet, inventory, review)
                output = {"errors": errors}; status = int(bool(errors))
        print(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False))
        return status
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]})); return 2


if __name__ == "__main__":
    sys.exit(main())
