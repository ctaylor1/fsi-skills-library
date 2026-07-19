#!/usr/bin/env python3
"""Deterministic input validation for data-loss-prevention-incident-assistant.

Validates a DLP event batch-intake file before an incident-assessment package is assembled.
Fails closed (exit 1) on structural problems; warns on enrichment/classification gaps that
force a `needs-data` disposition and on hard-boundary / suppression-override indicators.
Stdlib-only, self-contained, operates on a documented JSON schema (see
references/source-map.md) using a de-identified bundled fixture — no live DLP/SIEM/IAM calls.

Input schema (JSON): key fields:
  config_version, template_version, batch_id, source_queue,
  required_approvals[], recorded_approvals[{role, approver, date}],
  classification_config{}, severity_config{},
  approved_destinations[], approved_fp_patterns[],
  open_cases[{case_id, actor_id, dlp_rule_id, window{from,to}, event_ids[]}],
  events[{event_id, dlp_rule_id, policy, channel, vector, window{from,to}, source_ref, as_of,
    actor{identity_ref, privilege, department},
    asset{asset_id, asset_ref, managed},
    destination{dest_ref, trust, category, destination_id},
    data{data_types[], record_count, volume_mb},
    egress, active_exfiltration, event_ids[], fp_pattern_id, evidence_hash, legal_hold}]

Usage: python validate_input.py events.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "batch_id", "events", "required_approvals")
REQUIRED_EVENT = ("event_id", "dlp_rule_id", "channel", "window", "source_ref")
TRUST = {"external-untrusted", "personal", "sanctioned", "internal"}
REGULATED_TYPES = {"pci", "chd", "card", "pan", "phi", "health", "medical",
                   "pii", "npi", "ssn", "account-number", "dob"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    req_appr = doc.get("required_approvals")
    if not isinstance(req_appr, list) or not req_appr:
        errors.append("required_approvals must be a non-empty list of approver roles")

    events = doc.get("events") or []
    if not isinstance(events, list) or not events:
        errors.append("events must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, e in enumerate(events):
        if not isinstance(e, dict):
            errors.append(f"events[{i}] must be an object")
            continue
        tag = f"events[{i}] ({e.get('event_id','?')})"
        for k in REQUIRED_EVENT:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        eid = e.get("event_id")
        if eid in ids:
            errors.append(f"{tag}: duplicate event_id")
        ids.add(eid)
        win = e.get("window") or {}
        if not (win.get("from") and win.get("to")):
            errors.append(f"{tag}: window requires 'from' and 'to'")

        dest = e.get("destination") or {}
        if dest.get("trust") and dest.get("trust") not in TRUST:
            errors.append(f"{tag}: destination.trust {dest.get('trust')!r} not in {sorted(TRUST)}")

        data = e.get("data") or {}
        dtypes = data.get("data_types")
        if not dtypes:
            warnings.append(f"{tag}: data.data_types missing -> data cannot be classified (needs-data)")
        if not e.get("event_ids"):
            warnings.append(f"{tag}: no event_ids -> assessment context will lack signal evidence (needs-data)")

        regulated = bool(set(dtypes or []) & REGULATED_TYPES)
        if regulated and e.get("egress") is True and dest.get("trust") in ("external-untrusted", "personal"):
            warnings.append(f"{tag}: regulated data egress to an untrusted/personal destination -> high exposure; escalate for human breach adjudication")

        if e.get("active_exfiltration") is True:
            warnings.append(f"{tag}: active_exfiltration is true -> HARD BOUNDARY: package will be blocked and routed urgently to incident response; this skill performs NO containment and makes NO breach determination")
        if e.get("fp_pattern_id") and e.get("active_exfiltration"):
            warnings.append(f"{tag}: false-positive suppression will be OVERRIDDEN by the active-exfiltration indicator (escalate)")

    if doc.get("open_cases") is None:
        warnings.append("no open_cases provided -> correlation/deduplication limited")
    if doc.get("recorded_approvals") is None:
        warnings.append("no recorded_approvals -> approval ledger will list all required approvals as pending (expected for a draft)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "events_example.json"
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
