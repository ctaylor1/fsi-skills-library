#!/usr/bin/env python3
"""Deterministic resilience-report assembler for operational-resilience-reporter.

Consumes a resilience dataset (critical-service register, critical-third-party register,
CMDB/dependency map, incidents, tests, impact tolerances, jurisdictional ruleset, and
recorded human approvals) and assembles a DRAFT report package for the requested
report_type + jurisdiction, filling every required template section with evidence-cited
facts. It computes only deterministic, explainable facts (incident chronology durations,
impact-tolerance breach = observed vs threshold, register completeness, third-party
concentration). It NEVER makes a regulatory determination, attests, files, or submits;
sections without supporting evidence are emitted as `gap` with no fabricated content.

Usage: python calculate_or_transform.py resilience_dataset.json | --selftest
Prints the report-package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

# --- Versioned contract: template + approval controls (overridable via input `ruleset`) ---
BASE_TEMPLATES = {
    "incident": ["executive-summary", "incident-chronology", "impacted-important-business-services",
                 "impact-tolerance-assessment", "root-cause-and-remediation", "customer-and-market-impact",
                 "regulatory-notification-status", "approvals"],
    "impact-tolerance": ["executive-summary", "important-business-services", "impact-tolerance-statements",
                         "mapping-and-third-parties", "vulnerabilities-and-remediation", "remediation-plan",
                         "approvals"],
    "dependency": ["executive-summary", "service-dependency-map", "critical-third-parties",
                   "concentration-and-substitutability", "exit-and-contingency", "approvals"],
    "testing": ["executive-summary", "scenario-testing-summary", "tolerance-outcomes",
                "vulnerabilities-and-remediation", "lessons-learned", "approvals"],
    "self-assessment": ["executive-summary", "important-business-services", "impact-tolerance-statements",
                        "mapping-and-third-parties", "scenario-testing-summary", "incident-experience",
                        "vulnerabilities-and-remediation", "lessons-learned", "board-attestation-status",
                        "approvals"],
}
JURISDICTION_SECTIONS = {
    "EU-DORA": ["ict-third-party-register", "major-incident-classification"],
    "UK-PRA-SS1-21": ["self-assessment-document-reference"],
    "US-INTERAGENCY": ["interconnection-and-concentration"],
}
REQUIRED_APPROVERS = ["accountable-executive", "second-line-review"]

DRAFT_WATERMARK = "DRAFT - for human review and adjudication; not filed or submitted to any regulator."
STANDING_NOTE = ("Draft resilience report only; this package makes no regulatory determination, files "
                 "nothing, and submits nothing. A named accountable executive and second-line reviewer "
                 "must adjudicate, and any regulatory submission is performed by an authorized human.")


def _dt(s):
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _minutes(a, b):
    da, db = _dt(a), _dt(b)
    if da and db:
        return int((db - da).total_seconds() // 60)
    return None


def build_context(doc):
    rr = doc.get("report_request") or {}
    services = doc.get("critical_services") or []
    tps = doc.get("third_parties") or []
    ver = doc.get("ruleset_version")
    asof = rr.get("as_of_date")
    return {
        "doc": doc, "rr": rr, "ver": ver, "asof": asof,
        "services": services, "tps": tps,
        "svc_by_id": {s.get("service_id"): s for s in services},
        "tp_by_id": {t.get("tp_id"): t for t in tps},
        "deps": doc.get("dependencies") or [],
        "incidents": doc.get("incidents") or [],
        "tests": doc.get("tests") or [],
        "approvals": doc.get("approvals") or [],
        "assessments": [],  # filled by compute_assessments
    }


# --- deterministic computations -------------------------------------------------------

def compute_assessments(ctx):
    """Impact-tolerance breach = observed metric vs threshold (direction 'max')."""
    out = []
    for inc in ctx["incidents"]:
        svc = ctx["svc_by_id"].get(inc.get("service_id"))
        if not svc:
            continue
        tol = svc.get("impact_tolerance") or {}
        metric, thr = tol.get("metric"), tol.get("threshold")
        if metric is None or thr is None:
            continue
        observed = (inc.get("metrics") or {}).get(metric)
        if observed is None:
            observed = _minutes(inc.get("detected") or inc.get("start"), inc.get("resolved"))
        if observed is None:
            continue
        direction = tol.get("direction", "max")
        breached = observed > thr if direction == "max" else observed < thr
        out.append({
            "incident_id": inc.get("incident_id"), "service_id": inc.get("service_id"),
            "metric": metric, "unit": tol.get("unit"), "threshold": thr,
            "observed": observed, "direction": direction, "breached": bool(breached),
            "citation": f"incidents:{inc.get('incident_id')}@{(inc.get('start') or '')[:10]}",
        })
    ctx["assessments"] = out
    return out


def register_completeness(ctx):
    missing = []
    for s in ctx["services"]:
        if s.get("is_important_business_service") and not (s.get("impact_tolerance") or {}).get("threshold"):
            missing.append(f"service {s.get('service_id')}: impact_tolerance.threshold")
    for t in ctx["tps"]:
        if t.get("is_critical"):
            if not t.get("contract_ref"):
                missing.append(f"third_party {t.get('tp_id')}: contract_ref")
            if not t.get("exit_plan_ref"):
                missing.append(f"third_party {t.get('tp_id')}: exit_plan_ref")
    return {
        "critical_services": len(ctx["services"]),
        "important_business_services": sum(1 for s in ctx["services"] if s.get("is_important_business_service")),
        "critical_third_parties": sum(1 for t in ctx["tps"] if t.get("is_critical")),
        "missing_fields": missing,
    }


def _concentration(ctx):
    hot = []
    for t in ctx["tps"]:
        if t.get("is_critical") and len(t.get("service_ids") or []) > 1:
            hot.append(t)
    return hot


# --- section builders (each returns (facts, citations)) -------------------------------

def _reg(ctx, sid):
    return f"register:service={sid}@{ctx['asof']}"


def _regtp(ctx, tid):
    return f"register:tp={tid}@{ctx['asof']}"


def sec_exec(ctx):
    rc = register_completeness(ctx)
    facts = [
        f"Reporting period {ctx['rr'].get('reporting_period', {}).get('from')} to "
        f"{ctx['rr'].get('reporting_period', {}).get('to')}; as of {ctx['asof']}.",
        f"In scope: {rc['important_business_services']} important business service(s), "
        f"{rc['critical_third_parties']} critical third part(y/ies).",
        f"{sum(1 for a in ctx['assessments'] if a['breached'])} impact-tolerance breach(es) observed in period.",
    ]
    return facts, [f"ruleset:{ctx['rr'].get('jurisdiction')}@{ctx['ver']}"] + [_reg(ctx, s.get("service_id")) for s in ctx["services"]]


def sec_ibs(ctx):
    facts, cites = [], []
    for s in ctx["services"]:
        if s.get("is_important_business_service"):
            facts.append(f"{s.get('service_id')} - {s.get('name')}")
            cites.append(_reg(ctx, s.get("service_id")))
    return facts, cites


def sec_tolerances(ctx):
    facts, cites = [], []
    for s in ctx["services"]:
        tol = s.get("impact_tolerance") or {}
        if tol.get("threshold") is not None:
            facts.append(f"{s.get('service_id')}: {tol.get('metric')} {tol.get('direction', 'max')} "
                         f"{tol.get('threshold')} {tol.get('unit')}")
            cites.append(_reg(ctx, s.get("service_id")))
    return facts, cites


def sec_mapping(ctx):
    facts, cites = [], []
    for d in ctx["deps"]:
        tp = ctx["tp_by_id"].get(d.get("depends_on"))
        label = tp.get("name") if tp else d.get("depends_on")
        facts.append(f"{d.get('service_id')} depends on {d.get('depends_on')} ({label}) - {d.get('type')}")
        cites.append(f"cmdb:{d.get('service_id')}->{d.get('depends_on')}@{ctx['asof']}")
    return facts, cites


def sec_critical_tps(ctx):
    facts, cites = [], []
    for t in ctx["tps"]:
        if t.get("is_critical"):
            facts.append(f"{t.get('tp_id')} - {t.get('name')}; services {', '.join(t.get('service_ids') or [])}; "
                         f"contract {t.get('contract_ref')}; exit plan {t.get('exit_plan_ref')}")
            cites.append(_regtp(ctx, t.get("tp_id")))
    return facts, cites


def sec_concentration(ctx):
    facts, cites = [], []
    for t in _concentration(ctx):
        facts.append(f"{t.get('tp_id')} ({t.get('name')}) supports multiple in-scope services: "
                     f"{', '.join(t.get('service_ids') or [])} - concentration/substitutability review indicated")
        cites.append(_regtp(ctx, t.get("tp_id")))
    return facts, cites


def sec_exit(ctx):
    facts, cites = [], []
    for t in ctx["tps"]:
        if t.get("is_critical"):
            facts.append(f"{t.get('tp_id')}: exit/contingency plan {t.get('exit_plan_ref')}")
            cites.append(_regtp(ctx, t.get("tp_id")))
    return facts, cites


def sec_tests(ctx):
    facts, cites = [], []
    for t in sorted(ctx["tests"], key=lambda x: x.get("date", "")):
        facts.append(f"{t.get('test_id')} {t.get('date')}: {t.get('service_id')} '{t.get('scenario')}' -> "
                     f"{t.get('outcome')}; within tolerance: {t.get('within_tolerance')}")
        cites.append(f"tests:{t.get('test_id')}@{t.get('date')}")
    return facts, cites


def sec_tolerance_outcomes(ctx):
    facts, cites = [], []
    for a in ctx["assessments"]:
        facts.append(f"{a['incident_id']} / {a['service_id']}: observed {a['observed']} vs threshold "
                     f"{a['threshold']} {a['unit']} -> breached: {a['breached']}")
        cites.append(a["citation"])
    return facts, cites


def sec_incidents(ctx):
    facts, cites = [], []
    for inc in sorted(ctx["incidents"], key=lambda x: x.get("start", "")):
        dur = _minutes(inc.get("detected") or inc.get("start"), inc.get("resolved"))
        facts.append(f"{inc.get('incident_id')} {inc.get('start')}: {inc.get('service_id')} "
                     f"severity {inc.get('severity')}; detected {inc.get('detected')}, resolved {inc.get('resolved')} "
                     f"({dur} min); third party {inc.get('third_party')}")
        cites.append(f"incidents:{inc.get('incident_id')}@{(inc.get('start') or '')[:10]}")
    return facts, cites


def sec_customer_impact(ctx):
    facts, cites = [], []
    for inc in ctx["incidents"]:
        if inc.get("customer_impact"):
            facts.append(f"{inc.get('incident_id')} / {inc.get('service_id')}: {inc.get('customer_impact')}")
            cites.append(f"incidents:{inc.get('incident_id')}@{(inc.get('start') or '')[:10]}")
    return facts, cites


def sec_root_cause(ctx):
    facts, cites = [], []
    for inc in ctx["incidents"]:
        if inc.get("root_cause_ref"):
            facts.append(f"{inc.get('incident_id')}: root cause {inc.get('root_cause_ref')}; "
                         f"remediation {inc.get('remediation_ref')}")
            cites.append(f"incidents:{inc.get('incident_id')}@{(inc.get('start') or '')[:10]}")
    return facts, cites


def sec_vulnerabilities(ctx):
    facts, cites = [], []
    for a in ctx["assessments"]:
        if a["breached"]:
            facts.append(f"Impact-tolerance breach on {a['service_id']} (incident {a['incident_id']}): "
                         f"observed {a['observed']} > threshold {a['threshold']} {a['unit']}")
            cites.append(a["citation"])
    for t in ctx["tests"]:
        if t.get("within_tolerance") is False:
            facts.append(f"Test {t.get('test_id')} on {t.get('service_id')} recovered outside tolerance "
                         f"('{t.get('scenario')}'); remediation {t.get('remediation_ref')}")
            cites.append(f"tests:{t.get('test_id')}@{t.get('date')}")
    return facts, cites


def sec_remediation(ctx):
    facts, cites = [], []
    for inc in ctx["incidents"]:
        if inc.get("remediation_ref"):
            facts.append(f"{inc.get('remediation_ref')} (from incident {inc.get('incident_id')})")
            cites.append(f"incidents:{inc.get('incident_id')}@{(inc.get('start') or '')[:10]}")
    for t in ctx["tests"]:
        if t.get("remediation_ref"):
            facts.append(f"{t.get('remediation_ref')} (from test {t.get('test_id')})")
            cites.append(f"tests:{t.get('test_id')}@{t.get('date')}")
    return facts, cites


def sec_lessons(ctx):
    facts, cites = sec_remediation(ctx)
    if facts:
        facts = ["Lessons/actions tracked against the following remediation items:"] + facts
    return facts, cites


def sec_board_attestation(ctx):
    a = ctx["rr"].get("attestation_status") or {}
    if not a:
        return [], []
    facts = [f"Board attestation status: {a.get('status')} with {a.get('body')} "
             f"(target {a.get('target_date')}); not yet attested - human governance step."]
    return facts, [f"request:attestation_status@{ctx['asof']}"]


def sec_notification(ctx):
    n = ctx["rr"].get("notification_status") or {}
    if not n:
        return [], []
    facts = [f"Regulatory notification status (as recorded by human owner {n.get('owner_ref')}): "
             f"{n.get('status')} for {n.get('regulator')}. Any notification decision and act belong to an authorized human."]
    return facts, [f"request:notification_status@{ctx['asof']}"]


def sec_doc_ref(ctx):
    ref = ctx["rr"].get("self_assessment_doc_ref")
    if not ref:
        return [], []
    return [f"Self-assessment document reference: {ref}"], [f"request:self_assessment_doc_ref@{ctx['asof']}"]


def sec_ict_register(ctx):
    return sec_critical_tps(ctx)


def sec_major_incident_class(ctx):
    facts, cites = [], []
    for inc in ctx["incidents"]:
        facts.append(f"{inc.get('incident_id')}: severity {inc.get('severity')} (classification input; "
                     f"final major-incident classification is a human determination)")
        cites.append(f"incidents:{inc.get('incident_id')}@{(inc.get('start') or '')[:10]}")
    return facts, cites


def sec_interconnection(ctx):
    return sec_concentration(ctx)


def sec_approvals(ctx):
    facts, cites = [], []
    for ap in ctx["approvals"]:
        facts.append(f"{ap.get('role')}: {ap.get('name')} - {ap.get('decision')} on {ap.get('date')}")
        cites.append(f"approval:{ap.get('approver_ref')}@{ap.get('date')}")
    return facts, cites


BUILDERS = {
    "executive-summary": sec_exec,
    "important-business-services": sec_ibs,
    "impacted-important-business-services": sec_ibs,
    "impact-tolerance-statements": sec_tolerances,
    "impact-tolerance-assessment": sec_tolerance_outcomes,
    "tolerance-outcomes": sec_tolerance_outcomes,
    "mapping-and-third-parties": sec_mapping,
    "service-dependency-map": sec_mapping,
    "critical-third-parties": sec_critical_tps,
    "concentration-and-substitutability": sec_concentration,
    "exit-and-contingency": sec_exit,
    "scenario-testing-summary": sec_tests,
    "incident-experience": sec_incidents,
    "incident-chronology": sec_incidents,
    "customer-and-market-impact": sec_customer_impact,
    "root-cause-and-remediation": sec_root_cause,
    "vulnerabilities-and-remediation": sec_vulnerabilities,
    "remediation-plan": sec_remediation,
    "lessons-learned": sec_lessons,
    "board-attestation-status": sec_board_attestation,
    "regulatory-notification-status": sec_notification,
    "self-assessment-document-reference": sec_doc_ref,
    "ict-third-party-register": sec_ict_register,
    "major-incident-classification": sec_major_incident_class,
    "interconnection-and-concentration": sec_interconnection,
    "approvals": sec_approvals,
}

SECTION_TITLES = {
    "executive-summary": "Executive summary",
    "important-business-services": "Important business services",
    "impacted-important-business-services": "Impacted important business services",
    "impact-tolerance-statements": "Impact-tolerance statements",
    "impact-tolerance-assessment": "Impact-tolerance assessment",
    "tolerance-outcomes": "Tolerance outcomes",
    "mapping-and-third-parties": "Mapping and third parties",
    "service-dependency-map": "Service dependency map",
    "critical-third-parties": "Critical third parties",
    "concentration-and-substitutability": "Concentration and substitutability",
    "exit-and-contingency": "Exit and contingency",
    "scenario-testing-summary": "Scenario testing summary",
    "incident-experience": "Incident experience",
    "incident-chronology": "Incident chronology",
    "customer-and-market-impact": "Customer and market impact",
    "root-cause-and-remediation": "Root cause and remediation",
    "vulnerabilities-and-remediation": "Vulnerabilities and remediation",
    "remediation-plan": "Remediation plan",
    "lessons-learned": "Lessons learned",
    "board-attestation-status": "Board attestation status",
    "regulatory-notification-status": "Regulatory notification status",
    "self-assessment-document-reference": "Self-assessment document reference",
    "ict-third-party-register": "ICT third-party register",
    "major-incident-classification": "Major-incident classification",
    "interconnection-and-concentration": "Interconnection and concentration",
    "approvals": "Approvals",
}


def required_sections(doc):
    rr = doc.get("report_request") or {}
    rtype = rr.get("report_type")
    juris = rr.get("jurisdiction")
    over = doc.get("ruleset") or {}
    base = (over.get("templates") or {}).get(rtype) or BASE_TEMPLATES.get(rtype, [])
    js = (over.get("jurisdiction_sections") or {}).get(juris)
    if js is None:
        js = JURISDICTION_SECTIONS.get(juris, [])
    # jurisdiction extras appear before the approvals section
    keys = [k for k in base if k != "approvals"] + [k for k in js if k not in base] + ["approvals"]
    return keys


def assemble(doc):
    ctx = build_context(doc)
    compute_assessments(ctx)
    rr = ctx["rr"]
    keys = required_sections(doc)
    sections, gaps = [], []
    for k in keys:
        builder = BUILDERS.get(k)
        if builder is None:
            facts, cites = [], []
        else:
            facts, cites = builder(ctx)
        if facts and cites:
            sections.append({"key": k, "title": SECTION_TITLES.get(k, k),
                             "status": "drafted", "content_facts": facts, "citations": sorted(set(cites))})
        else:
            note = f"No supporting evidence in dataset for '{k}'; requires human input."
            sections.append({"key": k, "title": SECTION_TITLES.get(k, k),
                             "status": "gap", "content_facts": [], "citations": [], "gap_note": note})
            gaps.append(f"{k}: {note}")

    pkg = {
        "report_type": rr.get("report_type"),
        "jurisdiction": rr.get("jurisdiction"),
        "template_version": rr.get("template_version"),
        "ruleset_version": ctx["ver"],
        "as_of_date": ctx["asof"],
        "reporting_period": rr.get("reporting_period"),
        "required_sections": keys,
        "sections": sections,
        "impact_tolerance_assessments": ctx["assessments"],
        "register_completeness": register_completeness(ctx),
        "gaps": gaps,
        "approvals_recorded": ctx["approvals"],
        "required_approvers": REQUIRED_APPROVERS,
        "unsupported_claims": [],
        "draft_watermark": DRAFT_WATERMARK,
        "standing_note": STANDING_NOTE,
    }
    return {"report_package": pkg}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "resilience_dataset.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
