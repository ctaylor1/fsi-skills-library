"""Compose source-field and recipient checks for a separately reviewed draft.

The entire return value is operator-only. Only recipient_draft may be handed to
the specified audience, and only after professional approval outside this tool.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path

import audience_gate
import evidence_gate

CRITERIA = ("content-supported", "dependencies-complete", "recipient-scope-correct")


def assemble(candidate, packet, inventory, field_review, request, plan, draft_review=None):
    """Rebuild both gates from detached originals; record semantic review separately."""
    result = {"schema_version": "wealth-quality-result-v1", "status": "blocked",
              "visibility": "operator-only", "recipient_draft": None, "findings": [],
              "action_taken": False, "professional_approval": "not-established",
              "reviewer_authentication": "not-established"}
    try:
        field_receipt = evidence_gate.check(candidate, packet, inventory, field_review)
        result["field_receipt"] = field_receipt
        if field_receipt["status"] != "reviewed-for-draft":
            result["findings"].append("Candidate requires complete separate source-field review.")
            return result
        projected = audience_gate.project(request, packet, plan)
        claims = {r["claim_id"]: r for r in field_receipt["claim_reviews"]}
        blocks = {b["block_id"]: b for b in plan["blocks"]}

        # Audience validation has already rejected cycles and unknown blocks.
        # Calculate each transitive closure once without recursive depth limits.
        waiting = {bid: len(block["depends_on_block_ids"]) for bid, block in blocks.items()}
        dependants = {bid: [] for bid in blocks}
        for bid, block in blocks.items():
            for dep in block["depends_on_block_ids"]:
                dependants[dep].append(bid)
        ready = deque(bid for bid, count in waiting.items() if count == 0)
        closures = {}
        while ready:
            bid = ready.popleft()
            refs = set(blocks[bid]["source_ids"])
            for dep in blocks[bid]["depends_on_block_ids"]:
                refs.update(closures[dep])
            closures[bid] = refs
            for dependant in dependants[bid]:
                waiting[dependant] -= 1
                if waiting[dependant] == 0:
                    ready.append(dependant)

        # Check all declared blocks, including restricted blocks that may be
        # projected for a different audience later. Audience gate checks cycles.
        for block in plan["blocks"]:
            if not block["claim_ids"]:
                raise ValueError("Every content block requires reviewed claim dependencies.")
            refs = closures[block["block_id"]]
            for cid in block["claim_ids"]:
                if cid not in claims or claims[cid]["status"] != "reviewed":
                    raise ValueError("Content plan references an unreviewed or unknown claim.")
                if not set(claims[cid]["source_ids"]) <= refs:
                    raise ValueError("Content plan omits a claim's source dependencies.")
        result["audience_receipt"] = projected["receipt"]
        bindings = {
            "candidate_sha256": evidence_gate.hash_object(candidate),
            "source_packet_sha256": evidence_gate.hash_object(packet),
            "field_receipt_sha256": evidence_gate.hash_object(field_receipt),
            "request_sha256": evidence_gate.hash_object(request),
            "content_plan_sha256": evidence_gate.hash_object(plan),
            "rendered_sha256": hashlib.sha256(projected["rendered_markdown"].encode("utf-8")).hexdigest(),
        }
        result["review_request"] = {"bindings": bindings, "criteria": list(CRITERIA),
                                    "recipient_ids": sorted(request["recipient_ids"])}
        if draft_review is None:
            result["status"] = "pending-draft-review"
            result["findings"].append("Separate review of actual recipient text and complete semantic dependencies is missing.")
            return result
        if not isinstance(draft_review, dict) or draft_review.get("schema_version") != "wealth-draft-review-v1" or draft_review.get("bindings") != bindings:
            raise ValueError("Draft review does not bind this exact candidate, sources, plan, audience and rendered text.")
        reviewer = draft_review.get("reviewer", {})
        reviewer_id = reviewer.get("reviewer_id")
        if not isinstance(reviewer_id, str) or not reviewer_id.strip() or reviewer.get("kind") not in ("human", "model") or reviewer.get("independent_from_producer") is not True:
            raise ValueError("Draft reviewer identity and declared independence are required.")
        if reviewer_id.strip().casefold() == inventory["producer_id"].strip().casefold():
            raise ValueError("The draft producer cannot supply its independent review.")
        reviewed = datetime.fromisoformat(draft_review.get("reviewed_at", "").replace("Z", "+00:00"))
        if reviewed.utcoffset() is None or not isinstance(draft_review.get("review_reference"), str) or not draft_review["review_reference"].strip():
            raise ValueError("Draft review requires a dated, referenced decision record.")
        checks = draft_review.get("checks")
        if not isinstance(checks, list) or len(checks) != len(CRITERIA) or any(not isinstance(c, dict) for c in checks) or {c.get("criterion") for c in checks} != set(CRITERIA):
            raise ValueError("Draft review must cover each semantic criterion exactly once.")
        for check in checks:
            if check.get("status") != "pass" or not isinstance(check.get("rationale"), str) or not check["rationale"].strip():
                raise ValueError("A draft semantic criterion failed or remains unreviewed.")
        result.update(status="reviewed-draft", recipient_draft=projected["rendered_markdown"],
                      draft_review_sha256=evidence_gate.hash_object(draft_review),
                      review_basis="Recorded independent assessment; identity and judgment are not authenticated.")
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        result["findings"].append(str(exc))
    return result


def validate(result, candidate, packet, inventory, field_review, request, plan, draft_review, rendered_bytes):
    """Verify the exact recipient file and all recorded inputs, not just status."""
    try:
        expected = assemble(candidate, packet, inventory, field_review, request, plan, draft_review)
        errors = []
        if evidence_gate.hash_object(result) != evidence_gate.hash_object(expected):
            errors.append("Quality result differs from reconstructed checks.")
        if expected["status"] != "reviewed-draft" or not isinstance(rendered_bytes, bytes) or rendered_bytes != expected["recipient_draft"].encode("utf-8"):
            errors.append("Actual recipient bytes are absent, changed or not reviewed.")
        return errors
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError, OverflowError):
        return ["Quality validation inputs are malformed or exceed supported bounds."]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "sources", "inventory", "field-review", "request", "plan"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--draft-review")
    parser.add_argument("--receipt", required=True, help="New restricted operator-only result file")
    parser.add_argument("--rendered", required=True, help="New exact-recipient Markdown file; written only on reviewed-draft")
    parser.add_argument("--verify", action="store_true", help="Reconstruct and verify existing receipt and actual rendered file")
    args = parser.parse_args(argv)
    input_paths = [getattr(args, name) for name in ("candidate", "sources", "inventory", "field_review", "request", "plan")]
    if args.draft_review:
        input_paths.append(args.draft_review)
    try:
        output_paths = [Path(args.receipt).resolve(), Path(args.rendered).resolve()]
        if len(set(output_paths)) != 2 or set(output_paths) & {Path(p).resolve() for p in input_paths}:
            raise ValueError("Inputs, restricted receipt and recipient draft must use distinct paths.")
        values = [evidence_gate._load(p) for p in input_paths[:6]]
        draft_review = evidence_gate._load(args.draft_review) if args.draft_review else None
        if args.verify:
            errors = validate(evidence_gate._load(args.receipt), *values, draft_review, Path(args.rendered).read_bytes())
            print("Verified exact reviewed recipient draft." if not errors else audience_gate.PUBLIC_FAILURE)
            return bool(errors)
        if any(p.exists() for p in output_paths):
            raise ValueError("Output already exists; preserve prior attempts and choose new filenames.")
        result = assemble(*values, draft_review)
        def private_opener(path, flags):
            return os.open(path, flags, 0o600)
        with open(args.receipt, "x", encoding="utf-8", opener=private_opener) as stream:
            stream.write(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        if result["status"] == "reviewed-draft":
            with open(args.rendered, "xb", opener=private_opener) as stream:
                stream.write(result["recipient_draft"].encode("utf-8"))
            print("Reviewed recipient draft written; professional approval remains required.")
            return 0
        print(audience_gate.PUBLIC_FAILURE)
        return 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError):
        # Do not leak source IDs, filenames or restricted diagnostics to recipients.
        print(audience_gate.PUBLIC_FAILURE)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
