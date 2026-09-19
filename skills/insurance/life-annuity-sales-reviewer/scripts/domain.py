"""Assemble product-specific evidence for a qualified sales/supervisory reviewer."""

from domain_support import evidence, fields, finding, finish, known, profile, profile_errors, refs, shape, unique

PRODUCTS = {
    "fixed-annuity",
    "fixed-indexed-annuity",
    "deferred-variable-annuity",
    "variable-life",
    "term-life",
    "permanent-life",
}
CONSUMER = (
    "insurance-needs",
    "financial-objectives",
    "liquidity-needs",
    "funding-source",
    "financial-capacity",
    "age",
    "time-horizon",
    "risk-tolerance",
    "financial-experience",
    "tax-status",
)
PRODUCT = (
    "charges",
    "surrender-terms",
    "guarantees",
    "non-guaranteed-elements",
    "restrictions",
    "death-benefit",
    "compensation-and-conflicts",
    "disclosures-and-training",
)
REPLACEMENT = (
    "existing-values",
    "existing-benefits",
    "existing-charges",
    "new-charges",
    "lost-guarantees",
    "new-surrender-period",
    "replacement-rationale",
    "retain-or-modify-alternative",
    "replacement-disclosures",
)


def validate(doc):
    errors = shape(
        doc,
        ("consumer_evidence", "product_evidence", "alternatives", "replacement_evidence", "applicability"),
        ("profile", "transaction", "recommendation_rationale"),
    )
    if errors:
        return errors
    d = doc["data"]
    errors += profile_errors(doc)
    if d.get("transaction", {}).get("product_type") not in PRODUCTS | {None}:
        errors.append("unsupported product_type; route to a specialist profile")
    if d.get("transaction", {}).get("replacement_status") not in ("yes", "no", "unknown", None):
        errors.append("replacement_status must be yes/no/unknown")
    for k in ("consumer_evidence", "product_evidence", "replacement_evidence"):
        errors += fields(d.get(k, []), dates=("verified_on",))
        if any("value" in r and isinstance(r["value"], (list, dict)) for r in d.get(k, [])):
            errors.append(
                k + " values must be scalar reviewed summaries, with detailed source evidence separately identified"
            )
    errors += fields([d.get("recommendation_rationale", {})], dates=("verified_on",))
    errors += fields(d.get("alternatives", []), dates=("verified_on",))
    if d.get("applicability") and not unique(d["applicability"], "rule_id"):
        errors.append("rule_id applicability must be unique")
    errors += fields(d.get("applicability", []), lists=("product_types", "distribution_channels"))
    errors += fields([d.get("profile", {})], lists=("product_types",))
    p = d.get("profile", {})
    for k in ("additional_consumer_topics", "additional_product_topics"):
        if k in p and (not isinstance(p[k], list) or any(not isinstance(v, str) for v in p[k])):
            errors.append(k + " must list topic strings")
    return errors


def _matrix(doc, rows, topics, p, label, findings):
    result = []
    for topic in dict.fromkeys(topics):
        matches = [r for r in rows if r.get("topic") == topic]
        problems = []
        row = matches[0] if len(matches) == 1 else {}
        if len(matches) != 1:
            problems.append(
                "missing evidence" if not matches else "conflicting/duplicate topic evidence requires reconciliation"
            )
        else:
            problems += evidence(doc, row, p.get("max_evidence_age_days"))
            if row.get("value") is None or row.get("value") == "":
                problems.append("value unknown")
            if p.get("max_evidence_age_days") is None:
                problems.append("freshness interval is unconfigured")
        result.append(
            {
                "topic": topic,
                "status": "missing-or-unresolved" if problems else "evidence-present",
                "value": row.get("value") if not problems else None,
                "source_refs": list(dict.fromkeys(x for r in matches for x in refs(r))),
                "issues": problems,
            }
        )
        if problems:
            findings.append(
                finding(label + "-evidence", topic + ": " + "; ".join(problems), [x for r in matches for x in refs(r)])
            )
    return result


def evaluate(doc):
    d = doc["data"]
    p, findings = profile(doc)
    t = d.get("transaction", {})
    product = t.get("product_type")
    annuity = product in {"fixed-annuity", "fixed-indexed-annuity", "deferred-variable-annuity"}
    variable = product in {"deferred-variable-annuity", "variable-life"}
    bd = t.get("distribution_channel") == "registered-broker-dealer"
    if not product:
        findings.append(
            finding("product-classification", "Product type must be established before selecting the review standard.")
        )
    if not t.get("distribution_channel"):
        findings.append(
            finding("distribution-channel", "Distribution channel and recommending capacity must be established.")
        )
    if t.get("jurisdiction") != doc["context"]["jurisdiction"]:
        findings.append(finding("jurisdiction-mismatch", "Transaction jurisdiction must match the review context."))
    if product and product not in p.get("product_types", []):
        findings.append(finding("product-profile", "Reviewed profile does not establish this product type."))
    topics = list(CONSUMER) + p.get("additional_consumer_topics", [])
    product_topics = (
        list(PRODUCT)
        + (["annuitization-options", "riders"] if annuity else ["premium-obligations", "coverage-duration"])
        + p.get("additional_product_topics", [])
    )
    consumer = _matrix(doc, d.get("consumer_evidence", []), topics, p, "consumer", findings)
    products = _matrix(doc, d.get("product_evidence", []), product_topics, p, "product", findings)
    alternatives = []
    if not d.get("alternatives"):
        findings.append(
            finding(
                "alternatives-missing", "No documented considered alternatives or reasons for comparison were supplied."
            )
        )
    for alt in d.get("alternatives", []):
        problems = evidence(doc, alt, p.get("max_evidence_age_days"))
        if not alt.get("reason_reviewed"):
            problems.append("reason for consideration missing")
        alternatives.append(
            {
                "alternative_id": alt.get("alternative_id"),
                "description": alt.get("description"),
                "reason_reviewed": alt.get("reason_reviewed"),
                "status": "unresolved" if problems else "documented",
                "issues": problems,
                "source_refs": refs(alt),
            }
        )
        if problems:
            findings.append(finding("alternative-evidence", "; ".join(problems), refs(alt)))
    rationale = d.get("recommendation_rationale", {})
    rationale_issues = evidence(doc, rationale, p.get("max_evidence_age_days"))
    if not rationale.get("text"):
        rationale_issues.append("source-backed recommendation rationale absent")
    if rationale_issues:
        findings.append(finding("rationale-evidence", "; ".join(rationale_issues), refs(rationale)))
    replacement = t.get("replacement_status")
    replacement_matrix = []
    if replacement not in ("yes", "no"):
        findings.append(
            finding(
                "replacement-unknown",
                "Existing contracts, planned dispositions and financed purchases must establish replacement status.",
            )
        )
    elif not known(doc, t.get("replacement_source_ref")):
        findings.append(finding("replacement-unsubstantiated", "Replacement declaration has no registered evidence."))
    if replacement == "yes":
        replacement_matrix = _matrix(doc, d.get("replacement_evidence", []), REPLACEMENT, p, "replacement", findings)
    rules = ["state-sales-standard", "state-replacement"]
    if variable:
        rules += ["finra-2320", "finra-2330", "regulation-bi"]
    rules = list(dict.fromkeys(rules + [r["rule_id"] for r in d.get("applicability", [])]))
    applicability = []
    for rule in rules:
        rows = [r for r in d.get("applicability", []) if r.get("rule_id") == rule]
        row = rows[0] if rows else {}
        state = row.get("status")
        reasons = []
        if state not in ("applies", "not-applicable"):
            reasons.append("applicability unresolved")
        if not known(doc, row.get("source_ref")) or not row.get("rationale"):
            reasons.append("applicability needs source and rationale")
        if row.get("authority_type") not in ("enacted-law", "regulator-rule", "institution-policy"):
            reasons.append("model text alone does not establish applicability")
        if product not in row.get("product_types", []) or t.get("distribution_channel") not in row.get(
            "distribution_channels", []
        ):
            reasons.append("applicability scope does not cover product/channel")
        if rule == "finra-2330" and state == "applies" and (product != "deferred-variable-annuity" or not bd):
            reasons.append("FINRA 2330 profile is inconsistent with deferred variable annuity/member scope")
        if rule in ("finra-2320", "regulation-bi") and state == "applies" and not bd:
            reasons.append("broker-dealer/member capacity must be established")
        applicability.append(
            {"rule_id": rule, "status": "unknown" if reasons else state, "issues": reasons, "source_refs": refs(row)}
        )
        if reasons:
            findings.append(finding("rule-applicability", rule + ": " + "; ".join(reasons), refs(row)))
    return finish(
        {
            "product_type": product,
            "consumer_matrix": consumer,
            "product_matrix": products,
            "alternatives": alternatives,
            "replacement_status": replacement or "unknown",
            "replacement_matrix": replacement_matrix,
            "applicability_matrix": applicability,
            "recommendation_rationale": None if rationale_issues else rationale["text"],
            "suitability_or_best_interest_decision": "not-made",
            "principal_approval": "not-performed",
        },
        findings,
    )
