#!/usr/bin/env python3
"""Deterministic input validation for earnings-preview-packet-builder.

Validates a preview build request before assembly. Fails closed on structural problems (a
packet cannot be assembled without a durable packet_id, an issuer/event, a versioned
template contract, and items); warns on completeness, source, attribution, and approval gaps
that will force a `hold-for-approval` status.

Input schema (JSON): see references/source-map.md. Key fields:
  packet_id, job_id, as_of_date,
  issuer{name, ticker}, event{fiscal_period, report_date, comparable_period},
  template{template_id, version, required_sections[]},
  required_approvals[], approvals[{role, status, approver, date}],
  metrics[{metric, unit, consensus_value, consensus_source, guidance_low, guidance_high,
           guidance_source}],
  kpi_history[{kpi, unit, series[{period, value}], source}],
  items[{item_id, section, title, source_component, takeaway,
         data_points[{label, value, kind, attribution, source_ref, approved}],
         sources[], approval{status, approver, date}}]

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("packet_id", "issuer", "event", "template", "required_approvals", "items")
REQUIRED_TEMPLATE = ("template_id", "version", "required_sections")
REQUIRED_EVENT = ("fiscal_period", "report_date", "comparable_period")
REQUIRED_ITEM = ("item_id", "section", "title", "takeaway")
FORWARD_KINDS = {"consensus", "guidance", "sensitivity"}
SELF_ATTRIB = {"self", "own", "analyst", "analyst-own", "house", "our-model", "skill"}
PROHIBITED_KINDS = {"own_forecast", "target", "price_target", "rating", "trade_view"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not doc.get("packet_id"):
        errors.append("packet_id is required (durable per-issuer/period identifier)")

    issuer = doc.get("issuer") or {}
    for k in ("name", "ticker"):
        if not issuer.get(k):
            errors.append(f"issuer: missing '{k}'")

    event = doc.get("event") or {}
    for k in REQUIRED_EVENT:
        if not event.get(k):
            errors.append(f"event: missing '{k}' (pre-event calendar is required)")

    tmpl = doc.get("template") or {}
    for k in REQUIRED_TEMPLATE:
        if k not in tmpl or tmpl[k] in (None, "", []):
            errors.append(f"template: missing '{k}' (the approved template is a versioned contract)")
    required_sections = tmpl.get("required_sections") or []
    if not isinstance(required_sections, list) or not required_sections:
        errors.append("template.required_sections must be a non-empty list")

    items = doc.get("items") or []
    if not isinstance(items, list) or not items:
        errors.append("items must be a non-empty list")
        return errors, warnings

    ids: set = set()
    covered: set = set()
    for i, it in enumerate(items):
        tag = f"items[{i}] ({it.get('item_id','?')})"
        for k in REQUIRED_ITEM:
            if k not in it or it[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        iid = it.get("item_id")
        if iid in ids:
            errors.append(f"{tag}: duplicate item_id")
        ids.add(iid)
        covered.add(it.get("section"))

        if not it.get("sources"):
            warnings.append(f"{tag}: no source citation -> item will be marked needs-source")
        for j, c in enumerate(it.get("data_points") or []):
            kind = c.get("kind")
            if kind in PROHIBITED_KINDS:
                errors.append(f"{tag}: data_point[{j}] kind {kind!r} originates a forecast/rating/target/trade view -> prohibited")
            if not c.get("source_ref"):
                warnings.append(f"{tag}: data_point[{j}] has no source_ref -> unsupported (hold-for-approval)")
            elif c.get("approved") is not True:
                warnings.append(f"{tag}: data_point[{j}] source not approved -> unapproved (hold-for-approval)")
            if kind in FORWARD_KINDS:
                attr = str(c.get("attribution", "")).strip().lower()
                if not attr:
                    warnings.append(f"{tag}: data_point[{j}] is forward-looking but has no third-party attribution")
                elif attr in SELF_ATTRIB:
                    errors.append(f"{tag}: data_point[{j}] forward-looking figure attributed to the analyst/house -> the packet never carries an originated estimate")
        appr = it.get("approval") or {}
        if appr.get("status") != "approved":
            warnings.append(f"{tag}: content approval status is {appr.get('status')!r} -> needs-approval")

    for sec in required_sections:
        if sec not in covered:
            warnings.append(f"required section '{sec}' has no item -> completeness gap (hold-for-approval)")

    approvals = {a.get("role"): a.get("status") for a in (doc.get("approvals") or [])}
    for role in doc.get("required_approvals") or []:
        if role not in approvals:
            warnings.append(f"required approval '{role}' not recorded -> hold-for-approval")
        elif approvals[role] != "approved":
            warnings.append(f"required approval '{role}' status is {approvals[role]!r} -> hold-for-approval")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "preview_request_example.json"
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
