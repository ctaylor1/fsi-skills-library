#!/usr/bin/env python3
"""Deterministic operational-risk event analysis for operational-risk-event-analyzer.

Reads an operational-risk event record (see validate_input.py), then deterministically:
  1. Normalizes the Basel Level-1 event type and business line.
  2. Quantifies impact: total recoveries, net loss, indirect costs, total impact, and the
     banding amount (potential loss for a near-miss, total impact for a realized loss).
  3. Maps contributing causes to control themes and a People/Process/Systems/External
     root-cause category, attaching a citation to each finding.
  4. Raises escalation *candidates* (regulatory-reporting, board-notifiable) as flags.
  5. Assigns a severity band from the documented deterministic mapping.
  6. Derives remediation *recommendations* from the control themes.

IMPORTANT: This produces findings, cited evidence, escalation candidates, and remediation
recommendations ONLY. It never makes a risk decision, closes the event/case, files a
regulatory report, posts a journal, or writes any system of record. Classification,
materiality, and remediation require human adjudication (aws-fsi-human-approval: required).
The severity mapping is deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py event.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "moderate_threshold": 25000.0,
    "high_threshold": 250000.0,
    "critical_threshold": 1000000.0,
    "regulatory_reporting_threshold": 100000.0,
    "board_notify_threshold": 1000000.0,
    "board_customer_threshold": 250,
    "sensitive_reporting_factor": 0.5,
}

DISCLAIMER = (
    "Analysis and recommendations only; not a risk decision or regulatory filing. Event "
    "classification, materiality, and remediation require human adjudication before any "
    "case update, escalation, or system-of-record change. No case action has been taken."
)

# Basel II Level-1 operational-risk event types (position of record for classification).
BASEL_L1 = [
    "Internal Fraud",
    "External Fraud",
    "Employment Practices and Workplace Safety",
    "Clients, Products & Business Practices",
    "Damage to Physical Assets",
    "Business Disruption and System Failures",
    "Execution, Delivery & Process Management",
]
BASEL_BUSINESS_LINES = [
    "Corporate Finance", "Trading & Sales", "Retail Banking", "Commercial Banking",
    "Payment & Settlement", "Agency Services", "Asset Management", "Retail Brokerage",
]
# Event types that carry heightened conduct/reporting sensitivity (lower reporting bar).
SENSITIVE_EVENT_TYPES = {"Internal Fraud", "Clients, Products & Business Practices"}

# Contributing-cause code -> (control theme, root-cause category). See references/domain-rules.md.
CAUSE_MAP = {
    "PEOPLE-ERR": ("Supervision & error prevention", "People"),
    "PEOPLE-SKILL": ("Training & competency", "People"),
    "PEOPLE-CONDUCT": ("Conduct & segregation of duties", "People"),
    "PROC-DESIGN": ("Process & control design", "Process"),
    "PROC-BREAK": ("Control execution & reconciliation", "Process"),
    "PROC-DOC": ("Procedures & documentation", "Process"),
    "SYS-FAIL": ("IT resilience & availability", "Systems"),
    "SYS-CONFIG": ("Change management", "Systems"),
    "SYS-CAPACITY": ("Capacity & performance management", "Systems"),
    "EXT-VENDOR": ("Third-party / vendor oversight", "External"),
    "EXT-FRAUD": ("Fraud prevention controls", "External"),
    "EXT-EVENT": ("Business continuity & resilience", "External"),
}
# Control theme -> recommended remediation action (recommendation only; human owns it).
REMEDIATION_MAP = {
    "Supervision & error prevention": "Recommend strengthening supervisory review and second-check controls for the affected process.",
    "Training & competency": "Recommend targeted retraining and a competency attestation for staff on the affected procedure.",
    "Conduct & segregation of duties": "Recommend a segregation-of-duties review and conduct escalation to the accountable manager.",
    "Process & control design": "Recommend redesigning the control step and validating its design with control owners.",
    "Control execution & reconciliation": "Recommend reinstating the reconciliation control with exception monitoring and a completion check.",
    "Procedures & documentation": "Recommend updating the procedure and confirming staff acknowledgement.",
    "IT resilience & availability": "Recommend a resilience review of the affected system and its recovery objectives.",
    "Change management": "Recommend reinforcing pre-deployment validation and change-window enforcement.",
    "Capacity & performance management": "Recommend capacity monitoring and performance thresholds for the affected system.",
    "Third-party / vendor oversight": "Recommend a third-party control review and routing to third-party risk assessment.",
    "Fraud prevention controls": "Recommend a fraud-control gap review for the affected channel.",
    "Business continuity & resilience": "Recommend a continuity-plan review and resilience testing for the affected service.",
}
# Deterministic tie-break order when a single primary root cause must be named.
ROOT_CAUSE_ORDER = ["Process", "People", "Systems", "External"]


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _cite(ref: str) -> str:
    return str(ref) if ref else ""


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    fin = doc.get("financials") or {}
    is_near_miss = bool(doc.get("is_near_miss"))
    event_ref = _cite(doc.get("event_source_ref", ""))

    not_evaluable = []

    # --- 1. Classification (normalize against the Basel standard) ---
    reported_type = str(doc.get("reported_event_type", "")).strip()
    event_type = reported_type if reported_type in BASEL_L1 else None
    if event_type is None:
        not_evaluable.append({"item": "event_type",
                              "why": f"reported_event_type {reported_type!r} is not a Basel L1 event type"})
    reported_bl = str(doc.get("reported_business_line", "")).strip()
    business_line = reported_bl if reported_bl in BASEL_BUSINESS_LINES else None
    if business_line is None:
        not_evaluable.append({"item": "business_line",
                              "why": f"reported_business_line {reported_bl!r} is not a Basel business line"})

    # --- 2. Impact quantification (deterministic arithmetic) ---
    gross_loss = 0.0 if is_near_miss else _num(fin.get("gross_loss"))
    recoveries = fin.get("recoveries") or []
    total_recoveries = round(sum(_num(r.get("amount")) for r in recoveries), 2)
    net_loss = round(max(gross_loss - total_recoveries, 0.0), 2)
    indirect_costs = _num(fin.get("indirect_costs"))
    total_impact = round(net_loss + indirect_costs, 2)
    potential_loss = fin.get("potential_loss")

    if is_near_miss:
        if potential_loss is None:
            banding_amount = None
            not_evaluable.append({"item": "materiality",
                                  "why": "near-miss without potential_loss; severity from escalators only"})
        else:
            banding_amount = round(_num(potential_loss), 2)
    else:
        banding_amount = total_impact

    # --- 3. Escalation candidates (flags for human adjudication, never actions) ---
    reg_threshold = cfg["regulatory_reporting_threshold"]
    ba = banding_amount if banding_amount is not None else 0.0
    reg_candidate = ba >= reg_threshold or (
        event_type in SENSITIVE_EVENT_TYPES and ba >= cfg["sensitive_reporting_factor"] * reg_threshold
    )
    board_notifiable = ba >= cfg["board_notify_threshold"] or (
        bool(doc.get("customer_harm")) and int(doc.get("affected_customers") or 0) >= cfg["board_customer_threshold"]
    )

    # --- 4. Severity band (deterministic; see references/domain-rules.md) ---
    if banding_amount is None:
        severity = "Critical" if board_notifiable else ("High" if reg_candidate else "Low")
    elif banding_amount >= cfg["critical_threshold"] or board_notifiable:
        severity = "Critical"
    elif banding_amount >= cfg["high_threshold"] or reg_candidate:
        severity = "High"
    elif banding_amount >= cfg["moderate_threshold"]:
        severity = "Moderate"
    else:
        severity = "Low"

    # --- 5. Findings (each carries >= 1 cited evidence row) ---
    findings = []
    # classification finding
    findings.append({
        "id": "F-CLASS", "type": "classification",
        "statement": (f"Event classified as Basel L1 '{event_type}' in business line "
                      f"'{business_line}'." if event_type and business_line
                      else "Event classification incomplete; see not_evaluable."),
        "evidence": [{"citation": event_ref}] if event_ref else [],
    })
    # materiality finding
    mat_evidence = ([{"citation": event_ref}] if event_ref else []) + [
        {"citation": _cite(r.get("source_ref"))} for r in recoveries if r.get("source_ref")
    ]
    findings.append({
        "id": "F-IMPACT", "type": "materiality",
        "statement": (
            f"Net loss {net_loss:.2f} {doc.get('currency','')} + indirect {indirect_costs:.2f} "
            f"= total impact {total_impact:.2f}; banding amount {ba:.2f}."
            if not is_near_miss else
            f"Near-miss; potential loss {ba:.2f} {doc.get('currency','')} used for banding."),
        "evidence": mat_evidence,
    })
    # control-theme findings (one per contributing cause)
    control_themes, root_counts = [], {}
    for i, c in enumerate(doc.get("causes") or []):
        code = str(c.get("cause_code", "")).strip()
        mapped = CAUSE_MAP.get(code)
        if not mapped:
            not_evaluable.append({"item": f"cause[{i}]", "why": f"unknown cause_code {code!r}"})
            continue
        theme, category = mapped
        control_themes.append(theme)
        root_counts[category] = root_counts.get(category, 0) + 1
        findings.append({
            "id": f"F-CAUSE-{i+1}", "type": "control",
            "control_theme": theme, "root_cause_category": category,
            "statement": f"[{category}] {theme}: {c.get('description','')}",
            "evidence": [{"citation": _cite(c.get("source_ref"))}] if c.get("source_ref") else [],
        })

    # primary root cause: most frequent, tie-break by fixed order
    primary_root_cause = None
    if root_counts:
        top = max(root_counts.values())
        primary_root_cause = next(cat for cat in ROOT_CAUSE_ORDER
                                  if root_counts.get(cat, 0) == top)

    # --- 6. Remediation recommendations (recommendations only) ---
    seen, remediation = set(), []
    for theme in control_themes:
        if theme in seen:
            continue
        seen.add(theme)
        remediation.append({"control_theme": theme,
                            "recommendation": REMEDIATION_MAP.get(theme, "Recommend a control review for this theme.")})

    return {
        "event_id": doc.get("event_id"),
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "analysis_id": f"ore-{str(doc.get('event_id','')).replace(':','-')}-{doc.get('as_of')}",
        "is_near_miss": is_near_miss,
        "classification": {"basel_event_type": event_type, "business_line": business_line},
        "impact": {
            "currency": doc.get("currency"),
            "is_near_miss": is_near_miss,
            "gross_loss": round(gross_loss, 2),
            "total_recoveries": total_recoveries,
            "net_loss": net_loss,
            "indirect_costs": round(indirect_costs, 2),
            "total_impact": total_impact,
            "potential_loss": (round(_num(potential_loss), 2) if potential_loss is not None else None),
            "banding_amount": banding_amount,
        },
        "thresholds": {
            "moderate_threshold": cfg["moderate_threshold"],
            "high_threshold": cfg["high_threshold"],
            "critical_threshold": cfg["critical_threshold"],
            "regulatory_reporting_threshold": cfg["regulatory_reporting_threshold"],
            "board_notify_threshold": cfg["board_notify_threshold"],
        },
        "escalation": {
            "regulatory_reporting_candidate": bool(reg_candidate),
            "board_notifiable": bool(board_notifiable),
        },
        "severity_band": severity,
        "root_cause": {"primary": primary_root_cause, "distribution": root_counts},
        "control_themes": sorted(set(control_themes)),
        "findings": findings,
        "remediation_recommendations": remediation,
        "not_evaluable": not_evaluable,
        "requires_human_adjudication": True,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "event_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
