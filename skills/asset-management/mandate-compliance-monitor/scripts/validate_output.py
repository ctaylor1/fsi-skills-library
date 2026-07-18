#!/usr/bin/env python3
"""Deterministic output validation for mandate-compliance-monitor.

Validates the monitoring pack (the calculate_or_transform core + an optional narrative)
before it is queued or delivered. Because this is a SCHEDULED, READ-ONLY, ALERT-ONLY
monitor, the checks specifically confirm the alert-only posture and that no autonomous
action was taken:

  1. Every alert is well-formed: identity, cited evidence, status, severity, and a routing
     queue; threshold alerts carry a measured value and a limit.
  2. severity ties out to the deterministic mapping from (rule_type, status, breach_type),
     and queue ties out to severity (no ad-hoc escalation).
  3. Deduplication integrity: new vs still-open queues partition the alerts by fingerprint;
     duplicates are routed to still-open, not re-raised as new.
  4. Freshness handling: stale portfolios are flagged (freshness alert + stale_input), never
     silently dropped or treated as fresh.
  5. No autonomous-action / decision language (no block, sell, rebalance, waiver, cure,
     alert-closure) in the narrative or notes.
  6. The standing alert-only disclaimer is present.
  7. Escalation packaging ties out: escalation counts sum to the alert count.

Fail closed on any miss.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

THRESHOLD_TYPES = {"concentration", "regulatory", "guideline"}
SEVERITIES = {"High", "Medium", "Low"}
STATUSES = {"WARN", "BREACH"}
SEVERITY_QUEUE = {"High": "compliance-escalation",
                  "Medium": "compliance-review-queue",
                  "Low": "monitoring-watchlist"}
DISCLAIMER = ("Monitoring alert only; no trade, block, waiver, cure, or system-of-record "
              "change has been made. Mandate exceptions require human compliance review and "
              "disposition.")
# Autonomous action / decision language this alert-only monitor must never emit:
ACTION_PATTERNS = [
    r"\bblock(?:ed|ing)? the (?:trade|order)\b", r"\btrade (?:was |is )?blocked\b",
    r"\bcancel(?:led|ed)? the (?:order|trade)\b", r"\bwe (?:sold|sell)\b",
    r"\bsold the position\b", r"\bliquidat(?:e|ed|ing)\b", r"\brebalanc(?:e|ed|ing)\b",
    r"\bwaiver (?:was )?granted\b", r"\bgranted a waiver\b", r"\bcured the breach\b",
    r"\bcorrected the breach\b", r"\bwe have corrected\b", r"\bauto[- ]?closed\b",
    r"\bclosed the alert\b", r"\bsuppressed the alert\b", r"\boverr(?:ode|ide) the (?:limit|rule)\b",
    r"\bexecuted the (?:trade|order)\b", r"\bplaced the (?:order|trade)\b",
    r"\btrimmed the position\b", r"\bexited the position\b", r"\breduced the position\b",
    r"\bforced (?:the )?compliance\b",
]


def _expected_severity(rule_type: str, status: str, breach_type: str) -> str:
    if rule_type == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    if rule_type in ("restriction", "regulatory"):
        return "High"
    if breach_type == "pre_trade":
        return "High"
    return "Medium"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    alerts = pack.get("alerts")
    if not isinstance(alerts, list):
        return ["pack has no 'alerts' list"]

    fps_seen = set()
    for i, a in enumerate(alerts):
        tag = f"alert[{i}] ({a.get('fingerprint','?')})"
        for k in ("fingerprint", "portfolio_id", "rule_id", "rule_type", "status",
                  "breach_type", "severity", "queue"):
            if not a.get(k):
                errors.append(f"{tag}: missing '{k}'")
        status = a.get("status")
        if status not in STATUSES:
            errors.append(f"{tag}: status {status!r} not in {sorted(STATUSES)}")
        sev = a.get("severity")
        if sev not in SEVERITIES:
            errors.append(f"{tag}: severity {sev!r} not in {sorted(SEVERITIES)}")
        ev = a.get("evidence") or []
        if not ev:
            errors.append(f"{tag}: no evidence rows")
        else:
            if not any((row.get("citation") or "").strip() for row in ev):
                errors.append(f"{tag}: no cited evidence row")
        # severity + queue tie-out
        exp = _expected_severity(a.get("rule_type"), status, a.get("breach_type"))
        if sev != exp:
            errors.append(f"{tag}: severity {sev!r} != deterministic {exp!r} "
                          f"for (type={a.get('rule_type')}, status={status}, breach_type={a.get('breach_type')})")
        if sev in SEVERITY_QUEUE and a.get("queue") != SEVERITY_QUEUE.get(sev):
            errors.append(f"{tag}: queue {a.get('queue')!r} != {SEVERITY_QUEUE.get(sev)!r} for severity {sev}")
        # threshold alerts must carry measured + limit
        if a.get("rule_type") in THRESHOLD_TYPES:
            if a.get("measured_pct") is None:
                errors.append(f"{tag}: threshold alert missing measured_pct")
            if a.get("limit") is None:
                errors.append(f"{tag}: threshold alert missing limit")
        fp = a.get("fingerprint")
        if fp in fps_seen:
            errors.append(f"{tag}: duplicate fingerprint within alerts")
        fps_seen.add(fp)

    # deduplication integrity
    new_fps = pack.get("new_alerts")
    open_fps = pack.get("still_open")
    if not isinstance(new_fps, list) or not isinstance(open_fps, list):
        errors.append("pack missing 'new_alerts' and/or 'still_open' lists")
    else:
        set_new, set_open = set(new_fps), set(open_fps)
        if len(new_fps) != len(set_new):
            errors.append("duplicate fingerprint within new_alerts (re-raised alert)")
        both = set_new & set_open
        if both:
            errors.append(f"fingerprint(s) in both new_alerts and still_open (dedup broken): {sorted(both)}")
        for a in alerts:
            fp = a.get("fingerprint")
            if a.get("is_duplicate"):
                if fp not in set_open:
                    errors.append(f"duplicate alert {fp} not routed to still_open")
                if fp in set_new:
                    errors.append(f"duplicate alert {fp} wrongly re-raised in new_alerts")
            else:
                if fp not in set_new:
                    errors.append(f"new alert {fp} missing from new_alerts")

    # freshness handling — stale portfolios must be flagged, never silently dropped
    freshness = pack.get("data_freshness")
    if not isinstance(freshness, list):
        errors.append("pack missing 'data_freshness'")
    else:
        stale_pids = {f.get("portfolio_id") for f in freshness if f.get("stale")}
        fresh_alert_pids = {a.get("portfolio_id") for a in alerts if a.get("breach_type") == "freshness"}
        for pid in stale_pids:
            if pid not in fresh_alert_pids:
                errors.append(f"stale portfolio {pid} has no freshness alert (freshness not surfaced)")
        for a in alerts:
            if a.get("portfolio_id") in stale_pids and not a.get("stale_input"):
                errors.append(f"alert {a.get('fingerprint')} on stale portfolio not flagged stale_input")

    # escalation packaging tie-out
    esc = pack.get("escalations")
    if not isinstance(esc, list):
        errors.append("pack missing 'escalations'")
    else:
        total = sum(int(e.get("count", 0)) for e in esc)
        if total != len(alerts):
            errors.append(f"escalation counts sum {total} != alert count {len(alerts)}")
        for e in esc:
            if e.get("severity") in SEVERITY_QUEUE and e.get("queue") != SEVERITY_QUEUE[e["severity"]]:
                errors.append(f"escalation queue mismatch for severity {e.get('severity')}")

    # no autonomous-action / decision language (scan narrative + notes only)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))])
    for pat in ACTION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"autonomous-action language detected: {m.group(0)!r} "
                          f"(this monitor alerts only; it never acts, decides, or closes)")

    # standing disclaimer present
    hay = (str(pack.get("disclaimer", "")) + " " + str(pack.get("narrative", ""))).lower()
    if DISCLAIMER.lower() not in hay:
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
