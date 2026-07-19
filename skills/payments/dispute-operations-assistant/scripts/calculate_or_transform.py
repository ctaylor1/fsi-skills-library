#!/usr/bin/env python3
"""Deterministic issuer/acquirer dispute case engine for dispute-operations-assistant.

For each card-dispute case worked from the issuing or acquiring bank side, this engine:
  1. Verifies role and transaction identity (issuer|acquirer; amount/currency tie-out).
  2. Validates the network reason code against a versioned rule registry.
  3. Computes the response deadline (received date + reason-code window) and days remaining.
  4. Checks evidence sufficiency against the reason code's required-evidence groups.
  5. Confirms the cited network rule version is the CURRENT effective version.
  6. Only when every gate holds, assembles a DRAFT case-response package (template
     sections + exhibit citations) and a decision-SUPPORT recommendation.

It NEVER decides a dispute, accepts/denies a chargeback, issues provisional or final credit,
assigns liability, submits/files a response, closes a case, or writes a system of record.
Fraud determinations, merchant-side representment, and ISO 20022 exceptions are routed out.
Every disposition below is decision-support for a human adjudicator; a human authorizes and
performs any submission.

Usage: python calculate_or_transform.py cases.json | --selftest
Normal mode prints the case-work JSON to stdout; --selftest runs bundled assertions and
prints a summary line ending "N error(s)" (exit 0 pass / 1 fail).
"""
from __future__ import annotations
import json, sys
from datetime import date, timedelta
from pathlib import Path

ROLES = {"issuer", "acquirer"}
AT_RISK_DAYS = 5  # <= this many days remaining flags the deadline as at-risk

STANDING_NOTE = (
    "Draft decision-support only. This skill does not decide any dispute, accept or deny a "
    "chargeback, issue provisional or final credit, assign liability, submit or file a "
    "response, or close a case; no cardholder or merchant account is debited or credited. A "
    "human adjudicator must review every recommendation and authorize any submission."
)

# Reason-code registry (a VERSIONED CONTRACT; override via doc['rule_registry']). Illustrative
# defaults only — a deployment loads the current network rulebook version. Each reason code
# maps to a category, the response window (days), and required-evidence groups. A group is
# satisfied if ANY of its evidence types is present.
RULE_REGISTRY = {
    "visa:10.4": {"title": "Fraud - Card-Absent Environment", "network": "visa",
                  "category": "fraud", "window_days": 30,
                  "required": [["auth_record"],
                               ["avs_result", "cvv_result", "three_ds_authentication"],
                               ["prior_undisputed_history", "transaction_receipt"]]},
    "visa:13.1": {"title": "Merchandise / Services Not Received", "network": "visa",
                  "category": "consumer_dispute", "window_days": 30,
                  "required": [["proof_of_delivery", "proof_of_service"],
                               ["order_confirmation"], ["terms_of_service"]]},
    "visa:13.3": {"title": "Not as Described or Defective", "network": "visa",
                  "category": "consumer_dispute", "window_days": 30,
                  "required": [["item_description_evidence"], ["terms_of_service"],
                               ["proof_no_valid_return"]]},
    "mastercard:4853": {"title": "Cardholder Dispute", "network": "mastercard",
                        "category": "consumer_dispute", "window_days": 45,
                        "required": [["proof_of_delivery", "proof_of_service"],
                                     ["order_confirmation"], ["terms_of_service"]]},
    "mastercard:4837": {"title": "No Cardholder Authorization", "network": "mastercard",
                        "category": "fraud", "window_days": 45,
                        "required": [["auth_record"],
                                     ["avs_result", "cvv_result", "three_ds_authentication"],
                                     ["prior_undisputed_history"]]},
}

ALLOWED_DISPOSITIONS = {
    "draft-ready-for-review", "evidence-insufficient", "needs-data",
    "out-of-time-review", "rule-version-stale", "route-specialist",
}
# route target -> catalog skill (all exist in catalog/skills-catalog.json)
ROUTE_TARGETS = {
    "fraud": "payment-fraud-case-investigator",
    "merchant_representment": "chargeback-dispute-packager",
    "iso_exception": "payment-exception-investigator",
}
RECOMMENDED = {
    "draft-ready-for-review": "represent-defend",
    "evidence-insufficient": "gather-evidence",
    "needs-data": "human-review-required",
    "out-of-time-review": "human-review-required",
    "rule-version-stale": "refresh-rule-version",
}


def _processing_date(doc) -> date:
    v = doc.get("processing_date")
    return date.fromisoformat(v) if v else date.today()


def _money(v) -> float:
    return round(float(v or 0), 2)


def _registry(doc) -> dict:
    return {**RULE_REGISTRY, **(doc.get("rule_registry") or {})}


def _identity_check(c) -> dict:
    txn = c.get("transaction") or {}
    issues = []
    if c.get("role") not in ROLES:
        issues.append(f"role {c.get('role')!r} is not issuer/acquirer")
    if not txn.get("txn_id"):
        issues.append("transaction.txn_id missing")
    if txn.get("currency") and c.get("currency") and str(txn["currency"]) != str(c["currency"]):
        issues.append(f"transaction currency {txn.get('currency')!r} != dispute currency {c.get('currency')!r}")
    if _money(c.get("dispute_amount")) > _money(txn.get("amount")) and _money(txn.get("amount")) > 0:
        issues.append(f"dispute amount {c.get('dispute_amount')} exceeds transaction amount {txn.get('amount')}")
    return {"ok": not issues, "issues": issues}


def _deadline(c, spec, proc: date) -> dict:
    window = int(c.get("response_window_days") or spec["window_days"])
    received = date.fromisoformat(c["dispute_received_date"])
    due = received + timedelta(days=window)
    remaining = (due - proc).days
    if remaining < 0:
        status = "out-of-time"
    elif remaining <= AT_RISK_DAYS:
        status = "at-risk"
    else:
        status = "on-time"
    return {"received_date": received.isoformat(), "window_days": window,
            "response_deadline": due.isoformat(), "days_remaining": remaining, "status": status}


def _evidence_check(c, spec) -> dict:
    present = sorted({e.get("type") for e in c.get("evidence") or [] if e.get("type")})
    present_set = set(present)
    missing = [grp for grp in spec["required"] if not (set(grp) & present_set)]
    return {"required_groups": spec["required"], "present_types": present,
            "missing_groups": missing, "complete": not missing}


def _citations(c, code, current_version) -> list:
    cites = [f"network-rules:{code}@{current_version}", f"casesys:{c.get('source_ref', '?')}"]
    cites += [f"evidence:{e.get('type')}:{e.get('ref', '')}" for e in c.get("evidence") or []]
    return cites


def _draft_response(c, spec, code, ded, ev, current_version, proc: date) -> dict:
    txn = c.get("transaction") or {}
    role = c.get("role")
    present = ", ".join(ev["present_types"]) or "none"
    narrative = (
        f"Under {c.get('network')} reason code {code} ({spec['title']}), the {role}-side case "
        f"is within the {ded['window_days']}-day response window (deadline {ded['response_deadline']}, "
        f"{ded['days_remaining']} day(s) remaining as of {proc.isoformat()}). Bundled evidence "
        f"satisfies every required group for this reason code: {present}. Recommend the {role} "
        f"prepare a {code} response (represent / defend) subject to analyst adjudication and "
        f"human-authorized submission. Each statement cites a bundled exhibit; no dispute "
        f"outcome is predicted and this skill performs no submission."
    )
    sections = {
        "case_identification": {
            "case_id": c.get("case_id"), "role": role, "network": c.get("network"),
            "reason_code": code, "reason_title": spec["title"],
            "transaction": {"txn_id": txn.get("txn_id"), "auth_id": txn.get("auth_id"),
                            "card_last4": txn.get("card_last4"), "txn_date": txn.get("txn_date")},
            "dispute_amount": _money(c.get("dispute_amount")), "currency": c.get("currency"),
            "identity_status": "verified"},
        "reason_code_and_rule_basis": {
            "reason_code": code, "reason_title": spec["title"], "category": spec["category"],
            "rule_version": current_version, "rule_current": True},
        "deadline_and_timeline": ded,
        "evidence_inventory": {
            "required_groups": ev["required_groups"], "present_types": ev["present_types"],
            "complete": ev["complete"],
            "exhibits": [{"type": e.get("type"), "ref": e.get("ref")} for e in c.get("evidence") or []]},
        "draft_response_narrative": narrative,
        "recommended_disposition": {
            "recommended_action": "represent-defend",
            "rationale": "reason code valid, deadline open, evidence sufficient, rule version current",
            "note": "decision-support recommendation only; the human adjudicator decides"},
        "human_review_and_authorization": {
            "reviewer_role": "Disputes analyst / dispute operations lead",
            "review_checklist": [
                "Reason code and deadline verified against the current network rulebook",
                "Evidence complete, correctly masked, and tied to the disputed transaction",
                "Narrative contains no unsupported claim, outcome guarantee, or advice",
                "Authorized to submit via the dispute case system"],
            "authorization_status": "pending-human-authorization",
            "authorized_submission": False},
    }
    return {"sections": sections, "citations": _citations(c, code, current_version)}


def work_case(c, doc, proc: date, registry: dict, current_version: str) -> dict:
    code = f"{c.get('network')}:{c.get('reason_code')}"
    rec = {"case_id": c.get("case_id"), "role": c.get("role"), "network": c.get("network"),
           "reason_code": c.get("reason_code"),
           "citations": [f"casesys:{c.get('source_ref', '?')}"],
           "flags": [], "needs": [], "draft_response": None}

    identity = _identity_check(c)
    rec["identity_check"] = identity
    spec = registry.get(code)
    rec["reason_code_status"] = "known" if spec else "unknown"

    # 1) identity / structural completeness -> needs-data (never guess to clear a case)
    if not identity["ok"] or not spec:
        rec["disposition"] = "needs-data"
        rec["recommended_action"] = RECOMMENDED["needs-data"]
        if not identity["ok"]:
            rec["needs"] += identity["issues"]
        if not spec:
            rec["needs"].append(f"reason_code {c.get('reason_code')!r} not in rule registry for {c.get('network')}")
        return rec

    rec["reason_title"] = spec["title"]
    ded = _deadline(c, spec, proc)
    ev = _evidence_check(c, spec)
    cited = c.get("rule_version_cited")
    rule_ok = (cited == current_version)
    rec["deadline"] = ded
    rec["evidence_check"] = ev
    rec["rule_currency"] = {"cited": cited, "current": current_version, "current_ok": rule_ok}
    rec["citations"] = _citations(c, code, current_version)
    if ded["status"] == "at-risk":
        rec["flags"].append("deadline-at-risk")

    # 2) out-of-scope work is routed to a specialist skill (fraud / merchant / ISO)
    if c.get("fraud_investigation_required"):
        rec.update({"disposition": "route-specialist", "route_specialist": ROUTE_TARGETS["fraud"],
                    "recommended_action": "route-to-fraud-investigation"})
        return rec
    if c.get("merchant_representment_requested"):
        rec.update({"disposition": "route-specialist",
                    "route_specialist": ROUTE_TARGETS["merchant_representment"],
                    "recommended_action": "route-to-merchant-representment"})
        return rec
    if c.get("iso_exception"):
        rec.update({"disposition": "route-specialist", "route_specialist": ROUTE_TARGETS["iso_exception"],
                    "recommended_action": "route-to-payment-exception"})
        return rec

    # 3) stale rule version -> refresh before trusting windows/requirements
    if not rule_ok:
        rec["flags"].append("rule-version-stale")
        rec.update({"disposition": "rule-version-stale",
                    "recommended_action": RECOMMENDED["rule-version-stale"]})
        rec["needs"].append(f"refresh cited rule version {cited!r} to current {current_version!r}")
        return rec

    # 4) response window elapsed -> human review; NEVER auto-accept liability or write off
    if ded["status"] == "out-of-time":
        rec.update({"disposition": "out-of-time-review",
                    "recommended_action": RECOMMENDED["out-of-time-review"]})
        return rec

    # 5) evidence gap -> cannot draft a complete response
    if not ev["complete"]:
        rec.update({"disposition": "evidence-insufficient",
                    "recommended_action": RECOMMENDED["evidence-insufficient"]})
        rec["needs"] += [f"evidence for group {grp}" for grp in ev["missing_groups"]]
        return rec

    # 6) clean -> assemble a draft case response for human adjudication + authorized submission
    rec.update({"disposition": "draft-ready-for-review",
                "recommended_action": RECOMMENDED["draft-ready-for-review"]})
    rec["draft_response"] = _draft_response(c, spec, code, ded, ev, current_version, proc)
    return rec


def run(doc: dict) -> dict:
    proc = _processing_date(doc)
    registry = _registry(doc)
    current_version = doc.get("current_rule_version")
    records = [work_case(c, doc, proc, registry, current_version) for c in doc["cases"]]

    def _count(d):
        return sum(1 for r in records if r.get("disposition") == d)

    summary = {"total": len(records)}
    for d in sorted(ALLOWED_DISPOSITIONS):
        summary[d] = _count(d)
    return {"current_rule_version": current_version, "processing_date": proc.isoformat(),
            "cases": records, "summary": summary, "standing_note": STANDING_NOTE}


# Expected dispositions for the bundled golden fixture (used by --selftest).
EXPECTED = {
    "DC-3001": "draft-ready-for-review",
    "DC-3002": "evidence-insufficient",
    "DC-3003": "needs-data",
    "DC-3004": "out-of-time-review",
    "DC-3005": "rule-version-stale",
    "DC-3006": "route-specialist",
    "DC-3007": "draft-ready-for-review",
}


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "cases_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = run(doc)
    errors = []
    by_id = {r["case_id"]: r for r in out["cases"]}
    for cid, want in EXPECTED.items():
        got = (by_id.get(cid) or {}).get("disposition")
        mark = "PASS" if got == want else "ERROR"
        print(f"{mark} {cid}: disposition={got} (expected {want})")
        if got != want:
            errors.append(cid)
    # DC-3006 must route to the fraud investigator; DC-3007 must be flagged deadline-at-risk.
    if by_id.get("DC-3006", {}).get("route_specialist") != "payment-fraud-case-investigator":
        errors.append("DC-3006 route target")
        print("ERROR DC-3006: route target != payment-fraud-case-investigator")
    if "deadline-at-risk" not in by_id.get("DC-3007", {}).get("flags", []):
        errors.append("DC-3007 at-risk flag")
        print("ERROR DC-3007: missing deadline-at-risk flag")
    if by_id.get("DC-3001", {}).get("draft_response") is None:
        errors.append("DC-3001 draft missing")
        print("ERROR DC-3001: draft_response missing for draft-ready case")
    print(f"transform selftest: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(run(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
