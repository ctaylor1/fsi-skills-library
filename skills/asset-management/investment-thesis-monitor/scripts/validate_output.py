#!/usr/bin/env python3
"""Deterministic output validation for investment-thesis-monitor.

Validates the final monitor-run pack (calculate_or_transform core + a narrative) before it
is queued/delivered. Enforces the scheduled, read-only, ALERT-ONLY posture. Checks:
  1. Every fired signal has >= 1 cited evidence row, and every evidence row is FRESH.
  2. Escalation band equals the deterministic mapping from each alert's fired-challenging set.
  3. FRESHNESS handled: each alert carries a data_freshness block; no fired signal is stale.
  4. DEDUPLICATION applied: each alert has a boolean 'duplicate'; queue.new/deduplicated
     partition the alert keys, duplicates route to 'deduplicated', new to 'new', and every
     key appears in by_escalation under its own band.
  5. NO AUTONOMOUS ACTION: 'action_taken' == 'none' and no trade/rebalance/exit/close-thesis
     or investment-advice language in the narrative or signal reasons.
  6. Standing disclaimer present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"stop_breach", "catalyst_missed"}
DISCLAIMER = ("Monitoring alert only; not investment advice or a trading decision. "
              "No position or thesis action has been taken.")
# Autonomous-action / advice assertions a read-only alert-only monitor must never make:
ACTION_PATTERNS = [
    r"\bsell (the )?(position|stock|shares|holding)\b", r"\bbuy (more|the stock|shares)\b",
    r"\bexit (the )?(position|thesis|trade)\b", r"\btrim (the )?position\b",
    r"\badd to (the )?position\b", r"\bincrease (the )?(position|weight|holding)\b",
    r"\breduce (the )?(position|weight|exposure)\b", r"\bcut (the )?position\b",
    r"\bclose (the )?(position|thesis)\b", r"\bretire (the )?thesis\b",
    r"\bliquidat", r"\brebalanc", r"\bplace (a|an) (trade|order)\b", r"\bexecute (a|the) (trade|order)\b",
    r"\bhedge (the )?(position|book)\b", r"\bwe (should|recommend) (buy|sell|trim|add|exit)\b",
    r"\byou should (buy|sell|trim|add|exit)\b", r"\bwe are (buying|selling|trimming|exiting)\b",
]


def _expected_escalation(fired_challenging, fired_confirming):
    if len(fired_challenging) >= 3 or (ESCALATORS & set(fired_challenging)):
        return "Elevated"
    if fired_challenging:
        return "Review"
    if fired_confirming:
        return "Informational"
    return None


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    alerts = pack.get("alerts") or []
    queue = pack.get("queue") or {}

    if not pack.get("monitor_run_id"):
        errors.append("missing durable monitor_run_id")

    # 5a. no autonomous action posture flag
    if str(pack.get("action_taken", "")).lower() != "none":
        errors.append(f"action_taken must be 'none' for a read-only monitor, got {pack.get('action_taken')!r}")

    all_keys = []
    for a in alerts:
        key = a.get("alert_key")
        all_keys.append(key)
        fired = [s for s in (a.get("signals") or []) if s.get("fired")]
        fired_ch = [s["signal"] for s in fired if s.get("side") == "challenging"]
        fired_cf = [s["signal"] for s in fired if s.get("side") == "confirming"]

        # 1. evidence + citation + freshness on every fired signal
        for s in fired:
            ev = s.get("evidence") or []
            if not ev:
                errors.append(f"alert {key}: fired signal {s['signal']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"alert {key}: fired signal {s['signal']} evidence row missing citation")

        # 3. freshness block + no stale fired signal
        df = a.get("data_freshness")
        if not isinstance(df, dict) or "is_stale" not in df:
            errors.append(f"alert {key}: missing data_freshness block")
        else:
            if df.get("is_stale") and fired:
                errors.append(f"alert {key}: fired on stale data (is_stale=true) — freshness gate violated")
            age = df.get("stalest_fresh_evidence_age_days")
            mx = df.get("max_staleness_days")
            if fired and isinstance(age, (int, float)) and isinstance(mx, (int, float)) and age > mx:
                errors.append(f"alert {key}: fired evidence age {age}d exceeds staleness gate {mx}d")

        # 2. deterministic escalation
        exp = _expected_escalation(fired_ch, fired_cf)
        if a.get("escalation") != exp:
            errors.append(f"alert {key}: escalation {a.get('escalation')!r} != deterministic {exp!r} "
                          f"for challenging={fired_ch} confirming={fired_cf}")

        # 4a. dedup flag present + routing
        if not isinstance(a.get("duplicate"), bool):
            errors.append(f"alert {key}: missing boolean 'duplicate' (dedup not applied)")
        else:
            in_new = key in (queue.get("new") or [])
            in_dedup = key in (queue.get("deduplicated") or [])
            if a["duplicate"] and not in_dedup:
                errors.append(f"alert {key}: duplicate alert not routed to queue.deduplicated")
            if (not a["duplicate"]) and not in_new:
                errors.append(f"alert {key}: new alert not routed to queue.new")
        band = a.get("escalation")
        if band and key not in (queue.get("by_escalation", {}).get(band) or []):
            errors.append(f"alert {key}: not present in queue.by_escalation[{band!r}]")

    # 4b. queue partitions the alert keys exactly
    partition = set(queue.get("new") or []) | set(queue.get("deduplicated") or [])
    if partition != set(all_keys):
        errors.append(f"queue.new|deduplicated {sorted(partition)} != alert keys {sorted(set(all_keys))}")
    if set(queue.get("new") or []) & set(queue.get("deduplicated") or []):
        errors.append("queue.new and queue.deduplicated overlap (an alert cannot be both)")

    # 5b. no autonomous-action / advice language in free text
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("reason", "")) for a in alerts for s in (a.get("signals") or [])])
    for pat in ACTION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"autonomous-action/advice language detected: {m.group(0)!r} "
                          "(monitor alerts only; the human PM/analyst decides and acts)")

    # 6. disclaimer
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
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
