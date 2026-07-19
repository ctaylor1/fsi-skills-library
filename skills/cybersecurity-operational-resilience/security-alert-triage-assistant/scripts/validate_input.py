#!/usr/bin/env python3
"""Deterministic input validation for security-alert-triage-assistant.

Validates a security-alert batch-intake file before a triage package is assembled. Fails
closed (exit 1) on structural problems; warns on enrichment gaps that force a `needs-data`
disposition and on hard-boundary / suppression-override indicators. Stdlib-only,
self-contained, operates on a documented JSON schema (see references/source-map.md) using a
de-identified bundled fixture — no live SIEM/SOAR/IAM calls.

Input schema (JSON): key fields:
  config_version, template_version, batch_id, source_queue,
  required_approvals[], recorded_approvals[{role, approver, date}],
  priority_config{}, approved_scanner_sources[], approved_maintenance_windows[{id,signature,from,to}],
  open_cases[{case_id, asset_id, signature_id, window{from,to}, signal_ids[]}],
  alerts[{alert_id, signature_id, alert_class, window{from,to}, source_ref, as_of,
    asset{asset_id, asset_ref, criticality, internet_facing},
    identity{identity_ref, privilege},
    threat_intel{severity, known_malicious, active_compromise, iocs[]},
    vuln_posture{kev_nexus, exposure},
    signal_ids[], source_scanner, maintenance_window_id, correlated_count}]

Usage: python validate_input.py alerts.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "batch_id", "alerts", "required_approvals")
REQUIRED_ALERT = ("alert_id", "signature_id", "alert_class", "window", "source_ref")
CRITICALITY = {"Critical", "High", "Medium", "Low"}


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

    alerts = doc.get("alerts") or []
    if not isinstance(alerts, list) or not alerts:
        errors.append("alerts must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, a in enumerate(alerts):
        if not isinstance(a, dict):
            errors.append(f"alerts[{i}] must be an object")
            continue
        tag = f"alerts[{i}] ({a.get('alert_id','?')})"
        for k in REQUIRED_ALERT:
            if k not in a or a[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        aid = a.get("alert_id")
        if aid in ids:
            errors.append(f"{tag}: duplicate alert_id")
        ids.add(aid)
        win = a.get("window") or {}
        if not (win.get("from") and win.get("to")):
            errors.append(f"{tag}: window requires 'from' and 'to'")

        asset = a.get("asset") or {}
        if asset.get("criticality") not in CRITICALITY:
            warnings.append(f"{tag}: asset.criticality missing/invalid (asset unresolved in CMDB) -> needs-data")
        if not a.get("signal_ids"):
            warnings.append(f"{tag}: no signal_ids -> investigation context will lack signal evidence (needs-data)")

        ti = a.get("threat_intel") or {}
        if ti.get("active_compromise") is True:
            warnings.append(f"{tag}: threat_intel.active_compromise is true -> HARD BOUNDARY: package will be blocked and routed to incident response; this skill performs NO containment")
        if ti.get("known_malicious") is True:
            warnings.append(f"{tag}: threat_intel.known_malicious is true -> will escalate (overrides suppression)")
        if a.get("maintenance_window_id") and ti.get("known_malicious"):
            warnings.append(f"{tag}: maintenance-window suppression will be OVERRIDDEN by known-malicious threat intel (escalate)")

    if doc.get("open_cases") is None:
        warnings.append("no open_cases provided -> correlation/deduplication limited")
    if doc.get("recorded_approvals") is None:
        warnings.append("no recorded_approvals -> approval ledger will list all required approvals as pending (expected for a draft)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "alerts_example.json"
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
