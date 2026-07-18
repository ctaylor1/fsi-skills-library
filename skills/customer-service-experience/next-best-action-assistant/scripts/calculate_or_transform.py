#!/usr/bin/env python3
"""Deterministic next-best-action engine for next-best-action-assistant.

Reads a customer-context file (CRM/transcript/case-derived context plus the APPROVED action
catalog) and assembles a DRAFT next-best-action package: a ranked, cited, eligibility-gated
list of policy-compliant service, education, referral, and retention actions.

It never produces a binding decision. Any catalog entry carrying a `binding_category`
(credit_decision, claim_decision, investment_advice, suitability_determination) is EXCLUDED
from recommendations and routed to a licensed specialist. Actions are gated by product/
tenure/signal eligibility, by marketing consent and do-not-contact, and by a vulnerability
flag (which suppresses retention/cross-sell and routes to specialist support). The package
is draft-only: nothing is sent, submitted, or written to a system of record.

Usage: python calculate_or_transform.py context.json | --selftest
Normal mode prints the draft package JSON to stdout (exit 0).
--selftest runs the engine on the bundled fixture, checks internal invariants and the
consent/vulnerability/prohibited gating branches, and prints a line ending "N error(s)".
Exit 0 if the selftest passes, 1 otherwise.
"""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path

PROHIBITED_BINDING = {
    "credit_decision", "claim_decision", "investment_advice", "suitability_determination",
}
SALES_PRESSURE_TYPES = {"retention", "cross-sell"}
SPECIALIST_ROUTES = {
    "licensed_mortgage_lending": "loan-affordability-precheck / licensed mortgage lending specialist",
    "licensed_investment_advice": "suitability-reg-bi-reviewer / licensed investment adviser",
    "licensed_claims": "licensed claims adjuster",
}
BINDING_ROUTES = {
    "credit_decision": "loan-affordability-precheck / licensed lending specialist",
    "claim_decision": "licensed claims adjuster",
    "investment_advice": "suitability-reg-bi-reviewer / licensed investment adviser",
    "suitability_determination": "suitability-reg-bi-reviewer / licensed investment adviser",
}
STANDING_NOTE = (
    "Draft recommendations only. No action here is a binding credit, claims, or investment "
    "decision; nothing has been delivered to the customer or written to any system of record. "
    "A human agent must review each recommendation, record the required approvals, and read "
    "the applicable disclosures before acting."
)
REQUIRED_APPROVALS = [
    "Servicing supervisor or QA reviewer before external delivery",
    "Licensed specialist sign-off before any referral is acted on",
]


def _eligibility_check(action, customer):
    """Return (ok: bool, reason: str, basis: list[str])."""
    elig = action.get("eligibility") or {}
    products = set(customer.get("products") or [])
    signals = customer.get("signals") or {}
    basis = []

    any_req = elig.get("products_any") or []
    if any_req:
        if not (products & set(any_req)):
            return False, f"ineligible: requires one of products {any_req}", basis
        basis.append("holds " + "/".join(sorted(products & set(any_req))))

    none_req = elig.get("products_none") or []
    held_excluded = products & set(none_req)
    if held_excluded:
        return False, f"ineligible: already holds {sorted(held_excluded)}", basis
    if none_req:
        basis.append("does not already hold " + "/".join(none_req))

    min_tenure = int(elig.get("min_tenure_months") or 0)
    if int(customer.get("tenure_months") or 0) < min_tenure:
        return False, f"ineligible: tenure < {min_tenure} months", basis
    if min_tenure:
        basis.append(f"tenure >= {min_tenure}m")

    seg = customer.get("segment")
    if seg in (elig.get("excluded_segments") or []):
        return False, f"ineligible: segment {seg} excluded", basis

    for sig in elig.get("requires_signals") or []:
        if not signals.get(sig):
            return False, f"ineligible: missing signal {sig}", basis
        basis.append(f"signal {sig}")

    return True, "", basis


def _consent_ok(action, customer):
    """Return (ok, reason). Any outbound action gated by do_not_contact + channel consent."""
    channel = action.get("requires_consent")
    if not channel:
        return True, ""
    if customer.get("do_not_contact"):
        return False, "consent_gated: do-not-contact set"
    consent = customer.get("consent") or {}
    if consent.get(channel) is not True:
        return False, f"consent_gated: {channel} consent not granted"
    return True, ""


def _evaluate(action, customer):
    """Classify one catalog action -> ('recommend'|'exclude'|'route', payload)."""
    aid = action.get("action_id")

    # 1. Prohibited binding decisions are never recommended; route to a licensed specialist.
    binding = action.get("binding_category")
    if binding in PROHIBITED_BINDING:
        return "route", {
            "action_id": aid,
            "route": BINDING_ROUTES.get(binding, "licensed specialist"),
            "reason": f"{binding.replace('_', ' ')} is a licensed decision excluded from NBA",
        }

    # 2. Eligibility.
    ok, reason, basis = _eligibility_check(action, customer)
    if not ok:
        return "exclude", {"action_id": aid, "reason": reason}

    # 3. Vulnerability suppresses sales/retention pressure and routes to specialist support.
    if customer.get("vulnerability_flag") and action.get("type") in SALES_PRESSURE_TYPES:
        return "exclude", {
            "action_id": aid,
            "reason": "vulnerability_suppressed: retention/cross-sell not offered",
            "route": "vulnerable-customer-support-assistant",
        }

    # 4. Consent / do-not-contact gating for outbound actions.
    cok, creason = _consent_ok(action, customer)
    if not cok:
        return "exclude", {"action_id": aid, "reason": creason}

    # 5. Eligible -> recommendation.
    score = int(action.get("benefit_score") or 0) + sum(
        1 for s in (action.get("eligibility") or {}).get("requires_signals") or []
        if (customer.get("signals") or {}).get(s)
    )
    rec = {
        "action_id": aid,
        "type": action.get("type"),
        "title": action.get("title"),
        "rationale": action.get("description") or action.get("title"),
        "eligibility_basis": "; ".join(basis) if basis else "no eligibility constraints",
        "score": score,
        "citations": list(action.get("source_refs") or []),
        "required_disclosures": list(action.get("required_disclosures") or []),
        "requires_specialist": action.get("requires_specialist"),
    }
    return "recommend", rec


def build_package(doc: dict) -> dict:
    customer = doc.get("customer") or {}
    recs, excluded, referrals = [], [], []

    for action in doc.get("action_catalog") or []:
        kind, payload = _evaluate(action, customer)
        if kind == "recommend":
            recs.append(payload)
            spec = action.get("requires_specialist")
            if spec:
                referrals.append({
                    "action_id": action.get("action_id"),
                    "route": SPECIALIST_ROUTES.get(spec, spec),
                    "reason": "referral to a licensed specialist; NBA refers, it does not decide",
                })
        elif kind == "route":
            referrals.append(payload)
        else:
            excluded.append(payload)

    recs.sort(key=lambda r: (-r["score"], r["action_id"]))
    for i, r in enumerate(recs, 1):
        r["rank"] = i

    disclosures = []
    for r in recs:
        for d in r["required_disclosures"]:
            if d not in disclosures:
                disclosures.append(d)

    sources = list(doc.get("context_refs") or [])
    for r in recs:
        for c in r["citations"]:
            if c not in sources:
                sources.append(c)

    consent = customer.get("consent") or {}
    consent_line = (
        f"do-not-contact: {'yes' if customer.get('do_not_contact') else 'no'}; "
        f"vulnerability flag: {'yes' if customer.get('vulnerability_flag') else 'no'}; "
        f"channel consent: {json.dumps(consent, sort_keys=True)}."
    )

    package = {
        "config_version": doc.get("config_version"),
        "template_version": "nba-package-v1",
        "customer_ref": customer.get("customer_ref"),
        "sections": {
            "Customer Context Snapshot": (
                f"Segment {customer.get('segment')}, tenure {customer.get('tenure_months')} months; "
                f"products {customer.get('products')}; open complaint: "
                f"{'yes' if customer.get('open_complaint') else 'no'}. "
                f"Context sources: {'; '.join(doc.get('context_refs') or [])}."
            ),
            "Recommended Next Best Actions": f"{len(recs)} ranked action(s); see recommendations[].",
            "Consent & Eligibility Checks": consent_line,
            "Excluded or Routed to Specialist": (
                f"{len(excluded)} excluded, {len(referrals)} routed to a licensed specialist; "
                "see excluded[] and specialist_referrals[]."
            ),
            "Required Disclosures": (
                "; ".join(disclosures) if disclosures
                else "No action-specific disclosures; agent applies standard call disclosures."
            ),
            "Approvals & Handling": "Draft-only. Required approvals are pending; see approvals{}.",
            "Sources": "; ".join(sources),
        },
        "recommendations": recs,
        "excluded": excluded,
        "specialist_referrals": referrals,
        "approvals": {
            "required": list(REQUIRED_APPROVALS),
            "status": "pending",
            "external_delivery": False,
            "recorded_by": None,
        },
        "standing_note": STANDING_NOTE,
    }
    return package


def _selftest_checks(doc: dict) -> list[str]:
    """Exercise the golden fixture and the three critical gating branches."""
    errors: list[str] = []
    pkg = build_package(doc)

    recs = pkg["recommendations"]
    if not recs:
        errors.append("golden: no recommendations produced")
    # Every recommendation must be cited (no unsupported action).
    for r in recs:
        if not r.get("citations"):
            errors.append(f"golden: recommendation {r.get('action_id')} has no citation")
        if r.get("type") in PROHIBITED_BINDING:
            errors.append(f"golden: prohibited action type recommended: {r.get('action_id')}")
    # Ranks contiguous from 1.
    ranks = [r["rank"] for r in recs]
    if ranks != list(range(1, len(recs) + 1)):
        errors.append(f"golden: ranks not contiguous: {ranks}")
    # Scores monotonically non-increasing.
    scores = [r["score"] for r in recs]
    if scores != sorted(scores, reverse=True):
        errors.append(f"golden: recommendations not ranked by score: {scores}")

    ids = {r["action_id"] for r in recs}
    # Prohibited binding decision must be routed, never recommended.
    if "ADV-INVEST-ALLOCATE-01" in ids:
        errors.append("branch(prohibited): investment_advice was recommended, not routed")
    if not any(r["action_id"] == "ADV-INVEST-ALLOCATE-01" for r in pkg["specialist_referrals"]):
        errors.append("branch(prohibited): investment_advice not routed to a specialist")
    # Consent-gated outbound call must be excluded.
    if not any(e["action_id"] == "RET-WINBACK-CALL-01" for e in pkg["excluded"]):
        errors.append("branch(consent): outbound-call action not consent-gated")

    # Vulnerability branch: flip the flag and confirm retention/cross-sell are suppressed.
    vdoc = copy.deepcopy(doc)
    vdoc["customer"]["vulnerability_flag"] = True
    vpkg = build_package(vdoc)
    if any(r["type"] in SALES_PRESSURE_TYPES for r in vpkg["recommendations"]):
        errors.append("branch(vulnerability): retention/cross-sell not suppressed for vulnerable customer")
    if not any(e.get("route") == "vulnerable-customer-support-assistant" for e in vpkg["excluded"]):
        errors.append("branch(vulnerability): no route to vulnerable-customer-support")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "context_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        errors = _selftest_checks(doc)
        for e in errors:
            print("ERROR", e)
        print(f"transform selftest: {len(errors)} error(s)")
        return 1 if errors else 0
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_package(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
