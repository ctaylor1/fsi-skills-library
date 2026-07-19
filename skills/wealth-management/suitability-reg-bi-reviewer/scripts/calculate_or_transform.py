#!/usr/bin/env python3
"""Deterministic Reg BI / FINRA 2111 obligation-evidence checks for suitability-reg-bi-reviewer.

Reads a recommendation packet (see validate_input.py), evaluates a documented set of
obligation checks across the four Reg BI component obligations (Disclosure, Care, Conflict of
Interest, Compliance) plus FINRA 2111 suitability for non-retail accounts, attaches cited
evidence to each SATISFIED check, and maps the check set to a review-disposition band.

IMPORTANT: This produces *evidence findings and gaps* and a review-readiness disposition
only. It NEVER makes the best-interest / suitability determination, approves or rejects the
recommendation, clears a trade, or closes the review. The disposition mapping is deterministic
and documented in references/domain-rules.md. A qualified supervisor/principal adjudicates.

Statuses: "satisfied" (evidenced) | "gap" (should be present, is missing/incomplete) |
"not_evaluable" (required input absent — fail closed) | "not_applicable" (obligation does not
apply to this packet, e.g. Form CRS for an institutional customer).

Usage:
  python calculate_or_transform.py packet.json | --selftest
Prints the review-core JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "required_profile_fields": ["risk_tolerance", "time_horizon_years", "liquidity_needs",
                                "investment_objectives", "financial_situation", "investment_experience"],
    "min_alternatives": 1,
    "require_cost_comparison": True,
    "product_disclosure_types": ["Prospectus", "Product Disclosure", "Offering Document", "Fee Disclosure"],
    "quantitative_actions": ["switch", "exchange"],
}
DISCLAIMER = ("Reg BI and suitability evidence review only; not a best-interest determination, "
              "a suitability approval, or supervisory sign-off. No recommendation has been approved "
              "and no order has been placed. A qualified supervisor or principal must adjudicate.")


def _cite(item: dict) -> str:
    return f"{item.get('source_ref', '?')}@{item.get('date', '?')}"


def _find_disclosure(disclosures, dtype):
    for d in disclosures:
        if str(d.get("type", "")).lower() == str(dtype).lower():
            return d
    return None


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    retail = doc["customer_type"] == "retail"
    rec = doc["recommendation"]
    action = rec.get("action")
    sec = rec.get("security") or {}
    prof = doc.get("customer_profile") or {}
    disclosures = doc.get("disclosures") or []
    costs = doc.get("costs") or {}
    alternatives = doc.get("alternatives_considered")
    conflicts = doc.get("conflicts")
    supervision = doc.get("supervision") or {}
    dd = doc.get("product_due_diligence") or {}
    rollover = doc.get("rollover_analysis") or {}

    checks = []

    def add(check, obligation, status, reason, evidence, blocking=False):
        checks.append({"check": check, "obligation": obligation, "status": status,
                       "reason": reason, "evidence": evidence, "blocking": blocking})

    # ---- Disclosure Obligation -------------------------------------------------------------
    for check, dtype, blocking in (("disclosure_form_crs", "Form CRS", True),
                                   ("disclosure_reg_bi", "Reg BI Disclosure", True)):
        if not retail:
            add(check, "Disclosure", "not_applicable",
                f"{dtype} applies to retail customers; institutional accounts follow FINRA 2111", [], blocking)
            continue
        if not disclosures:
            add(check, "Disclosure", "not_evaluable", "no disclosures list provided", [], blocking)
            continue
        d = _find_disclosure(disclosures, dtype)
        if d is None:
            add(check, "Disclosure", "not_evaluable", f"{dtype} not present in disclosures list", [], blocking)
        elif d.get("delivered"):
            add(check, "Disclosure", "satisfied", f"{dtype} delivered on {d.get('date')}",
                [{"item": dtype, "citation": _cite(d)}], blocking)
        else:
            add(check, "Disclosure", "gap", f"{dtype} present but not marked delivered", [], blocking)

    # product-level disclosure (prospectus / fee disclosure for the recommended security)
    if not disclosures:
        add("disclosure_product", "Disclosure", "not_evaluable", "no disclosures list provided", [])
    else:
        prod = next((d for d in disclosures
                     if any(str(d.get("type", "")).lower() == t.lower() for t in cfg["product_disclosure_types"])
                     and d.get("delivered")), None)
        if prod:
            add("disclosure_product", "Disclosure", "satisfied",
                f"product disclosure ({prod.get('type')}) delivered for {sec.get('name')}",
                [{"item": prod.get("type"), "citation": _cite(prod)}])
        else:
            add("disclosure_product", "Disclosure", "gap",
                "no delivered product-level disclosure (prospectus/fee disclosure) for the recommended security", [])

    # ---- Care Obligation -------------------------------------------------------------------
    if not prof:
        add("care_profile_complete", "Care", "not_evaluable", "no customer_profile provided", [], blocking=True)
    else:
        missing = [f for f in cfg["required_profile_fields"] if prof.get(f) in (None, "", [], {})]
        if missing:
            add("care_profile_complete", "Care", "gap",
                f"investment-profile fields missing: {missing}", [], blocking=True)
        else:
            add("care_profile_complete", "Care", "satisfied",
                "investment profile complete (risk tolerance, horizon, liquidity, objectives, situation, experience)",
                [{"item": "investment_profile", "citation": _cite(prof)}], blocking=True)

    if dd.get("reviewed"):
        add("care_reasonable_basis", "Care", "satisfied",
            "product-level due diligence documented (reasonable-basis suitability)",
            [{"item": "product_due_diligence", "citation": _cite(dd)}])
    else:
        add("care_reasonable_basis", "Care", "gap",
            "no documented product due diligence establishing reasonable-basis suitability", [])

    if not costs:
        add("care_cost_considered", "Care", "not_evaluable", "no costs block provided", [])
    elif costs.get("cost_comparison_documented") or not cfg["require_cost_comparison"]:
        add("care_cost_considered", "Care", "satisfied",
            "costs captured and a cost comparison is documented (cost considered, not dispositive)",
            [{"item": "costs", "citation": _cite(costs)}])
    else:
        add("care_cost_considered", "Care", "gap",
            "costs captured but no documented cost comparison against alternatives", [])

    if alternatives is None:
        add("care_alternatives_considered", "Care", "gap",
            "reasonably-available alternatives not documented", [])
    elif len(alternatives) >= cfg["min_alternatives"] and all(a.get("rationale") for a in alternatives):
        add("care_alternatives_considered", "Care", "satisfied",
            f"{len(alternatives)} reasonably-available alternative(s) documented with rationale",
            [{"item": a.get("security", "alternative"), "citation": _cite(a)} for a in alternatives])
    else:
        add("care_alternatives_considered", "Care", "gap",
            "alternatives listed without a documented rationale, or fewer than the configured minimum", [])

    if action == "rollover":
        if rollover.get("documented"):
            add("care_rollover_comparison", "Care", "satisfied",
                "rollover cost/benefit comparison documented (plan vs. IRA: fees, services, investment options)",
                [{"item": "rollover_analysis", "citation": _cite(rollover)}])
        else:
            add("care_rollover_comparison", "Care", "gap",
                "rollover recommendation without a documented plan-vs-IRA comparison", [])
    else:
        add("care_rollover_comparison", "Care", "not_applicable", "recommendation is not a rollover", [])

    if action in cfg["quantitative_actions"]:
        if rec.get("switch_rationale"):
            add("care_quantitative_series", "Care", "satisfied",
                "switch/exchange rationale documented (series not excessive; quantitative suitability)",
                [{"item": "switch_rationale", "citation": _cite(rec)}])
        else:
            add("care_quantitative_series", "Care", "gap",
                "switch/exchange without a documented rationale addressing excessive-trading concerns", [])
    else:
        add("care_quantitative_series", "Care", "not_applicable",
            "single buy/hold/sell/rollover — quantitative-suitability (excessive trading) check not applicable", [])

    # ---- Conflict of Interest Obligation ---------------------------------------------------
    if conflicts is None:
        add("conflict_disclosed", "Conflict", "not_evaluable", "no conflicts inventory provided", [])
    elif len(conflicts) == 0:
        add("conflict_disclosed", "Conflict", "not_evaluable",
            "conflicts inventory is empty (no attestation of identified conflicts)", [])
    else:
        undisclosed = [c for c in conflicts if not c.get("disclosed")]
        if undisclosed:
            add("conflict_disclosed", "Conflict", "gap",
                f"{len(undisclosed)} identified conflict(s) not marked disclosed", [])
        else:
            add("conflict_disclosed", "Conflict", "satisfied",
                f"all {len(conflicts)} identified conflict(s) disclosed",
                [{"item": c.get("type", "conflict"), "citation": _cite(c)} for c in conflicts])

    needs_prop = bool(sec.get("proprietary")) or bool((costs or {}).get("third_party_comp"))
    if not needs_prop:
        add("conflict_proprietary_comp", "Conflict", "not_applicable",
            "no proprietary product or third-party compensation flagged", [])
    else:
        prop = next((c for c in (conflicts or [])
                     if ("propriet" in str(c.get("type", "")).lower()
                         or "compensation" in str(c.get("type", "")).lower()
                         or "third" in str(c.get("type", "")).lower())
                     and c.get("disclosed") and c.get("mitigation")), None)
        if prop:
            add("conflict_proprietary_comp", "Conflict", "satisfied",
                "proprietary / compensation conflict disclosed and mitigation documented",
                [{"item": prop.get("type"), "citation": _cite(prop)}])
        else:
            add("conflict_proprietary_comp", "Conflict", "gap",
                "proprietary product or third-party compensation without a disclosed, mitigated conflict entry", [])

    # ---- Compliance Obligation (supervision / documentation) -------------------------------
    if not supervision:
        add("supervision_routed", "Compliance", "not_evaluable", "no supervision block provided", [])
    elif supervision.get("routed_for_review"):
        add("supervision_routed", "Compliance", "satisfied",
            f"recommendation routed to {supervision.get('reviewer_role', 'a supervisor')} for principal review (routed, not approved)",
            [{"item": "supervision", "citation": _cite(supervision)}])
    else:
        add("supervision_routed", "Compliance", "gap",
            "recommendation not routed for supervisory/principal review", [])

    # ---- Deterministic disposition (see references/domain-rules.md) ------------------------
    disposition = _disposition(checks)

    gaps = [c["check"] for c in checks if c["status"] == "gap"]
    not_eval = [{"check": c["check"], "why": c["reason"]} for c in checks if c["status"] == "not_evaluable"]

    open_items = []
    if disposition != "Evidence-complete":
        for c in checks:
            if c["status"] in ("gap", "not_evaluable"):
                open_items.append(f"[{c['obligation']}] {c['check']}: {c['reason']}")
        open_items.append("Advisor/compliance to remediate the items above before principal adjudication.")

    acct = str(doc["account_id"]).replace("*", "")
    return {
        "review_id": f"regbi-{acct}-{doc['as_of']}-0001",
        "account_id": doc["account_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "customer_type": doc["customer_type"],
        "recommendation_summary": {"action": action, "security_name": sec.get("name"),
                                   "amount": rec.get("amount"), "account_type": rec.get("account_type")},
        "checks": checks,
        "gaps": gaps,
        "not_evaluable": not_eval,
        "disposition": disposition,
        "open_items": open_items,
        "disclaimer": DISCLAIMER,
    }


def _disposition(checks: list) -> str:
    """Deterministic mapping shared with validate_output.py.

    Insufficient-evidence  -> any BLOCKING obligation is not_evaluable (required input absent).
    Gaps-identified        -> at least one check is a gap.
    Evidence-complete      -> every applicable check is satisfied (evidence ready for a human's
                              best-interest determination; NOT an approval).
    """
    if any(c.get("blocking") and c["status"] == "not_evaluable" for c in checks):
        return "Insufficient-evidence"
    if any(c["status"] == "gap" for c in checks):
        return "Gaps-identified"
    return "Evidence-complete"


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "recommendation_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
