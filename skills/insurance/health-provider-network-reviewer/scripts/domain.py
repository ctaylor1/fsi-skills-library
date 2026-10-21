"""Supplied provider-site evidence and complete-population access comparisons."""

from decimal import Decimal
from fractions import Fraction
from design_support import validate_with
from specialist_support import SpecialistReview

METHOD = "reviewed-health-network-access-v1"
DIMENSIONS = ("plan_id", "specialty_id", "geography_id", "metric", "unit", "travel_mode")


def strict_references(value):
    """Do not accept a scalar or duplicate reference list as the documented schema."""
    if isinstance(value, dict):
        refs = value.get("source_refs")
        if refs is not None and (
            not isinstance(refs, list)
            or any(not isinstance(x, str) or not x.strip() for x in refs)
            or len(set(refs)) != len(refs)
        ):
            raise ValueError("source_refs must be an explicit array of unique nonblank strings or null")
        for child in value.values():
            strict_references(child)
    elif isinstance(value, list):
        for child in value:
            strict_references(child)


def evaluate(doc):
    strict_references(doc)
    r = SpecialistReview(doc, METHOD)
    d = r.data
    r.need(
        doc["context"].get("capacity") == "health-network-review"
        and doc["context"].get("line_of_business") == "health"
        and doc["context"].get("object_id") == d.get("plan_id"),
        "professional-context",
        "Health network review capacity, health line and exact plan object are required",
        d,
    )
    for source in doc["sources"]:
        r.fields(source, ("locator",))
    r.evidence(d)
    r.fields(d, ("plan_id", "population_basis", "inventory_statement", "source_locator", "reviewed_by"))
    observed = r.date(d, "observed_on")
    reviewed = r.date(d, "reviewed_on")
    r.need(
        observed is not None and reviewed is not None and reviewed >= observed,
        "review-date",
        "Network scope review cannot predate the underlying observation",
        d,
    )
    for flag in (
        "provider_inventory_complete",
        "member_population_complete",
        "measurement_inventory_complete",
        "threshold_inventory_complete",
    ):
        r.flag(d, flag)
    r.need(
        d.get("weighting") == "one-per-unique-member-per-threshold",
        "weighting",
        "Only explicit unique-member equal weighting per threshold is supported",
        d,
    )
    providers = r.rows("providers", "provider_record_id", nonempty=False)
    expected = set(r.strings(d, "expected_provider_record_ids"))
    r.need(
        {p["provider_record_id"] for p in providers} == expected,
        "provider-inventory",
        "Provider inventory must reconcile to its complete source-bound ID list",
        d,
    )
    triples = set()
    eligible = {}
    inventory = []
    for row in providers:
        r.fields(row, ("provider_id", "site_id", "specialty_id", "geography_id", "source_locator"))
        triple = tuple(row.get(k) for k in ("provider_id", "site_id", "specialty_id"))
        r.need(
            triple not in triples,
            "duplicate-provider-site",
            "Duplicate provider/site/specialty record; distinct sites must retain distinct identities",
            row,
        )
        triples.add(triple)
        npi = row.get("npi")
        if npi is not None and not isinstance(npi, str):
            raise ValueError("npi must be exact text or null; never numeric identity")
        contract = row.get("contract")
        credentials = row.get("credentials")
        directory = row.get("directory")
        if not all(isinstance(x, dict) for x in (contract, credentials, directory)):
            raise ValueError("contract, credentials and directory must be objects")
        r.evidence(contract)
        r.fields(contract, ("contract_id", "version", "source_locator", "plan_id"))
        r.need(
            contract.get("plan_id") == d.get("plan_id"),
            "contract-plan",
            "Provider contract must name the actual reviewed plan",
            contract,
        )
        start = r.date(contract, "effective_from", future=True)
        end = r.date(contract, "effective_to", future=True)
        r.need(
            start is not None and end is not None and start <= end,
            "contract-period",
            "Contract dates must be ordered and explicit",
            contract,
        )
        r.need(
            contract.get("status") in {"executed", "not-executed"},
            "contract-status",
            "Contract status must be executed or not-executed; unknown is a gap",
            contract,
        )
        active = (
            contract.get("status") == "executed"
            and all(x is not None for x in (start, end, observed))
            and start <= observed <= end
        )
        r.evidence(credentials)
        r.fields(credentials, ("credential_evidence_id", "license_evidence_id", "reviewed_by", "source_locator"))
        reviewed = r.date(credentials, "reviewed_on")
        due = r.date(credentials, "next_review_due", future=True)
        r.need(
            reviewed is not None
            and due is not None
            and observed is not None
            and reviewed <= observed
            and reviewed <= due,
            "credential-period",
            "Credential review must precede observation and next-review date",
            credentials,
        )
        for key in ("credential_status", "license_status"):
            r.need(
                credentials.get(key) in {"verified", "not-current"},
                "credential-status",
                key + " requires explicit evidence; NPI or registry presence is insufficient",
                credentials,
            )
        credential_current = (
            credentials.get("credential_status") == "verified"
            and credentials.get("license_status") == "verified"
            and due is not None
            and observed is not None
            and observed <= due
        )
        r.evidence(directory)
        r.fields(directory, ("source_locator",))
        directory_date = r.date(directory, "observed_on")
        r.need(
            directory_date == observed,
            "directory-date",
            "Directory observation must match review observation basis",
            directory,
        )
        present = directory.get("present")
        if present is not None and not isinstance(present, bool):
            raise ValueError("directory.present must be boolean or null")
        r.need(
            present is not None,
            "directory-unknown",
            "Directory visibility is separately observed; contract does not establish it",
            directory,
        )
        included = bool(active and credential_current)
        eligible[row["provider_record_id"]] = included
        if not active or not credential_current:
            r.add(
                "provider-exception",
                "Supplied contract or credential evidence excludes this record from the reviewed eligible inventory",
                row,
                severity="review",
            )
        if present is not None and present != included:
            r.add(
                "directory-discrepancy",
                "Observed directory presence differs from supplied contract/credential eligibility; owner review required",
                row,
                severity="review",
            )
        inventory.append(
            {
                "provider_record_id": row["provider_record_id"],
                "provider_id": row.get("provider_id"),
                "site_id": row.get("site_id"),
                "specialty_id": row.get("specialty_id"),
                "contract_active": bool(active),
                "credential_current": bool(credential_current),
                "directory_present": present,
                "eligible_for_supplied_access_test": included,
                "source_refs": row["source_refs"],
            }
        )
    thresholds = r.rows("thresholds", "threshold_id")
    r.need(
        {t["threshold_id"] for t in thresholds} == set(r.strings(d, "expected_threshold_ids", nonempty=True)),
        "threshold-inventory",
        "Thresholds must reconcile to the complete supplied expected inventory",
        d,
    )
    threshold_by = {t["threshold_id"]: t for t in thresholds}
    parsed = {}
    for row in thresholds:
        r.fields(row, DIMENSIONS + ("market", "program", "product", "source_locator", "population_basis", "rule_basis"))
        r.need(
            all(row.get(k) == d.get(k) for k in ("market", "program", "product")),
            "threshold-program",
            "Threshold must expressly match the actual market, program and product",
            row,
        )
        r.applicable(row, observed, "Access threshold")
        r.need(
            row.get("plan_id") == d.get("plan_id") and row.get("population_basis") == d.get("population_basis"),
            "threshold-scope",
            "Threshold must match actual plan and eligible population",
            row,
        )
        metric = row.get("metric")
        unit = row.get("unit")
        r.need(
            (metric == "distance" and unit in {"miles", "kilometers"}) or (metric == "time" and unit == "minutes"),
            "measurement-unit",
            "Metric/unit must be distance with miles/kilometers or time with minutes",
            row,
        )
        r.need(
            row.get("travel_mode") in {"driving", "walking", "transit"},
            "travel-mode",
            "Travel mode must be supplied driving/walking/transit",
            row,
        )
        maximum = r.num(row, "maximum_value")
        count = r.num(row, "minimum_distinct_providers", integer=True)
        fraction = r.num(row, "required_member_fraction", proportion=True)
        r.need(
            count is not None and count >= 1, "provider-count", "Required distinct provider count must be positive", row
        )
        parsed[row["threshold_id"]] = (maximum, count, fraction)
    populations = r.rows("populations", "population_id")
    r.need(
        len(populations) == len(thresholds) and {p.get("threshold_id") for p in populations} == set(threshold_by),
        "population-inventory",
        "Exactly one complete eligible member population is required for every threshold",
        d,
    )
    population_by = {}
    member_sets = {}
    for row in populations:
        r.fields(row, ("threshold_id", "plan_id", "specialty_id", "geography_id", "population_basis", "source_locator"))
        r.flag(row, "complete")
        threshold = threshold_by.get(row.get("threshold_id"))
        r.need(
            threshold is not None
            and all(
                row.get(k) == threshold.get(k) for k in ("plan_id", "specialty_id", "geography_id", "population_basis")
            ),
            "population-scope",
            "Member population must match threshold plan, specialty, geography and population basis",
            row,
        )
        members = r.strings(row, "member_ids")
        declared = r.num(row, "eligible_member_count", integer=True)
        r.need(
            declared is not None and declared == len(members),
            "member-denominator",
            "Unique member list must reconcile to complete eligible member denominator",
            row,
        )
        r.need(
            declared is not None and declared > 0,
            "empty-population",
            "Zero eligible members withholds percentage and threshold comparison",
            row,
        )
        population_by[row.get("threshold_id")] = row
        member_sets[row.get("threshold_id")] = set(members)
    observations = r.rows("measurements", "measurement_id", nonempty=False)
    measurements = {}
    provider_by = {p["provider_record_id"]: p for p in providers}
    for row in observations:
        r.fields(
            row,
            DIMENSIONS + ("threshold_id", "member_id", "provider_record_id", "source_locator", "measurement_method"),
        )
        day = r.date(row, "observed_on")
        r.need(day == observed, "measurement-date", "All travel measurements must use the exact observation date", row)
        threshold = threshold_by.get(row.get("threshold_id"))
        provider = provider_by.get(row.get("provider_record_id"))
        r.need(
            threshold is not None and all(row.get(k) == threshold.get(k) for k in DIMENSIONS),
            "measurement-scope",
            "Measurement dimensions must exactly match the reviewed threshold",
            row,
        )
        r.need(
            provider is not None
            and provider.get("specialty_id") == row.get("specialty_id")
            and provider.get("geography_id") == row.get("geography_id"),
            "measurement-provider",
            "Measurement requires a matching supplied provider specialty/geography record",
            row,
        )
        r.need(
            row.get("member_id") in member_sets.get(row.get("threshold_id"), set()),
            "measurement-member",
            "Measurement member is outside the exact eligible population",
            row,
        )
        key = (row.get("threshold_id"), row.get("member_id"), row.get("provider_record_id"))
        r.need(
            key not in measurements,
            "duplicate-measurement",
            "One measurement per threshold/member/provider-site record is permitted",
            row,
        )
        measurements[key] = r.num(row, "value")
    output = []
    for row in thresholds:
        tid = row["threshold_id"]
        members = member_sets.get(tid, set())
        candidates = [
            p
            for p in providers
            if eligible.get(p["provider_record_id"])
            and all(p.get(k) == row.get(k) for k in ("specialty_id", "geography_id"))
        ]
        expected = {(tid, member, p["provider_record_id"]) for member in members for p in candidates}
        supplied = {key for key in measurements if key[0] == tid and eligible.get(key[2])}
        r.need(
            expected == supplied,
            "measurement-completeness",
            "Complete measurements for every eligible member and candidate provider-site are required; no sample extrapolation",
            row,
        )
        maximum, needed, fraction = parsed[tid]
        met = 0
        per_member = []
        for member in sorted(members):
            provider_ids = {
                p["provider_id"]
                for p in candidates
                if measurements.get((tid, member, p["provider_record_id"])) is not None
                and maximum is not None
                and measurements[(tid, member, p["provider_record_id"])] <= maximum
            }
            count = len(provider_ids)
            passes = needed is not None and count >= needed
            met += int(passes)
            per_member.append(
                {"member_id": member, "distinct_qualifying_providers": count, "meets_supplied_access_test": passes}
            )
        actual = Decimal(met) / len(members) if members else None
        meets = (
            Fraction(met, len(members)) >= Fraction(fraction) if actual is not None and fraction is not None else None
        )
        if meets is False:
            r.add(
                "access-exception",
                "Complete supplied population does not meet its reviewed threshold",
                row,
                severity="review",
            )
        output.append(
            {
                "threshold_id": tid,
                "eligible_members": len(members),
                "members_meeting_test": met,
                "member_fraction": actual,
                "meets_supplied_threshold": meets,
                "member_results": per_member,
                "source_refs": row["source_refs"],
            }
        )
    if not r.clear:
        for row in output:
            for key in ("eligible_members", "members_meeting_test", "member_fraction", "meets_supplied_threshold"):
                row[key] = None
            for member in row["member_results"]:
                member["distinct_qualifying_providers"] = None
                member["meets_supplied_access_test"] = None
        for row in inventory:
            for key in ("contract_active", "credential_current", "eligible_for_supplied_access_test"):
                row[key] = None
    return r.finish(
        {
            "provider_inventory": inventory,
            "access_comparisons": output,
            "network_adequacy_certified": False,
            "licensure_inferred_from_npi": False,
            "network_changed": False,
            "directory_changed": False,
        }
    )


def validate(doc):
    return validate_with(evaluate, doc)
