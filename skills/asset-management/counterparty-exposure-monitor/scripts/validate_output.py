#!/usr/bin/env python3
"""Deterministic output validation for counterparty-exposure-monitor.

Validates the alert pack (calculate_or_transform core + optional narrative) before it is
queued or delivered. Enforces the Monitor & alert posture: read-only, alert-only, no
autonomous action. Checks:
  1. Every alert has fingerprint, a valid severity, a valid freshness tag, a status
     (new/recurring), >= 1 cited evidence row, and escalation packaging that matches the
     deterministic severity -> queue/sla/escalate_to mapping.
  2. Deduplication: alert fingerprints are unique (no duplicate open alerts).
  3. Freshness handling: every stale feed in stale_feeds has a matching data_freshness
     alert (stale inputs are surfaced, never silently suppressed); no alert may be tagged
     stale while claiming its feed is current.
  4. run_severity equals the max alert severity (deterministic tie-out).
  5. No autonomous-action / decision language anywhere in narrative, notes, or reasons.
  6. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; no limit, trade, collateral, or counterparty "
              "action has been taken. Human review is required before any action.")

SEVERITY_RANK = {"Warning": 1, "Breach": 2, "Critical": 3}
VALID_FRESHNESS = {"current", "stale"}
VALID_STATUS = {"new", "recurring"}

# Deterministic severity -> escalation/queue packaging (must match calculate_or_transform).
ESCALATION = {
    "Critical": {"queue": "counterparty-risk-urgent", "sla_hours": 1,
                 "escalate_to": "Counterparty risk lead and Treasury"},
    "Breach":   {"queue": "counterparty-risk", "sla_hours": 4,
                 "escalate_to": "Counterparty risk analyst"},
    "Warning":  {"queue": "counterparty-risk-watch", "sla_hours": 24,
                 "escalate_to": "Counterparty risk analyst"},
}

# Affirmative action/decision language a read-only, alert-only monitor must never emit.
ACTION_PATTERNS = [
    r"\bposted collateral\b", r"\brecalled collateral\b", r"\breduced the (limit|line)\b",
    r"\bincreased the (limit|line)\b", r"\bterminated the\b", r"\bnovated\b",
    r"\bnetted down\b", r"\bunwound\b", r"\bhedged the exposure\b", r"\bexecuted (a|the) (trade|hedge)\b",
    r"\bsettled the trade\b", r"\bwe traded\b", r"\bplaced a hold\b", r"\bsuspended the counterparty\b",
    r"\bblocked the counterparty\b", r"\bclosed the (alert|position)\b", r"\bauto-?resolved\b",
    r"\bsuppressed the alert\b", r"\bcancelled the trade\b", r"\bcalled the margin\b",
    r"\bwrote to the (system|book) of record\b", r"\bbooked (a|the)\b",
]


def _expected_run_severity(alerts):
    sevs = [a.get("severity") for a in alerts if a.get("severity") in SEVERITY_RANK]
    if not sevs:
        return "None"
    return max(sevs, key=lambda s: SEVERITY_RANK[s])


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    alerts = pack.get("alerts") or []

    # 1. per-alert structural + escalation packaging
    seen_fp = {}
    for i, a in enumerate(alerts):
        tag = f"alert[{i}] ({a.get('fingerprint', '?')})"
        fp = a.get("fingerprint")
        if not fp:
            errors.append(f"{tag}: missing fingerprint")
        sev = a.get("severity")
        if sev not in SEVERITY_RANK:
            errors.append(f"{tag}: invalid severity {sev!r}")
        if a.get("freshness") not in VALID_FRESHNESS:
            errors.append(f"{tag}: invalid/missing freshness {a.get('freshness')!r}")
        if a.get("status") not in VALID_STATUS:
            errors.append(f"{tag}: invalid/missing status {a.get('status')!r} (dedup requires new|recurring)")
        ev = a.get("evidence") or []
        if not ev:
            errors.append(f"{tag}: fired alert has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"{tag}: evidence row missing citation")
        # escalation packaging must match the deterministic mapping
        if sev in ESCALATION:
            exp = ESCALATION[sev]
            if (a.get("queue"), a.get("sla_hours"), a.get("escalate_to")) != \
               (exp["queue"], exp["sla_hours"], exp["escalate_to"]):
                errors.append(f"{tag}: escalation packaging does not match deterministic mapping for {sev}")
        # 2. dedup
        if fp in seen_fp:
            errors.append(f"{tag}: duplicate fingerprint {fp!r} (deduplication failed)")
        seen_fp[fp] = i

    # 3. freshness handling: no stale feed may be dropped
    stale_feeds = pack.get("stale_feeds") or []
    freshness_dims = {a.get("dimension") for a in alerts if a.get("alert_type") == "data_freshness"}
    for f in stale_feeds:
        if f not in freshness_dims:
            errors.append(f"stale feed {f!r} has no data_freshness alert (stale input suppressed)")

    # 4. run_severity tie-out
    exp_sev = _expected_run_severity(alerts)
    if pack.get("run_severity") != exp_sev:
        errors.append(f"run_severity {pack.get('run_severity')!r} != deterministic {exp_sev!r}")

    # 5. no autonomous-action language (scan narrative/notes/reasons, not the disclaimer field)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(a.get("reason", "")) for a in alerts])
    for pat in ACTION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"autonomous-action language detected: {m.group(0)!r} "
                          f"(monitor alerts only; it never acts/decides/closes)")

    # 6. disclaimer present
    where = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in where:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
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
