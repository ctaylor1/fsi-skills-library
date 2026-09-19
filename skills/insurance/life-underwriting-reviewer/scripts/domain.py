"""Life underwriting evidence and financial referral preparation."""

from domain_support import evidence_check, finding, money, num, profile_findings, result, structural


def validate(doc):
    errors = structural(
        doc,
        objects=("application", "criteria"),
        arrays=("evidence", "disclosures"),
        amounts=(
            "application.coverage_amount",
            "application.existing_coverage",
            "application.annual_income",
            "criteria.financial_multiple_limit",
        ),
    )
    d = doc.get("data", {})
    criteria = d.get("criteria", {})
    if not isinstance(criteria, dict):
        return errors
    reqs = criteria.get("requirements", [])
    if not isinstance(reqs, list) or not all(isinstance(r, dict) for r in reqs):
        errors.append("criteria.requirements must be an array of objects")
    else:
        ids = [r.get("requirement_id") for r in reqs]
        for req in reqs:
            if (
                not isinstance(req.get("requirement_id"), str)
                or not req.get("requirement_id")
                or ids.count(req.get("requirement_id")) != 1
                or not isinstance(req.get("document_type"), str)
                or not req.get("document_type")
            ):
                errors.append("each requirement needs a unique requirement_id and document_type")
            if req.get("max_age_days") is not None and (
                isinstance(req["max_age_days"], bool)
                or not isinstance(req["max_age_days"], int)
                or req["max_age_days"] < 0
            ):
                errors.append("max_age_days must be a nonnegative integer")
            if req.get("kind") not in ("medical", "financial"):
                errors.append("requirement kind must be medical or financial")
    return errors


def evaluate(doc):
    d, f = doc["data"], []
    app, criteria = d["application"], d["criteria"]
    f += profile_findings(doc, criteria, "criteria")
    for key in ("application_id", "applicant_id", "currency", "purpose", "source_ref"):
        if not app.get(key):
            f.append(finding("application_gap", f"application.{key} missing", [app.get("source_ref")]))
    if app.get("application_id") != doc["context"]["object_id"]:
        f.append(finding("identity_mismatch", "Application differs from context object", [app.get("source_ref")]))
    reqs = criteria.get("requirements", [])
    if not reqs or {r.get("kind") for r in reqs} != {"medical", "financial"}:
        f.append(
            finding(
                "criteria_coverage_gap",
                "Supply explicit medical and financial evidence requirements; zero requirements is not completeness",
                [criteria.get("source_ref")],
            )
        )
    checks, gaps = evidence_check(
        doc,
        d["evidence"],
        reqs,
        {"application_id": app.get("application_id"), "applicant_id": app.get("applicant_id")},
        criteria.get("source_ref"),
    )
    f += gaps
    discrepancies = []
    known_evidence = {e.get("evidence_id"): e for e in d["evidence"]}
    for item in d["disclosures"]:
        evidence = known_evidence.get(item.get("evidence_id"))
        discrepancy = item.get("application_value") != item.get("evidence_value")
        provenance_ok = bool(
            evidence
            and evidence.get("applicant_id") == app.get("applicant_id")
            and evidence.get("application_id") == app.get("application_id")
        )
        discrepancies.append({**item, "values_differ": discrepancy, "identity_linked": provenance_ok})
        if not provenance_ok:
            f.append(
                finding(
                    "disclosure_unlinked",
                    f"Disclosure {item.get('topic')} has no identity-linked evidence",
                    [item.get("source_ref")],
                )
            )
        if discrepancy:
            f.append(
                finding(
                    "disclosure_conflict",
                    f"Reviewer must reconcile differing supplied values for {item.get('topic')}; no medical inference made",
                    [item.get("source_ref"), evidence.get("source_ref") if evidence else None],
                    "review",
                )
            )
    coverage, existing, income = [num(app.get(k)) for k in ("coverage_amount", "existing_coverage", "annual_income")]
    limit = num(criteria.get("financial_multiple_limit"))
    multiple = None
    if (
        None in (coverage, existing, income, limit)
        or any(v < 0 for v in (coverage, existing, income, limit) if v is not None)
        or income == 0
    ):
        f.append(
            finding(
                "financial_inputs_unknown",
                "Coverage, existing coverage, positive income and supplied nonnegative referral threshold needed",
                [app.get("source_ref"), criteria.get("source_ref")],
            )
        )
    elif any(x["code"].startswith("profile_") for x in f):
        f.append(
            finding(
                "financial_profile_unusable",
                "Financial referral comparison withheld for unusable criteria profile",
                [criteria.get("source_ref")],
            )
        )
    else:
        multiple = (coverage + existing) / income
        if multiple > limit:
            f.append(
                finding(
                    "financial_referral",
                    "Total disclosed coverage / disclosed annual income exceeds supplied referral multiple; investigate financial justification",
                    [app.get("source_ref"), criteria.get("source_ref")],
                    "review",
                )
            )
    return result(
        f,
        {
            "application_id": app.get("application_id"),
            "applicant_id": app.get("applicant_id"),
            "evidence_checks": checks,
            "disclosure_reconciliation": discrepancies,
            "financial_review": {
                "currency": app.get("currency"),
                "total_coverage_to_income": money(multiple),
                "supplied_referral_threshold": money(limit),
                "basis": "disclosed amounts; no income authentication",
            },
            "referral_reasons": [x["code"] for x in f],
            "risk_class": None,
            "medical_diagnosis": None,
            "issue_decision": None,
        },
    )
