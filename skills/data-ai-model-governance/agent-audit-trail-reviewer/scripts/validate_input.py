#!/usr/bin/env python3
"""Deterministic input validation for agent-audit-trail-reviewer.

Validates an agent-run audit trail before the review is computed. Fails closed on
structural problems (so a malformed trail can never be reviewed as if complete); warns on
data-quality gaps that limit which control checks are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  run_id, agent_id, as_of (YYYY-MM-DD), policy_version,
  run{model_id,model_version,prompt_version,config_version,seed,temperature,...},
  config{allowed_tools[],required_repro_fields[],approval_required_action_classes[],
         required_retained_objects[]},
  events[{event_id,type,ts, ...type-specific...}]
    types: prompt | retrieval | tool_call | approval | override | output | retention

Usage:
  python validate_input.py trail.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("run_id", "agent_id", "as_of", "policy_version", "run", "events")
REQUIRED_EVENT = ("event_id", "type", "ts")
EVENT_TYPES = {"prompt", "retrieval", "tool_call", "approval", "override", "output", "retention"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if not isinstance(doc.get("run"), dict):
        errors.append("'run' header must be an object")
    events = doc.get("events") or []
    if not isinstance(events, list) or not events:
        errors.append("events must be a non-empty list")
        return errors, warnings

    ids = set()
    seen_types: set = set()
    for i, e in enumerate(events):
        tag = f"events[{i}] ({e.get('event_id', '?')})"
        for k in REQUIRED_EVENT:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        et = e.get("type")
        if et is not None and et not in EVENT_TYPES:
            errors.append(f"{tag}: unknown event type {et!r} (allowed: {sorted(EVENT_TYPES)})")
        eid = e.get("event_id")
        if eid in ids:
            errors.append(f"{tag}: duplicate event_id")
        ids.add(eid)
        seen_types.add(et)
        # type-specific structural checks
        if et == "tool_call":
            if not e.get("tool"):
                errors.append(f"{tag}: tool_call missing 'tool'")
            if e.get("action_class") not in ("read", "write", "decision", None):
                errors.append(f"{tag}: action_class must be read|write|decision")
        if et == "approval":
            if not e.get("for_event"):
                errors.append(f"{tag}: approval missing 'for_event' reference")
        if et == "override" and not e.get("actor"):
            errors.append(f"{tag}: override missing 'actor'")

    # cross-references: approval.for_event must point to an existing event
    for e in events:
        if e.get("type") == "approval" and e.get("for_event") and e["for_event"] not in ids:
            errors.append(f"approval {e.get('event_id')}: for_event {e['for_event']!r} not found")

    # data-quality warnings (limit evaluability, do not fail closed)
    run = doc.get("run") or {}
    req_repro = (doc.get("config") or {}).get(
        "required_repro_fields", ["model_id", "model_version", "prompt_version", "config_version"])
    missing_repro = [f for f in req_repro if not run.get(f)]
    if missing_repro:
        warnings.append(f"run header missing reproducibility field(s): {missing_repro} — reproducibility will be flagged incomplete")
    if "prompt" not in seen_types:
        warnings.append("no prompt event — the run's instructions are not captured; traceability limited")
    if "retention" not in seen_types:
        warnings.append("no retention events — retention control not evaluable from this trail")
    if "output" not in seen_types:
        warnings.append("no output event — output traceability not evaluable")
    if not (doc.get("config") or {}).get("allowed_tools"):
        warnings.append("no config.allowed_tools — out-of-scope-tool check will be skipped")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "trail_example.json"
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
