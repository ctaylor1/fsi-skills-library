#!/usr/bin/env python3
"""Bounded, source-linked concern evidence. No determination or account action."""

from __future__ import annotations
import json
import math
import statistics
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from wealth_contract import make_output, source_errors, validate_envelope

SKILL = "senior-investor-protection-screener"
SIGNALS = (
    "unusual_disbursement",
    "new_external_payee",
    "rapid_liquidation",
    "account_or_beneficiary_change",
    "trusted_contact_gap",
    "third_party_influence",
    "capacity_concern_indicators",
    "communication_red_flags",
)
GROUPS = {
    "third_party_influence": ("third_party_present", "new_caregiver_or_poa"),
    "capacity_concern_indicators": ("confusion_observed", "cannot_recall_transaction", "repeated_questions"),
    "communication_red_flags": (
        "unusual_urgency",
        "requests_secrecy",
        "refuses_family_involvement",
        "scam_narrative_flag",
    ),
}
HIGH = {"rapid_liquidation", "third_party_influence", "communication_red_flags"}
PARAMS = {
    "amount_k": (0, 10),
    "min_baseline_n": (2, 10000),
    "new_payee_amount": (0, 1e12),
    "liquidation_amount": (0, 1e12),
    "cluster_days": (1, 365),
    "change_window_days": (1, 3650),
    "tc_stale_days": (1, 3650),
}
DISCLAIMER = "Screening evidence only; not a determination of exploitation or capacity. No hold, report, contact, account action, or clearance has occurred."


def timestamp(value):
    # Compare on an explicit UTC timeline; date-only records start at midnight UTC.
    from datetime import timezone

    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def assess(doc):
    errors = validate_envelope(doc)
    findings = []
    if errors:
        return errors, findings

    def gap(code, message):
        findings.append({"code": code, "message": message})

    def sourced(item, label):
        if not isinstance(item, dict):
            gap("missing-data", f"{label}: missing record")
            return False
        issues = source_errors(item.get("source_ids"), doc)
        for issue in issues:
            gap("source-gap", f"{label}: {issue}")
        return not issues

    for key in ("client", "trusted_contact", "observations", "config", "history_coverage"):
        if doc.get(key) is not None and not isinstance(doc[key], dict):
            errors.append(f"{key} must be an object when supplied")
    if errors:
        return errors, findings
    asof = date.fromisoformat(doc["as_of"])
    lookback = doc.get("lookback_days")
    if not isinstance(lookback, int) or isinstance(lookback, bool) or not 1 <= lookback <= 3650:
        errors.append("lookback_days must be an integer in [1,3650]")
    txns = doc.get("transactions")
    if not isinstance(txns, list) or not txns or len(txns) > 10000:
        errors.append("transactions must contain 1..10000 records")
        txns = []
    seen = set()
    for txn in txns:
        if not isinstance(txn, dict):
            errors.append("transaction must be an object")
            continue
        tid = txn.get("txn_id")
        if not isinstance(tid, str) or not tid or tid in seen:
            errors.append("transaction IDs must be nonempty and unique")
        else:
            seen.add(tid)
        if not number(txn.get("amount")) or txn["amount"] < 0:
            errors.append(f"{tid}: amount must be finite and nonnegative")
        if txn.get("direction") not in ("debit", "credit"):
            errors.append(f"{tid}: direction must be debit or credit")
        if txn.get("lifecycle") not in ("executed", "proposed", "pending", "cancelled"):
            errors.append(f"{tid}: lifecycle must explicitly be executed, proposed, pending or cancelled")
        try:
            ts = timestamp(txn.get("date"))
            if ts.date() > asof:
                gap("future-transaction", f"{tid}: excluded because it occurs after as_of")
        except (ValueError, TypeError):
            errors.append(f"{tid}: invalid transaction date")
        sourced(txn, f"transaction {tid}")
    focal = doc.get("focal_txn_ids")
    if not isinstance(focal, list) or not focal or any(not isinstance(x, str) for x in focal):
        errors.append("focal_txn_ids must be a nonempty list of transaction IDs; window-only mode is unsupported")
    elif len(set(focal)) != len(focal) or any(x not in seen for x in focal):
        errors.append("focal IDs must be unique and resolve to transactions")
    cfg = doc.get("config")
    if sourced(cfg, "configuration"):
        if not cfg.get("version") or not cfg.get("owner"):
            gap("configuration-gap", "configuration needs version and responsible owner")
        if (
            cfg.get("jurisdiction") != doc["engagement"]["jurisdiction"]
            or cfg.get("capacity") != doc["engagement"]["capacity"]
        ):
            gap("configuration-scope", "configuration capacity and jurisdiction must match engagement")
        for key, (lo, hi) in PARAMS.items():
            value = cfg.get(key)
            if value is None:
                gap("configuration-gap", f"missing approved {key}; no default substituted")
            elif (
                not number(value)
                or not lo <= value <= hi
                or (key.endswith("days") or key == "min_baseline_n")
                and not isinstance(value, int)
            ):
                errors.append(f"config.{key} outside permitted bounds or type")
    for key in ("client", "trusted_contact", "history_coverage"):
        sourced(doc.get(key), key)
    client = doc.get("client") or {}
    if client.get("age") is None:
        gap("client-context", "age is unknown; adult and specified-adult context cannot be assumed")
    elif not isinstance(client["age"], int) or isinstance(client["age"], bool) or not 0 <= client["age"] <= 125:
        errors.append("client.age must be an integer in [0,125]")
    impairment = client.get("impairment_flag")
    if impairment is None:
        gap("client-context", "human-recorded impairment applicability is unknown")
    elif not isinstance(impairment, bool):
        errors.append("client.impairment_flag must be boolean when known")
    tc = doc.get("trusted_contact") or {}
    if tc.get("on_file") not in (True, False) or not isinstance(tc.get("on_file"), bool):
        gap("trusted-contact", "trusted-contact record status is unknown")
    elif tc["on_file"]:
        try:
            if date.fromisoformat(tc.get("last_confirmed", "")) > asof:
                errors.append("trusted_contact.last_confirmed cannot be in the future")
        except (ValueError, TypeError):
            gap("trusted-contact", "last confirmation date is unknown")
    elif tc.get("collection_status") not in ("declined", "requested", "not-requested"):
        gap("trusted-contact", "missing contact requires documented collection status, not an inferred rule violation")
    obs = doc.get("observations")
    if sourced(obs, "observations"):
        if not obs.get("observed_by"):
            gap("observations", "trained-human observer is not recorded")
        for flags in GROUPS.values():
            for flag in flags:
                if obs.get(flag) is None:
                    gap("observations", f"{flag}: not assessed")
                elif not isinstance(obs[flag], bool):
                    errors.append(f"observations.{flag} must be boolean or null")
    changes = doc.get("recent_changes")
    if not isinstance(changes, list):
        gap("changes", "recent changes not supplied; absence is not a negative finding")
    elif len(changes) > 1000:
        errors.append("recent_changes exceeds 1000 records")
    else:
        for change in changes:
            if not isinstance(change, dict):
                errors.append("change must be an object")
                continue
            sourced(change, "change")
            try:
                if date.fromisoformat(change.get("date", "")) > asof:
                    errors.append("change date cannot be in the future")
            except (ValueError, TypeError):
                errors.append("change date must be ISO date")
            if change.get("type") not in ("beneficiary", "registration", "address"):
                errors.append("unsupported change type")
    if errors:
        return errors, findings
    start = asof - timedelta(days=lookback - 1)
    for txn in txns:
        if txn["txn_id"] in focal and not start <= timestamp(txn["date"]).date() <= asof:
            errors.append("focal activity must be inside the declared as_of/lookback window")
        if txn["txn_id"] in focal and txn["lifecycle"] == "cancelled":
            errors.append("cancelled activity may be supporting history but cannot be an active focal request")
    coverage = doc.get("history_coverage") or {}
    try:
        if date.fromisoformat(coverage.get("start", "")) > start or date.fromisoformat(coverage.get("end", "")) < asof:
            gap("history-coverage", "history does not cover the declared lookback through as_of")
    except (ValueError, TypeError):
        gap("history-coverage", "history coverage dates are missing or invalid")
    return errors, findings


def disposition(fired, unknown):
    concerns = [name for name in fired if name != "trusted_contact_gap"]
    if len(concerns) >= 3 or HIGH.intersection(concerns):
        return "Escalate"
    if concerns:
        return "Review"
    return "Insufficient evidence" if unknown else "Monitor"


def compute(doc):
    errors, findings = assess(doc)
    if errors:
        raise ValueError("; ".join(errors))
    asof = date.fromisoformat(doc["as_of"])
    start = asof - timedelta(days=doc["lookback_days"] - 1)
    focal = [t for t in doc["transactions"] if t["txn_id"] in doc["focal_txn_ids"]]
    cutoff = min(timestamp(t["date"]) for t in focal)
    history = [
        t for t in doc["transactions"] if start <= timestamp(t["date"]).date() <= asof and t["lifecycle"] == "executed"
    ]
    baseline = [t for t in history if t["txn_id"] not in doc["focal_txn_ids"] and timestamp(t["date"]) < cutoff]
    cfg = doc.get("config") or {}
    config_ok = all(k in cfg for k in PARAMS) and not any(
        f["code"].startswith("configuration") or f["code"] == "source-gap" and f["message"].startswith("configuration:")
        for f in findings
    )

    def valid(item):
        return isinstance(item, dict) and not source_errors(item.get("source_ids"), doc)

    txn_ok = all(valid(t) for t in history + focal)
    coverage_ok = valid(doc.get("history_coverage")) and not any(f["code"] == "history-coverage" for f in findings)
    signals = []

    def add(name, fired, reason, evidence, basis=None):
        signals.append(
            {
                "signal": name,
                "fired": fired,
                "assessment": "not-evaluable" if fired is None else "observed" if fired else "assessed-absent",
                "reason": reason,
                "source_ids": sorted(
                    {
                        sid
                        for e in evidence
                        if isinstance(e.get("source_ids"), list)
                        for sid in e["source_ids"]
                        if isinstance(sid, str)
                    }
                ),
                "evidence": evidence,
                "basis": basis or {},
            }
        )

    debits = [t for t in baseline if t["direction"] == "debit"]
    if config_ok and txn_ok and coverage_ok and len(debits) >= cfg["min_baseline_n"]:
        amounts = [t["amount"] for t in debits]
        mean, stdev = statistics.mean(amounts), statistics.pstdev(amounts)
        threshold = mean + cfg["amount_k"] * stdev
        hits = [t for t in focal if t["direction"] == "debit" and t["amount"] > threshold]
        add(
            SIGNALS[0],
            bool(hits),
            "Focal requested/executed amount compared with bounded executed pre-focal debit history; not evidence that a request executed",
            focal + debits,
            {"n": len(debits), "mean": mean, "stdev": stdev, "threshold": threshold},
        )
    else:
        add(SIGNALS[0], None, "Insufficient sourced baseline or approved configuration", [])
    if config_ok and txn_ok and coverage_ok and all(t.get("counterparty") for t in baseline + focal):
        known = {t["counterparty"].casefold() for t in baseline}
        hits = [
            t
            for t in focal
            if t["direction"] == "debit"
            and t["amount"] >= cfg["new_payee_amount"]
            and t["counterparty"].casefold() not in known
        ]
        add(
            SIGNALS[1],
            bool(hits),
            "Payee first seen within supplied pre-focal lookback; not a lifetime-history claim",
            focal + baseline,
        )
    else:
        add(SIGNALS[1], None, "Payee history, coverage, or configuration incomplete", [])
    if config_ok and txn_ok and coverage_ok and doc["lookback_days"] >= cfg["cluster_days"]:
        rows = [
            t
            for t in history
            if t["direction"] == "debit"
            and timestamp(t["date"]).date() >= asof - timedelta(days=cfg["cluster_days"] - 1)
        ]
        total = sum(t["amount"] for t in rows)
        add(
            SIGNALS[2],
            total >= cfg["liquidation_amount"],
            "Executed debit outflow only; proposed, pending and cancelled activity excluded; not proof of asset liquidation",
            rows,
            {"total_out": total, "threshold": cfg["liquidation_amount"], "included_lifecycle": "executed"},
        )
    else:
        add(SIGNALS[2], None, "Cluster coverage or approved configuration incomplete", [])
    changes = doc.get("recent_changes")
    if config_ok and txn_ok and isinstance(changes, list) and all(valid(c) for c in changes):
        recent = [c for c in changes if (asof - date.fromisoformat(c["date"])).days < cfg["change_window_days"]]
        add(
            SIGNALS[3],
            bool(recent) and any(t["direction"] == "debit" for t in focal),
            "Recent sourced account changes coincident with a requested or executed focal debit; see lifecycle",
            recent + focal,
        )
    else:
        add(SIGNALS[3], None, "Account change evidence or configuration incomplete", [])
    tc = doc.get("trusted_contact") or {}
    tc_ok = config_ok and valid(tc) and not any(f["code"] == "trusted-contact" for f in findings)
    if tc_ok:
        gap = not tc["on_file"] or (asof - date.fromisoformat(tc["last_confirmed"])).days > cfg["tc_stale_days"]
        add(
            SIGNALS[4],
            gap,
            "Contact collection/recency observation; not a rule-breach or exploitation determination",
            [tc],
        )
    else:
        add(SIGNALS[4], None, "Contact collection/recency is unknown", [])
    obs = doc.get("observations") or {}
    for name, flags in GROUPS.items():
        values = [obs.get(k) for k in flags]
        if valid(obs) and obs.get("observed_by"):
            state = True if True in values else False if all(v is False for v in values) else None
            add(
                name,
                state,
                "Human observations only; unassessed flags remain unknown",
                [obs],
                {"flags": {k: obs.get(k) for k in flags}},
            )
        else:
            add(name, None, "Structured trained-human observations unavailable", [])
    unknown = [s["signal"] for s in signals if s["fired"] is None]
    for name in unknown:
        findings.append({"code": "not-evaluable", "message": f"{name}: evidence is incomplete"})
    fired = [s["signal"] for s in signals if s["fired"] is True]
    client = doc.get("client") or {}
    age = client.get("age")
    adult = age >= 18 if age is not None else None
    specified = None
    if age is not None and valid(client):
        if age >= 65:
            specified = True
        elif age < 18:
            specified = False
            findings.append(
                {
                    "code": "applicability",
                    "message": "Minor: route safeguarding concerns to the authorized specialist; do not infer specified-adult applicability.",
                }
            )
        elif isinstance(client.get("impairment_flag"), bool):
            specified = client["impairment_flag"]
    result = {
        "screening_context": {
            "adult": adult,
            "specified_adult_context": specified,
            "applicability_note": "FINRA context does not establish legal applicability; reviewer applies engagement and jurisdiction policy. Age alone is not a concern signal.",
        },
        "window": {
            "start": start.isoformat(),
            "as_of": doc["as_of"],
            "baseline_precedes": cutoff.isoformat(),
            "baseline_count": len(baseline),
        },
        "config_version": cfg.get("version"),
        "focal_activity": [
            {key: txn.get(key) for key in ("txn_id", "date", "amount", "direction", "lifecycle", "source_ids")}
            for txn in focal
        ],
        "signals": signals,
        "fired_signals": fired,
        "not_evaluable": unknown,
        "suggested_disposition": disposition(fired, unknown or findings),
        "benign_prompts": [
            "Documented planned purchase or withdrawal",
            "Client-directed gifting or assistance",
            "Communication/accessibility preference",
        ]
        if fired
        else [],
        "disclaimer": DISCLAIMER,
    }
    out = make_output(SKILL, doc, result, findings)
    out["input_snapshot"] = doc
    return out


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/case_example.json"
        if "--selftest" in argv
        else Path(argv[0])
        if argv
        else None
    )
    try:
        doc = json.loads(path.read_text() if path else sys.stdin.read())
        print(json.dumps(compute(doc), indent=2, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
