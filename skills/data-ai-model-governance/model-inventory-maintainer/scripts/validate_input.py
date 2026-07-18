#!/usr/bin/env python3
"""Deterministic input validation for model-inventory-maintainer.

Validates an inventory change request before the proposal is computed. Fails closed on
structural problems; warns on data-quality gaps that limit completeness, tie-out, or
reconciliation.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  record_id, as_of (YYYY-MM-DD), config_version, change_type ('create'|'update'),
  asset_kind ('model'|'agent'),
  proposed_record{name,owner,purpose,lifecycle_status,materiality_tier,
                  materiality_factors{financial_exposure,decision_autonomy,
                  customer_impact,regulatory_use},versions[],dependencies[],lineage[],
                  approvals[], latest_version},
  current_record{...}|null, evidence[{attribute,system,source_ref}],
  sources{registry{...},catalog{...},eval{...},agent_log{...}}, config{...}

Usage:
  python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("record_id", "as_of", "config_version", "change_type", "asset_kind",
                "proposed_record", "evidence")
REQUIRED_ATTRS = ("name", "owner", "purpose", "lifecycle_status", "materiality_factors",
                  "versions", "dependencies", "lineage", "approvals")
FACTOR_KEYS = ("financial_exposure", "decision_autonomy", "customer_impact", "regulatory_use")
LIFECYCLE_STATES = {"proposed", "in-development", "in-validation", "approved", "in-use",
                    "on-hold", "retired"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if doc["change_type"] not in ("create", "update"):
        errors.append(f"change_type must be 'create' or 'update', got {doc['change_type']!r}")
    if doc["asset_kind"] not in ("model", "agent"):
        errors.append(f"asset_kind must be 'model' or 'agent', got {doc['asset_kind']!r}")
    if doc["change_type"] == "update" and not doc.get("current_record"):
        errors.append("change_type 'update' requires a current_record for the transition check")

    rec = doc.get("proposed_record")
    if not isinstance(rec, dict):
        errors.append("proposed_record must be an object")
        return errors, warnings

    # required attributes: missing/empty -> warning (surfaces as a completeness finding later)
    for a in REQUIRED_ATTRS:
        if a not in rec or rec[a] in (None, "", [], {}):
            warnings.append(f"proposed_record missing/empty required attribute '{a}' — completeness finding expected")

    ls = rec.get("lifecycle_status")
    if ls is not None and ls not in LIFECYCLE_STATES:
        errors.append(f"proposed_record.lifecycle_status {ls!r} not a known state {sorted(LIFECYCLE_STATES)}")

    factors = rec.get("materiality_factors") or {}
    if not isinstance(factors, dict):
        errors.append("proposed_record.materiality_factors must be an object")
    else:
        for fk in FACTOR_KEYS:
            if fk not in factors:
                warnings.append(f"materiality_factors missing '{fk}' — scored as 0 for the tie-out")
            else:
                try:
                    v = int(factors[fk])
                except (TypeError, ValueError):
                    errors.append(f"materiality_factors['{fk}'] must be an integer 0-3, got {factors[fk]!r}")
                    continue
                if not 0 <= v <= 3:
                    errors.append(f"materiality_factors['{fk}']={v} out of range 0-3")

    ev = doc.get("evidence")
    if not isinstance(ev, list) or not ev:
        errors.append("evidence must be a non-empty list of {attribute, system, source_ref}")
    else:
        cited_attrs = set()
        for i, e in enumerate(ev):
            tag = f"evidence[{i}]"
            for k in ("attribute", "source_ref"):
                val = e.get(k)
                if val is None or (isinstance(val, str) and not val.strip()):
                    errors.append(f"{tag}: missing '{k}'")
            if e.get("attribute"):
                cited_attrs.add(e["attribute"])
        for a in ("materiality_factors", "lineage"):
            if a in rec and a not in cited_attrs:
                warnings.append(f"attribute '{a}' has no evidence row — traceability limited")

    if not doc.get("sources"):
        warnings.append("no 'sources' snapshots — reconciliation will report attributes as unverifiable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default rubric/lifecycle config will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "change_request_example.json"
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
