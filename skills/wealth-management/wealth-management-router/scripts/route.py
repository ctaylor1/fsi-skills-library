"""Choose bounded P0/P1/P2/P3 workflows from explicit intents; never execute them."""
from copy import deepcopy
import json
import sys
from pathlib import Path
from wealth_contract import make_output, nonempty, source_errors, validate_envelope, validate_output_envelope

SKILL = "wealth-management-router"
# Sequence is a lifecycle convention, not an obligation to run unrequested work.
ROUTES = {
    "book-review": ("advisor-book-of-business-reviewer", "Explicit book scope, per-household service records, policy priorities, owner capacity and economic measures"),
    "prospect-referral": ("wealth-prospect-referral-preparer", "Permitted prospect/referral sources, attributed facts, service-fit questions, contact permissions and suppression evidence"),
    "discovery": ("wealth-client-discovery-assistant", "Household facts, goals and cited unknowns"),
    "household-reconciliation": ("household-wealth-data-reconciler", "Confirmed account scope, snapshots and explicit ownership shares"),
    "onboarding": ("wealth-onboarding-packager", "Account registration and current firm onboarding profile"),
    "risk-profile": ("investment-risk-profile-reviewer", "Cited willingness, capacity, horizon, liquidity and constraint evidence"),
    "financial-plan": ("household-financial-planning-assistant", "Reconciled household balance sheet, cash flow, debts, goals and supplied scenario assumptions"),
    "investment-policy": ("investment-policy-statement-builder", "Household objectives, six distinct risk dimensions, constraints and a human-owned investment mandate"),
    "retirement-plan": ("retirement-income-scenario-modeler", "Account balances/treatments, spending, dated income streams and scenario assumptions"),
    "portfolio-construction": ("portfolio-construction-assistant", "Approved supplied models, investable assets, target allocation, restrictions and concentration constraints"),
    "proposal-comparison": ("portfolio-proposal-comparator", "Comparable proposal positions, underlying exposures, costs, liquidity and client constraints"),
    "rebalancing": ("portfolio-rebalancing-assistant", "Position and tax-lot inventory, targets, price/fee/settlement evidence and transition constraints"),
    "tax-review": ("tax-aware-investment-reviewer", "Cited tax lots, household/spouse/IRA activity, supplied equivalence, rates and asset-location policy"),
    "estate-review": ("estate-wealth-transfer-reviewer", "Sourced estate intentions, account title, beneficiary designations and governing-document inventory"),
    "family-governance": ("family-wealth-governance-preparer", "Explicit family-group scope, sourced participation and audience permissions, decision records, succession evidence and discussion objectives"),
    "trust-administration": ("trust-administration-reviewer", "Explicit single-trust scope, trust-capacity engagement, governing-document clauses and legal applicability, fiduciary/beneficiary records, obligations, distribution evidence and accounting classifications"),
    "protection-needs": ("protection-needs-reviewer", "Sourced survivor, disability, long-term-care or liability scenario and existing coverage"),
    "performance-report": ("wealth-performance-report-builder", "Valuations at cash-flow boundaries, fees, approved benchmark and official reconciliation reference"),
    "account-service": ("wealth-account-service-packager", "Requested service, account/authority records, balances, positions and firm service conditions"),
    "fee-review": ("advisory-fee-reviewer", "Effective agreement, household billing group, valuation segments, exclusions, charges and conflict review"),
    "manager-due-diligence": ("investment-manager-due-diligence-reviewer", "Investor mandate, manager evidence, cited diligence policy, fees/liquidity and monitoring requirements"),
    "lending-liquidity": ("wealth-lending-liquidity-reviewer", "Household funding need, protected cash, supplied liquidation analysis, current loan terms, encumbrances and rate/collateral stresses"),
    "private-markets": ("private-market-client-reviewer", "Client commitments, dated notices and settlements, valuation/eligibility evidence, manager diligence and account-specific liquidity budgets"),
    "recommendation-evidence": ("investment-recommendation-evidence-reviewer", "Proposed recommendation and controlled capacity/applicability profile"),
    "client-review": ("client-review-preparer", "Cited household review records and current template/applicability configuration"),
    "follow-up": ("advisor-follow-up-assistant", "Sourced meeting record, decisions, recipients and current communication configuration"),
    "investor-protection": ("senior-investor-protection-screener", "Dated observations, transactions and firm screening configuration"),
}
ALIASES = {"goal-progress": "financial-plan"}
P0_INTENTS = {"discovery", "household-reconciliation", "onboarding", "risk-profile", "recommendation-evidence",
              "client-review", "follow-up", "investor-protection"}
HUMAN_ACTIONS = {"trade", "transfer", "account-opening", "send", "crm-write", "legal-determination", "place-hold"}
SUBJECT_SCOPES = {
    "book-review": ("advisor-book", "book_id", "book:", "book-scope-required"),
    "family-governance": ("family-group", "family_id", "family:", "family-scope-required"),
    "trust-administration": ("trust", "trust_id", "trust:", "trust-scope-required"),
}


def validate_input(doc):
    errors = validate_envelope(doc)
    if errors:
        return errors
    intents = doc.get("intents")
    if not isinstance(intents, list) or not intents or not all(nonempty(x) for x in intents):
        errors.append("intents must be a nonempty list of explicit intent strings")
    elif len(intents) != len(set(intents)):
        errors.append("duplicate intents")
    if isinstance(intents, list) and any(isinstance(i, str) and ALIASES.get(i, i) in ROUTES and ALIASES.get(i, i) not in P0_INTENTS for i in intents):
        for field in ("unresolved_issues", "upstream_artifact_ids"):
            if field not in doc:
                errors.append(f"{field} must be explicit for P1/P2/P3 routing; use [] only after scope review")
    if 'scope_type' in doc and doc['scope_type'] not in ('advisor-book', 'family-group', 'trust', 'household', 'prospect-case'):
        errors.append('scope_type must identify a supported subject scope')
    for key in ('book_id', 'family_id', 'trust_id'):
        if key in doc and not nonempty(doc[key]):
            errors.append(key + ' must be a nonempty identifier when supplied')
    issues = doc.get("unresolved_issues", [])
    if not isinstance(issues, list):
        errors.append("unresolved_issues must be a list when supplied")
    else:
        for issue in issues:
            if not isinstance(issue, dict) or not nonempty(issue.get("code")) or not nonempty(issue.get("message")):
                errors.append("each unresolved issue needs a code and message")
            else:
                errors.extend(source_errors(issue.get("source_ids"), doc))
    lineage = doc.get("upstream_artifact_ids", [])
    if not isinstance(lineage, list) or not all(nonempty(x) for x in lineage) or len(lineage) != len(set(lineage)):
        errors.append("upstream_artifact_ids must contain unique nonempty identifiers")
    return errors


def route(doc):
    errors = validate_input(doc)
    if errors:
        raise ValueError("; ".join(errors))
    intents = list(dict.fromkeys(ALIASES.get(i, i) for i in doc["intents"]))
    findings, steps = deepcopy(doc.get("unresolved_issues", [])), []
    for intent, (scope, key, prefix, code) in SUBJECT_SCOPES.items():
        matching = doc.get('scope_type') == scope and nonempty(doc.get(key)) and doc['household_id'] == prefix + doc[key]
        if intent in intents and not matching:
            findings.append({'code': code, 'message': f'Prepare {key} and scope_type {scope} with household_id {prefix}<{key}>; source identities are not interchangeable.'})
        declared = doc.get('scope_type') == scope or doc['household_id'].startswith(prefix) or key in doc
        if declared and any(i in ROUTES and i != intent for i in intents):
            findings.append({'code': 'separate-subject-requests', 'message': f'Prepare separate reviewed subject requests for targets outside {scope}; never pass a book/family/trust marker as another subject or client identity.'})
    if doc.get('scope_type') == 'prospect-case' and any(i in ROUTES and i != 'prospect-referral' for i in intents):
        findings.append({'code': 'separate-subject-requests', 'message': 'Map the provisional prospect case to a separately reviewed subject request before household, book, family or trust work; prospect identity is not an authenticated client association.'})
    # Protection review precedes routine work when both are expressly requested.
    ordered = ["investor-protection"] + [k for k in ROUTES if k != "investor-protection"]
    for intent in ordered:
        if intent in intents:
            target, needs = ROUTES[intent]
            steps.append({"intent": intent, "target_skill": target, "required_input": needs,
                          "target_category": "asset-management" if intent == "manager-due-diligence" else "wealth-management",
                          "target_scope": SUBJECT_SCOPES[intent][0] if intent in SUBJECT_SCOPES else "prospect-case" if intent == "prospect-referral" else "household",
                          "requested_modes": [i for i in doc["intents"] if ALIASES.get(i, i) == intent],
                          "handoff_status": "prepare-and-validate-target-input",
                          "blocks_on": "Unresolved target-specific required evidence or deployment profile"})
    for intent in intents:
        if intent not in ROUTES:
            findings.append({"code": "human-action-required" if intent in HUMAN_ACTIONS else "outside-priority-scope",
                             "message": f"{intent}: no implemented draft route; clarify scope with the responsible professional."})
    return make_output(SKILL, doc, {
        "input_snapshot": deepcopy(doc), "steps": steps,
        "unrouted_intents": [i for i in intents if i not in ROUTES],
        "routing_only": True,
        "handoff_context": {**{k: deepcopy(doc[k]) for k in ("household_id", "as_of", "engagement", "sources")},
                            **{k: deepcopy(doc[k]) for k in ("scope_type", "book_id", "family_id", "trust_id") if k in doc},
                            "unresolved_issues": deepcopy(doc.get("unresolved_issues", [])),
                            "upstream_artifact_ids": deepcopy(doc.get("upstream_artifact_ids", []))},
    }, findings)


def validate_output(out):
    errors = validate_output_envelope(out, SKILL)
    if errors:
        return errors
    snapshot = out["result"].get("input_snapshot")
    errors = validate_input(snapshot)
    if errors:
        return errors
    return [] if out == route(snapshot) else ["route artifact differs from its bound request"]


def main():
    args = sys.argv[1:]
    if not args:
        print("usage: python scripts/route.py INPUT.json | --validate OUTPUT.json | --selftest")
        return 2
    try:
        if args == ["--selftest"]:
            path = Path(__file__).resolve().parents[1] / "evals/files/request.json"
            out = route(json.loads(path.read_text()))
            assert not validate_output(out)
            print(json.dumps(out, indent=2))
        elif len(args) == 2 and args[0] == "--validate":
            errors = validate_output(json.loads(Path(args[1]).read_text()))
            print(json.dumps({"errors": errors}))
            return int(bool(errors))
        elif len(args) == 1:
            print(json.dumps(route(json.loads(Path(args[0]).read_text())), indent=2))
        else:
            return 2
        return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
