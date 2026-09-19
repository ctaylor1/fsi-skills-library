"""Assemble market evidence without selecting coverage or binding a placement."""

from copy import deepcopy
from domain_support import day, fields, finding, finish, key, known, money, profile, profile_errors, refs, shape, unique


def validate(doc):
    errors = shape(doc, ("market_responses",), ("profile", "selected_versions", "placement"))
    if errors:
        return errors
    d = doc["data"]
    rows = d.get("market_responses", [])
    errors += profile_errors(doc)
    if rows and not unique(rows, "response_id"):
        errors.append("response_id must be unique and nonempty")
    errors += fields(
        rows,
        dates=("issued_on", "valid_until", "period_start", "period_end"),
        numbers=("premium", "fees", "taxes", "limit", "retention"),
        lists=("coverages", "exclusions", "subjectivities"),
    )
    for row in rows:
        if any(not isinstance(s, dict) for s in row.get("subjectivities", [])):
            errors.append("subjectivities must contain objects")
        if row.get("status") not in ("quoted", "declined", "no-response", None):
            errors.append("unsupported market response status")
    if any(not isinstance(k, str) or not isinstance(v, str) for k, v in d.get("selected_versions", {}).items()):
        errors.append("selected_versions maps market_id to response_id")
    return errors


def evaluate(doc):
    d = doc["data"]
    p, findings = profile(doc)
    placement = d.get("placement", {})
    rows = d.get("market_responses", [])
    groups = {}
    selected = []
    assessments = []
    if not placement.get("placement_id") or not placement.get("insured_id"):
        findings.append(finding("placement-identity", "Placement and insured identity are required."))
    if not rows:
        findings.append(finding("market-evidence", "No market evidence is supplied."))
    market_ids = list(dict.fromkeys(r.get("market_id") for r in rows))
    for market_id in market_ids:
        candidates = [r for r in rows if r.get("market_id") == market_id]
        chosen = d.get("selected_versions", {}).get(market_id)
        chosen_rows = (
            [r for r in candidates if r["response_id"] == chosen]
            if chosen
            else candidates
            if len(candidates) == 1
            else []
        )
        if not market_id or len(chosen_rows) != 1:
            findings.append(
                finding(
                    "market-version",
                    f"Market {market_id}: identify the current response explicitly; no version is inferred from its label.",
                    [x for r in candidates for x in refs(r)],
                )
            )
            continue
        row = chosen_rows[0]
        selected.append(row["response_id"])
        reasons = []
        if not row.get("version") or not known(doc, row.get("source_ref")):
            reasons.append("source or response version missing")
        if not row.get("issued_on") or not row.get("valid_until"):
            reasons.append("quote observation/expiry dates missing")
        elif day(row["issued_on"]) > day(doc["as_of"]) or day(row["valid_until"]) < day(doc["as_of"]):
            reasons.append("response is outside its validity period")
        if row.get("insured_id") != placement.get("insured_id"):
            reasons.append("insured identity mismatch")
        for k in ("jurisdiction", "line_of_business"):
            if row.get(k) != doc["context"].get(k):
                reasons.append(k + " does not match review scope")
        status = row.get("status")
        if not status:
            reasons.append("market response status unknown")
        subjectivities = []
        for sub in row.get("subjectivities", []):
            state = sub.get("status")
            if state == "satisfied" and not known(doc, sub.get("evidence_source_ref")):
                state = "unknown"
            if state not in ("satisfied", "open", "waived-by-carrier"):
                state = "unknown"
            if state == "waived-by-carrier" and not known(doc, sub.get("evidence_source_ref")):
                state = "unknown"
            subjectivities.append(
                {
                    "subjectivity_id": sub.get("subjectivity_id"),
                    "description": sub.get("description"),
                    "observed_status": state,
                    "evidence_source_ref": sub.get("evidence_source_ref"),
                }
            )
            if state != "satisfied" and state != "waived-by-carrier":
                findings.append(
                    finding(
                        "subjectivity-" + state,
                        f"{row['response_id']}: {sub.get('description', 'subjectivity lacks description')}",
                        refs(row),
                        "gap" if state == "unknown" else "review",
                    )
                )
        total = None
        comp = None
        if status == "quoted":
            for k in (
                "currency",
                "period_start",
                "period_end",
                "layer",
                "coverage_basis",
                "coverages",
                "exclusions",
                "limit",
                "retention",
            ):
                if k not in row or row[k] is None:
                    reasons.append(k + " is missing")
            if "subjectivities" not in row:
                reasons.append("subjectivities were not supplied; absence is not an empty confirmed schedule")
            if row.get("period_start") and row.get("period_end") and day(row["period_start"]) >= day(row["period_end"]):
                reasons.append("policy period is invalid")
            components = [money(row.get(k)) for k in ("premium", "fees", "taxes")]
            if None in components:
                reasons.append("premium, fees or taxes missing; total withheld")
            if not reasons:
                total = str(sum(components))
                comp = key(
                    {
                        k: row[k]
                        for k in (
                            "currency",
                            "period_start",
                            "period_end",
                            "layer",
                            "coverage_basis",
                            "coverages",
                            "exclusions",
                            "limit",
                            "retention",
                        )
                    }
                )
                groups.setdefault(comp, []).append(row["response_id"])
        for reason in reasons:
            findings.append(finding("market-gap", row["response_id"] + ": " + reason, refs(row)))
        assessments.append(
            {
                "response_id": row["response_id"],
                "market_id": market_id,
                "response_status": status or "unknown",
                "evidence_status": "partial" if reasons else "reviewable",
                "quoted_total": total,
                "currency": row.get("currency"),
                "subjectivities": subjectivities,
            }
        )
    for market_id, chosen in d.get("selected_versions", {}).items():
        if not any(r.get("market_id") == market_id and r.get("response_id") == chosen for r in rows):
            findings.append(
                finding("selection-unresolved", f"{market_id}: selected response {chosen} was not supplied.")
            )
    return finish(
        {
            "placement_id": placement.get("placement_id"),
            "response_history": deepcopy(rows),
            "selected_response_ids": selected,
            "market_assessments": assessments,
            "comparable_groups": [{"basis": __import__("json").loads(k), "response_ids": v} for k, v in groups.items()],
            "market_selection": "not-performed",
            "binding_status": "not-performed",
        },
        findings,
    )
