#!/usr/bin/env python3
"""Deterministic input validation for data-lineage-documenter.

Validates a lineage build request before a lineage document is drafted. Fails closed on
structural problems (so a lineage document is never assembled from an ill-formed request);
warns on data gaps that will force a `needs-data`, `control-gap`, `orphan-node`,
`undocumented-transform`, or `dangling-edge` status on individual nodes/edges.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  spec_version, as_of_date?, data_product{product_id, name?, domain?,
    criticality(High|Medium|Low), catalog_ref?},
  authoritative_sources[{source_id, type(data-catalog|model-registry|agent-tool-log|policy|
    data-contract|issue-log), ref, owner?}],
  nodes[{node_id, layer(source|ingestion|transformation|store|feature|output), name?, system?,
    owner?, classification?, source_id?, catalog_ref?, controls[]?, quality_rules[]?,
    retention{policy_id, period}?}],
  edges[{edge_id, from_node, to_node, transformation?, source_id?, transform_ref?}]

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("spec_version", "data_product", "nodes", "edges")
REQUIRED_NODE = ("node_id", "layer")
REQUIRED_EDGE = ("edge_id", "from_node", "to_node")
KNOWN_LAYERS = {"source", "ingestion", "transformation", "store", "feature", "output"}
CRITICALITY = {"High", "Medium", "Low"}


def _is_iso_date(v) -> bool:
    try:
        date.fromisoformat(str(v))
        return True
    except Exception:
        return False


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if doc.get("as_of_date") and not _is_iso_date(doc.get("as_of_date")):
        errors.append("as_of_date is not an ISO date (YYYY-MM-DD)")

    dp = doc.get("data_product") or {}
    if not isinstance(dp, dict):
        errors.append("data_product must be an object")
    else:
        if not dp.get("product_id"):
            errors.append("data_product.product_id is required (identify the data product)")
        if dp.get("criticality") not in CRITICALITY:
            errors.append(f"data_product.criticality must be one of {sorted(CRITICALITY)} (drives required documentation)")

    sources = doc.get("authoritative_sources") or []
    source_ids = set()
    for i, s in enumerate(sources):
        if not s.get("source_id"):
            errors.append(f"authoritative_sources[{i}]: missing source_id")
        else:
            source_ids.add(s["source_id"])
    if not sources:
        warnings.append("no authoritative_sources supplied -> every node/edge will be untraced (needs-data)")

    nodes = doc.get("nodes") or []
    if not isinstance(nodes, list) or not nodes:
        errors.append("nodes must be a non-empty list")
        return errors, warnings

    node_ids = set()
    layers_present = set()
    for i, n in enumerate(nodes):
        tag = f"nodes[{i}] ({n.get('node_id','?')})"
        for k in REQUIRED_NODE:
            if k not in n or n[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        nid = n.get("node_id")
        if nid in node_ids:
            errors.append(f"{tag}: duplicate node_id")
        node_ids.add(nid)
        layer = n.get("layer")
        if layer:
            layers_present.add(layer)
            if layer not in KNOWN_LAYERS:
                warnings.append(f"{tag}: layer {layer!r} not in taxonomy {sorted(KNOWN_LAYERS)} -> needs-data")
        if not n.get("owner"):
            warnings.append(f"{tag}: no owner/steward -> needs-data")
        sid = n.get("source_id")
        if not sid:
            warnings.append(f"{tag}: no source_id -> untraced provenance (needs-data)")
        elif source_ids and sid not in source_ids:
            warnings.append(f"{tag}: source_id {sid!r} not in authoritative_sources -> untraced (needs-data)")

    if "source" not in layers_present:
        warnings.append("no 'source' layer node -> lineage has no documented origin (graph not sound)")
    if "output" not in layers_present:
        warnings.append("no 'output' layer node -> lineage has no documented consumer/output (graph not sound)")

    edges = doc.get("edges")
    if not isinstance(edges, list):
        errors.append("edges must be a list")
        return errors, warnings
    if not edges:
        warnings.append("no edges supplied -> no documented dependencies (nodes may be orphaned)")

    edge_ids = set()
    for i, e in enumerate(edges):
        tag = f"edges[{i}] ({e.get('edge_id','?')})"
        for k in REQUIRED_EDGE:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        eid = e.get("edge_id")
        if eid in edge_ids:
            errors.append(f"{tag}: duplicate edge_id")
        edge_ids.add(eid)
        for endpoint in ("from_node", "to_node"):
            ref = e.get(endpoint)
            if ref and ref not in node_ids:
                warnings.append(f"{tag}: {endpoint} {ref!r} not among nodes -> dangling-edge")
        if not e.get("transformation"):
            warnings.append(f"{tag}: no transformation documented -> undocumented-transform")
        esid = e.get("source_id")
        if esid and source_ids and esid not in source_ids:
            warnings.append(f"{tag}: source_id {esid!r} not in authoritative_sources -> untraced (undocumented-transform)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "lineage_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
