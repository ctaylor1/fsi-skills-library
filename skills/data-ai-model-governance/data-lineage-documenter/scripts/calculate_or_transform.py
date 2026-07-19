#!/usr/bin/env python3
"""Deterministic data-lineage document builder for data-lineage-documenter.

For a data product it takes documented lineage NODES (source-to-output stages) and EDGES
(dependencies with their transformations) and assembles an audit-ready lineage document as a
DRAFT for data-governance review. For each node it: confirms the layer is in the approved
taxonomy, resolves the PROVENANCE of the node against the authoritative-source list (traced vs
untraced), checks the required documented attributes for the product's criticality (owner,
classification, controls, quality rules, retention), checks whether the node is connected
(no orphan), and assigns a deterministic status. For each edge it resolves whether the
transformation is documented and traced. It then computes graph integrity (source/output
present, cycle-free, no orphans, no dangling edges) and a criticality-scaled coverage matrix.

It NEVER certifies, attests to, or approves the lineage, never asserts the data is accurate,
complete, or fit for regulatory reporting, never invents a source it cannot trace, and never
writes to the data catalog or any system of record. `governance_approval` is always emitted as
`pending`; every node/edge asserting a traced provenance carries the source it traces to.

Usage: python calculate_or_transform.py request.json | --selftest
Prints the lineage document JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

STANDING_NOTE = (
    "Draft data-lineage documentation for human review only; this skill does not certify, "
    "attest to, or approve the lineage, makes no data-accuracy or regulatory-fitness "
    "determination, and writes nothing to the data catalog or any system of record - a data-"
    "governance owner and data steward must review and approve before use."
)

# Approved node-layer taxonomy (the ONLY layers permitted).
KNOWN_LAYERS = ("source", "ingestion", "transformation", "store", "feature", "output")

# Documented node attributes required by the data product's criticality (versioned methodology,
# not judgment). 'owner' and 'provenance' are structural (missing -> needs-data); the rest are
# documentation attributes (missing -> control-gap).
REQUIRED_ATTRS = {
    "High": ("owner", "provenance", "classification", "controls", "quality_rules", "retention"),
    "Medium": ("owner", "provenance", "classification", "controls", "retention"),
    "Low": ("owner", "provenance"),
}
DOC_ATTRS = ("classification", "controls", "quality_rules", "retention")


def _source_ids(doc):
    return {s.get("source_id") for s in (doc.get("authoritative_sources") or []) if s.get("source_id")}


def _has(node, attr):
    v = node.get(attr)
    if attr == "retention":
        return isinstance(v, dict) and bool(v.get("policy_id"))
    if attr in ("controls", "quality_rules"):
        return isinstance(v, list) and len(v) > 0
    return bool(v)


def build_edge(e, node_ids, source_ids):
    eid = e.get("edge_id")
    frm = e.get("from_node")
    to = e.get("to_node")
    transform = e.get("transformation")
    sid = e.get("source_id")
    prov = "traced" if (sid and sid in source_ids) else "untraced"
    citations = []
    if sid:
        citations.append(f"source:{sid}")
    if e.get("transform_ref"):
        citations.append(f"transform:{e['transform_ref']}")
    notes = []
    rec = {
        "edge_id": eid, "from_node": frm, "to_node": to,
        "transformation": transform,
        "provenance": {"status": prov, "source_id": sid},
        "citations": citations, "notes": notes,
    }
    if frm not in node_ids or to not in node_ids:
        missing = [x for x in (frm, to) if x not in node_ids]
        notes.append(f"edge references unknown node(s): {missing}")
        rec["status"] = "dangling-edge"
        return rec
    if not transform or prov != "traced":
        if not transform:
            notes.append("transformation not documented")
        if prov != "traced":
            notes.append("transformation not traced to an authoritative source")
        rec["status"] = "undocumented-transform"
        return rec
    notes.append("edge documented and traced")
    rec["status"] = "ready-for-review"
    return rec


def build_node(n, source_ids, required_attrs, inbound):
    nid = n.get("node_id")
    layer = n.get("layer")
    owner = n.get("owner")
    sid = n.get("source_id")
    prov = "traced" if (sid and sid in source_ids) else "untraced"
    citations = []
    if sid:
        citations.append(f"source:{sid}")
    if n.get("catalog_ref"):
        citations.append(f"data-catalog:{n['catalog_ref']}")
    notes = []
    gaps = []
    rec = {
        "node_id": nid, "layer": layer, "name": n.get("name"),
        "system": n.get("system"), "owner": owner,
        "classification": n.get("classification"),
        "provenance": {"status": prov, "source_id": sid},
        "controls": n.get("controls") or [],
        "quality_rules": n.get("quality_rules") or [],
        "retention": n.get("retention") or {},
        "citations": citations, "gaps": gaps, "notes": notes,
    }

    # Deterministic status precedence (fail closed; never invent a source).
    if layer not in KNOWN_LAYERS:
        notes.append(f"layer {layer!r} not in approved taxonomy {list(KNOWN_LAYERS)}")
        rec["status"] = "needs-data"
        return rec
    if not owner:
        notes.append("no data owner/steward recorded")
        gaps.append("owner")
        rec["status"] = "needs-data"
        return rec
    if prov != "traced":
        notes.append("node not traced to an authoritative source (untraced provenance)")
        gaps.append("provenance")
        rec["status"] = "needs-data"
        return rec
    if layer != "source" and nid not in inbound:
        notes.append("non-source node has no inbound dependency (orphan)")
        rec["status"] = "orphan-node"
        return rec
    for attr in DOC_ATTRS:
        if attr in required_attrs and not _has(n, attr):
            gaps.append(attr)
    if gaps:
        notes.append(f"required documentation missing for criticality: {gaps}")
        rec["status"] = "control-gap"
        return rec
    notes.append("owner, provenance, classification, controls, quality rules, and retention documented")
    rec["status"] = "ready-for-review"
    return rec


def _cycle_free(node_ids, edges):
    adj = {nid: [] for nid in node_ids}
    for e in edges:
        if e["status"] == "dangling-edge":
            continue
        adj[e["from_node"]].append(e["to_node"])
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in node_ids}

    def dfs(u):
        color[u] = GRAY
        for v in adj.get(u, []):
            if color[v] == GRAY:
                return False
            if color[v] == WHITE and not dfs(v):
                return False
        color[u] = BLACK
        return True

    return all(dfs(nid) for nid in node_ids if color[nid] == WHITE)


def build(doc: dict) -> dict:
    dp = doc.get("data_product") or {}
    crit = dp.get("criticality")
    required_attrs = REQUIRED_ATTRS.get(crit, REQUIRED_ATTRS["High"])
    source_ids = _source_ids(doc)
    node_ids = {n.get("node_id") for n in (doc.get("nodes") or [])}

    edges = [build_edge(e, node_ids, source_ids) for e in (doc.get("edges") or [])]
    inbound = {e["to_node"] for e in edges if e["status"] != "dangling-edge"}
    nodes = [build_node(n, source_ids, required_attrs, inbound) for n in (doc.get("nodes") or [])]

    layers_present = {n["layer"] for n in nodes}
    orphan_nodes = [n["node_id"] for n in nodes if n["status"] == "orphan-node"]
    dangling_edges = [e["edge_id"] for e in edges if e["status"] == "dangling-edge"]
    cycle_free = _cycle_free(node_ids, edges)
    graph_sound = ("source" in layers_present and "output" in layers_present
                   and cycle_free and not orphan_nodes and not dangling_edges)
    graph_integrity = {
        "has_source": "source" in layers_present,
        "has_output": "output" in layers_present,
        "cycle_free": cycle_free,
        "orphan_nodes": orphan_nodes,
        "dangling_edges": dangling_edges,
        "sound": graph_sound,
    }

    nodes_ready = sum(1 for n in nodes if n["status"] == "ready-for-review")
    edges_ready = sum(1 for e in edges if e["status"] == "ready-for-review")
    complete = bool(nodes) and nodes_ready == len(nodes) and edges_ready == len(edges) and graph_sound
    coverage = {
        "criticality": crit,
        "required_node_attributes": list(required_attrs),
        "nodes_total": len(nodes),
        "nodes_ready": nodes_ready,
        "nodes_with_gaps": len(nodes) - nodes_ready,
        "edges_total": len(edges),
        "edges_ready": edges_ready,
        "edges_with_gaps": len(edges) - edges_ready,
        "complete": complete,
    }
    package_status = "ready-for-governance-review" if complete else "draft-incomplete"

    def _ncount(s):
        return sum(1 for n in nodes if n["status"] == s)

    def _ecount(s):
        return sum(1 for e in edges if e["status"] == s)

    summary = {
        "nodes": {
            "ready_for_review": _ncount("ready-for-review"),
            "control_gap": _ncount("control-gap"),
            "orphan_node": _ncount("orphan-node"),
            "needs_data": _ncount("needs-data"),
        },
        "edges": {
            "ready_for_review": _ecount("ready-for-review"),
            "undocumented_transform": _ecount("undocumented-transform"),
            "dangling_edge": _ecount("dangling-edge"),
        },
    }

    return {
        "spec_version": doc.get("spec_version"),
        "as_of_date": doc.get("as_of_date"),
        "data_product": {
            "product_id": dp.get("product_id"),
            "name": dp.get("name"),
            "domain": dp.get("domain"),
            "criticality": crit,
            "catalog_ref": dp.get("catalog_ref"),
        },
        "nodes": nodes,
        "edges": edges,
        "graph_integrity": graph_integrity,
        "coverage": coverage,
        "package_status": package_status,
        "approvals": {
            "governance_approval": "pending",
            "reviewer_signoff_required": True,
            "steward_attestation_required": True,
            "approver_role": "Data Governance Office / Chief Data Office",
        },
        "summary": summary,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "lineage_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
