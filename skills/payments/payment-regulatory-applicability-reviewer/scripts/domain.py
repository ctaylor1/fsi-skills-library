"""Payment perimeter and obligation triage; not a legal opinion or permission check."""
from datetime import date
from payment_contract import stable_hash
from payment_foundation import finding, load_resource

SKILL = "payment-regulatory-applicability-reviewer"
SERVICE_TYPES = {"credit-transfer", "direct-debit", "payment-initiation", "account-information", "money-remittance", "e-money-issuance", "acquiring", "card-issuing", "technical-processing"}
ENTITY_TYPES = {"bank", "payment-institution", "e-money-institution", "nonbank", "merchant", "agent", "technical-provider"}
SOURCES = {
    "US": ["https://www.fincen.gov/resources/money-services-business-msb-registration", "https://www.consumerfinance.gov/rules-policy/regulations/1005/", "https://www.consumerfinance.gov/rules-policy/regulations/1026/"],
    "EA": ["https://eur-lex.europa.eu/eli/dir/2015/2366/oj/eng", "https://eur-lex.europa.eu/eli/reg/2024/886/oj/eng"],
    "UK": ["https://www.fca.org.uk/firms/payment-services-regulations-e-money-regulations", "https://www.fca.org.uk/firms/emi-payment-institutions-safeguarding-requirements", "https://www.fca.org.uk/consumers/fraudulent-payments"],
}


def validate(data):
    errors = []
    for key in ("entity", "activity"):
        if key in data and not isinstance(data[key], dict):
            errors.append(key + " must be an object")
    for key in ("funds_flow", "legal_reviews"):
        if key in data and (not isinstance(data[key], list) or any(not isinstance(x, dict) for x in data[key])):
            errors.append(key + " must be an object list")
    for review in data.get("legal_reviews", []) if isinstance(data.get("legal_reviews", []), list) else []:
        if isinstance(review, dict):
            for key in ("reviewed_on", "review_due"):
                if key in review:
                    try:
                        date.fromisoformat(review[key])
                    except (ValueError, TypeError):
                        errors.append(key + " must be an ISO date")
    activity = data.get("activity", {})
    if isinstance(activity, dict):
        for key in ("services", "countries", "us_states"):
            if key in activity and (not isinstance(activity[key], list) or any(not isinstance(x, str) for x in activity[key])):
                errors.append(key + " must be a string list")
        if "holds_client_funds" in activity and activity["holds_client_funds"] not in (True, False, None):
            errors.append("holds_client_funds must be boolean or null")
    return errors


def analyze(request):
    data, jur = request["data"], request["jurisdiction"]
    if not "2026-09-18" <= request["as_of"] <= "2026-10-18":
        return {"result": {"applicability_matrix": [], "consumer_error_profiles": []},
                "findings": [finding("profile-date-unresolved", "Bundled regulatory orientation was reviewed 2026-09-18 and requires refresh after 2026-10-18; no retrospective/current-law conclusion is inferred.")], "handoffs": []}
    entity, activity = data.get("entity", {}), data.get("activity", {})
    findings, matrix = [], []
    entity_sources, activity_sources = entity.get("source_ids", []), activity.get("source_ids", [])
    source_ids = list(dict.fromkeys(entity_sources + activity_sources))
    kind = entity.get("kind")
    services = set(activity.get("services", []))
    if kind not in ENTITY_TYPES or not entity.get("legal_entity_id") or not entity.get("home_country") or not entity_sources:
        findings.append(finding("entity-scope-incomplete", "Identify the legal entity, entity type, home country and evidence; a provider brand is not a legal entity.", entity_sources))
    if not services or services - SERVICE_TYPES or not activity_sources:
        findings.append(finding("activity-scope-incomplete", "Describe supported services with evidence; unknown activity types need specialist mapping.", activity_sources))
    customers = activity.get("customer_type")
    if customers not in {"consumer", "business", "mixed"}:
        findings.append(finding("customer-scope-incomplete", "Consumer and business scope must be distinguished.", activity_sources))
    countries = activity.get("countries", [])
    if not countries:
        findings.append(finding("territorial-scope-incomplete", "List establishment, payer, payee and service-delivery countries before determining territorial obligations.", activity_sources))
    if jur == "US" and any(c != "US" for c in countries) or jur == "UK" and any(c not in {"GB", "UK"} for c in countries):
        findings.append(finding("cross-border-overlay", "This domestic profile cannot resolve the other countries' licensing, consumer or cross-border requirements.", activity_sources))
    if jur == "EA" and not activity.get("national_profile_ref"):
        findings.append(finding("national-transposition-required", "PSD2 is a framework; supply applicable national law and regulator/perimeter review for each country.", activity_sources))
    holds = activity.get("holds_client_funds")
    if type(holds) is not bool:
        findings.append(finding("custody-unknown", "Identify who receives, owns, holds and owes customer funds; do not infer a technical-service exclusion.", activity_sources))
    flows = data.get("funds_flow", [])
    flow_ids = set()
    for flow in flows:
        if not flow.get("flow_id") or flow.get("flow_id") in flow_ids:
            findings.append(finding("flow-identity", "Funds-flow identifiers must be present and unique.", flow.get("source_ids", [])))
        flow_ids.add(flow.get("flow_id"))
        if any(not flow.get(k) for k in ("from_entity", "to_entity", "holder", "customer_claim_against", "source_ids")):
            findings.append(finding("flow-ownership-incomplete", "Each flow needs sender/receiver, holder, customer claim and evidence.", flow.get("source_ids", [])))
    if not flows and holds is not False:
        findings.append(finding("funds-flow-missing", "Customer-fund custody cannot be assessed without an ownership and liability flow.", activity_sources))

    def obligation(ident, topic, condition, analysis, source_refs, required):
        reviews = [r for r in data.get("legal_reviews", []) if r.get("obligation_id") == ident]
        review = reviews[0] if len(reviews) == 1 else {}
        matched = (review.get("entity_id") == entity.get("legal_entity_id") and review.get("jurisdiction") == jur
                   and review.get("reviewer") and review.get("reference") and review.get("source_ids")
                   and review.get("scope_hash") == stable_hash({"entity": entity, "activity": activity})
                   and review.get("reviewed_on", "9999") <= request["as_of"] <= review.get("review_due", ""))
        if not matched:
            findings.append(finding("legal-review:" + ident, "Obligation requires scoped specialist review: " + topic, source_ids))
        matrix.append({"obligation_id": ident, "topic": topic, "condition": condition, "assessment": "candidate-obligation-for-review",
                       "analysis": analysis, "source_ids": source_ids, "authority_refs": source_refs,
                       "evidence_needed": required, "review_status": "supplied-scoped-review" if matched else "unresolved",
                       "review": review if matched else None, "legal_conclusion_verified": False})

    refs = SOURCES[jur]
    if jur == "US":
        if kind not in {"bank", "merchant"} and services & {"credit-transfer", "money-remittance", "e-money-issuance", "payment-initiation"}:
            obligation("us-money-services", "Money services / money transmission perimeter", "Nonbank payment service activity", "FinCEN MSB registration and BSA assessment are distinct from state money-transmitter licensing; neither a bank partner nor registration alone establishes permissions.", [refs[0]], ["activity/exemption analysis", "FinCEN/BSA scope", "state licensing or exemption evidence"])
            if not activity.get("us_states"):
                findings.append(finding("state-scope-missing", "U.S. state licensing coverage needs the relevant state footprint; no nationwide license is inferred.", activity_sources))
        if customers in {"consumer", "mixed"}:
            obligation("us-consumer", "Consumer payment and credit protections", "Consumer or mixed customer base", "Map covered EFT/debit/prepaid activity to Regulation E and consumer open-end credit billing errors to Regulation Z. Commercial status, excluded wires and remittances need separate scope review.", refs[1:], ["account/product type", "consumer notice and disclosures", "error and liability process"])
        obligation("us-funds-model", "Customer funds and partner responsibilities", "Declared payment activity", "Determine the legal holder and obligor, applicable custody/state requirements and any bank-partner responsibilities; a funds-flow drawing does not establish deposit insurance.", [refs[0]], ["executed partner agreements", "ownership and insolvency analysis", "customer disclosures"])
    else:
        obligation(jur.lower() + "-permissions", "Payment/e-money perimeter and permissions", "Payment or e-money activity", "Compare the precise service and legal entity against its permissions, agency arrangement or reviewed exclusion. A technical provider that never holds funds still needs an evidenced perimeter assessment.", [refs[0]], ["service classification", "regulator register and exact permissions", "agent/principal responsibilities"])
        if holds is not False or "e-money-issuance" in services:
            obligation(jur.lower() + "-safeguarding", "Safeguarding customer funds", "Holding relevant customer funds or e-money issuance", "Identify relevant funds and the entity's safeguarding regime; a bank deposit model and a payment/e-money safeguarding model are different. UK review includes current FCA CASS/SUP requirements, not only old PSR summaries." if jur == "UK" else "Assess PSD2/e-money and national safeguarding duties for the actual fund holder and permission model; do not apply a bank-deposit model to payment-institution funds.", [refs[1] if jur == "UK" else refs[0]], ["relevant-funds classification", "safeguarding accounts/guarantee", "reconciliation and insolvency treatment"])
        if customers in {"consumer", "mixed"}:
            obligation(jur.lower() + "-consumer", "Consent, execution, error and liability protections", "Consumer payment service", "Keep unauthorized payment review, authorized scams and direct-debit refund rights separate; authentication does not itself establish customer authority.", [refs[-1] if jur == "UK" else refs[0]], ["authorization/consent evidence", "notice and error process", "applicable national/product exceptions"])
        if services & {"credit-transfer", "payment-initiation", "acquiring", "card-issuing", "account-information"}:
            obligation(jur.lower() + "-authentication", "Authentication and payment initiation controls", "Electronic payment/account access activity", "Assess applicable strong customer authentication, exemptions and secure communication obligations against the actual flow; an exemption or API credential is not payer consent.", [refs[0]], ["channel and actor roles", "consent and revocation", "authentication/exemption legal basis"])
        if jur == "EA" and "credit-transfer" in services:
            obligation("ea-instant", "Instant euro transfer obligations", "Euro credit-transfer provider activity", "Map the Instant Payments Regulation by provider type, currency, location and phased effective date; a scheme participant listing alone does not establish all obligations or exceptions.", [refs[1]], ["provider type", "national/currency scope", "current effective-date and verification-of-payee assessment"])

    profiles = load_resource("consumer-error-profiles.json")["profiles"]
    selected = [p for p in profiles.values() if jur in p["jurisdictions"] and activity.get("customer_product") in p["products"]]
    if customers in {"consumer", "mixed"} and not selected:
        findings.append(finding("consumer-product-profile-unresolved", "Supply the specific consumer product before choosing an error-resolution profile.", activity_sources))
    return {"result": {"entity": entity, "activity": activity, "funds_flow": flows, "applicability_matrix": matrix,
                       "consumer_error_profiles": selected, "conclusion": "Candidate obligations and decision dependencies for specialist review; no legal clearance or permission granted.",
                       "excluded_conclusions": ["licensed", "exempt", "compliant", "deposit-insured", "customer-liability-determined"]},
            "findings": findings, "handoffs": [
                {"target_skill": "payment-initiation-control-reviewer", "reason": "Apply reviewed authority and control requirements to exact proposed instructions.", "required_inputs": ["entity/activity review", "exact instruction", "unresolved applicability issues"]},
                {"target_skill": "issuer-payment-dispute-reviewer", "reason": "Review consumer-error cases under separately scoped legal and scheme profiles.", "required_inputs": ["customer product and claim", "reviewed legal profile", "trigger evidence and clocks"]},
                {"target_skill": "sanctions-match-adjudicator", "reason": "Resolve sanctions matches through the shared specialist when present.", "required_inputs": ["match evidence", "payment parties", "current screening sources"]}],
            "limitations": ["FinCEN registration is not a state license; safeguarding is not deposit insurance; scheme recovery is not statutory redress."]}
