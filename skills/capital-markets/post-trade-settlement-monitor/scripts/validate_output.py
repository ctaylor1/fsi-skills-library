#!/usr/bin/env python3
"""Deterministic output validation for post-trade-settlement-monitor.

Validates the final alert queue (the calculate_or_transform core + a narrative) before it
is queued for a human or delivered. As a SCHEDULED, READ-ONLY, ALERT-ONLY monitor, the pack
must package alerts and NEVER record an action or a settlement decision. Checks:
  1. Escalation packaging: every queued item has a severity (allowed set) and a
     non-empty suggested_route; every alert has >= 1 cited evidence row.
  2. Threshold behavior: each item's severity equals the deterministic max over its alert
     types' fixed severities (references/domain-rules.md).
  3. Deduplication: no two active (state=="new") alerts share a dedup_key, and any alert
     whose dedup_key is in `deduped_against` is marked state=="duplicate" (not re-raised).
  4. Freshness handling: a freshness block with as_of + max_source_staleness_minutes; the
     set of items flagged stale exactly matches freshness.stale_instruction_ids.
  5. NO autonomous action: `actions_taken` is present and empty; no action/decision
     language in the narrative, notes, or alert reasons.
  6. Standing disclaimer present.

Usage:
  python validate_output.py queue.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Monitoring alerts only; no settlement action has been taken. "
              "A human must review, decide, and act.")
ALERT_SEVERITY = {
    "unmatched_near_cutoff": "High",
    "cutoff_breach": "Critical",
    "settlement_fail": "Warning",
    "fail_aging_high": "High",
    "fail_aging_critical": "Critical",
    "buyin_exposure": "Critical",
    "material_cash_impact": "High",
    "penalty_accrual": "Warning",
}
SEV_ORDER = {"Info": 0, "Warning": 1, "High": 2, "Critical": 3}

# A read-only monitor must never claim to have acted or decided. These assert a settlement
# action/decision was taken — all prohibited for an alert-only agent.
ACTION_PATTERNS = [
    r"\bcancel(?:led|ed)? (the )?instruction\b",
    r"\binitiat(?:e|ed) (a )?buy-in\b",
    r"\bexecut(?:e|ed) (a )?buy-in\b",
    r"\bsettl(?:e|ed) the (fail|trade|instruction)\b",
    r"\bmatch(?:ed)? the instruction\b",
    r"\baffirm(?:ed)? the (trade|instruction)\b",
    r"\bclos(?:e|ed) the (fail|alert|exception|break)\b",
    r"\bsuppress(?:ed)? the alert\b",
    r"\binstruct(?:ed)? the (custodian|csd|counterparty|agent)\b",
    r"\bcontact(?:ed)? the (counterparty|custodian|client)\b",
    r"\breleas(?:e|ed) the (payment|settlement)\b",
    r"\b(posted|wrote) to the book of record\b",
]


def _expected_severity(alerts: list) -> str:
    sevs = [ALERT_SEVERITY.get(a.get("type"), a.get("severity", "Info")) for a in alerts]
    return max(sevs, key=lambda s: SEV_ORDER.get(s, 0)) if sevs else "Info"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    queue = pack.get("queue") or []
    deduped_against = set(pack.get("deduped_against") or [])

    active_keys, all_reasons = {}, []
    for item in queue:
        iid = item.get("instruction_id", "?")
        alerts = item.get("alerts") or []
        if not alerts:
            errors.append(f"item {iid} is queued with no alerts")

        # 1. escalation packaging
        if item.get("severity") not in SEV_ORDER:
            errors.append(f"item {iid} severity {item.get('severity')!r} not in {sorted(SEV_ORDER)}")
        if not (item.get("suggested_route") or "").strip():
            errors.append(f"item {iid} missing suggested_route (escalation packaging)")

        # 2. threshold-behavior severity tie-out
        exp = _expected_severity(alerts)
        if item.get("severity") != exp:
            errors.append(f"item {iid} severity {item.get('severity')!r} != deterministic {exp!r}")

        for a in alerts:
            all_reasons.append(str(a.get("reason", "")))
            ev = a.get("evidence") or []
            if not ev:
                errors.append(f"item {iid} alert {a.get('type')} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"item {iid} alert {a.get('type')} evidence row missing citation")

            # 3. deduplication
            key, state = a.get("dedup_key"), a.get("state")
            if key in deduped_against and state != "duplicate":
                errors.append(f"alert {key} is in deduped_against but state {state!r} (should be deduplicated)")
            if state == "new":
                if key in active_keys:
                    errors.append(f"duplicate active alert dedup_key {key} (deduplication failed)")
                active_keys[key] = iid

    # 4. freshness handling
    fr = pack.get("freshness")
    if not isinstance(fr, dict):
        errors.append("missing freshness block")
    else:
        if not str(fr.get("as_of", "")).strip():
            errors.append("freshness.as_of missing")
        if "max_source_staleness_minutes" not in fr:
            errors.append("freshness.max_source_staleness_minutes missing")
        flagged = {i.get("instruction_id") for i in queue if i.get("stale")}
        listed = set(fr.get("stale_instruction_ids") or [])
        if flagged != listed:
            errors.append(f"freshness mismatch: items flagged stale {sorted(flagged)} != stale_instruction_ids {sorted(listed)}")

    # 5. no autonomous action
    at = pack.get("actions_taken")
    if at is None:
        errors.append("actions_taken missing (alert-only monitor must record no actions)")
    elif at:
        errors.append(f"actions_taken must be empty (alert-only monitor); found {len(at)}")
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))] + all_reasons)
    for pat in ACTION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"action/decision language detected: {m.group(0)!r} (monitor alerts only, never acts)")

    # 6. disclaimer
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "settlement_queue_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
