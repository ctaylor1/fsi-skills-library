#!/usr/bin/env python3
"""Deterministic, explainable senior-investor concern-signal computation.

Reads a case file (see validate_input.py), computes configured concern signals across
exploitation, unusual-disbursement, account/beneficiary-change, trusted-contact,
third-party-influence, capacity-indicator, and communication-red-flag categories, attaches
cited evidence to each fired signal, and maps the fired set to a suggested review
DISPOSITION band. Emits a machine-readable core the SKILL wraps in a plain-language pack.

IMPORTANT: This produces explainable *signals and a triage suggestion* only. It NEVER
determines that financial exploitation or diminished capacity has occurred, places a
temporary hold, files a report, contacts a trusted contact, or closes a case. The
disposition mapping is deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py case.json     # prints screening JSON to stdout
  python calculate_or_transform.py --selftest    # runs bundled-fixture invariant checks
"""
from __future__ import annotations
import json, statistics, sys
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_CONFIG = {
    "specified_adult_age": 65, "amount_k": 3.0, "min_baseline_n": 10,
    "new_payee_amount": 5000.0, "liquidation_amount": 25000.0, "cluster_days": 30,
    "change_window_days": 90, "tc_stale_days": 365,
}
DISCLAIMER = ("Screening evidence only; not a determination of financial exploitation or "
              "capacity, and no hold, report, or account action has been taken.")
# Signals that, if fired, force the Escalate band regardless of count.
HIGH_SEVERITY = {"rapid_liquidation", "third_party_influence", "communication_red_flags"}


def _parse_dt(s: str) -> datetime:
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.strptime(s[:10], "%Y-%m-%d")


def _cite(t: dict) -> str:
    return f"txns:{t.get('source_ref','?')}@{t.get('date','?')}"


def expected_disposition(fired: list[str]) -> str:
    """Deterministic mapping documented in references/domain-rules.md."""
    if len(fired) >= 3 or (HIGH_SEVERITY & set(fired)):
        return "Escalate"
    return "Review" if fired else "Monitor"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    txns = sorted(doc["transactions"], key=lambda t: str(t["date"]))
    focal_ids = set(doc["focal_txn_ids"])
    focal = [t for t in txns if t["txn_id"] in focal_ids]
    baseline = [t for t in txns if t["txn_id"] not in focal_ids]
    client = doc.get("client") or {}
    tc = doc.get("trusted_contact")
    obs = doc.get("observations") or {}
    changes = doc.get("recent_changes") or []
    as_of = _parse_dt(doc["as_of"])

    def flag(name):
        return bool(obs.get(name))

    signals, not_evaluable = [], []

    def add(name, fired, reason, evidence, basis, contribution):
        signals.append({"signal": name, "fired": bool(fired), "reason": reason,
                        "evidence": evidence, "basis": basis, "contribution": contribution})

    # Context (NOT a concern signal; does not affect disposition): specified-adult status.
    age = client.get("age")
    specified_adult = (isinstance(age, (int, float)) and age >= cfg["specified_adult_age"]) or bool(client.get("impairment_flag"))

    # 1. unusual_disbursement — focal debit far above the client's own baseline
    base_debits = [float(t["amount"]) for t in baseline if t["direction"] == "debit"]
    if len(base_debits) >= cfg["min_baseline_n"]:
        mean = statistics.mean(base_debits)
        stdev = statistics.pstdev(base_debits) or 0.0
        thr = mean + cfg["amount_k"] * stdev
        hits = [t for t in focal if t["direction"] == "debit" and float(t["amount"]) > thr]
        add("unusual_disbursement", bool(hits),
            f"focal disbursement(s) exceed baseline mean {mean:.2f} + {cfg['amount_k']}*stdev {stdev:.2f} = {thr:.2f}"
            if hits else f"no focal disbursement exceeds {thr:.2f}",
            [{"txn_id": t["txn_id"], "amount": t["amount"], "citation": _cite(t)} for t in hits],
            {"mean": round(mean, 2), "stdev": round(stdev, 2), "threshold": round(thr, 2), "n": len(base_debits)},
            len(hits))
    else:
        not_evaluable.append({"signal": "unusual_disbursement", "why": f"baseline debits {len(base_debits)} < {cfg['min_baseline_n']}"})

    # 2. new_external_payee — first-seen counterparty receiving a high-value disbursement
    prior_payees = {str(t.get("counterparty", "")).lower() for t in baseline if t.get("counterparty")}
    ncp = [t for t in focal if t["direction"] == "debit" and t.get("counterparty")
           and str(t["counterparty"]).lower() not in prior_payees
           and float(t["amount"]) >= cfg["new_payee_amount"]]
    add("new_external_payee", bool(ncp),
        f"first-seen payee with disbursement >= {cfg['new_payee_amount']}" if ncp else "no new high-value external payee",
        [{"txn_id": t["txn_id"], "counterparty": t["counterparty"], "amount": t["amount"], "citation": _cite(t)} for t in ncp],
        {"new_payee_amount": cfg["new_payee_amount"]}, len(ncp))

    # 3. rapid_liquidation — large outflow within the cluster window (HIGH severity)
    win_start = as_of - timedelta(days=cfg["cluster_days"])
    recent_debits = [t for t in txns if t["direction"] == "debit" and win_start <= _parse_dt(t["date"]) <= as_of]
    total_out = sum(float(t["amount"]) for t in recent_debits)
    fired_rl = total_out >= cfg["liquidation_amount"]
    add("rapid_liquidation", fired_rl,
        f"debit outflow {total_out:.2f} within {cfg['cluster_days']}d >= {cfg['liquidation_amount']}"
        if fired_rl else f"debit outflow {total_out:.2f} within {cfg['cluster_days']}d (below {cfg['liquidation_amount']})",
        [{"txn_id": t["txn_id"], "amount": t["amount"], "citation": _cite(t)} for t in recent_debits] if fired_rl else [],
        {"window_days": cfg["cluster_days"], "total_out": round(total_out, 2), "threshold": cfg["liquidation_amount"]},
        1 if fired_rl else 0)

    # 4. account_or_beneficiary_change — recent registration/beneficiary/address change with a disbursement present
    recent_changes = [c for c in changes if c.get("date") and win_change(c, as_of, cfg["change_window_days"])]
    fired_chg = bool(recent_changes) and bool(focal)
    add("account_or_beneficiary_change", fired_chg,
        f"{len(recent_changes)} account/beneficiary change(s) within {cfg['change_window_days']}d coincident with a disbursement"
        if fired_chg else "no recent account/beneficiary change coincident with a disbursement",
        ([{"change_type": c.get("type"), "date": c.get("date"), "citation": f"crm:{c.get('source_ref','?')}@{c.get('date','?')}"} for c in recent_changes]
         + [{"txn_id": t["txn_id"], "amount": t["amount"], "citation": _cite(t)} for t in focal]) if fired_chg else [],
        {"change_window_days": cfg["change_window_days"], "changes": len(recent_changes)},
        len(recent_changes) if fired_chg else 0)

    # 5. trusted_contact_gap — Rule 4512: no trusted contact on file, or confirmation is stale
    if tc is None:
        gap, reason = True, "no trusted_contact block on file"
        ev_basis = {"on_file": False}
    elif not tc.get("on_file"):
        gap, reason = True, "no trusted contact person on file"
        ev_basis = {"on_file": False}
    else:
        lc = tc.get("last_confirmed")
        if lc and (as_of - _parse_dt(lc)).days > cfg["tc_stale_days"]:
            gap, reason = True, f"trusted contact last confirmed {(as_of - _parse_dt(lc)).days}d ago (> {cfg['tc_stale_days']})"
            ev_basis = {"on_file": True, "last_confirmed": lc, "stale": True}
        else:
            gap, reason = False, "trusted contact on file and confirmation current"
            ev_basis = {"on_file": True, "last_confirmed": lc, "stale": False}
    add("trusted_contact_gap", gap, reason,
        [{"trusted_contact": ev_basis, "citation": f"crm:trusted_contact@{doc['as_of']}"}] if gap else [],
        ev_basis, 1 if gap else 0)

    # 6. third_party_influence — structural third-party presence (HIGH severity)
    tp = flag("third_party_present") or flag("new_caregiver_or_poa")
    tp_flags = [f for f in ("third_party_present", "new_caregiver_or_poa") if flag(f)]
    add("third_party_influence", tp,
        f"observed third-party indicators: {', '.join(tp_flags)}" if tp else "no third-party indicators observed",
        [{"indicator": f, "citation": f"crm:{obs.get('observation_ref','?')}"} for f in tp_flags] if tp else [],
        {"indicators": tp_flags, "observed_by": obs.get("observed_by")}, len(tp_flags))

    # 7. capacity_concern_indicators — observed indicators only, NOT a diagnosis
    cap_flags = [f for f in ("confusion_observed", "cannot_recall_transaction", "repeated_questions") if flag(f)]
    add("capacity_concern_indicators", bool(cap_flags),
        f"observed indicators (not a clinical determination): {', '.join(cap_flags)}" if cap_flags
        else "no capacity indicators observed",
        [{"indicator": f, "citation": f"crm:{obs.get('observation_ref','?')}"} for f in cap_flags] if cap_flags else [],
        {"indicators": cap_flags, "note": "observed indicators, not a diagnosis"}, len(cap_flags))

    # 8. communication_red_flags — pressure / secrecy / isolation / scam markers (HIGH severity)
    comm_flags = [f for f in ("unusual_urgency", "requests_secrecy", "refuses_family_involvement", "scam_narrative_flag") if flag(f)]
    add("communication_red_flags", bool(comm_flags),
        f"observed communication red flags: {', '.join(comm_flags)}" if comm_flags else "no communication red flags observed",
        [{"indicator": f, "citation": f"crm:{obs.get('observation_ref','?')}"} for f in comm_flags] if comm_flags else [],
        {"indicators": comm_flags, "observed_by": obs.get("observed_by")}, len(comm_flags))

    fired_names = [s["signal"] for s in signals if s["fired"]]
    disposition = expected_disposition(fired_names)

    benign = []
    if fired_names:
        benign = [
            "a legitimate large purchase (home, vehicle, medical/long-term care)",
            "planned gifting to family or charity",
            "estate, tax, or RMD/Roth-conversion planning",
            "a genuine new professional or caregiver engaged by the client",
            "a relocation to assisted living",
            "a real, client-directed personal relationship or new payee",
        ]

    return {
        "screening_id": f"sips-{str(doc['client_id']).replace('*','')}-{doc['as_of']}-0001",
        "client_id": doc["client_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "window": {"lookback_days": doc.get("lookback_days"), "as_of": doc["as_of"]},
        "context": {"specified_adult": specified_adult, "specified_adult_age": cfg["specified_adult_age"]},
        "signals": signals,
        "fired_signals": fired_names,
        "not_evaluable": not_evaluable,
        "suggested_disposition": disposition,
        "benign_prompts": benign,
        "disclaimer": DISCLAIMER,
    }


def win_change(change: dict, as_of: datetime, window_days: int) -> bool:
    try:
        return 0 <= (as_of - _parse_dt(change["date"])).days <= window_days
    except (KeyError, ValueError):
        return False


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    pack = compute(doc)
    errors = []
    disp = pack["suggested_disposition"]
    print(f"suggested_disposition: {disp}")
    print(f"fired_signals: {', '.join(pack['fired_signals'])}")
    # Invariant 1: disposition ties out to the deterministic mapping.
    if disp != expected_disposition(pack["fired_signals"]):
        errors.append("disposition does not match deterministic mapping")
    # Invariant 2: bundled fixture is a textbook exploitation cluster -> Escalate.
    if disp != "Escalate":
        errors.append(f"expected Escalate for bundled fixture, got {disp}")
    # Invariant 3: every fired signal carries cited evidence.
    for s in pack["signals"]:
        if s["fired"]:
            if not s["evidence"]:
                errors.append(f"fired signal {s['signal']} has no evidence")
            for row in s["evidence"]:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired signal {s['signal']} evidence row missing citation")
    # Invariant 4: never emits a determination/closure — only signals + a suggestion.
    if "determination" in json.dumps(pack).lower() and "not a determination" not in pack["disclaimer"].lower():
        errors.append("output appears to assert a determination")
    for e in errors:
        print("ERROR", e)
    print(f"calculate self-check: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
