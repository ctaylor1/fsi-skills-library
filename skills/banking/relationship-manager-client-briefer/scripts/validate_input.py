#!/usr/bin/env python3
"""Deterministic input validation for relationship-manager-client-briefer.

Validates a client-intake file before an RM brief is drafted. Fails closed on structural
problems (so a brief is never assembled from an ill-formed record); warns on data gaps that
force a `needs-data`, `unresolved-entity`, `unsupported-content`, or `stale-source` status
downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  as_of_date, freshness_days?, critical_freshness_days?, clients[
    {client_id, legal_name, relationship_manager?, entity_resolved(bool),
     sources[{source_id, system, ref, date, classification?, stale_ack?}],
     exposures[{facility, committed, outstanding, source_id}],
     covenants[{name, status(compliant|at-risk|breached), test_date?, source_id}]?,
     profitability[{metric, value, period?, source_id}]?,
     products[{product, status?, source_id}]?,
     service_cases[{case_ref, summary, status, severity?, source_id}]?,
     news[{headline, date?, adverse?, source_id}]?,
     pipeline[{opportunity, stage, amount?, source_id}]?,
     contacts[{name, role, source_id}]?,
     cross_sell[{idea, rationale, source_id}]?,
     open_actions[{action, owner?, due_date?, status, source_id}]?}]

Usage: python validate_input.py clients.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("as_of_date", "clients")
REQUIRED_CLIENT = ("client_id", "legal_name")  # structural; error if missing
COVENANT_STATUS = {"compliant", "at-risk", "breached"}
# (list_key, label, text_field) -- content lists that must cite a source in the inventory
CONTENT_SPEC = [
    ("exposures", "exposure", "facility"),
    ("covenants", "covenant", "name"),
    ("profitability", "profitability metric", "metric"),
    ("products", "product", "product"),
    ("service_cases", "service case", "case_ref"),
    ("news", "news item", "headline"),
    ("pipeline", "pipeline opportunity", "opportunity"),
    ("contacts", "contact", "name"),
    ("cross_sell", "cross-sell idea", "idea"),
    ("open_actions", "open action", "action"),
]


def _is_iso_date(v) -> bool:
    try:
        date.fromisoformat(str(v))
        return True
    except Exception:
        return False


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _is_iso_date(doc.get("as_of_date")):
        errors.append("as_of_date is not an ISO date (YYYY-MM-DD)")

    clients = doc.get("clients") or []
    if not isinstance(clients, list) or not clients:
        errors.append("clients must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, c in enumerate(clients):
        tag = f"clients[{i}] ({c.get('client_id','?')})"
        for k in REQUIRED_CLIENT:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        cid = c.get("client_id")
        if cid in ids:
            errors.append(f"{tag}: duplicate client_id")
        ids.add(cid)

        # source inventory (structural)
        sources = c.get("sources") or []
        if not isinstance(sources, list):
            errors.append(f"{tag}: sources must be a list")
            sources = []
        source_ids = set()
        for j, s in enumerate(sources):
            if not s.get("source_id") or not s.get("system") or not s.get("ref"):
                errors.append(f"{tag}: sources[{j}] needs source_id, system, and ref")
            if s.get("date") and not _is_iso_date(s.get("date")):
                errors.append(f"{tag}: sources[{j}] date is not an ISO date")
            source_ids.add(s.get("source_id"))

        # content-required gaps are WARNINGS -> drive statuses downstream, not input errors
        if not c.get("relationship_manager"):
            warnings.append(f"{tag}: missing 'relationship_manager'")
        if not c.get("exposures"):
            warnings.append(f"{tag}: no exposures -> needs-data (relationship summary incomplete)")
        if "entity_resolved" not in c:
            warnings.append(f"{tag}: entity_resolved not set -> unresolved-entity")
        elif not c.get("entity_resolved"):
            warnings.append(f"{tag}: entity_resolved is false -> unresolved-entity (do not guess identity)")

        # exposure numerics are structural
        for k, e in enumerate(c.get("exposures") or []):
            for fld in ("committed", "outstanding"):
                if fld in e and e[fld] is not None and not _is_number(e[fld]):
                    errors.append(f"{tag}: exposures[{k}].{fld} must be a number")

        # covenant status enumeration
        for k, cov in enumerate(c.get("covenants") or []):
            st = cov.get("status")
            if st is not None and st not in COVENANT_STATUS:
                warnings.append(f"{tag}: covenants[{k}].status {st!r} not in {sorted(COVENANT_STATUS)}")

        # every content item should cite a source in the inventory
        for list_key, label, _text in CONTENT_SPEC:
            for k, item in enumerate(c.get(list_key) or []):
                sid = item.get("source_id")
                if not sid:
                    warnings.append(f"{tag}: {label}[{k}] has no source_id -> unsupported-content")
                elif sid not in source_ids:
                    warnings.append(f"{tag}: {label}[{k}] cites source {sid!r} not in inventory -> unsupported-content")

        for k, a in enumerate(c.get("open_actions") or []):
            if a.get("due_date") and not _is_iso_date(a.get("due_date")):
                errors.append(f"{tag}: open_actions[{k}] due_date is not an ISO date")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "clients_example.json"
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
