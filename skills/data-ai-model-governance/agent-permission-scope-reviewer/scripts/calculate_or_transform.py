#!/usr/bin/env python3
"""Deterministic least-privilege rule engine for agent-permission-scope-reviewer.

Reads an agent permission manifest (see validate_input.py), evaluates every operation
against the approved least-privilege ruleset (see references/domain-rules.md), attaches
cited evidence to each finding, and maps the finding-severity profile to a recommended
disposition band. Emits a machine-readable core the SKILL wraps in a plain-language pack.

IMPORTANT: This produces *findings and a recommended disposition for a human adjudicator*
only. It never renders an access decision and never grants, revokes, or provisions an
entitlement. The disposition mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py manifest.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "max_recert_days": 365,
    "max_recert_days_restricted": 90,
    "high_classes": ["Highly Confidential", "Restricted"],
    "log_required_classes": ["Confidential", "Highly Confidential", "Restricted"],
}
DISCLAIMER = ("Least-privilege review evidence only; not an access approval or denial. No "
              "entitlement has been granted, revoked, or provisioned, and no review has been "
              "closed. Human adjudication is required.")
SEVERITY_RANK = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}


def _eff_write(op: dict) -> bool:
    return bool(op.get("writes")) or op.get("access_mode") == "auto-write"


def _cite_field(op: dict, field, as_of: str) -> str:
    return f"manifest:op={op.get('op_id','?')};field={field}@{as_of}"


def _cite_rule(rule_id: str, policy_version) -> str:
    return f"policy:{policy_version}#{rule_id}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    high_classes = set(cfg["high_classes"])
    log_required = set(cfg["log_required_classes"])
    ops = doc["operations"]
    as_of = doc["as_of"]
    policy_version = doc.get("policy_version")
    environment = doc.get("environment")
    declared_scope = set(doc.get("data_classifications_in_scope") or [])

    findings, not_evaluable = [], []

    def add(rule_id, op, dimension, severity, reason, evidence, remediation):
        findings.append({
            "rule_id": rule_id,
            "op_id": op.get("op_id") if isinstance(op, dict) else op,
            "tool": op.get("tool") if isinstance(op, dict) else None,
            "operation": op.get("operation") if isinstance(op, dict) else None,
            "dimension": dimension,
            "severity": severity,
            "reason": reason,
            "evidence": evidence,
            "recommended_remediation": remediation,
        })

    def ne(op_id, rule_id, why):
        not_evaluable.append({"op_id": op_id, "rule_id": rule_id, "why": why})

    for op in ops:
        oid = op.get("op_id")
        dc = op.get("data_classification")
        mode = op.get("access_mode")
        gate = op.get("approval_gate")
        eff_write = _eff_write(op)

        # LP-NEED-01 — user need / justification
        if not op.get("declared_need") or not op.get("justification_ref"):
            add("LP-NEED-01", op, "need", "High",
                "operation lacks a declared business need and/or an approving justification reference",
                [{"field": "declared_need/justification_ref",
                  "value": {"declared_need": op.get("declared_need"),
                            "justification_ref": op.get("justification_ref")},
                  "citation": _cite_field(op, "declared_need", as_of)},
                 {"field": "policy", "value": "LP-NEED-01", "citation": _cite_rule("LP-NEED-01", policy_version)}],
                "recommend the adjudicator require a documented business need and approving reference before any grant")

        # LP-WRITE-NOGATE — effective write without a required approval gate
        if eff_write and gate != "required":
            add("LP-WRITE-NOGATE", op, "approval-gate", "Critical",
                f"effective write (access_mode={mode!r}, writes={op.get('writes')!r}) with approval_gate={gate!r} (not 'required')",
                [{"field": "approval_gate", "value": gate, "citation": _cite_field(op, "approval_gate", as_of)},
                 {"field": "access_mode", "value": mode, "citation": _cite_field(op, "access_mode", as_of)},
                 {"field": "policy", "value": "LP-WRITE-NOGATE", "citation": _cite_rule("LP-WRITE-NOGATE", policy_version)}],
                "recommend the adjudicator require approval_gate='required' or reduce the operation to read-only")

        # LP-CLASS-MODE — auto-write over sensitive data without required gate
        if dc is None:
            ne(oid, "LP-CLASS-MODE", "missing data_classification")
            ne(oid, "LP-CLASS-UNDECLARED", "missing data_classification")
        else:
            if dc in high_classes and mode == "auto-write" and gate != "required":
                add("LP-CLASS-MODE", op, "least-privilege", "Critical",
                    f"auto-write access to {dc!r} data without approval_gate='required'",
                    [{"field": "data_classification", "value": dc, "citation": _cite_field(op, "data_classification", as_of)},
                     {"field": "access_mode", "value": mode, "citation": _cite_field(op, "access_mode", as_of)},
                     {"field": "policy", "value": "LP-CLASS-MODE", "citation": _cite_rule("LP-CLASS-MODE", policy_version)}],
                    "recommend the adjudicator narrow the mode to read-only or require an approval gate for sensitive-data writes")
            # LP-CLASS-UNDECLARED — touches a classification not in declared scope
            if declared_scope and dc not in declared_scope:
                add("LP-CLASS-UNDECLARED", op, "data-classification", "High",
                    f"operation touches {dc!r} data, which is not in the manifest's declared classification scope",
                    [{"field": "data_classification", "value": dc, "citation": _cite_field(op, "data_classification", as_of)},
                     {"field": "declared_scope", "value": sorted(declared_scope),
                      "citation": _cite_field(op, "data_classification", as_of)},
                     {"field": "policy", "value": "LP-CLASS-UNDECLARED", "citation": _cite_rule("LP-CLASS-UNDECLARED", policy_version)}],
                    "recommend the adjudicator require the classification be added to declared scope with justification, or remove the operation")
            elif not declared_scope:
                ne(oid, "LP-CLASS-UNDECLARED", "manifest has no data_classifications_in_scope")

        # LP-LOG-OFF — audit logging off for a classified source
        if dc in log_required:
            if op.get("logged") is False:
                add("LP-LOG-OFF", op, "logging", "High",
                    f"audit logging is disabled for a {dc!r} source",
                    [{"field": "logged", "value": op.get("logged"), "citation": _cite_field(op, "logged", as_of)},
                     {"field": "policy", "value": "LP-LOG-OFF", "citation": _cite_rule("LP-LOG-OFF", policy_version)}],
                    "recommend the adjudicator require audit logging be enabled before any grant")
            elif "logged" not in op:
                ne(oid, "LP-LOG-OFF", "logged flag absent; cannot confirm audit logging")

        # LP-ENV-PROD — production effective write with no gate at all
        if environment == "production" and eff_write and gate == "none":
            add("LP-ENV-PROD", op, "least-privilege", "High",
                "production environment with an ungated effective-write operation",
                [{"field": "environment", "value": environment, "citation": _cite_field(op, "environment", as_of)},
                 {"field": "approval_gate", "value": gate, "citation": _cite_field(op, "approval_gate", as_of)},
                 {"field": "policy", "value": "LP-ENV-PROD", "citation": _cite_rule("LP-ENV-PROD", policy_version)}],
                "recommend the adjudicator block production promotion until the write is gated or removed")

        # LP-REVOKE-MISSING — no revocation / recert cadence, or cadence too long
        rev = op.get("revocation")
        max_r = cfg["max_recert_days_restricted"] if dc == "Restricted" else cfg["max_recert_days"]
        if not rev or rev.get("recert_days") is None:
            add("LP-REVOKE-MISSING", op, "revocation", "Medium",
                "no revocation terms or recertification cadence defined",
                [{"field": "revocation", "value": rev, "citation": _cite_field(op, "revocation", as_of)},
                 {"field": "policy", "value": "LP-REVOKE-MISSING", "citation": _cite_rule("LP-REVOKE-MISSING", policy_version)}],
                "recommend the adjudicator require a revocation owner and a recertification cadence")
        elif rev.get("recert_days") > max_r:
            add("LP-REVOKE-MISSING", op, "revocation", "Medium",
                f"recertification cadence {rev.get('recert_days')}d exceeds the maximum {max_r}d for {dc!r}",
                [{"field": "revocation.recert_days", "value": rev.get("recert_days"), "citation": _cite_field(op, "revocation", as_of)},
                 {"field": "policy", "value": "LP-REVOKE-MISSING", "citation": _cite_rule("LP-REVOKE-MISSING", policy_version)}],
                "recommend the adjudicator require a shorter recertification cadence for this classification")

    # LP-SOD-COMBO — agent-level segregation-of-duties conflict (write + approve duties)
    write_ops = [op for op in ops if _eff_write(op)]
    approve_ops = [op for op in ops if op.get("segregation_group") == "approve"]
    if write_ops and approve_ops:
        ev = [{"field": "segregation_group", "value": "write",
               "citation": _cite_field(op, "segregation_group", as_of)} for op in write_ops]
        ev += [{"field": "segregation_group", "value": "approve",
                "citation": _cite_field(op, "segregation_group", as_of)} for op in approve_ops]
        ev.append({"field": "policy", "value": "LP-SOD-COMBO", "citation": _cite_rule("LP-SOD-COMBO", policy_version)})
        findings.append({
            "rule_id": "LP-SOD-COMBO", "op_id": "AGENT", "tool": None, "operation": None,
            "dimension": "segregation-of-duties", "severity": "High",
            "reason": "agent holds both effective-write and approve duties, a segregation-of-duties conflict",
            "evidence": ev,
            "recommended_remediation": "recommend the adjudicator split write and approve duties across separate agents/identities",
        })

    severities = [f["severity"] for f in findings]
    counts = {s: severities.count(s) for s in ("Critical", "High", "Medium", "Low") if severities.count(s)}
    if "Critical" in severities:
        disposition = "Remediate-before-approval"
    elif "High" in severities:
        disposition = "Conditional-adjudication-required"
    elif severities:
        disposition = "Review-minor-findings"
    else:
        disposition = "No-exceptions-adjudication-required"

    return {
        "review_id": f"apsr-{str(doc.get('agent_id','agent')).replace(' ', '_')}-{as_of}-0001",
        "agent_id": doc.get("agent_id"),
        "as_of": as_of,
        "policy_version": policy_version,
        "environment": environment,
        "operations_reviewed": len(ops),
        "severity_counts": counts,
        "findings": findings,
        "not_evaluable": not_evaluable,
        "recommended_disposition": disposition,
        "human_adjudication_required": True,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "scope_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
