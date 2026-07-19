#!/usr/bin/env python3
"""Deterministic output validation for key-risk-indicator-monitor.

Validates the KRI monitoring pack (the calculate_or_transform core + an optional narrative)
before it is queued or delivered. Because this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor
at risk tier R3 (decision support with mandatory human adjudication), the checks specifically
confirm the alert-only posture and that no autonomous regulated action or decision was taken:

  1. Every alert is well-formed: identity, cited evidence, status, severity, and a routing
     queue; threshold and seasonal alerts carry a measured value and a threshold.
  2. severity ties out to the deterministic mapping from (breach_type, status, critical),
     and queue ties out to severity (no ad-hoc escalation).
  3. Deduplication integrity: new vs still-open queues partition the alerts by fingerprint;
     duplicates are routed to still-open, not re-raised as new.
  4. Freshness handling: KRIs whose latest observation is stale are flagged (freshness alert
     + stale_input), never silently dropped or treated as current.
  5. No autonomous-action / regulated-decision language (no risk acceptance, breach waiver,
     limit/appetite change, risk- or control-rating change, alert/incident/case closure,
     regulatory filing, or system-of-record write) in the narrative or notes. R3:
     recommendations/evidence only.
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

MEASURED_TYPES = {"threshold", "seasonal"}
SEVERITIES = {"High", "Medium", "Low"}
STATUSES = {"WARN", "BREACH"}
SEVERITY_QUEUE = {"High": "risk-committee-escalation",
                  "Medium": "risk-review-queue",
                  "Low": "kri-monitoring-watchlist"}
DISCLAIMER = ("Monitoring alert only; no risk acceptance, breach waiver, limit or appetite "
              "change, risk- or control-rating change, incident or case closure, regulatory "
              "filing, or system-of-record change has been made or recommended. KRI exceptions "
              "require human risk review and adjudication.")
# Autonomous action / regulated-decision language this alert-only monitor must never emit:
ACTION_PATTERNS = [
    r"\baccept(?:ed|ing)? the (?:risk|breach)\b", r"\brisk (?:was |is )?accepted\b",
    r"\b(?:granted|approved|issued|executed) (?:a |the )?(?:breach )?waiver\b",
    r"\bwaiver (?:was |is )?(?:granted|approved|issued)\b", r"\bwaived the (?:breach|limit|kri)\b",
    r"\b(?:raised|lowered|changed|adjusted|reset|widened|relaxed) the (?:limit|threshold|appetite|tolerance)\b",
    r"\b(?:limit|threshold|appetite) (?:was |is )?(?:raised|lowered|changed|adjusted|widened|relaxed)\b",
    r"\boverr(?:ode|ide) the (?:limit|threshold|kri)\b",
    r"\b(?:downgrad|upgrad|chang|re-?rat)(?:e|ed|ing) the (?:risk rating|control rating)\b",
    r"\b(?:risk|control)[ -]?rating (?:was |is )?(?:downgraded|upgraded|changed|re-?rated)\b",
    r"\bauto[- ]?closed\b", r"\bclosed the (?:alert|incident|case|breach)\b",
    r"\bsuppress(?:ed)? the alert\b", r"\bsnoozed the alert\b", r"\bcleared the (?:alert|breach)\b",
    r"\bmark(?:ed)? (?:the kri |every kri |it |them )?(?:as )?compliant\b",
    r"\bcured the breach\b", r"\bremediated the (?:breach|kri)\b", r"\bcorrected the breach\b",
    r"\bwe have corrected\b", r"\breset the kri\b",
    r"\bfiled (?:the |a )?(?:regulatory )?(?:report|filing|return)\b",
    r"\bsubmitted (?:the |a )?(?:regulatory )?(?:report|filing|return)\b",
    r"\b(?:regulatory )?(?:report|filing|return) (?:was |is )?(?:filed|submitted)\b",
    r"\bnotifi(?:ed|es) the regulator\b", r"\breported (?:it |the breach )?to the regulator\b",
    r"\bwrote (?:back )?to the (?:register|system of record)\b",
    r"\bupdated the (?:risk register|system of record)\b",
]


def _expected_severity(breach_type: str, status: str, critical: bool) -> str:
    if breach_type == "freshness":
        return "Low"
    if breach_type == "data_quality":
        return "Medium" if critical else "Low"
    if status == "WARN":
        return "Low"
    if breach_type == "threshold":
        return "High" if critical else "Medium"
    return "Medium"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    alerts = pack.get("alerts")
    if not isinstance(alerts, list):
        return ["pack has no 'alerts' list"]

    fps_seen = set()
    for i, a in enumerate(alerts):
        tag = f"alert[{i}] ({a.get('fingerprint','?')})"
        for k in ("fingerprint", "kri_id", "category", "status", "breach_type",
                  "severity", "queue"):
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
        exp = _expected_severity(a.get("breach_type"), status, bool(a.get("critical")))
        if sev != exp:
            errors.append(f"{tag}: severity {sev!r} != deterministic {exp!r} "
                          f"for (breach_type={a.get('breach_type')}, status={status}, critical={bool(a.get('critical'))})")
        if sev in SEVERITY_QUEUE and a.get("queue") != SEVERITY_QUEUE.get(sev):
            errors.append(f"{tag}: queue {a.get('queue')!r} != {SEVERITY_QUEUE.get(sev)!r} for severity {sev}")
        # threshold / seasonal alerts must carry measured + threshold
        if a.get("breach_type") in MEASURED_TYPES:
            if a.get("measured") is None:
                errors.append(f"{tag}: {a.get('breach_type')} alert missing measured")
            if a.get("threshold") is None:
                errors.append(f"{tag}: {a.get('breach_type')} alert missing threshold")
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
            elif fp not in set_new:
                errors.append(f"new alert {fp} missing from new_alerts")

    # freshness handling — stale KRIs must be flagged, never silently dropped
    freshness = pack.get("data_freshness")
    if not isinstance(freshness, list):
        errors.append("pack missing 'data_freshness'")
    else:
        stale_ids = {f.get("kri_id") for f in freshness if f.get("stale")}
        fresh_alert_ids = {a.get("kri_id") for a in alerts if a.get("breach_type") == "freshness"}
        for kid in stale_ids:
            if kid not in fresh_alert_ids:
                errors.append(f"stale KRI {kid} has no freshness alert (freshness not surfaced)")
        for a in alerts:
            if a.get("kri_id") in stale_ids and not a.get("stale_input"):
                errors.append(f"alert {a.get('fingerprint')} on stale KRI not flagged stale_input")

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

    # no autonomous-action / regulated-decision language (scan narrative + notes only)
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
