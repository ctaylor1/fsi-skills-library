"""Deterministic, stdlib-only recipient projection for supplied wealth evidence.

This checks declared source permissions and declared dependencies, not whether
the permission is authentic or a model declared every semantic dependency.
The receipt is INTERNAL. Only rendered_markdown is a recipient draft. A caller
must compose this gate with independent evidence review and deployment access.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import sys


PACKET_SCHEMA = "wealth-source-packet-v1"
REQUEST_SCHEMA = "wealth-audience-request-v1"
PLAN_SCHEMA = "wealth-audience-plan-v1"
PROJECTION_SCHEMA = "wealth-audience-projection-v1"
RECEIPT_SCHEMA = "wealth-audience-receipt-v1"
PUBLIC_FAILURE = "Draft unavailable: recipient and evidence checks require review."
_GENERIC = {"all", "anyone", "everyone", "public", "internal", "staff", "team",
            "reviewers", "internal-reviewers", "all-audiences", "*"}
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,127}\Z")
_BAD_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u202a-\u202e\u2066-\u2069]")


class GateError(ValueError):
    """Detailed diagnostics are operator-only; never render them to recipients."""

    def __init__(self, errors):
        self.errors = list(errors)
        self.public_message = PUBLIC_FAILURE
        super().__init__("; ".join(self.errors))


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _json_shape(value):
    """Reject Python-only types and non-string keys before structural inspection."""
    pending, seen = [value], set()
    while pending:
        item = pending.pop()
        if isinstance(item, (dict, list)):
            if id(item) in seen:
                continue  # canonical serialization separately rejects cycles.
            seen.add(id(item))
            if isinstance(item, dict):
                if not all(isinstance(key, str) for key in item):
                    return False
                pending.extend(item.values())
            else:
                pending.extend(item)
        elif item is not None and not isinstance(item, (str, int, float, bool)):
            return False
    return True


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and not _BAD_CONTROL.search(value)


def _id(value):
    return isinstance(value, str) and bool(_ID.fullmatch(value)) and value.lower() not in _GENERIC


def _date(value):
    try:
        d = date.fromisoformat(value) if isinstance(value, str) else None
        return d if d and d.isoformat() == value else None
    except ValueError:
        return None


def _pointer(value):
    return (isinstance(value, str) and value.startswith("/")
            and not re.search(r"~(?![01])", value) and not _BAD_CONTROL.search(value))


def _unique_list(value, check, allow_empty=False):
    return (isinstance(value, list) and (bool(value) or allow_empty)
            and all(check(v) for v in value) and len(set(value)) == len(value))


def _object(value, required, allowed, label, errors):
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    if not required <= value.keys():
        errors.append(f"{label}: missing required fields {sorted(required - value.keys())}")
    if allowed is not None and not value.keys() <= allowed:
        errors.append(f"{label}: unknown fields {sorted(value.keys() - allowed)}")
    return True


def _validate(request, packet, plan):
    errors = []
    for name, doc in [("request", request), ("source_packet", packet), ("content_plan", plan)]:
        try:
            if not _json_shape(doc):
                raise ValueError("not JSON")
            canonical_bytes(doc)
        except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError):
            errors.append(f"{name} must be finite serializable JSON")
    if errors:
        raise GateError(errors)

    request_keys = {"schema_version", "request_id", "as_of", "recipient_ids"}
    if not _object(request, request_keys, request_keys, "request", errors):
        raise GateError(errors)
    if request.get("schema_version") != REQUEST_SCHEMA:
        errors.append("unsupported audience request schema")
    if not _id(request.get("request_id")):
        errors.append("request_id must be a concrete identifier")
    if _date(request.get("as_of")) is None:
        errors.append("request.as_of must be an ISO calendar date")
    if not _unique_list(request.get("recipient_ids"), _id):
        errors.append("recipient_ids must be nonempty unique exact person identifiers")

    packet_keys = {"schema_version", "packet_id", "recipients", "sources"}
    if not _object(packet, packet_keys, None, "source_packet", errors):
        raise GateError(errors)
    if packet.get("schema_version") != PACKET_SCHEMA:
        errors.append("unsupported detached source packet schema")
    if not _id(packet.get("packet_id")):
        errors.append("packet_id must be a concrete identifier")
    people = set()
    if not isinstance(packet.get("recipients"), list) or not packet["recipients"]:
        errors.append("detached packet requires an exact recipient registry")
    else:
        for i, row in enumerate(packet["recipients"]):
            if not _object(row, {"recipient_id", "kind"}, {"recipient_id", "kind"}, f"recipients[{i}]", errors):
                continue
            rid = row.get("recipient_id")
            if not _id(rid) or row.get("kind") != "person":
                errors.append(f"recipients[{i}] must identify one person, not an audience group")
            elif rid in people:
                errors.append(f"duplicate recipient_id: {rid}")
            else:
                people.add(rid)
    if _unique_list(request.get("recipient_ids"), _id):
        for rid in request["recipient_ids"]:
            if rid not in people:
                errors.append(f"unknown requested recipient: {rid}")

    sources = {}
    if not isinstance(packet.get("sources"), list) or not packet["sources"]:
        errors.append("detached packet requires nonempty sources")
    else:
        for i, row in enumerate(packet["sources"]):
            label = f"sources[{i}]"
            if not _object(row, {"source_id", "reference", "content", "access"}, None, label, errors):
                continue
            sid = row.get("source_id")
            if not _id(sid):
                errors.append(f"{label}.source_id must be a concrete identifier")
            elif sid in sources:
                errors.append(f"duplicate source_id: {sid}")
            else:
                sources[sid] = row
            for field in ("reference", "content"):
                if not _text(row.get(field)):
                    errors.append(f"{label}.{field} must be nonempty safe text")
            access = row.get("access")
            keys = {"allowed_recipient_ids", "effective_date", "valid_until"}
            if not _object(access, keys, keys, f"{label}.access", errors):
                continue
            ids = access.get("allowed_recipient_ids")
            if not _unique_list(ids, _id, allow_empty=True):
                errors.append(f"{label}.access needs explicit unique person IDs (empty denies all)")
            else:
                for rid in ids:
                    if rid not in people:
                        errors.append(f"{label}.access names an unknown recipient: {rid}")
            start, end = _date(access.get("effective_date")), _date(access.get("valid_until"))
            if not start or not end or end < start:
                errors.append(f"{label}.access needs an ordered ISO permission interval")

    if not _object(plan, {"schema_version", "blocks"}, {"schema_version", "blocks"}, "content_plan", errors):
        raise GateError(errors)
    if plan.get("schema_version") != PLAN_SCHEMA:
        errors.append("unsupported content plan schema")
    blocks = {}
    if not isinstance(plan.get("blocks"), list) or not plan["blocks"]:
        errors.append("content_plan.blocks must be nonempty")
    else:
        keys = {"block_id", "heading", "text", "source_ids", "depends_on_block_ids", "claim_ids"}
        for i, block in enumerate(plan["blocks"]):
            label = f"blocks[{i}]"
            if not _object(block, keys, keys, label, errors):
                continue
            bid = block.get("block_id")
            if not _id(bid):
                errors.append(f"{label}.block_id must be a concrete identifier")
            elif bid in blocks:
                errors.append(f"duplicate block_id: {bid}")
            else:
                blocks[bid] = block
            for field in ("heading", "text"):
                if not _text(block.get(field)):
                    errors.append(f"{label}.{field} must be nonempty safe text")
            if not _unique_list(block.get("source_ids"), _id):
                errors.append(f"{label}.source_ids must be explicit and nonempty")
            else:
                for sid in block["source_ids"]:
                    if sid not in sources:
                        errors.append(f"{label}: unknown source {sid}")
            if not _unique_list(block.get("depends_on_block_ids"), _id, allow_empty=True):
                errors.append(f"{label}.depends_on_block_ids must be explicit unique identifiers")
            if not _unique_list(block.get("claim_ids"), _pointer):
                errors.append(f"{label}.claim_ids must be nonempty unique JSON Pointers")
    if errors:
        raise GateError(errors)
    for bid, block in blocks.items():
        for dep in block["depends_on_block_ids"]:
            if dep not in blocks:
                errors.append(f"block {bid} has unknown dependency {dep}")
    if errors:
        raise GateError(errors)
    # Iterative dependency order avoids recursion limits for long valid chains.
    waiting = {bid: len(block["depends_on_block_ids"]) for bid, block in blocks.items()}
    dependants = {bid: [] for bid in blocks}
    for bid, block in blocks.items():
        for dep in block["depends_on_block_ids"]:
            dependants[dep].append(bid)
    ready = deque(bid for bid, count in waiting.items() if count == 0)
    dependency_order = []
    while ready:
        bid = ready.popleft()
        dependency_order.append(bid)
        for dependant in dependants[bid]:
            waiting[dependant] -= 1
            if waiting[dependant] == 0:
                ready.append(dependant)
    if len(dependency_order) != len(blocks):
        raise GateError(["cyclic block dependency"])
    return sources, blocks, dependency_order


def _literal(text):
    """Render text literally: no author-supplied markup, HTML, links or images."""
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    escaped = re.sub(r"([\\`*_{}\[\]()#+.!|~-])", r"\\\1", escaped)
    # Indentation cannot turn source text into executable/hidden code or markup.
    return "\n".join(line.strip() for line in escaped.splitlines())


def render_projection(projection):
    """Internal renderer. Release checks must rebuild, not trust this input alone."""
    lines = ["# Draft for review", "", "Recipients: " + ", ".join(
        _literal(rid) for rid in projection["recipient_ids"]), "",
        "Human review required. Not delivered.", ""]
    for block in projection["blocks"]:
        lines += ["## " + _literal(block["heading"]), "", _literal(block["text"]), "",
                  "Sources: " + ", ".join(_literal(s) for s in block["source_ids"]), ""]
    lines += ["## Sources used", ""]
    for source in projection["sources"]:
        lines += ["- " + _literal(source["source_id"]) + ": " + _literal(source["reference"])]
    return "\n".join(lines) + "\n"


def project(request, source_packet, content_plan):
    """Return one exact-recipient draft plus a separate INTERNAL receipt.

    source_packet must be detached operator-supplied evidence; no permission is
    inferred from source ownership, professional roles or the generated plan.
    claim_ids are JSON Pointer references for the composing evidence gate. This
    module does not resolve or semantically approve those claims.
    """
    sources, blocks, dependency_order = _validate(request, source_packet, content_plan)
    recipients = set(request["recipient_ids"])
    as_of = _date(request["as_of"])
    allowed_sources = {sid for sid, s in sources.items()
                       if recipients <= set(s["access"]["allowed_recipient_ids"])
                       and _date(s["access"]["effective_date"]) <= as_of
                       <= _date(s["access"]["valid_until"])}
    closures = {}

    for bid in dependency_order:
        refs = set(blocks[bid]["source_ids"])
        for dep in blocks[bid]["depends_on_block_ids"]:
            refs.update(closures[dep])
        closures[bid] = refs

    included = [b for b in content_plan["blocks"] if closures[b["block_id"]] <= allowed_sources]
    if not included:
        raise GateError(["no blocks are authorized by current declared permissions for all recipients"])
    used = set()
    public_blocks = []
    for block in included:
        refs = sorted(closures[block["block_id"]])
        used.update(refs)
        # Do not expose original block IDs, claim pointers, dependency IDs,
        # excluded labels/counts or the full packet/permission registry.
        public_blocks.append({"heading": block["heading"], "text": block["text"], "source_ids": refs})
    projection = {"schema_version": PROJECTION_SCHEMA,
                  "recipient_ids": sorted(recipients), "blocks": public_blocks,
                  "sources": [{"source_id": sid, "reference": sources[sid]["reference"]}
                              for sid in sorted(used)]}
    rendered = render_projection(projection)
    receipt = {"schema_version": RECEIPT_SCHEMA, "visibility": "operator-only",
               "status": "declared-audience-projection-checked",
               "request_sha256": digest(request), "source_packet_sha256": digest(source_packet),
               "content_plan_sha256": digest(content_plan), "projection_sha256": digest(projection),
               "rendered_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
               "recipient_ids": sorted(recipients),
               "included_block_ids": [b["block_id"] for b in included],
               "claim_ids": sorted({p for b in included for p in b["claim_ids"]}),
               "human_review_required": True, "action_taken": False,
               "permission_authentication": "not-established",
               "semantic_dependency_completeness": "not-established",
               "deployment_access_enforcement": "not-established"}
    return {"projection": projection, "rendered_markdown": rendered, "receipt": receipt}


def validate_projection(request, source_packet, content_plan, bundle):
    """Operator-only errors. Recompute every component from the detached inputs."""
    try:
        expected = project(request, source_packet, content_plan)
    except GateError as exc:
        return exc.errors
    try:
        return [] if canonical_bytes(bundle) == canonical_bytes(expected) else ["projection bundle differs from reconstructed artifact"]
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError):
        return ["projection bundle is not finite serializable JSON"]


def validate_rendered(request, source_packet, content_plan, rendered_bytes, receipt):
    """Reject raw Markdown plus copied/forged sidecars unless exact reconstruction matches."""
    try:
        expected = project(request, source_packet, content_plan)
    except GateError as exc:
        return exc.errors
    errors = []
    if not isinstance(rendered_bytes, bytes) or rendered_bytes != expected["rendered_markdown"].encode("utf-8"):
        errors.append("actual rendered bytes differ from the recipient-specific reconstruction")
    try:
        if canonical_bytes(receipt) != canonical_bytes(expected["receipt"]):
            errors.append("receipt differs from reconstructed internal binding")
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError):
        errors.append("receipt is not finite serializable JSON")
    return errors


def _load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite JSON")))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["render", "validate"])
    parser.add_argument("--request", required=True)
    parser.add_argument("--source-packet", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--rendered", required=True, help="one exact-recipient UTF-8 Markdown file")
    parser.add_argument("--receipt", required=True, help="separate operator-only receipt; never recipient content")
    args = parser.parse_args(argv)
    try:
        paths = [Path(p).resolve() for p in [args.request, args.source_packet, args.plan, args.rendered, args.receipt]]
        if len(set(paths)) != len(paths):
            raise GateError(["inputs, rendered draft and operator receipt must use distinct paths"])
        existing = [p for p in paths if p.exists()]
        if any(p.samefile(q) for i, p in enumerate(existing) for q in existing[i + 1:]):
            raise GateError(["input and output files must not be hard-link aliases"])
        request, packet, plan = _load(args.request), _load(args.source_packet), _load(args.plan)
        if args.mode == "render":
            if Path(args.rendered).exists() or Path(args.receipt).exists():
                raise GateError(["render does not overwrite existing files"])
            result = project(request, packet, plan)
            # Separate explicit destinations; never emit an all-audiences bundle.
            # Exclusive creation also prevents symlink substitution/overwrite
            # between the earlier check and the actual file creation.
            def private_opener(path, flags):
                return os.open(path, flags, 0o600)
            with open(args.receipt, "xb", opener=private_opener) as receipt_file:
                with open(args.rendered, "xb", opener=private_opener) as rendered_file:
                    receipt_file.write(canonical_bytes(result["receipt"]) + b"\n")
                    rendered_file.write(result["rendered_markdown"].encode("utf-8"))
        else:
            errors = validate_rendered(request, packet, plan, Path(args.rendered).read_bytes(), _load(args.receipt))
            if errors:
                raise GateError(errors)
    except (GateError, ValueError, OSError, UnicodeError):
        # Even stderr is generic, so clients cannot infer private source details.
        print(PUBLIC_FAILURE, file=sys.stderr)
        return 1
    print("Recipient draft check completed; no delivery or authorization performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
