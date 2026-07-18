#!/usr/bin/env python3
"""Deterministic output validation for catastrophe-exposure-monitor.

Validates the alert-queue package (the calculate_or_transform core + a narrative) before it
is queued or delivered. A Monitor & alert skill only ALERTS and QUEUES; this check fails
closed if the package looks like it acted, decided, or closed something. Checks:

  1. Freshness handling — every declared source carries a freshness status (fresh|stale);
     if any source is stale the package must record confidence == "degraded".
  2. Deduplication — every alert has a stable alert_key and a status in
     {new, ongoing, cleared}; no duplicate alert_keys; the dedup summary ties to the alerts.
  3. Escalation / queue packaging — every active (new|ongoing) alert has a queue target,
     >= 1 cited evidence row, and a severity + suggested_response_priority that equal the
     deterministic mapping from its exceedance_ratio.
  4. NO autonomous action — no bind/decline/cede/cancel/endorse/reserve/limit-change/
     alert-closure language anywhere in the free text; the standing disclaimer is present.

Usage:
  python validate_output.py alert_package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; exposure and modeled-loss figures are estimates for "
              "human review. No underwriting, reinsurance, capacity, reserving, or "
              "system-of-record action has been taken.")
PRIORITY = {"Critical": "P1", "Elevated": "P2", "Watch": "P3", "Informational": "P4"}
VALID_STATUS = {"new", "ongoing", "cleared"}

# Autonomous-action / decision / closure language a read-only alert-only monitor must never
# use. The monitor observes and queues; humans and downstream skills act.
ACTION_PATTERNS = [
    r"\bbound (the |additional )?(coverage|reinsurance|capacity)", r"\bwe (have )?bound\b",
    r"\bpurchased reinsurance\b", r"\bceded\b", r"\bplaced (the )?reinsurance\b",
    r"\b(reduced|increased|adjusted|changed) the limit\b", r"\bmoved capacity\b",
    r"\bcancel(l)?ed the policy\b", r"\bnon-renew(ed)?\b", r"\bdeclined the (risk|submission)\b",
    r"\bissued (an )?endorsement\b", r"\bbooked (the )?reserve\b", r"\badjusted (the )?reserve",
    r"\bclosed the alert\b", r"\bsuppressed the alert\b", r"\bwrote (it )?to (the )?system of record\b",
    r"\bbind (additional |more )?(coverage|reinsurance|capacity)\b",
]


def band_for_ratio(r: float, approaching: float = 0.9) -> str | None:
    if r >= 1.5:
        return "Critical"
    if r >= 1.25:
        return "Elevated"
    if r >= 1.0:
        return "Watch"
    if r >= approaching:
        return "Informational"
    return None


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    # 1. freshness handling
    sources = pack.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("no sources[] freshness report present")
        sources = []
    any_stale = False
    for s in sources:
        fr = s.get("freshness")
        if fr not in ("fresh", "stale"):
            errors.append(f"source {s.get('source','?')} missing freshness status")
        if fr == "stale":
            any_stale = True
    if any_stale and pack.get("confidence") != "degraded":
        errors.append("a source is stale but confidence != 'degraded' (freshness not handled)")

    # 2. deduplication
    alerts = pack.get("alerts")
    if not isinstance(alerts, list):
        errors.append("alerts[] missing")
        alerts = []
    seen = set()
    for a in alerts:
        key = a.get("alert_key")
        if not key:
            errors.append("alert missing alert_key (dedup key)")
        elif key in seen:
            errors.append(f"duplicate alert_key {key!r} (deduplication failed)")
        else:
            seen.add(key)
        if a.get("status") not in VALID_STATUS:
            errors.append(f"alert {key!r} status {a.get('status')!r} not in {sorted(VALID_STATUS)}")

    active = [a for a in alerts if a.get("status") in ("new", "ongoing")]
    dd = pack.get("dedup") or {}
    for st, cnt in (("new", sum(1 for a in active if a.get("status") == "new")),
                    ("ongoing", sum(1 for a in active if a.get("status") == "ongoing")),
                    ("cleared", sum(1 for a in alerts if a.get("status") == "cleared"))):
        if dd.get(st) != cnt:
            errors.append(f"dedup summary {st}={dd.get(st)!r} does not tie to alerts ({cnt})")

    # 3. escalation / queue packaging (deterministic tie-out on active alerts)
    for a in active:
        key = a.get("alert_key", "?")
        if not a.get("queue"):
            errors.append(f"alert {key} missing queue target")
        ev = a.get("evidence") or []
        if not ev:
            errors.append(f"active alert {key} has no evidence")
        for row in ev:
            if not str(row.get("citation") or "").strip():
                errors.append(f"active alert {key} evidence row missing citation")
        ratio = a.get("exceedance_ratio")
        if not isinstance(ratio, (int, float)):
            errors.append(f"active alert {key} missing numeric exceedance_ratio")
            continue
        exp_band = band_for_ratio(float(ratio))
        if a.get("severity") != exp_band:
            errors.append(f"alert {key} severity {a.get('severity')!r} != deterministic {exp_band!r} for ratio {ratio}")
        if a.get("suggested_response_priority") != PRIORITY.get(exp_band):
            errors.append(f"alert {key} priority {a.get('suggested_response_priority')!r} != mapping {PRIORITY.get(exp_band)!r}")

    # 4. no autonomous action + disclaimer present
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(a.get("reason", "")) for a in alerts])
    for pat in ACTION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"autonomous-action language detected: {m.group(0)!r} (monitor alerts and queues only)")
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "alert_package.json"
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
