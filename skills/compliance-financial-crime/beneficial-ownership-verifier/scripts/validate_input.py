#!/usr/bin/env python3
"""Deterministic input validation for beneficial-ownership-verifier.

Validates a legal-entity ownership file before the UBO computation runs. Fails closed on
structural problems (broken graph references, non-numeric percentages, unknown declared
parties); warns on data-quality gaps that limit which requirements are evaluable
(missing documents, ownership sums over 100%, no control edges when the control prong is
required).

Input schema (JSON): see references/source-map.md. Key fields:
  case_id, as_of (YYYY-MM-DD), jurisdiction, config_version, legal_entity{entity_id,...},
  config{...jurisdiction pack...},
  nodes[{node_id, kind: entity|person, name, country}],
  ownership_edges[{owner, owned, pct, doc_id, source_ref}],
  control_edges[{controller, entity, role, type, doc_id, source_ref}],
  declared_ubos[{person_id, name, basis: ownership|control, declared_pct?, doc_id?}],
  documents[{doc_id, type, subject, issued, expires, source_ref}]

Usage:
  python validate_input.py ownership.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("case_id", "as_of", "jurisdiction", "config_version", "legal_entity",
                "nodes", "ownership_edges", "declared_ubos")
REQUIRED_EDGE = ("owner", "owned", "pct")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    nodes = doc.get("nodes") or []
    if not isinstance(nodes, list) or not nodes:
        errors.append("nodes must be a non-empty list")
        return errors, warnings

    kind = {}
    for i, n in enumerate(nodes):
        nid = n.get("node_id")
        tag = f"nodes[{i}] ({nid or '?'})"
        if not nid:
            errors.append(f"{tag}: missing node_id")
            continue
        if nid in kind:
            errors.append(f"{tag}: duplicate node_id")
        if n.get("kind") not in ("entity", "person"):
            errors.append(f"{tag}: kind must be 'entity' or 'person'")
        if not n.get("name"):
            warnings.append(f"{tag}: missing name")
        kind[nid] = n.get("kind")

    le = doc["legal_entity"]
    root = le.get("entity_id") if isinstance(le, dict) else None
    if not root:
        errors.append("legal_entity.entity_id missing")
    elif kind.get(root) != "entity":
        errors.append(f"legal_entity.entity_id {root!r} is not an 'entity' node")

    # ownership edges
    owned_sums: dict[str, float] = {}
    for i, e in enumerate(doc.get("ownership_edges") or []):
        tag = f"ownership_edges[{i}]"
        for k in REQUIRED_EDGE:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        o, w = e.get("owner"), e.get("owned")
        if o not in kind:
            errors.append(f"{tag}: owner {o!r} not a known node")
        if w not in kind:
            errors.append(f"{tag}: owned {w!r} not a known node")
        elif kind.get(w) == "person":
            errors.append(f"{tag}: owned {w!r} is a person; persons cannot be owned")
        p = _num(e.get("pct"))
        if p is None:
            errors.append(f"{tag}: pct not numeric")
        elif not (0 < p <= 100):
            errors.append(f"{tag}: pct {p} out of range (0, 100]")
        else:
            owned_sums[w] = owned_sums.get(w, 0.0) + p
        if not e.get("source_ref"):
            warnings.append(f"{tag}: no source_ref — evidence citation will be missing")
    for w, s in owned_sums.items():
        if s > 100.0 + 1e-6:
            warnings.append(f"ownership of {w} sums to {s:.2f}% (> 100%) — data-quality issue, review the cap table")

    # control edges
    control = doc.get("control_edges") or []
    for i, c in enumerate(control):
        tag = f"control_edges[{i}]"
        if c.get("controller") not in kind or kind.get(c.get("controller")) != "person":
            errors.append(f"{tag}: controller {c.get('controller')!r} is not a known person node")
        if c.get("entity") not in kind:
            errors.append(f"{tag}: entity {c.get('entity')!r} not a known node")
        if not c.get("type"):
            warnings.append(f"{tag}: no control 'type' (e.g. senior_managing_official)")

    cfg = doc.get("config") or {}
    if cfg.get("require_control_prong", True) and not control:
        warnings.append("control prong required by config but no control_edges provided — control_prong_unsatisfied gap will surface")

    # declared UBOs referential integrity
    for i, d in enumerate(doc["declared_ubos"]):
        tag = f"declared_ubos[{i}] ({d.get('person_id','?')})"
        pid = d.get("person_id")
        if pid not in kind:
            errors.append(f"{tag}: person_id not a known node")
        elif kind.get(pid) != "person":
            errors.append(f"{tag}: person_id {pid!r} is not a 'person' node")
        if d.get("basis") not in ("ownership", "control"):
            warnings.append(f"{tag}: basis should be 'ownership' or 'control'")
        if not d.get("doc_id"):
            warnings.append(f"{tag}: no supporting doc_id — missing_document gap may surface")

    # documents
    doc_ids = set()
    for i, dc in enumerate(doc.get("documents") or []):
        tag = f"documents[{i}] ({dc.get('doc_id','?')})"
        did = dc.get("doc_id")
        if not did:
            errors.append(f"{tag}: missing doc_id")
        elif did in doc_ids:
            errors.append(f"{tag}: duplicate doc_id")
        doc_ids.add(did)
        if dc.get("issued") and not DATE_RE.match(str(dc["issued"])):
            warnings.append(f"{tag}: issued not YYYY-MM-DD")

    if not doc.get("config"):
        warnings.append("no 'config' block — default jurisdiction thresholds will be used; record the config_version")
    if not doc.get("documents"):
        warnings.append("no 'documents' block — document-freshness requirements are not evaluable")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ownership_example.json"
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
