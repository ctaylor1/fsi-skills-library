#!/usr/bin/env python3
"""Check CAT arithmetic, no-false-clear states, binding and read-only boundaries."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from insurance_contract import amount, stable_hash, validate_artifact
from calculate_or_transform import DISCLAIMER, PRIORITY, band_for_ratio

ACTION_PATTERNS = [r"\bbound (the |additional )?(coverage|reinsurance|capacity)", r"\bwe (have )?bound\b",
                  r"\bpurchased reinsurance\b", r"\bplaced (the )?reinsurance\b", r"\bmoved capacity\b",
                  r"\b(reduced|increased|adjusted|changed) the limit\b", r"\bcancel(l)?ed the policy\b",
                  r"\bdeclined the (risk|submission)\b", r"\bissued (an )?endorsement\b",
                  r"\b(booked|adjusted) (the )?reserve\b", r"\b(closed|suppressed) the alert\b",
                  r"\bwrote (it )?to (the )?system of record\b", r"\bbind (additional |more )?(coverage|reinsurance|capacity)\b"]


def validate(pack, input_doc=None):
    if not isinstance(pack, dict):
        return ["output must be an object"]
    errors = validate_artifact(pack.get("artifact"), input_doc=input_doc, output=pack)
    sources, alerts = pack.get("sources"), pack.get("alerts")
    if not isinstance(sources, list) or not all(isinstance(s, dict) for s in sources):
        return errors + ["sources freshness report must contain objects"]
    if not isinstance(alerts, list) or not all(isinstance(a, dict) for a in alerts):
        return errors + ["alerts must contain objects"]
    roles = [s.get("source") for s in sources]
    if any(roles.count(role) != 1 for role in ("policy_admin", "event_feed", "cat_model")):
        errors.append("required source freshness not handled")
    unknown_alerts = [a for a in alerts if a.get("status") == "unknown"]
    current_evidence = pack.get("current_evidence", {})
    if not isinstance(current_evidence, dict):
        return errors + ["current_evidence must be an object"]
    current_degraded = (any(s.get("freshness") != "fresh" for s in sources)
                        or bool(pack.get("data_gaps"))
                        or current_evidence.get("completeness") != "complete"
                        or bool(current_evidence.get("unresolved_issues")))
    degraded = current_degraded or bool(pack.get("unresolved_issues")) or bool(unknown_alerts)
    for alert in unknown_alerts:
        if f"prior alert {alert.get('alert_key')} remains unknown" not in pack.get("unresolved_issues", []):
            errors.append("unknown prior alert must remain an unresolved issue")
    if degraded and pack.get("confidence") != "degraded":
        errors.append("freshness not handled: incomplete/stale sources require degraded confidence")
    if degraded and (pack.get("completeness") == "complete" or pack.get("evaluability") == "evaluable"):
        errors.append("incomplete or stale evidence cannot claim complete evaluability")
    policy_source = next((s for s in sources if s.get("source") == "policy_admin"), {})
    for metric in pack.get("evaluated_metrics", []):
        zero_evidence = [e for e in metric.get("evidence", []) if e.get("zero_observed_locations")]
        if zero_evidence and (policy_source.get("freshness") != "fresh"
                              or not policy_source.get("source_ref")
                              or policy_source.get("version") != pack.get("exposure_snapshot_id")
                              or any(e.get("citation") != policy_source.get("source_ref") for e in zero_evidence)):
            errors.append("zero exposure observation requires available fresh exposure-source evidence")
    seen = set()
    for alert in alerts:
        key, state = alert.get("alert_key"), alert.get("status")
        if not isinstance(key, str) or not key:
            errors.append("alert_key required")
        elif key in seen:
            errors.append(f"duplicate alert_key {key}")
        else:
            seen.add(key)
        if state not in ("new", "ongoing", "cleared", "unknown"):
            errors.append(f"invalid alert status {state}")
        if state == "cleared":
            if current_degraded or not isinstance(alert.get("evaluation"), dict):
                errors.append("clearing requires complete current measured evidence")
            else:
                try:
                    row = alert["evaluation"]
                    if row.get("alert_key") != key or band_for_ratio(amount(row["metric"]) / amount(row["threshold"]), pack["approaching_ratio"]) is not None:
                        errors.append("cleared alert is not demonstrably below threshold")
                except (KeyError, ValueError, ArithmeticError):
                    errors.append("cleared alert has invalid measured evidence")
        if state not in ("new", "ongoing"):
            continue
        evidence = alert.get("evidence")
        if not alert.get("queue") or not isinstance(evidence, list) or not evidence or not all(isinstance(e, dict) and e.get("citation") for e in evidence):
            errors.append(f"active alert {key} needs queue and cited evidence")
        try:
            threshold, metric = amount(alert.get("threshold")), amount(alert.get("metric"))
            if threshold <= 0 or metric < 0:
                raise ValueError()
            ratio = metric / threshold
            if amount(alert.get("exceedance_ratio")) != ratio:
                errors.append(f"alert {key} ratio differs from metric/threshold")
            band = band_for_ratio(ratio, pack.get("approaching_ratio"))
            if alert.get("severity") != band or alert.get("suggested_response_priority") != PRIORITY.get(band):
                errors.append(f"alert {key} severity/priority does not match configured ratio")
            if alert.get("breach_type") == "modeled_loss":
                vals = [amount(alert.get("modeled_range", {}).get(k)) for k in ("low", "mid", "high")]
                if not 0 <= vals[0] <= vals[1] <= vals[2] or vals[2] != metric or alert.get("statistic") != "scenario_range" or not alert.get("scenario_set_id"):
                    errors.append(f"alert {key} incompatible modeled range")
        except (ValueError, TypeError, ArithmeticError):
            errors.append(f"alert {key} invalid finite monetary values")
    dd = pack.get("dedup")
    if not isinstance(dd, dict) or any(dd.get(state) != sum(a.get("status") == state for a in alerts) for state in ("new", "ongoing", "cleared", "unknown")):
        errors.append("dedup summary does not reconcile")
    if pack.get("overall_severity") == "None" and (degraded or pack.get("completeness") != "complete"):
        errors.append("unknown/incomplete monitoring cannot report all-clear severity")
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))] + [str(a.get("reason", "")) for a in alerts])
    for pattern in ACTION_PATTERNS:
        match = re.search(pattern, text, re.I)
        if match:
            errors.append(f"autonomous-action language detected: {match.group(0)}")
    if DISCLAIMER.lower() not in str(pack.get("disclaimer", "")).lower():
        errors.append("missing standing disclaimer")
    if input_doc is not None:
        from calculate_or_transform import compute
        try:
            if stable_hash(compute(input_doc)) != stable_hash(pack):
                errors.append("output differs from recomputed CAT snapshot")
        except (TypeError, ValueError) as exc:
            errors.append(f"input cannot be recomputed: {exc}")
    return errors


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/alert_package.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    errors = validate(json.loads(path.read_text() if path else sys.stdin.read()))
    for error in errors:
        print("ERROR", error)
    print(f"output validation: {len(errors)} error(s)")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
