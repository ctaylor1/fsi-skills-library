from native_helpers import data, finding, pack, profile, refs, txt, unique, validate_with


def evaluate(doc):
    d = data(doc)
    f = []
    profile(doc, f)
    for key in ("product_name", "target_market", "coverage_basis"):
        if not txt(d.get(key)):
            finding(f, "design-gap", key + " required")
    channels = d.get("distribution_channels", [])
    if not isinstance(channels, list) or not channels or any(not txt(x) for x in channels):
        finding(f, "channel-gap", "Distribution channels and participant responsibilities unknown")
    features = d.get("features", [])
    requirements = d.get("requirements", [])
    unique(features, "feature_id")
    unique(requirements, "requirement_id")
    if not features:
        finding(f, "feature-gap", "No product features supplied")
    matrix = []
    for r in features:
        linked = refs(doc, r, f, r["feature_id"])
        missing = [k for k in ("promise", "wording_ref", "operational_owner") if not txt(r.get(k))]
        if missing:
            finding(
                f, "feature-gap", r["feature_id"] + ": " + ", ".join(missing) + " unknown", r.get("source_refs", [])
            )
        test = r.get("claims_test_status", "unknown")
        if test not in {"pass", "fail", "unknown"}:
            raise ValueError("claims_test_status invalid")
        if test != "pass":
            finding(
                f,
                "claims-test",
                r["feature_id"] + ": claims operation test " + test,
                r.get("source_refs", []),
                "review" if test == "fail" else "gap",
            )
        matrix.append({**r, "traceability": "complete" if linked and not missing else "partial"})
    categories = set()
    for r in requirements:
        category = r.get("category")
        categories.add(category)
        if category not in {"actuarial", "wording", "distribution", "operations", "filing"}:
            raise ValueError("requirement category invalid")
        if not isinstance(r.get("required"), bool):
            raise ValueError("required must be a boolean")
        state = r.get("status", "unknown")
        if state not in {"satisfied", "unsatisfied", "unknown"}:
            raise ValueError("requirement status invalid")
        refs(doc, r, f, r["requirement_id"])
        if r["required"] and state != "satisfied":
            finding(
                f,
                "requirement-open",
                r["requirement_id"] + ": " + state,
                r.get("source_refs", []),
                "review" if state == "unsatisfied" else "gap",
            )
    for cat in sorted({"actuarial", "wording", "distribution", "operations", "filing"} - categories):
        finding(f, "scope-gap", cat + " review scope not documented")
    return pack(
        {
            "feature_matrix": matrix,
            "requirement_matrix": requirements,
            "review_scope": sorted(categories),
            "launch_authorized": False,
            "product_approval": "not_determined",
            "next_owner": "product governance",
        },
        f,
    )


def validate(doc):
    return validate_with(evaluate, doc)
