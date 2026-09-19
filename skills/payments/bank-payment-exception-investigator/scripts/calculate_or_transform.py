#!/usr/bin/env python3
"""Deterministic payment-exception investigation builder for bank-payment-exception-investigator.

For each ISO 20022 payment exception (pacs/camt messages) this:
  1. Emits a supplied case_id or an explicitly local-only PEI reference.
  2. Builds a cited message chronology (sorted by timestamp) and traces the last status.
  3. Resolves parties and amounts into an evidence bundle with citations on every item.
  4. Computes a documented priority band from amount, scheme criticality, aging, and severity.
  5. Derives a disposition RECOMMENDATION only (repair / return / honor-recall / reject-recall /
     request-info / route-specialist / needs-data / possible-duplicate).

It NEVER moves funds, repairs a payment, closes a case, files, or makes a determination. A
fraud indicator or an explicit sanctions hold forces a specialist route; a match to an
open case links (never merges); missing identifiers/messages yield needs-data (no guessing).

Usage: python calculate_or_transform.py exceptions.json | --selftest
Prints the investigation JSON (evidence bundles + recommendations) to stdout.
"""
from __future__ import annotations
import copy, json, sys
from datetime import timezone
from payment_contract import money, stable_hash, timestamp
from datetime import date
from pathlib import Path

STANDING_NOTE = ("Investigation evidence and recommendations only; no case has been closed, "
                 "no determination made, no payment repaired, returned, or released, and no "
                 "filing performed. Every next step requires human adjudication and approval.")

# ISO 20022 external reason-code set (default; overridable via doc['reason_code_config']).
DEFAULT_REASON_CODES = {
    "AC01": {"name": "IncorrectAccountNumber", "family": "account", "action": "recommend-repair-and-resubmit"},
    "AC04": {"name": "ClosedAccountNumber", "family": "account", "action": "recommend-return-to-originator"},
    "AC06": {"name": "BlockedAccount", "family": "account", "action": "recommend-return-to-originator"},
    "AM04": {"name": "InsufficientFunds", "family": "funds", "action": "recommend-return-to-originator"},
    "BE01": {"name": "InconsistentWithEndCustomer", "family": "party", "action": "recommend-request-information"},
    "RC01": {"name": "BankIdentifierIncorrect", "family": "agent", "action": "recommend-repair-and-resubmit"},
    "RR04": {"name": "RegulatoryReason", "family": "regulatory", "action": "route-specialist"},
    "DUPL": {"name": "DuplicatePayment", "family": "duplicate", "action": "recommend-honor-recall"},
    "TECH": {"name": "TechnicalProblem", "family": "recall", "action": "recommend-honor-recall"},
    "FRAD": {"name": "FraudulentOrigin", "family": "fraud", "action": "route-specialist"},
    "CUST": {"name": "RequestedByCustomer", "family": "recall", "action": "recommend-reject-recall"},
    "FOCR": {"name": "FollowingCancellationRequest", "family": "recall", "action": "recommend-request-information"},
    "MS03": {"name": "NotSpecifiedReason", "family": "unknown", "action": "recommend-request-information"},
}

DEFAULT_PRIORITY = {
    "amount_currency": "USD",
    "amount": [(1000000, 3), (100000, 2), (10000, 1)],
    "scheme_critical": {"Fedwire": 2, "CHIPS": 2, "T2": 2, "RTP": 2, "FedNow": 2, "FPS": 2,
                        "SEPA": 1, "ACH": 1, "BACS": 1},
    "aging": [(5, 2), (2, 1)],
    "severity": {"recall_requested": 2, "returned": 2, "rejected": 1, "nondelivery": 1, "duplicate": 1},
    "risk_override": 3, "p1_min": 6, "p2_min": 3,
}

ROUTE_SANCTIONS = "sanctions-match-adjudicator"
ROUTE_FRAUD = "payment-fraud-and-scam-investigator"


def _parse_day(ts):
    try:
        return date.fromisoformat(str(ts)[:10])
    except (ValueError, TypeError):
        return None


def _sorted_messages(msgs):
    return sorted(msgs or [], key=lambda m: timestamp(m["timestamp"]).astimezone(timezone.utc))


def _chronology(msgs):
    events = []
    for i, m in enumerate(_sorted_messages(msgs), start=1):
        events.append({
            "seq": i,
            "timestamp": m.get("timestamp"),
            "msg_type": m.get("msg_type"),
            "direction": m.get("direction"),
            "status": m.get("status"),
            "reason_code": m.get("reason_code"),
            "cite": m.get("msg_ref"),
        })
    return events


def _last_status(msgs, codes):
    s = _sorted_messages(msgs)
    if not s:
        return None
    status_messages = [m for m in s if m.get("status") or m.get("reason_code")]
    if not status_messages:
        return None
    last = status_messages[-1]
    rc = last.get("reason_code")
    meaning = codes.get(rc, {}).get("name") if rc else None
    return {"status": last.get("status"), "reason_code": rc, "reason_name": meaning,
            "reason_source": last.get("reason_source"), "cite": last.get("msg_ref")}


def _has_identifier(ex):
    ids = ex.get("identifiers") or {}
    return any(ids.get(k) for k in ("uetr", "instruction_id", "end_to_end_id", "transaction_id"))


def _priority(ex, as_of, cfg):
    score, why = 0, []
    amount = ex.get("amount") or {}
    amt = money(amount["value"]) if amount.get("value") is not None else None
    if amt is not None and amount.get("currency") == cfg["amount_currency"]:
        for thr, pts in cfg["amount"]:
            if amt >= money(thr):
                score += pts; why.append(f"{cfg['amount_currency']} amount>={thr} +{pts}"); break
    else:
        why.append("amount contribution not evaluated: missing amount or threshold currency mismatch")
    sch = cfg["scheme_critical"].get(ex.get("scheme"), 0)
    if sch:
        score += sch; why.append(f"scheme {ex.get('scheme')} +{sch}")
    days = _msg_age_days(ex, as_of)
    if days is not None:
        for thr, pts in cfg["aging"]:
            if days >= thr:
                score += pts; why.append(f"aging {days}d +{pts}"); break
    sev = cfg["severity"].get(ex.get("exception_type"), 0)
    if sev:
        score += sev; why.append(f"severity {ex.get('exception_type')} +{sev}")
    risk = bool(ex.get("fraud_indicator") or ex.get("sanctions_hold"))
    if risk:
        score += cfg["risk_override"]; why.append(f"fraud/sanctions signal +{cfg['risk_override']}")
    band = "P1 (Critical)" if (score >= cfg["p1_min"] or risk) \
        else "P2 (Standard)" if score >= cfg["p2_min"] else "P3 (Low)"
    return score, band, why, risk


def _msg_age_days(ex, as_of):
    days_ref = _parse_day(as_of)
    first = None
    for m in _sorted_messages(ex.get("messages")):
        d = _parse_day(m.get("timestamp"))
        if d:
            first = d; break
    if not (days_ref and first):
        return None
    return (days_ref - first).days


def _dup_parent(ex, open_cases):
    ids = ex.get("identifiers") or {}
    for c in open_cases or []:
        if c.get("uetr") and c.get("uetr") == ids.get("uetr"):
            return c
        if c.get("instruction_id") and c.get("instruction_id") == ids.get("instruction_id"):
            return c
    return None


def _eligible(ex, operation):
    evidence = ex.get("disposition_evidence") or {}
    required = ("source_ref", "scheme_rule_ref", "rule_profile_version", "assessment_owner", "assessed_at")
    return (all(evidence.get(key) for key in required)
            and evidence.get("scheme") == ex.get("scheme")
            and evidence.get("operation") == operation
            and evidence.get("window_valid") is True
            and evidence.get("eligibility") == "eligible"
            and evidence.get("finality_state") in {"not_settled", "settled"})


def _recall_disposition(ex, last, codes):
    # A recall is a request, not evidence of recovery. Supplied flags alone cannot decide it.
    if not _eligible(ex, "recall"):
        return "recommend-request-information"
    evidence = ex["disposition_evidence"]
    if ex.get("funds_available") is not True:
        return "recommend-request-information"
    consent = evidence.get("consent_requirement")
    if consent not in {"required", "not_required"} or (consent == "required" and ex.get("beneficiary_consent") is not True):
        return "recommend-request-information"
    rc = (last or {}).get("reason_code")
    if rc == "DUPL" and not ex.get("duplicate_of"):
        return "recommend-request-information"
    return "recommend-honor-recall" if rc in {"DUPL", "TECH", "CUST"} else "recommend-request-information"


def investigate_one(ex, doc, codes, cfg):
    eid = ex.get("exception_id")
    case_id = ex.get("case_id") or f"PEI-{eid}"
    msgs = ex.get("messages") or []
    chron = _chronology(msgs)
    last = _last_status(msgs, codes)
    score, band, why, risk = _priority(ex, doc.get("as_of"), cfg)

    citations = [c["cite"] for c in chron if c.get("cite")]
    if ex.get("case_ref"):
        citations = [ex["case_ref"]] + citations

    rec = {
        "exception_id": eid, "case_id": case_id,
        "case_identity_status": "supplied" if ex.get("case_id") else "local-only-not-persisted",
        "lead_owner": ex.get("lead_owner") or "unassigned",
        "owner_status": "supplied" if ex.get("lead_owner") else "assignment-required",
        "evidence_status": "supplied-not-authenticated",
        "source_hash": stable_hash(ex),
        "finality_state": (ex.get("disposition_evidence") or {}).get("finality_state", "unknown"),
        "priority_score": score, "priority_band": band, "priority_reason": "; ".join(why),
        # Explicit risk-override flag (fraud_indicator/sanctions_hold) so the output validator
        # can recompute the band exactly as the builder did — not inferred from the disposition.
        "priority_risk_override": risk,
        "decision_authority": "human-adjudication-required",
        "needs": [], "citations": citations,
        "evidence_bundle": None, "disposition_recommendation": None,
    }

    # 1. needs-data — never guess to clear an exception
    if not msgs or not _has_identifier(ex):
        if not msgs:
            rec["needs"].append("payment messages (no pacs/camt chronology available)")
        if not _has_identifier(ex):
            rec["needs"].append("a payment identifier (uetr / instruction_id / end_to_end_id)")
        rec["disposition"] = "needs-data"
        return rec

    bundle = {
        "case_id": case_id,
        "exception_id": eid,
        "scheme": ex.get("scheme"),
        "identifiers": ex.get("identifiers"),
        "parties": ex.get("parties"),
        "amount": ex.get("amount"),
        "chronology": chron,
        "last_status": last,
        "disposition_evidence": ex.get("disposition_evidence"),
        "finality_note": "Recall request does not establish recovered funds; completion messages require scheme and ledger confirmation.",
        "linked_cases": [],
        "citations": citations,
    }
    rec["evidence_bundle"] = bundle

    fam = codes.get((last or {}).get("reason_code"), {}).get("family")

    # 2. routing overrides — a fraud/sanctions signal is never hidden by dedup or repair
    if ex.get("fraud_indicator") or fam == "fraud":
        rec["disposition"] = "route-specialist"
        rec["route_specialist"] = ROUTE_FRAUD
        reason = "fraud indicator present" if ex.get("fraud_indicator") else "fraudulent-origin reason code"
        rec["disposition_recommendation"] = _reco("route-specialist",
            f"{reason}; route to fraud investigation. No repair or return recommended here.",
            "Refer the evidence bundle to payment fraud investigation for adjudication.", ROUTE_FRAUD)
        return rec
    if ex.get("sanctions_hold"):
        rec["disposition"] = "route-specialist"
        rec["route_specialist"] = ROUTE_SANCTIONS
        reason = "sanctions hold flag set" if ex.get("sanctions_hold") else "regulatory reason code (RR04)"
        rec["disposition_recommendation"] = _reco("route-specialist",
            f"{reason}; route to sanctions adjudication. No repair, return, or release recommended here.",
            "Refer the evidence bundle to sanctions adjudication for a match decision.", ROUTE_SANCTIONS)
        return rec

    if fam == "regulatory":
        rec["disposition"] = "recommend-request-information"
        rec["disposition_recommendation"] = _reco("recommend-request-information",
            "Regulatory reason alone does not establish a sanctions match or hold.",
            "Obtain the regulatory cause and route to the relevant compliance owner.", None)
        return rec

    # 3. possible-duplicate — link to an open case, never merge or re-investigate
    parent = _dup_parent(ex, doc.get("open_cases"))
    if parent:
        bundle["linked_cases"] = [parent.get("case_id")]
        rec["linked_case_id"] = parent.get("case_id")
        rec["disposition"] = "possible-duplicate"
        rec["disposition_recommendation"] = _reco("possible-duplicate",
            f"Matches open case {parent.get('case_id')} on payment identifier; link for human confirmation.",
            "Confirm the link with the owning investigator; do not merge automatically.", None)
        return rec

    # 4. recall (camt.056) handling
    if ex.get("exception_type") == "recall_requested" or any(m.get("msg_type") == "camt.056" for m in msgs):
        disp = _recall_disposition(ex, last, codes)
        rc = (last or {}).get("reason_code")
        nm = codes.get(rc, {}).get("name", rc)
        rec["disposition"] = disp
        verb = {"recommend-honor-recall": "recommend honoring the recall request",
                "recommend-reject-recall": "recommend rejecting the recall request",
                "recommend-request-information": "recommend requesting further information"}[disp]
        rec["disposition_recommendation"] = _reco(disp,
            f"Recall reason {rc} ({nm}); {verb}. A camt.029 response is a decision reserved for a human approver.",
            "Send the recommendation to the payments approver; the camt.029 response is issued only after approval.", None)
        return rec

    # 5. reason-code mapping for rejected / returned exceptions
    rc = (last or {}).get("reason_code")
    entry = codes.get(rc)
    if entry:
        disp = entry["action"]
        operation = {"recommend-repair-and-resubmit": "repair", "recommend-return-to-originator": "return"}.get(disp)
        if operation and not _eligible(ex, operation):
            rec["candidate_disposition"] = disp
            rec["needs"].append("cited scheme eligibility, current finality, and operation-specific evidence")
            disp = "recommend-request-information"
        if disp == "recommend-repair-and-resubmit":
            repair = ex.get("repair_evidence") or {}
            if (ex["disposition_evidence"].get("finality_state") != "not_settled"
                    or not all(repair.get(k) for k in ("field", "new_value", "verification_source"))
                    or repair.get("confirmed_defect") is not True):
                rec["needs"].append("confirmed defect and verified exact correction before a repair proposal")
                disp = "recommend-request-information"
        rec["disposition"] = disp
        nm = entry["name"]
        rec["disposition_recommendation"] = _reco(disp,
            f"Last status {last.get('status')} with reason {rc} ({nm}); {_action_phrase(disp)}.",
            _next_action(disp), None)
        return rec

    # 6. fallback — chronology exists but no actionable reason code
    rec["disposition"] = "recommend-request-information"
    rec["disposition_recommendation"] = _reco("recommend-request-information",
        "Exception has a chronology but no actionable reason code; recommend requesting information.",
        "Request the missing status/reason detail from the counterparty agent.", None)
    return rec


def _action_phrase(disp):
    return {
        "recommend-repair-and-resubmit": "the field is repairable — recommend correcting it and resubmitting",
        "recommend-return-to-originator": "no repair is possible — recommend return to originator",
        "recommend-request-information": "recommend requesting information before any repair",
    }.get(disp, "recommend human review")


def _next_action(disp):
    return {
        "recommend-repair-and-resubmit": "Propose the corrected field to payment-repair-planner; this produces an offline proposal and grants no execution authority.",
        "recommend-return-to-originator": "Propose a return to originator; the return message is sent only after approval.",
        "recommend-request-information": "Draft an information request to the counterparty; send only after approval.",
    }.get(disp, "Escalate for human review.")


def _reco(disp, rationale, next_action, route):
    r = {"disposition": disp, "rationale": rationale,
         "recommended_next_action": next_action, "requires_approval": True}
    if route:
        r["route_specialist"] = route
    return r


def investigate(doc: dict) -> dict:
    from validate_input import validate
    errors, _ = validate(doc)
    if errors: raise ValueError("; ".join(errors))
    doc = copy.deepcopy(doc)
    codes = {**DEFAULT_REASON_CODES, **(doc.get("reason_code_config") or {})}
    cfg = {**DEFAULT_PRIORITY, **(doc.get("priority_config") or {})}
    records = [investigate_one(ex, doc, codes, cfg) for ex in doc.get("exceptions") or []]
    summary = {"total": len(records)}
    for r in records:
        summary[r["disposition"]] = summary.get(r["disposition"], 0) + 1
    return {"source_request": doc, "source_hash": stable_hash(doc),
            "scope": "bank-payment / normalized ISO 20022 only",
            "priority_limitations": "Illustrative triage, calendar-day age, no SLA or currency conversion; supplied configs are not authenticated.",
            "config_version": doc.get("config_version"),
            "reason_code_set_version": doc.get("reason_code_set_version"),
            # Echo the effective priority thresholds the engine used so validate_output ties out
            # the band against the same config (never a hardcoded default).
            "priority_thresholds": {"p1_min": cfg["p1_min"], "p2_min": cfg["p2_min"]},
            "investigations": records, "summary": summary,
            "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exceptions_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    try:
        result = investigate(doc)
    except (ValueError, TypeError) as exc:
        print("ERROR", exc); return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
