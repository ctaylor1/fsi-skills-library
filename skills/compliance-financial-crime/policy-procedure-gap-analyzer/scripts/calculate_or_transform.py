#!/usr/bin/env python3
"""Deterministic policy-vs-requirement gap analysis for policy-procedure-gap-analyzer.

Reads a gap-analysis pack (see validate_input.py), maps internal policy/procedure controls
to authoritative requirements, and emits an explainable set of *findings* — coverage gaps,
parameter conflicts, evidence gaps, version drift (obsolete steps), and stale reviews — each
with cited evidence and a remediation recommendation. It then tallies findings by severity
and derives a triage remediation priority.

IMPORTANT: This produces findings, evidence, and remediation *recommendations* only. It
never states or implies a compliance determination, attestation, or filing; it never closes
a finding or writes a system of record. Severity and priority are deterministic and
documented in references/domain-rules.md. Human adjudication is mandatory (R3).

Usage:
  python calculate_or_transform.py analysis.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "review_max_days": 365,   # a control not reviewed within this window is stale
}
DISCLAIMER = ("Gap-analysis findings and recommendations only; not a compliance "
              "determination, attestation, or filing. Human adjudication required.")

# Base severity by finding type; guidance-level requirements drop one band.
BASE_SEVERITY = {
    "coverage_gap": "High",
    "parameter_conflict": "High",
    "evidence_gap": "Medium",
    "version_drift": "Medium",
    "stale_review": "Low",
}
_DROP = {"High": "Medium", "Medium": "Low", "Low": "Low"}

# Parameter comparators: requirement.parameter.kind -> (expected control kind, is_conflict, describe).
# is_conflict(req_value, ctrl_value) -> True when the control WEAKENS the requirement bound.
COMPARATORS = {
    "retention_min_years": (
        "retention_years",
        lambda r, c: c < r,
        lambda r, c: f"retains {c}y < required minimum {r}y",
    ),
    "reporting_threshold_max_usd": (
        "reporting_threshold_usd",
        lambda r, c: c > r,
        lambda r, c: f"reporting threshold {c:.0f} > required maximum {r:.0f}",
    ),
    "training_max_interval_months": (
        "training_interval_months",
        lambda r, c: c > r,
        lambda r, c: f"training every {c}mo > required maximum {r}mo",
    ),
}


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _severity(finding_type: str, criticality: str) -> str:
    base = BASE_SEVERITY[finding_type]
    return _DROP[base] if criticality == "guidance" else base


def _cite_req(req: dict) -> str:
    return f"reg:{req.get('citation', req['req_id'])}@{req.get('effective_date', 'n/a')}"


def _cite_ctrl(ctrl: dict) -> str:
    return f"policy:{ctrl.get('doc', '?')}#{ctrl.get('section', '?')}@{ctrl.get('last_reviewed', 'n/a')}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = _parse_date(doc["as_of"])
    reqs = sorted(doc["requirements"], key=lambda r: r["req_id"])
    ctrls = sorted(doc.get("policy_controls", []), key=lambda c: c["control_id"])
    {c["control_id"]: c for c in ctrls}

    findings: list[dict] = []
    clean: list[str] = []
    informational: list[dict] = []
    not_evaluable: list[dict] = []
    seq = [0]

    def add(ftype, req, ctrl, reason, evidence, recommendation):
        seq[0] += 1
        crit = (req or {}).get("criticality", "control")
        findings.append({
            "finding_id": f"F{seq[0]:03d}",
            "finding_type": ftype,
            "req_id": (req or {}).get("req_id"),
            "control_id": (ctrl or {}).get("control_id"),
            "criticality": crit,
            "severity": _severity(ftype, crit),
            "reason": reason,
            "evidence": evidence,
            "recommendation": recommendation,
        })

    # --- Requirement-driven findings ---
    for req in reqs:
        rid = req["req_id"]
        if not req.get("applicable", True):
            informational.append({"req_id": rid, "why": "marked not applicable to this scope"})
            continue
        if _parse_date(req["effective_date"]) > as_of:
            informational.append({"req_id": rid, "why": f"not yet in effect (effective {req['effective_date']})"})
            continue

        active = [c for c in ctrls if rid in (c.get("maps_to") or []) and c.get("status") == "active"]
        if not active:
            add("coverage_gap", req, None,
                f"no active policy/procedure control maps to in-effect requirement {rid}",
                [{"req_id": rid, "obligation": req.get("obligation"), "citation": _cite_req(req)}],
                f"Draft or adopt a policy/procedure covering {rid}; assign an owner and target "
                f"date. Recommendation only, for human adjudication.")
            continue

        # evidence_gap: requirement expects evidence but no active control records an evidence_ref
        if req.get("evidence_expected") and not any(c.get("evidence_ref") for c in active):
            ctrl = active[0]
            add("evidence_gap", req, ctrl,
                f"requirement {rid} expects retained evidence but mapped control(s) record none",
                [{"req_id": rid, "control_id": ctrl["control_id"], "citation": _cite_ctrl(ctrl)}],
                f"Establish and record the evidence artifact demonstrating {ctrl['control_id']} "
                f"operates as required by {rid}.")

        # parameter_conflict + version_drift: per active control
        rparam = req.get("parameter") or {}
        for ctrl in active:
            cparam = ctrl.get("parameter") or {}
            kind = rparam.get("kind")
            if kind in COMPARATORS:
                exp_kind, is_conflict, describe = COMPARATORS[kind]
                if cparam.get("kind") == exp_kind:
                    rv, cv = float(rparam["value"]), float(cparam["value"])
                    if is_conflict(rv, cv):
                        add("parameter_conflict", req, ctrl,
                            f"control {ctrl['control_id']} {describe(rv, cv)} (requirement {rid})",
                            [{"req_id": rid, "control_id": ctrl["control_id"],
                              "req_bound": rparam, "control_value": cparam,
                              "citation": _cite_ctrl(ctrl)},
                             {"req_id": rid, "citation": _cite_req(req)}],
                            f"Reconcile {ctrl['control_id']} to satisfy the {rid} bound; route the "
                            f"wording change to the policy owner.")
                elif cparam:
                    not_evaluable.append({"req_id": rid, "control_id": ctrl["control_id"],
                                          "why": f"control parameter kind {cparam.get('kind')!r} "
                                                 f"does not match requirement kind {kind!r}"})

            rver, cver = req.get("version"), ctrl.get("references_version")
            if rver and cver and str(rver) != str(cver):
                add("version_drift", req, ctrl,
                    f"control {ctrl['control_id']} references version {cver!r}; requirement {rid} "
                    f"is now version {rver!r} (procedure steps may be obsolete)",
                    [{"req_id": rid, "control_id": ctrl["control_id"],
                      "control_version": cver, "requirement_version": rver,
                      "citation": _cite_ctrl(ctrl)}],
                    f"Update {ctrl['control_id']} to reference requirement version {rver!r} and "
                    f"confirm the procedure steps still align.")

        produced = {f["req_id"] for f in findings if f["req_id"] == rid}
        if rid not in produced:
            clean.append(rid)

    # --- Control-driven finding: stale review (evaluate each active control once) ---
    for ctrl in ctrls:
        if ctrl.get("status") != "active":
            continue
        lr = ctrl.get("last_reviewed")
        if not lr:
            not_evaluable.append({"control_id": ctrl["control_id"], "why": "no last_reviewed date"})
            continue
        age = (as_of - _parse_date(lr)).days
        if age > cfg["review_max_days"]:
            add("stale_review", None, ctrl,
                f"control {ctrl['control_id']} last reviewed {lr} ({age}d ago), exceeds the "
                f"{cfg['review_max_days']}-day review cycle",
                [{"control_id": ctrl["control_id"], "last_reviewed": lr, "citation": _cite_ctrl(ctrl)}],
                f"Schedule a review of {ctrl['control_id']}; last reviewed {lr} exceeds the "
                f"{cfg['review_max_days']}-day cycle.")

    counts = {"High": 0, "Medium": 0, "Low": 0}
    for f in findings:
        counts[f["severity"]] += 1
    if counts["High"]:
        priority = "Priority-1"
    elif counts["Medium"]:
        priority = "Priority-2"
    elif counts["Low"]:
        priority = "Priority-3"
    else:
        priority = "None"

    return {
        "analysis_id": f"ppga-{doc.get('framework', 'fw').replace(' ', '')}-{doc['as_of']}-0001",
        "framework": doc.get("framework"),
        "jurisdiction": doc.get("jurisdiction"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "findings": findings,
        "clean_requirements": sorted(set(clean)),
        "informational": informational,
        "not_evaluable": not_evaluable,
        "severity_counts": counts,
        "remediation_priority": priority,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "analysis_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
