"""Reconcile supplied producer evidence against a reviewed, explicit scope."""

from domain_support import day, evidence, fields, finding, finish, known, profile, profile_errors, refs, shape, unique


def validate(doc):
    errors = shape(doc, ("entities", "requirements", "licenses", "appointments"), ("profile",))
    if errors:
        return errors
    d = doc["data"]
    errors += profile_errors(doc)
    for k in ("entities", "requirements"):
        if d.get(k) and not unique(d[k], "entity_id" if k == "entities" else "requirement_id"):
            errors.append(f"{k} identifiers must be unique nonempty strings")
    errors += fields(
        d.get("licenses", []) + d.get("appointments", []),
        dates=("effective_from", "effective_to", "verified_on"),
        booleans=("non_expiring",),
    )
    errors += fields(d.get("requirements", []), booleans=("license_required", "appointment_required"))
    return errors


def _check(doc, rows, req, kind, p, entity):
    keys = ("entity_id", "jurisdiction", "line_of_authority") + (("carrier_id",) if kind == "appointment" else ())
    matched = [r for r in rows if all(r.get(k) == req.get(k) and req.get(k) for k in keys)]
    result = {
        "kind": kind,
        "status": "unknown",
        "record_ids": [r.get("record_id") for r in matched],
        "source_refs": list(dict.fromkeys(x for r in matched for x in refs(r))),
        "reasons": [],
    }
    required = req.get(kind + "_required")
    if req.get("jurisdiction") not in p.get("jurisdictions", []) or not req.get("line_of_authority"):
        result["reasons"].append("requested jurisdiction/line scope is not established")
        return result
    if required is None:
        result["reasons"].append("requirement applicability is not established")
        return result
    if not known(doc, req.get("rule_source_ref")):
        result["reasons"].append("requirement has no registered rule source")
        return result
    if required is False:
        result["status"] = "not-required-by-supplied-profile"
        return result
    if len(matched) != 1:
        result["reasons"].append(
            "no matching record" if not matched else "multiple matching records require reconciliation"
        )
        return result
    row = matched[0]
    reasons = evidence(doc, row, p.get("max_evidence_age_days"))
    if p.get("max_evidence_age_days") is None:
        reasons.append("freshness interval has not been configured")
    if not entity or not entity.get("legal_name") or row.get("entity_name") != entity.get("legal_name"):
        reasons.append("entity legal name does not reconcile")
    if not row.get("effective_from"):
        reasons.append("effective date missing")
    if not row.get("effective_to") and row.get("non_expiring") is not True:
        reasons.append("expiration or explicit non-expiring status missing")
    if reasons:
        result["reasons"] = reasons
        return result
    asof = day(doc["as_of"])
    if row.get("status") not in ("active", "inactive", "suspended", "revoked", "terminated"):
        result["reasons"] = ["record status unknown"]
        return result
    result["status"] = "observed-match"
    if row["status"] != "active":
        result["status"] = "observed-exception"
        result["reasons"].append("record is " + row["status"])
    if day(row["effective_from"]) > asof:
        result["status"] = "observed-exception"
        result["reasons"].append("not yet effective")
    if row.get("effective_to") and day(row["effective_to"]) < asof:
        result["status"] = "observed-exception"
        result["reasons"].append("expired")
    return result


def evaluate(doc):
    d = doc["data"]
    p, findings = profile(doc)
    results = []
    entities = {r["entity_id"]: r for r in d.get("entities", [])}
    if not d.get("requirements"):
        findings.append(finding("scope-missing", "No entity/jurisdiction/line requirements were supplied."))
    if not entities:
        findings.append(
            finding(
                "entities-missing", "Producer individual and applicable business-entity identities are not established."
            )
        )
    for req in d.get("requirements", []):
        checks = []
        for kind, collection in [("license", "licenses"), ("appointment", "appointments")]:
            check = _check(doc, d.get(collection, []), req, kind, p, entities.get(req.get("entity_id")))
            if (
                findings
                and any(f["code"] == "profile-review" for f in findings)
                and check["status"].startswith("observed-")
            ):
                check["status"] = "unknown"
                check["reasons"].append("review profile applicability unresolved")
            checks.append(check)
            if check["status"] in ("unknown", "observed-exception"):
                findings.append(
                    finding(
                        kind + "-" + check["status"],
                        f"{req['requirement_id']}: " + "; ".join(check["reasons"]),
                        check["source_refs"],
                        "gap" if check["status"] == "unknown" else "review",
                    )
                )
        results.append({"requirement_id": req["requirement_id"], "scope": req, "checks": checks})
    checked_entities = {r.get("entity_id") for r in d.get("requirements", [])}
    for entity in d.get("entities", []):
        if entity["entity_id"] not in checked_entities:
            findings.append(
                finding("entity-scope-missing", f"No requirements establish the role of entity {entity['entity_id']}.")
            )
    return finish(
        {
            "scope_checks": results,
            "carrier_binding_authority": "not-determined",
            "onboarding_decision": "reserved-for-authorized-reviewer",
        },
        findings,
    )
