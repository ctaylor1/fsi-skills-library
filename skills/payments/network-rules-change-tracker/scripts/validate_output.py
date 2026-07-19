#!/usr/bin/env python3
"""Deterministic output validation for network-rules-change-tracker.

Validates the monitoring pack (the calculate_or_transform core + an optional narrative)
before it is queued or delivered. Because this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor
operating at R3 (regulated / control decision support), the checks specifically confirm the
alert-only posture and that no autonomous decision, closure, filing, or system-of-record
write was taken:

  1. Every alert is well-formed: identity, cited evidence, status, severity, routing queue;
     readiness alerts carry days_to_effective + effective_date; authenticity alerts a reason.
  2. severity ties out to the deterministic mapping from (category, status, breach_type), and
     queue ties out to severity (no ad-hoc escalation).
  3. Deduplication integrity: new vs still-open queues partition the alerts by fingerprint;
     duplicates are routed to still-open, not re-raised as new.
  4. Freshness handling: a stale bulletin feed is flagged (freshness alert + stale_input on
     every derived alert), never silently treated as fresh.
  5. Authenticity handling: every alert derived from an unauthentic bulletin is flagged
     unverified_source, never presented as trusted.
  6. No autonomous-action / decision / closure / filing language (R3 screen) in the narrative
     or notes.
  7. The standing alert-only disclaimer is present.
  8. Escalation packaging ties out: escalation counts sum to the alert count.

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
SEVERITY_QUEUE = {"High": "network-rules-escalation",
                  "Medium": "network-rules-review-queue",
                  "Low": "network-rules-watchlist"}
DISCLAIMER = ("Monitoring alert only; no network rule was adopted, no obligation was accepted, "
              "closed, filed, or attested, no product, procedure, control, contract, or system "
              "was changed, and no system of record was updated. Network-rule changes require "
              "human payments compliance, product, and operations review and adjudication.")
# Autonomous action / decision / closure / filing language this alert-only R3 monitor must
# never emit (it recommends and evidences only; a human adjudicates):
ACTION_PATTERNS = [
    r"\bauto[- ]?closed\b", r"\bclosed the (?:alert|case|obligation|item)\b",
    r"\bsuppressed the alert\b", r"\bwe (?:adopted|implemented|deployed) the (?:rule|change)\b",
    r"\baccepted the obligation\b", r"\bmarked (?:as )?(?:compliant|implemented|complete|done)\b",
    r"\bfiled the (?:attestation|filing|report|compliance)\b", r"\bsubmitted the (?:filing|attestation|report)\b",
    r"\battested\b", r"\bcertified compliance\b", r"\bsigned off\b", r"\bsign-off (?:was )?granted\b",
    r"\bapproved the (?:change|obligation|mapping|rule)\b", r"\bgranted (?:a |an )?(?:waiver|exception|extension)\b",
    r"\bwaived the (?:obligation|requirement|deadline)\b", r"\bdispositioned\b",
    r"\bupdated the (?:control|procedure|contract|system|system of record)\b",
    r"\bchanged the (?:control|procedure|contract|system)\b", r"\bamended the (?:contract|agreement)\b",
    r"\bremediated the (?:gap|obligation|breach)\b", r"\bno (?:reviewer|human) action (?:is )?(?:required|needed)\b",
    r"\bblocked the (?:transaction|payment)\b", r"\breleased the (?:payment|transaction)\b",
    r"\bwrote (?:back )?to the (?:system of record|ledger)\b",
]


def _expected_severity(category, status, breach_type):
    if category == "freshness":
        return "Low"
    if category == "authenticity":
        return "High"
    if category == "readiness":
        if breach_type in ("overdue", "critical"):
            return "High"
        if breach_type == "high":
            return "Medium"
        return "Low"
    if category in ("mapping", "ownership"):
        return "Medium"
    return "Low" if status == "WARN" else "Medium"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    alerts = pack.get("alerts")
    if not isinstance(alerts, list):
        return ["pack has no 'alerts' list"]

    fps_seen = set()
    for i, a in enumerate(alerts):
        tag = f"alert[{i}] ({a.get('fingerprint','?')})"
        for k in ("fingerprint", "bulletin_id", "category", "breach_type", "status",
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
        exp = _expected_severity(a.get("category"), status, a.get("breach_type"))
        if sev != exp:
            errors.append(f"{tag}: severity {sev!r} != deterministic {exp!r} "
                          f"for (category={a.get('category')}, status={status}, breach_type={a.get('breach_type')})")
        if sev in SEVERITY_QUEUE and a.get("queue") != SEVERITY_QUEUE.get(sev):
            errors.append(f"{tag}: queue {a.get('queue')!r} != {SEVERITY_QUEUE.get(sev)!r} for severity {sev}")
        # category-specific evidence payloads
        if a.get("category") == "readiness":
            if a.get("days_to_effective") is None:
                errors.append(f"{tag}: readiness alert missing days_to_effective")
            if not a.get("effective_date"):
                errors.append(f"{tag}: readiness alert missing effective_date")
        if a.get("category") == "authenticity" and not a.get("reason"):
            errors.append(f"{tag}: authenticity alert missing reason")
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

    # freshness handling — a stale feed must be flagged, never silently treated as fresh
    freshness = pack.get("data_freshness")
    if not isinstance(freshness, list):
        errors.append("pack missing 'data_freshness'")
    else:
        feed_stale = any(f.get("stale") for f in freshness)
        has_fresh_alert = any(a.get("category") == "freshness" for a in alerts)
        if feed_stale and not has_fresh_alert:
            errors.append("stale bulletin feed has no freshness alert (freshness not surfaced)")
        if feed_stale:
            for a in alerts:
                if a.get("category") != "freshness" and not a.get("stale_input"):
                    errors.append(f"alert {a.get('fingerprint')} on stale feed not flagged stale_input")

    # authenticity handling — alerts from an unauthentic bulletin must be flagged unverified
    summary = pack.get("summary") or {}
    unauth = set(summary.get("unauthentic_bulletins") or [])
    for a in alerts:
        if a.get("bulletin_id") in unauth and not a.get("unverified_source"):
            errors.append(f"alert {a.get('fingerprint')} from unauthentic bulletin not flagged unverified_source")

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
                          f"(this monitor alerts only; it never decides, closes, files, or writes a system of record)")

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
