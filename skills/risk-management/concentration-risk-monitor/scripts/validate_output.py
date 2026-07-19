#!/usr/bin/env python3
"""Deterministic output validation for concentration-risk-monitor.

Validates the monitoring pack (the calculate_or_transform core + an optional narrative)
before it is queued or delivered. Because this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor
at risk tier R3 (regulated decision support), the checks confirm the alert-only posture and
that NO autonomous regulated decision, closure, filing, or system-of-record write is present:

  1. Every alert is well-formed: identity, cited evidence, status, severity, a routing queue,
     and a measured value + limit + unit.
  2. severity ties out to the deterministic mapping from
     (rule_type, status, breach_type, regulatory); queue ties out to severity.
  3. Deduplication integrity: new vs still-open queues partition alerts by fingerprint;
     duplicates route to still-open, not re-raised as new.
  4. Freshness handling: stale books are flagged (freshness alert + stale_input), never
     silently dropped or treated as fresh.
  5. No autonomous-action OR decision/closure/filing language (regex screen) in the narrative
     or notes — this monitor recommends and evidences only; a human adjudicates.
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

SEVERITIES = {"High", "Medium", "Low"}
STATUSES = {"WARN", "BREACH"}
SEVERITY_QUEUE = {"High": "risk-escalation",
                  "Medium": "risk-review-queue",
                  "Low": "risk-monitoring-watchlist"}
DISCLAIMER = ("Monitoring alert only; no risk decision, limit change, waiver, case closure, "
              "regulatory filing, or system-of-record change has been made. Concentration "
              "exceptions require human risk review and adjudication.")

# Autonomous ACTION language an alert-only monitor must never emit:
ACTION_PATTERNS = [
    r"\breduc(?:e|ed|ing) the (?:exposure|position|limit)\b",
    r"\bexit(?:ed|ing)? the (?:exposure|position)\b",
    r"\bunwound the (?:position|exposure)\b", r"\bhedged the (?:exposure|position)\b",
    r"\bcut the (?:exposure|limit)\b", r"\bsold down\b", r"\bliquidat(?:e|ed|ing)\b",
    r"\bblock(?:ed|ing)? the (?:deal|onboarding|trade)\b",
    r"\bmigrat(?:e|ed|ing) (?:the )?workloads?\b", r"\bterminat(?:e|ed|ing) the vendor\b",
]
# Regulated DECISION / CLOSURE / FILING language (R3 — human adjudication is mandatory):
DECISION_PATTERNS = [
    r"\bbreach (?:was )?confirmed\b", r"\bconfirmed the breach\b",
    r"\bfinal(?:ly)? determin(?:ed|ation)\b", r"\badjudicat(?:e|ed|ing)\b",
    r"\bwe (?:have )?(?:approved|approve)\b", r"\bapproved (?:a|the|an) (?:waiver|limit|increase|exception)\b",
    r"\bwaiver (?:was )?(?:granted|approved)\b", r"\bgranted (?:a|an) (?:waiver|exception)\b",
    r"\blimit (?:was )?(?:raised|increased|changed|overridden)\b",
    r"\boverr(?:ode|ide|idden) the (?:limit|rule)\b",
    r"\bcase (?:was )?closed\b", r"\bclosed the (?:case|alert)\b",
    r"\bauto[- ]?closed\b", r"\bsuppressed the alert\b", r"\bdismissed the (?:alert|breach)\b",
    r"\bfil(?:e|ed|ing) (?:the |a )?(?:regulatory |large[- ]exposure )?(?:report|filing|return)\b",
    r"\bsubmitted the (?:report|filing|return|notification)\b",
    r"\breported (?:it |the breach )?to the regulator\b",
    r"\bno (?:further |reviewer )?action (?:is )?required\b",
]
ALL_PATTERNS = [("action", p) for p in ACTION_PATTERNS] + [("decision", p) for p in DECISION_PATTERNS]


def _expected_severity(rule_type, status, breach_type, regulatory) -> str:
    if rule_type == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    if breach_type == "proposed":
        return "High"
    if rule_type == "diversification":
        return "High"
    if regulatory:
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
        for k in ("fingerprint", "book_id", "rule_id", "rule_type", "status",
                  "breach_type", "severity", "queue", "unit"):
            if not a.get(k):
                errors.append(f"{tag}: missing '{k}'")
        status = a.get("status")
        if status not in STATUSES:
            errors.append(f"{tag}: status {status!r} not in {sorted(STATUSES)}")
        sev = a.get("severity")
        if sev not in SEVERITIES:
            errors.append(f"{tag}: severity {sev!r} not in {sorted(SEVERITIES)}")
        # measured + limit must be present (numeric, including 0)
        if a.get("measured") is None:
            errors.append(f"{tag}: missing measured value")
        if a.get("limit") is None:
            errors.append(f"{tag}: missing limit")
        ev = a.get("evidence") or []
        if not ev:
            errors.append(f"{tag}: no evidence rows")
        elif not any((row.get("citation") or "").strip() for row in ev):
            errors.append(f"{tag}: no cited evidence row")
        # severity + queue tie-out
        exp = _expected_severity(a.get("rule_type"), status, a.get("breach_type"),
                                 bool(a.get("regulatory", False)))
        if sev != exp:
            errors.append(f"{tag}: severity {sev!r} != deterministic {exp!r} for "
                          f"(type={a.get('rule_type')}, status={status}, "
                          f"breach_type={a.get('breach_type')}, regulatory={a.get('regulatory')})")
        if sev in SEVERITY_QUEUE and a.get("queue") != SEVERITY_QUEUE.get(sev):
            errors.append(f"{tag}: queue {a.get('queue')!r} != {SEVERITY_QUEUE.get(sev)!r} for severity {sev}")
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

    # freshness handling — stale books must be flagged, never silently dropped
    freshness = pack.get("data_freshness")
    if not isinstance(freshness, list):
        errors.append("pack missing 'data_freshness'")
    else:
        stale_bids = {f.get("book_id") for f in freshness if f.get("stale")}
        fresh_alert_bids = {a.get("book_id") for a in alerts if a.get("breach_type") == "freshness"}
        for bid in stale_bids:
            if bid not in fresh_alert_bids:
                errors.append(f"stale book {bid} has no freshness alert (freshness not surfaced)")
        for a in alerts:
            if a.get("book_id") in stale_bids and not a.get("stale_input"):
                errors.append(f"alert {a.get('fingerprint')} on stale book not flagged stale_input")

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

    # no autonomous-action / decision / closure / filing language (narrative + notes)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))])
    for kind, pat in ALL_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"autonomous-action or decision language detected ({kind}): "
                          f"{m.group(0)!r} (this monitor alerts only; it never acts, decides, "
                          f"closes, or files — a human adjudicates)")

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
