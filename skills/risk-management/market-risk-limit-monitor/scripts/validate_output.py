#!/usr/bin/env python3
"""Deterministic output validation for market-risk-limit-monitor.

Validates the monitoring pack (the calculate_or_transform core + an optional narrative)
before it is queued or delivered. Because this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor
at risk tier R3 (mandatory human adjudication), the checks specifically confirm the
alert-only posture and that no autonomous action, decision, closure, or filing was taken:

  1. Every alert is well-formed: identity, cited evidence, status, severity, and a routing
     queue; threshold-metric alerts carry a measured value and a limit.
  2. severity ties out to the deterministic mapping from (metric, status, breach_type), and
     queue ties out to severity (no ad-hoc escalation).
  3. Deduplication integrity: new vs still-open queues partition the alerts by fingerprint;
     duplicates are routed to still-open, not re-raised as new.
  4. Freshness handling: stale units are flagged (freshness alert + stale_input), never
     silently dropped or treated as current.
  5. No autonomous-action / decision / closure / filing language (no trade, hedge, cut,
     rebalance, limit change/excess, waiver, breach closure, alert closure, or breach
     filing) in the narrative or notes. R3: a decision/closure/filing screen must fail closed.
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

THRESHOLD_METRICS = {"var", "es", "sensitivity", "stress_loss", "notional", "concentration"}
SEVERITIES = {"High", "Medium", "Low"}
STATUSES = {"WARN", "BREACH"}
SEVERITY_QUEUE = {"High": "market-risk-escalation",
                  "Medium": "market-risk-review-queue",
                  "Low": "risk-monitoring-watchlist"}
DISCLAIMER = ("Monitoring alert only; no trade, hedge, position change, limit change, "
              "waiver, breach closure, or system-of-record change has been made. "
              "Market-risk limit exceptions require human risk-management review and "
              "disposition.")
# Autonomous action / decision / closure / filing language this alert-only R3 monitor must
# never emit. Disposition (trade/hedge, limit change, waiver, closure, filing) is human.
ACTION_PATTERNS = [
    r"\bblock(?:ed|ing)? the (?:trade|order)\b", r"\btrade (?:was |is )?blocked\b",
    r"\bcancel(?:led|ed)? the (?:order|trade)\b", r"\bwe (?:sold|sell|bought|buy)\b",
    r"\bhedged the (?:book|position|desk|risk)\b", r"\bput on a hedge\b",
    r"\bcut the (?:position|risk|book)\b", r"\breduced the (?:position|exposure|risk)\b",
    r"\btrimmed the position\b", r"\bexited the position\b", r"\bliquidat(?:e|ed|ing)\b",
    r"\brebalanc(?:e|ed|ing)\b", r"\bde-?risked\b",
    r"\braised the limit\b", r"\bincreased the limit\b",
    r"\blimit (?:was )?(?:raised|increased|reset)\b",
    r"\bgranted a (?:temporary )?(?:limit )?excess\b",
    r"\btemporary (?:limit )?excess (?:was )?granted\b",
    r"\bapproved the (?:excess|breach|limit)\b",
    r"\bwaiver (?:was )?granted\b", r"\bgranted a waiver\b",
    r"\bcleared the breach\b", r"\bcured the breach\b", r"\bclosed the breach\b",
    r"\bbreach (?:was )?(?:cleared|closed|cured|resolved)\b",
    r"\bauto[- ]?closed\b", r"\bclosed the alert\b", r"\bsuppressed the alert\b",
    r"\bdowngraded the alert\b", r"\bsnoozed the alert\b",
    r"\boverr(?:ode|ide) the (?:limit|rule)\b",
    r"\bfiled (?:the|a) (?:breach|regulatory)?\s*(?:report|filing)\b",
    r"\breported the breach to\b", r"\bnotified the regulator\b",
    r"\bsubmitted the (?:breach|regulatory) (?:report|filing)\b",
    r"\bexecuted the (?:trade|order|hedge)\b", r"\bplaced the (?:order|trade|hedge)\b",
]


def _expected_severity(metric: str, status: str, breach_type: str) -> str:
    if metric == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    if breach_type == "projected":
        return "High"
    if metric in ("var", "es", "stress_loss"):
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
        for k in ("fingerprint", "unit_id", "limit_id", "metric", "status",
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
        elif not any((row.get("citation") or "").strip() for row in ev):
            errors.append(f"{tag}: no cited evidence row")
        # severity + queue tie-out
        exp = _expected_severity(a.get("metric"), status, a.get("breach_type"))
        if sev != exp:
            errors.append(f"{tag}: severity {sev!r} != deterministic {exp!r} "
                          f"for (metric={a.get('metric')}, status={status}, breach_type={a.get('breach_type')})")
        if sev in SEVERITY_QUEUE and a.get("queue") != SEVERITY_QUEUE.get(sev):
            errors.append(f"{tag}: queue {a.get('queue')!r} != {SEVERITY_QUEUE.get(sev)!r} for severity {sev}")
        # threshold-metric alerts must carry measured + limit
        if a.get("metric") in THRESHOLD_METRICS:
            if a.get("measured") is None:
                errors.append(f"{tag}: threshold-metric alert missing measured")
            if a.get("limit") is None:
                errors.append(f"{tag}: threshold-metric alert missing limit")
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

    # freshness handling — stale units must be flagged, never silently dropped
    freshness = pack.get("data_freshness")
    if not isinstance(freshness, list):
        errors.append("pack missing 'data_freshness'")
    else:
        stale_units = {f.get("unit_id") for f in freshness if f.get("stale")}
        fresh_alert_units = {a.get("unit_id") for a in alerts if a.get("breach_type") == "freshness"}
        for uid in stale_units:
            if uid not in fresh_alert_units:
                errors.append(f"stale unit {uid} has no freshness alert (freshness not surfaced)")
        for a in alerts:
            if a.get("unit_id") in stale_units and not a.get("stale_input"):
                errors.append(f"alert {a.get('fingerprint')} on stale unit not flagged stale_input")

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

    # no autonomous-action / decision / closure / filing language (scan narrative + notes)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))])
    for pat in ACTION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"autonomous-action language detected: {m.group(0)!r} "
                          f"(this monitor alerts only; it never acts, decides, closes, or files)")

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
