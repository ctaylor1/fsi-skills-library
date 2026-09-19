#!/usr/bin/env python3
"""Offline issuer payment-dispute review. Supplied legal clocks, never a law engine."""
from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path
from payment_contract import money, require_currency, stable_hash, validate_rule_profile

STANDING_NOTE = ("Draft decision-support only. This skill does not decide any dispute, accept or deny a "
                 "chargeback, issue provisional or final credit, assign liability, submit or file a "
                 "response, or close a case; no account is debited or credited. An authorized issuer "
                 "reviewer determines applicable duties and performs any action.")
ALLOWED_DISPOSITIONS = {"draft-ready-for-review", "needs-data", "legal-profile-unresolved", "deadline-review-required", "route-specialist"}


def _clock_review(clock, as_of):
    issues = []
    for key in ("name", "source_ref", "trigger_event", "trigger_date", "trigger_source_ref", "due_date", "day_basis"):
        if not clock.get(key):
            issues.append(f"clock {clock.get('name', '?')}: {key} required")
    if clock.get("day_basis") not in {"calendar-days", "business-days", "explicit-date"}:
        issues.append("clock day_basis must be calendar-days, business-days or explicit-date")
    if clock.get("day_basis") == "business-days" and not clock.get("calendar_ref"):
        issues.append("business-day clock requires the named calendar/cutoff reference")
    try:
        trigger = date.fromisoformat(clock.get("trigger_date", ""))
        due = date.fromisoformat(clock.get("due_date", ""))
        if due < trigger:
            issues.append("clock due date precedes its trigger")
        remaining = (due - as_of).days
    except (ValueError, TypeError):
        issues.append("clock trigger/due date must be valid ISO dates")
        remaining = None
    return {**clock, "status": "unresolved" if issues else "overdue-review" if remaining < 0 else "review-open",
            "calendar_days_remaining": remaining, "issues": issues,
            "calculation_basis": "reviewer-supplied due date; no statutory period inferred"}


def work_case(c, doc, as_of):
    rec = {"case_id": c.get("case_id"), "role": c.get("role"), "case_owner": "issuer-payment-dispute-reviewer",
           "jurisdiction": c.get("jurisdiction"), "rail": c.get("rail"), "product": c.get("product"),
           "needs": [], "citations": [c.get("source_ref")], "draft_response": None,
           "statutory_review": {"status": "unresolved", "clocks": []}, "scheme_review": {"status": "not-assessed"},
           "consultations": []}
    if c.get("role") in {"merchant", "acquirer"} or c.get("merchant_representment_requested"):
        rec.update(disposition="route-specialist", route_specialist="merchant-chargeback-response-packager",
                   recommended_action="prepare-merchant-acquirer-response")
        return rec
    txn = c.get("transaction") or {}
    issues = []
    if c.get("role") != "issuer":
        issues.append("issuer role required")
    for key in ("jurisdiction", "rail", "product", "source_ref"):
        if not c.get(key): issues.append(f"case {key} required")
    if not txn.get("txn_id"):
        issues.append("transaction reference required")
    try:
        currency = require_currency(c.get("currency"))
        if require_currency(txn.get("currency")) != currency:
            issues.append("transaction and dispute currency differ")
        if money(c.get("dispute_amount")) < 0 or money(c.get("dispute_amount")) > money(txn.get("amount")):
            issues.append("disputed amount outside supplied transaction amount")
    except ValueError as exc:
        issues.append(str(exc))
    if issues:
        rec.update(disposition="needs-data", recommended_action="resolve-case-evidence", needs=issues)
        return rec
    # Consumer protections remain an independent track even when scheme recovery is unavailable.
    profile = c.get("statutory_profile")
    profile_issues = validate_rule_profile(profile, as_of.isoformat(), participant="issuer", jurisdiction=c["jurisdiction"])
    profile = profile if isinstance(profile, dict) else {}
    if "case_scope" in profile:
        scope = profile["case_scope"]
        expected = {"case_id": c.get("case_id"), "participant": c.get("role"),
                    "jurisdiction": c.get("jurisdiction"), "product": c.get("product"), "rail": c.get("rail")}
        if not isinstance(scope, dict) or any(scope.get(k) != value for k, value in expected.items()):
            profile_issues.append("prepared statutory profile is bound to a different case scope")
        elif profile.get("case_scope_hash") != stable_hash(scope):
            profile_issues.append("prepared statutory profile scope hash mismatch")
    if c["product"] not in (profile.get("products") or []): profile_issues.append("statutory profile does not cover product")
    if c["rail"] not in (profile.get("rails") or []): profile_issues.append("statutory profile does not cover rail")
    if not profile.get("regime") or not profile.get("applicability_rationale"):
        profile_issues.append("named legal regime and reviewed applicability rationale required")
    names = profile.get("required_clock_names") or []
    if not names: profile_issues.append("profile must identify required statutory clocks")
    clocks = [_clock_review(clock, as_of) for clock in (c.get("statutory_clocks") or [])]
    actual = [clock.get("name") for clock in clocks]
    if len(actual) != len(set(actual)): profile_issues.append("duplicate statutory clock names")
    for name in names:
        if name not in actual: profile_issues.append(f"required statutory clock missing: {name}")
    for clock in clocks:
        profile_issues.extend(clock["issues"])
    rec["statutory_review"] = {"status": "unresolved" if profile_issues else "supplied-for-review",
                                "profile": profile, "clocks": clocks,
                                "applicability_verified_by_agent": False}
    rec["citations"] += [profile.get("source_ref")] + [clock.get("source_ref") for clock in clocks]
    # Optional scheme information never supplies or extinguishes a statutory clock.
    scheme = c.get("scheme_profile")
    if scheme is not None or c.get("scheme_clocks"):
        scheme_issues = validate_rule_profile(scheme, as_of.isoformat(), participant="issuer", jurisdiction=c["jurisdiction"])
        scheme_clocks = [_clock_review(clock, as_of) for clock in c.get("scheme_clocks", [])]
        for clock in scheme_clocks:
            scheme_issues.extend(clock["issues"])
        rec["scheme_review"] = {"status": "unresolved" if scheme_issues else "supplied-for-review",
                                  "profile": scheme, "issues": scheme_issues, "clocks": scheme_clocks}
        rec["citations"] += [clock.get("source_ref") for clock in scheme_clocks]
    if c.get("fraud_investigation_required"):
        rec["consultations"].append({"target": "payment-fraud-and-scam-investigator", "scope": "payment fraud/scam evidence", "return_to": "issuer-payment-dispute-reviewer"})
    evidence = c.get("evidence") or []
    evidence_needs = [f"supplied evidence reference needed: {name}" for name in profile.get("required_evidence_types", [])
                      if not any(e.get("type") == name and e.get("ref") for e in evidence)]
    action_checks = c.get("statutory_action_reviews") or {}
    action_needs = [f"issuer reviewer must assess: {name}" for name in profile.get("required_action_reviews", [])
                    if not isinstance(action_checks.get(name), dict) or not action_checks[name].get("review_ref")]
    rec["needs"] = profile_issues + evidence_needs + action_needs
    if profile_issues:
        rec.update(disposition="legal-profile-unresolved", recommended_action="obtain-approved-legal-profile-and-clocks")
    elif any(clock["status"] == "overdue-review" for clock in clocks):
        rec.update(disposition="deadline-review-required", recommended_action="urgent-issuer-review")
    elif evidence_needs or action_needs:
        rec.update(disposition="needs-data", recommended_action="complete-issuer-review-evidence")
    else:
        rec.update(disposition="draft-ready-for-review", recommended_action="review-customer-error-case")
        rec["draft_response"] = {"case_id": c["case_id"], "purpose": "issuer customer-error review checklist, not merchant representment",
                                  "statutory_review": rec["statutory_review"], "scheme_review": rec["scheme_review"],
                                  "evidence_inventory": evidence, "evidence_status": "supplied",
                                  "statutory_action_reviews": action_checks,
                                  "authorization_status": "pending-human-review", "authorized_submission": False,
                                  "narrative": "Review authorization/error allegations, statutory action records and independent scheme recovery options. No outcome or liability conclusion is generated."}
    rec["citations"] = [x for x in rec["citations"] if x]
    return rec


def run(doc):
    as_of = date.fromisoformat(doc["processing_date"])
    records = [work_case(c, doc, as_of) for c in doc["cases"]]
    return {"processing_date": as_of.isoformat(), "input_snapshot_hash": stable_hash(doc), "execution_mode": "offline-draft-only",
            "cases": records, "summary": {"total": len(records), **{d: sum(r["disposition"] == d for r in records) for d in sorted(ALLOWED_DISPOSITIONS)}},
            "standing_note": STANDING_NOTE}


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/cases_example.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    doc = json.loads(path.read_text() if path else sys.stdin.read())
    from validate_input import validate
    errors, _ = validate(doc)
    if errors:
        print(json.dumps({"errors": errors})); return 1
    print(json.dumps(run(doc), indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
