#!/usr/bin/env python3
"""Deterministic output validation for transaction-monitoring-alert-investigator.

Validates the investigation pack (the calculate_or_transform core + an optional narrative)
before it is queued or delivered. Because this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor
and R3 decision-support, the checks confirm the alert-only / recommend-only posture and that
no autonomous decision, closure, or filing was made:

  1. Every indicator is well-formed: identity, >=1 cited evidence row, status in {WARN,BREACH},
     a severity, and a routing queue; threshold indicators carry a measured value + threshold.
  2. severity ties out to the deterministic (rule_type, status) mapping and queue ties out to
     severity (typology application; no ad-hoc escalation).
  3. Deduplication integrity: new_alerts and still_open partition indicators by fingerprint;
     duplicates route to still_open, not re-raised as new.
  4. Freshness handling: stale subjects are flagged (freshness indicator + stale_input), never
     silently dropped or treated as current.
  5. Each subject package has a chronology in non-decreasing date order (chronology integrity)
     and a recommended_disposition that (a) is in the recommend-only vocabulary and (b) ties
     out to the deterministic mapping from its indicator counts (disposition consistency).
  6. No autonomous decision / closure / filing language anywhere (no case closed, SAR filed,
     alert dispositioned/cleared, account frozen/blocked, or suspicion determination).
  7. The standing alert-only disclaimer is present.
  8. Escalation packaging ties out: escalation counts sum to the indicator count.

Fail closed on any miss.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

THRESHOLD_TYPES = {"structuring", "pass_through", "geography", "velocity", "cash_intensity"}
SEVERITIES = {"High", "Medium", "Low"}
STATUSES = {"WARN", "BREACH"}
SEVERITY_QUEUE = {"High": "fiu-escalation-queue",
                  "Medium": "aml-investigation-queue",
                  "Low": "aml-monitoring-watchlist"}
RECOMMENDATIONS = {"recommend_escalate", "recommend_further_review", "recommend_monitor"}
DISCLAIMER = (
    "Monitoring alert only; this package is investigative decision-support. No case has been "
    "closed, no suspicious activity report has been filed or decided, no alert has been "
    "dispositioned, no account has been frozen or blocked, and no system of record has been "
    "updated. Every AML disposition, escalation decision, and SAR filing is a human FIU "
    "decision.")
# Autonomous decision / closure / filing language this alert-only, R3 monitor must never emit:
ACTION_PATTERNS = [
    r"\bclosed the (?:case|alert)\b", r"\bcase (?:was |is )?closed\b",
    r"\balert (?:was |is )?closed\b", r"\bauto[- ]?closed\b", r"\bno further action taken\b",
    r"\bcleared the (?:alert|subject|customer)\b", r"\bdispositioned the (?:alert|case)\b",
    r"\bdetermined (?:it |this |the activity )?(?:to be )?(?:not )?suspicious\b",
    r"\b(?:filed|filing|submitted) (?:a |the )?(?:sar|suspicious activity report)\b",
    r"\bsar (?:was |has been )?filed\b", r"\breported to fincen\b", r"\bfiled with fincen\b",
    r"\bfroze the account\b", r"\bblocked the account\b", r"\bfrozen the account\b",
    r"\bsuspended the (?:account|customer)\b", r"\bfiled the report\b",
    r"\bexited the (?:customer|relationship)\b", r"\boffboarded the customer\b",
    r"\bmade (?:a |the )?(?:final )?determination\b", r"\bconfirmed money laundering\b",
    r"\bwrote (?:to|back to) the (?:case management|system of record)\b",
]


def _expected_severity(rule_type: str, status: str) -> str:
    if rule_type == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    if rule_type in ("structuring", "pass_through"):
        return "High"
    return "Medium"


def _expected_recommendation(high: int, medium: int, warn: int) -> str:
    if high >= 1 or medium >= 2:
        return "recommend_escalate"
    if medium >= 1 or warn >= 1:
        return "recommend_further_review"
    return "recommend_monitor"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    indicators = pack.get("indicators")
    if not isinstance(indicators, list):
        return ["pack has no 'indicators' list"]

    fps_seen = set()
    for i, a in enumerate(indicators):
        tag = f"indicator[{i}] ({a.get('fingerprint','?')})"
        for k in ("fingerprint", "subject_id", "rule_id", "rule_type", "status",
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
        exp = _expected_severity(a.get("rule_type"), status)
        if sev != exp:
            errors.append(f"{tag}: severity {sev!r} != deterministic {exp!r} "
                          f"for (type={a.get('rule_type')}, status={status})")
        if sev in SEVERITY_QUEUE and a.get("queue") != SEVERITY_QUEUE.get(sev):
            errors.append(f"{tag}: queue {a.get('queue')!r} != {SEVERITY_QUEUE.get(sev)!r} for severity {sev}")
        if a.get("rule_type") in THRESHOLD_TYPES:
            if a.get("measured") is None:
                errors.append(f"{tag}: threshold indicator missing measured")
            if a.get("threshold") is None:
                errors.append(f"{tag}: threshold indicator missing threshold")
        fp = a.get("fingerprint")
        if fp in fps_seen:
            errors.append(f"{tag}: duplicate fingerprint within indicators")
        fps_seen.add(fp)

    # deduplication integrity
    new_fps = pack.get("new_alerts")
    open_fps = pack.get("still_open")
    if not isinstance(new_fps, list) or not isinstance(open_fps, list):
        errors.append("pack missing 'new_alerts' and/or 'still_open' lists")
    else:
        set_new, set_open = set(new_fps), set(open_fps)
        if len(new_fps) != len(set_new):
            errors.append("duplicate fingerprint within new_alerts (re-raised indicator)")
        both = set_new & set_open
        if both:
            errors.append(f"fingerprint(s) in both new_alerts and still_open (dedup broken): {sorted(both)}")
        for a in indicators:
            fp = a.get("fingerprint")
            if a.get("is_duplicate"):
                if fp not in set_open:
                    errors.append(f"duplicate indicator {fp} not routed to still_open")
                if fp in set_new:
                    errors.append(f"duplicate indicator {fp} wrongly re-raised in new_alerts")
            elif fp not in set_new:
                errors.append(f"new indicator {fp} missing from new_alerts")

    # freshness handling — stale subjects must be flagged, never silently dropped
    freshness = pack.get("data_freshness")
    if not isinstance(freshness, list):
        errors.append("pack missing 'data_freshness'")
        stale_ids = set()
    else:
        stale_ids = {f.get("subject_id") for f in freshness if f.get("stale")}
        fresh_ind_ids = {a.get("subject_id") for a in indicators if a.get("rule_type") == "freshness"}
        for sid in stale_ids:
            if sid not in fresh_ind_ids:
                errors.append(f"stale subject {sid} has no freshness indicator (freshness not surfaced)")
        for a in indicators:
            if a.get("subject_id") in stale_ids and not a.get("stale_input"):
                errors.append(f"indicator {a.get('fingerprint')} on stale subject not flagged stale_input")

    # per-subject chronology + recommendation consistency (disposition + no-closure vocabulary)
    subjects = pack.get("subjects")
    if not isinstance(subjects, list):
        errors.append("pack missing 'subjects' packages")
    else:
        for s in subjects:
            sid = s.get("subject_id", "?")
            rec = s.get("recommended_disposition")
            if rec not in RECOMMENDATIONS:
                errors.append(f"subject {sid}: recommended_disposition {rec!r} not in recommend-only "
                              f"vocabulary {sorted(RECOMMENDATIONS)} (no autonomous closure/filing)")
            counts = s.get("indicator_counts") or {}
            exp_rec = _expected_recommendation(int(counts.get("High", 0)),
                                               int(counts.get("Medium", 0)),
                                               int(counts.get("warn", 0)))
            if rec in RECOMMENDATIONS and rec != exp_rec:
                errors.append(f"subject {sid}: recommended_disposition {rec!r} != deterministic "
                              f"{exp_rec!r} for counts {dict(counts)}")
            chron = s.get("chronology") or []
            dates = [str(r.get("date") or "") for r in chron]
            if dates != sorted(dates):
                errors.append(f"subject {sid}: chronology is not in non-decreasing date order")

    # escalation packaging tie-out
    esc = pack.get("escalations")
    if not isinstance(esc, list):
        errors.append("pack missing 'escalations'")
    else:
        total = sum(int(e.get("count", 0)) for e in esc)
        if total != len(indicators):
            errors.append(f"escalation counts sum {total} != indicator count {len(indicators)}")
        for e in esc:
            if e.get("severity") in SEVERITY_QUEUE and e.get("queue") != SEVERITY_QUEUE[e["severity"]]:
                errors.append(f"escalation queue mismatch for severity {e.get('severity')}")

    # no autonomous decision / closure / filing language (narrative + notes + subject rationale)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str((s or {}).get("rationale", "")) for s in (subjects or [])])
    for pat in ACTION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"autonomous decision/closure/filing language detected: {m.group(0)!r} "
                          f"(this monitor alerts and recommends only; every AML disposition, "
                          f"closure, and SAR filing is a human FIU decision)")

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
