#!/usr/bin/env python3
"""Deterministic output validation for data-lineage-documenter.

Enforces the R3 "Draft & package" guardrails before a data-lineage document is handed to a
data-governance owner and data steward for review and approval:
  1. Template fidelity / completeness: required top-level sections and per-node / per-edge
     fields are present; every node layer is in the approved taxonomy.
  2. No unsupported/unapproved claims: a node/edge asserting a `traced` provenance must cite
     the source it traces to; a node/edge marked `ready-for-review` must be fully documented
     (owner + traced provenance + the attributes its criticality requires; edges: a documented
     transformation traced to a source) - no untraced lineage passes as ready.
  3. Graph & coverage integrity: `coverage.complete` is consistent with the node/edge statuses
     and graph soundness; a package marked `ready-for-governance-review` is genuinely complete,
     graph-sound, and has every node and edge ready.
  4. No autonomous certification/attestation: the skill never certifies, attests to, or
     approves the lineage, never asserts the data is accurate/complete/fit for regulatory
     reporting, and never claims a catalog/system-of-record write.
  5. Required approvals: governance_approval is `pending` and reviewer_signoff_required is true.
  6. The standing disclaimer is present.

Fails closed on any miss so a defective or overreaching lineage document cannot be presented as
certified, complete, or a governance decision.

Usage: python validate_output.py document.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

KNOWN_LAYERS = {"source", "ingestion", "transformation", "store", "feature", "output"}
REQUIRED_ATTRS = {
    "High": ("owner", "provenance", "classification", "controls", "quality_rules", "retention"),
    "Medium": ("owner", "provenance", "classification", "controls", "retention"),
    "Low": ("owner", "provenance"),
}
DOC_ATTRS = ("classification", "controls", "quality_rules", "retention")
ALLOWED_NODE_STATUS = {"ready-for-review", "control-gap", "orphan-node", "needs-data"}
ALLOWED_EDGE_STATUS = {"ready-for-review", "undocumented-transform", "dangling-edge"}
REQUIRED_TOP = ("data_product", "nodes", "edges", "graph_integrity", "coverage", "approvals", "standing_note")
REQUIRED_NODE = ("node_id", "layer", "owner", "provenance", "status")
REQUIRED_EDGE = ("edge_id", "from_node", "to_node", "transformation", "status")

STANDING_NOTE = (
    "Draft data-lineage documentation for human review only; this skill does not certify, "
    "attest to, or approve the lineage, makes no data-accuracy or regulatory-fitness "
    "determination, and writes nothing to the data catalog or any system of record"
)

# Language that would turn a draft lineage document into a certification / attestation /
# accuracy or regulatory-fitness determination, or claim a system-of-record write.
DETERMINATION_PATTERNS = [
    r"\blineage (is )?(certified|approved|attested)\b",
    r"\bcertif(y|ied|ication) (the |that the )?(lineage|data)\b",
    r"\bcertified (complete|accurate|correct|compliant)\b",
    r"\bwe attest\b", r"\battestation (is )?complete\b",
    r"\bdata is (accurate|complete|correct|fit for)\b",
    r"\bfit for regulatory reporting\b", r"\bapproved for regulatory reporting\b",
    r"\bbcbs ?239 compliant\b", r"\bfully compliant\b",
    r"\bsign-?off (is )?complete\b", r"\bgovernance sign-?off (is )?complete\b",
    r"\bno further (review|validation|documentation) (is )?(needed|required)\b",
    r"\bcatalog (has been |was )?updated\b", r"\bwritten to the (data )?catalog\b",
    r"\bregistered in the catalog\b", r"\bsystem of record (has been |was )?updated\b",
]


def _has(node, attr):
    v = node.get(attr)
    if attr == "retention":
        return isinstance(v, dict) and bool(v.get("policy_id"))
    if attr in ("controls", "quality_rules"):
        return isinstance(v, list) and len(v) > 0
    return bool(v)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level section '{k}'")
    if errors:
        return errors

    nodes = doc.get("nodes") or []
    edges = doc.get("edges") or []
    if not nodes:
        return ["lineage document has no nodes"]

    crit = (doc.get("data_product") or {}).get("criticality")
    required_attrs = REQUIRED_ATTRS.get(crit, REQUIRED_ATTRS["High"])

    node_ids = {n.get("node_id") for n in nodes}

    for n in nodes:
        nid = n.get("node_id", "?")
        for k in REQUIRED_NODE:
            if k not in n:
                errors.append(f"{nid}: missing node field '{k}'")
        layer = n.get("layer")
        if layer not in KNOWN_LAYERS:
            errors.append(f"{nid}: unknown node layer {layer!r} (not in approved taxonomy)")
        status = n.get("status")
        if status not in ALLOWED_NODE_STATUS:
            errors.append(f"{nid}: invalid node status {status!r}")
        prov = n.get("provenance") or {}
        # A node asserting a traced provenance must cite the source it traces to.
        if prov.get("status") == "traced" and not prov.get("source_id"):
            errors.append(f"{nid}: provenance marked 'traced' without a source citation (unsupported claim)")
        # Strict invariants for anything presented as ready.
        if status == "ready-for-review":
            if not n.get("owner"):
                errors.append(f"{nid}: ready-for-review but no data owner/steward")
            if prov.get("status") != "traced":
                errors.append(f"{nid}: ready-for-review but provenance not traced to an authoritative source")
            if layer != "source" and nid not in {e.get("to_node") for e in edges if e.get("status") != "dangling-edge"}:
                errors.append(f"{nid}: ready-for-review but orphaned (no inbound dependency)")
            for attr in DOC_ATTRS:
                if attr in required_attrs and not _has(n, attr):
                    errors.append(f"{nid}: ready-for-review but required '{attr}' missing for {crit} criticality")

    for e in edges:
        eid = e.get("edge_id", "?")
        for k in REQUIRED_EDGE:
            if k not in e:
                errors.append(f"{eid}: missing edge field '{k}'")
        status = e.get("status")
        if status not in ALLOWED_EDGE_STATUS:
            errors.append(f"{eid}: invalid edge status {status!r}")
        prov = e.get("provenance") or {}
        if prov.get("status") == "traced" and not prov.get("source_id"):
            errors.append(f"{eid}: provenance marked 'traced' without a source citation (unsupported claim)")
        if status == "ready-for-review":
            if e.get("from_node") not in node_ids or e.get("to_node") not in node_ids:
                errors.append(f"{eid}: ready-for-review but references an unknown node (dangling)")
            if not e.get("transformation"):
                errors.append(f"{eid}: ready-for-review but transformation not documented")
            if prov.get("status") != "traced":
                errors.append(f"{eid}: ready-for-review but transformation not traced to an authoritative source")

    # Graph + coverage integrity.
    gi = doc.get("graph_integrity") or {}
    cov = doc.get("coverage") or {}
    non_ready = (any(n.get("status") != "ready-for-review" for n in nodes)
                 or any(e.get("status") != "ready-for-review" for e in edges)
                 or not gi.get("sound"))
    if bool(cov.get("complete")) == bool(non_ready):
        errors.append(f"coverage.complete={cov.get('complete')} inconsistent with node/edge statuses and graph soundness")

    if doc.get("package_status") == "ready-for-governance-review":
        if not gi.get("sound"):
            errors.append("package_status 'ready-for-governance-review' but graph is not sound")
        if not cov.get("complete"):
            errors.append("package_status 'ready-for-governance-review' but coverage is incomplete")
        if any(n.get("status") != "ready-for-review" for n in nodes) or any(e.get("status") != "ready-for-review" for e in edges):
            errors.append("package_status 'ready-for-governance-review' but not every node/edge is ready-for-review")

    # Required approvals: the skill proposes; it never self-approves.
    appr = doc.get("approvals") or {}
    if appr.get("governance_approval") != "pending":
        errors.append(f"governance_approval must be 'pending'; the skill cannot self-approve governance (got {appr.get('governance_approval')!r})")
    if appr.get("reviewer_signoff_required") is not True:
        errors.append("reviewer_signoff_required must be true")

    # Certification / attestation / accuracy-determination / catalog-write language screen.
    scan = json.dumps(nodes) + " " + json.dumps(edges) + " " + json.dumps(appr) + " " + str(doc.get("narrative", ""))
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited certification/attestation/write language detected: {m.group(0)!r} (this skill drafts lineage; it never certifies, attests, or writes a system of record)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "lineage_example.json"
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
