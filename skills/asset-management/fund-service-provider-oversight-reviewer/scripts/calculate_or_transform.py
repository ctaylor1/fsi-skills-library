"""Fund-service SLA observations, assurance freshness and issue aging from supplied evidence."""
from decimal import Decimal
from foundation_contract import D, date_value, exact, ratio, validate_common, validate_referenced_sources, validate_actual_date, finish, cli_compute

SKILL = "fund-service-provider-oversight-reviewer"


@exact
def compute(doc):
    errors = validate_common(doc) + validate_referenced_sources(doc)
    if errors: raise ValueError("; ".join(errors))
    if any(date_value(source["as_of"]) > date_value(source["known_at"]) for source in doc["sources"]): raise ValueError("historical observation source cannot be known before its economic as_of")
    if doc.get("mode") != "service_oversight" or not doc.get("policy_source_ref"): raise ValueError("service_oversight mode and supplied policy source required")
    services, ids, rows, issues = doc["services"], set(), [], []
    if not isinstance(services, list) or not 1 <= len(services) <= 1000: raise ValueError("1..1000 service rows required")
    when = date_value(doc["as_of"])
    for service in services:
        sid = service["service_id"]
        if not isinstance(sid, str) or not sid or sid in ids or not service.get("provider_id") or not service.get("source_ref"): raise ValueError("unique service_id, provider_id and source_ref required")
        ids.add(sid)
        start, end = date_value(service["period_start"]), date_value(service["period_end"])
        if not start < end <= when: raise ValueError("service observations require a completed positive period")
        validate_actual_date(doc, service["period_end"], service["source_ref"])
        total, failures = D(service["observed_events"]), D(service["failed_events"])
        threshold = D(service["max_failure_rate"])
        if total != int(total) or failures != int(failures) or not 0 <= failures <= total or not 0 <= threshold <= 1: raise ValueError("invalid event counts/threshold")
        rate = ratio(failures, total, 12) if total else None
        # Compare exact products, never a rounded failure rate against a threshold.
        sla = "unavailable" if not total else "exception" if failures > threshold * total else "within-supplied-threshold"
        assurance = service.get("assurance")
        if assurance is None: assurance_status = "unavailable"
        else:
            if not assurance.get("source_ref") or assurance["conclusion"] not in {"supplied-clean", "supplied-exceptions", "unknown"}: raise ValueError("dated assurance reference and supported supplied conclusion required")
            report_end, valid_until = date_value(assurance["period_end"]), date_value(assurance["valid_until"])
            if report_end > when or valid_until < report_end: raise ValueError("assurance chronology invalid")
            validate_actual_date(doc, assurance["period_end"], assurance["source_ref"])
            assurance_status = "expired" if valid_until < when else assurance["conclusion"]
        row = {"service_id": sid, "provider_id": service["provider_id"], "observed_events": str(total), "failed_events": str(failures), "observed_failure_rate": rate, "sla_status": sla, "assurance_status": assurance_status}
        if sla in {"exception", "unavailable"}: issues.append(sid + ": SLA " + sla)
        if assurance_status != "supplied-clean": issues.append(sid + ": assurance " + assurance_status)
        rows.append(row)
    open_items, item_ids = [], set()
    issue_rows = doc["issues"]
    if not isinstance(issue_rows, list) or len(issue_rows) > 1000: raise ValueError("issues list is bounded at1000")
    for item in issue_rows:
        if not item["issue_id"] or item["issue_id"] in item_ids or item["service_id"] not in ids or not item.get("source_ref"): raise ValueError("unique issue and registered service/source required")
        item_ids.add(item["issue_id"])
        opened, due = date_value(item["opened_date"]), date_value(item["due_date"])
        if opened > when or due < opened or item["severity"] not in {"low", "medium", "high", "critical"}: raise ValueError("issue chronology/severity invalid")
        validate_actual_date(doc, item["opened_date"], item["source_ref"])
        if item["status"] not in {"open", "supplied-closed"}: raise ValueError("explicit issue status required")
        if item["status"] == "supplied-closed":
            if not item.get("closure_source_ref") or not opened <= date_value(item["closed_date"]) <= when: raise ValueError("closed issues need dated closure evidence")
            validate_actual_date(doc, item["closed_date"], item["closure_source_ref"])
            continue
        days = max(0, (when - due).days)
        open_items.append({"issue_id": item["issue_id"], "service_id": item["service_id"], "severity": item["severity"], "days_overdue": days, "status": "open", "closure_performed": False})
        issues.append(item["issue_id"] + (": overdue open issue" if days else ": open issue retained"))
    return finish(doc, SKILL, "supplied-fund-service-observations-v1", {"services": rows, "open_issues": open_items, "provider_approved": False}, issues=issues,
                  limitations=["SLA thresholds and assurance conclusions are supplied; no provider approval, SOC opinion, outsourcing classification or legal applicability decision.", "Zero observed events yields unavailable failure rate. Exact cross-products determine SLA exceptions.", "No service termination, vendor communication or issue closure is performed; enterprise vendor controls remain separate."], handoffs=["fund-nav-control-reviewer", "investment-operating-model-planner"])


if __name__ == "__main__": cli_compute(compute)
