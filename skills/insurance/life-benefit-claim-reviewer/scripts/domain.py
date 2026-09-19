"""Death-benefit claim evidence, beneficiary chronology and amount bridge."""

from domain_support import day, evidence_check, finding, money, num, profile_findings, result, structural


COMPONENTS = (
    "base_benefit",
    "additional_benefits",
    "loan_balance",
    "loan_interest",
    "prior_payments",
    "interest_credit",
)


def validate(doc):
    errors = structural(
        doc,
        objects=("policy", "death", "claim_terms", "amount_bridge"),
        arrays=("beneficiary_records", "evidence"),
        amounts=tuple("amount_bridge." + k for k in COMPONENTS),
        dates=("policy.issue_date", "policy.effective_date", "death.date", "claim_terms.contestability_end"),
    )
    d = doc.get("data", {})
    for record in d.get("beneficiary_records", []) if isinstance(d.get("beneficiary_records"), list) else []:
        if not isinstance(record, dict):
            continue
        beneficiaries = record.get("beneficiaries", [])
        if not isinstance(beneficiaries, list) or not all(isinstance(x, dict) for x in beneficiaries):
            errors.append("beneficiaries must be an array of objects")
            continue
        for b in beneficiaries:
            try:
                num(b.get("share"))
            except ValueError as exc:
                errors.append(str(exc))
    terms = d.get("claim_terms", {})
    if isinstance(terms, dict):
        reqs = terms.get("requirements", [])
        if not isinstance(reqs, list) or not all(isinstance(r, dict) for r in reqs):
            errors.append("claim_terms.requirements must be an array of objects")
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
    return errors


def evaluate(doc):
    d, f = doc["data"], []
    p, death, terms, bridge = [d[k] for k in ("policy", "death", "claim_terms", "amount_bridge")]
    f += profile_findings(doc, terms, "claim_terms")
    identity = bool(
        p.get("policy_id")
        and p.get("insured_id")
        and death.get("insured_id") == p.get("insured_id")
        and p.get("policy_id") == doc["context"]["object_id"]
    )
    if not identity:
        f.append(
            finding(
                "identity_mismatch",
                "Policy, insured, death and context identities do not establish one claim",
                [p.get("source_ref"), death.get("source_ref")],
            )
        )
    for obj, keys in (
        (p, ("policy_id", "insured_id", "source_ref", "currency", "issue_date", "effective_date")),
        (death, ("date", "source_ref")),
        (bridge, ("source_ref",)),
    ):
        for key in keys:
            if not obj.get(key):
                f.append(finding("claim_field_missing", f"Claim field {key} missing", [obj.get("source_ref")]))
    chronology = {
        "contestability_end": terms.get("contestability_end"),
        "death_date": death.get("date"),
        "within_supplied_contestability_window": None,
    }
    try:
        dd = day(death["date"])
        if dd > day(doc["as_of"]) or dd < day(p["effective_date"]) or dd < day(p["issue_date"]):
            f.append(
                finding(
                    "claim_chronology_exception",
                    "Death date conflicts with issue/effective/as_of dates; investigate, do not deny",
                    [p.get("source_ref"), death.get("source_ref")],
                    "review",
                )
            )
        if not any(x["code"].startswith("profile_") for x in f):
            chronology["within_supplied_contestability_window"] = dd <= day(terms["contestability_end"])
            if chronology["within_supplied_contestability_window"]:
                f.append(
                    finding(
                        "contestability_review",
                        "Death falls within supplied contestability window; this requests investigation, not an automatic denial",
                        [terms.get("source_ref"), death.get("source_ref")],
                        "review",
                    )
                )
    except (KeyError, ValueError, TypeError):
        f.append(
            finding(
                "claim_chronology_unknown",
                "Issue/effective/death or supplied contestability dates missing; no universal period assumed",
                [terms.get("source_ref"), death.get("source_ref")],
            )
        )
    requirements = terms.get("requirements", [])
    if not requirements:
        f.append(
            finding(
                "claim_requirements_unknown", "Supply applicable claim-document requirements", [terms.get("source_ref")]
            )
        )
    checks, gaps = evidence_check(
        doc,
        d["evidence"],
        requirements,
        {"policy_id": p.get("policy_id"), "insured_id": p.get("insured_id")},
        terms.get("source_ref"),
    )
    f += gaps
    active, record_checks, record_ids = [], [], set()
    for row in d["beneficiary_records"]:
        usable = bool(
            row.get("record_id")
            and row.get("record_id") not in record_ids
            and row.get("policy_id") == p.get("policy_id")
            and row.get("version")
            and row.get("source_ref")
        )
        record_ids.add(row.get("record_id"))
        try:
            usable = usable and day(row["effective_date"]) <= day(death["date"])
        except (KeyError, ValueError, TypeError):
            usable = False
        record_checks.append(
            {
                "record_id": row.get("record_id"),
                "designation_status": row.get("designation_status"),
                "usable_identity_version_date": usable,
                "source_ref": row.get("source_ref"),
            }
        )
        if row.get("designation_status") == "active" and usable:
            active.append(row)
        elif row.get("designation_status") != "superseded" or not usable:
            f.append(
                finding(
                    "beneficiary_record_exception",
                    "Unresolved beneficiary record retained; no designation inferred",
                    [row.get("source_ref")],
                    "review",
                )
            )
    beneficiary_ok = len(active) == 1 and not any(x["code"] == "beneficiary_record_exception" for x in f)
    if len(active) != 1:
        f.append(
            finding(
                "beneficiary_conflict",
                "Exactly one reviewed active designation at death is needed; conflicting/absent records cannot be ranked by filename",
                [x.get("source_ref") for x in d["beneficiary_records"]],
            )
        )
    beneficiaries = active[0].get("beneficiaries", []) if len(active) == 1 else []
    shares = [num(b.get("share")) for b in beneficiaries]
    if (
        not beneficiaries
        or None in shares
        or sum(shares) != 1
        or any(s < 0 or s > 1 for s in shares)
        or len({b.get("beneficiary_id") for b in beneficiaries}) != len(beneficiaries)
        or any(not b.get("beneficiary_id") for b in beneficiaries)
    ):
        beneficiary_ok = False
        f.append(
            finding(
                "beneficiary_allocation_unknown",
                "Named unique beneficiary shares must be supplied and sum to one",
                [x.get("source_ref") for x in active],
            )
        )
    amounts = {k: num(bridge.get(k)) for k in COMPONENTS}
    net = None
    if (
        None in amounts.values()
        or any(v < 0 for v in amounts.values() if v is not None)
        or bridge.get("currency") != p.get("currency")
        or bridge.get("policy_id") != p.get("policy_id")
        or not bridge.get("source_ref")
        or not identity
    ):
        f.append(
            finding(
                "benefit_bridge_unknown",
                "Same-policy/currency sourced nonnegative amounts, including explicit zero offsets, are required",
                [bridge.get("source_ref"), p.get("source_ref")],
            )
        )
    else:
        net = (
            amounts["base_benefit"]
            + amounts["additional_benefits"]
            + amounts["interest_credit"]
            - amounts["loan_balance"]
            - amounts["loan_interest"]
            - amounts["prior_payments"]
        )
        if net < 0:
            f.append(
                finding(
                    "negative_benefit_bridge",
                    "Offsets exceed supplied benefits; refer for reconciliation",
                    [bridge.get("source_ref")],
                    "review",
                )
            )
    allocation = (
        [
            {
                "beneficiary_id": b["beneficiary_id"],
                "share": money(num(b["share"])),
                "illustrative_share": money(net * num(b["share"])),
            }
            for b in beneficiaries
        ]
        if beneficiary_ok and net is not None and net >= 0
        else None
    )
    return result(
        f,
        {
            "policy_id": p.get("policy_id"),
            "claim_id": doc["case_id"],
            "document_checks": checks,
            "chronology": chronology,
            "beneficiary_record_checks": record_checks,
            "benefit_bridge": {
                "currency": p.get("currency"),
                **{k: money(v) for k, v in amounts.items()},
                "illustrative_net_before_entitlement": money(net),
                "source_ref": bridge.get("source_ref"),
            },
            "illustrative_allocation": allocation,
            "beneficiary_entitlement_determined": False,
            "pay_or_deny_decision": None,
        },
    )
