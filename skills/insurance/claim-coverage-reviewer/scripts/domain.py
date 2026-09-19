from native_helpers import data, date, finding, pack, profile, refs, txt, unique, validate_with


def evaluate(doc):
    d = data(doc)
    f = []
    profile(doc, f)
    p = d.get("policy", {})
    refs(doc, p, f, "policy")
    for key in ("policy_id", "insured_id", "wording_version", "coverage_trigger"):
        if not txt(p.get(key)):
            finding(f, "policy-gap", key + " required")
    if p.get("coverage_trigger") not in {"occurrence", "claims_made", "other"}:
        finding(f, "trigger-gap", "Coverage trigger must be explicitly identified")
    if not txt(d.get("reported_insured_id")):
        finding(f, "insured-gap", "Reported insured identity required")
    elif d["reported_insured_id"] != p.get("insured_id"):
        finding(
            f,
            "insured-mismatch",
            "Reported insured differs from policy insured; establish insured status",
            p.get("source_refs", []),
            "review",
        )
    start = date(p.get("effective"))
    end = date(p.get("expiry"))
    loss = date(d.get("loss_date"))
    within = None
    if start is None or end is None or loss is None or start >= end:
        finding(f, "date-gap", "Policy interval and loss date required")
    else:
        within = start <= loss < end
        if not within:
            finding(
                f,
                "date-review",
                "Loss date falls outside supplied half-open policy interval; investigate applicability",
                p.get("source_refs", []),
                "review",
            )
    if p.get("coverage_trigger") == "claims_made":
        for key in ("claim_made_date", "reported_date", "retroactive_date"):
            if date(d.get(key)) is None:
                finding(f, "trigger-gap", key + " required for claims-made analysis")
        finding(
            f,
            "claims-made-review",
            "Claims-made terms, reporting provisions and extensions require specialist interpretation",
            p.get("source_refs", []),
            "review",
        )
    facts = d.get("facts", [])
    clauses = d.get("clauses", [])
    hypotheses = d.get("hypotheses", [])
    unique(facts, "fact_id")
    unique(clauses, "clause_id")
    unique(hypotheses, "hypothesis_id")
    factids = {r["fact_id"] for r in facts}
    clauseids = {r["clause_id"] for r in clauses}
    for label, rows in [("fact", facts), ("clause", clauses)]:
        for r in rows:
            refs(doc, r, f, r[label + "_id"])
            if not txt(r.get("quote")):
                finding(f, "quote-gap", r[label + "_id"] + ": source quote missing", r.get("source_refs", []))
    if not hypotheses:
        finding(f, "hypothesis-gap", "Coverage hypotheses and competing interpretations required")
    matrix = []
    for h in hypotheses:
        linked = refs(doc, h, f, h["hypothesis_id"])
        used = h.get("clause_ids", [])
        supporting = h.get("supporting_fact_ids", [])
        contrary = h.get("contrary_fact_ids", [])
        if any(x not in clauseids for x in used) or any(x not in factids for x in supporting + contrary):
            raise ValueError("hypothesis references unknown clause or fact")
        if not used or not supporting:
            finding(
                f,
                "evidence-gap",
                h["hypothesis_id"] + ": policy and supporting facts required",
                h.get("source_refs", []),
            )
        if h.get("contrary_evidence_reviewed") is not True:
            finding(f, "contrary-gap", h["hypothesis_id"] + ": contrary evidence search is not documented")
        if contrary:
            finding(
                f,
                "conflicting-evidence",
                h["hypothesis_id"] + ": contrary facts retained for review",
                h.get("source_refs", []),
                "review",
            )
        if h.get("effect") not in {
            "potential_grant",
            "potential_exclusion",
            "potential_exception",
            "condition",
            "unknown",
        }:
            raise ValueError("hypothesis effect invalid")
        matrix.append({**h, "assessment": "hypothesis_for_review", "source_linked": linked})
    return pack(
        {
            "policy_id": p.get("policy_id"),
            "loss_within_supplied_period": within,
            "facts": facts,
            "clauses": clauses,
            "coverage_hypotheses": matrix,
            "coverage_determination": "not_made",
            "reservation_of_rights": "not_issued",
            "decision_owner": "authorized claims coverage specialist",
        },
        f,
    )


def validate(doc):
    return validate_with(evaluate, doc)
