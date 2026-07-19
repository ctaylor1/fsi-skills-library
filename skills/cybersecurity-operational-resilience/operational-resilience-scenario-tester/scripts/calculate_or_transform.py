#!/usr/bin/env python3
"""Deterministic operational-resilience scenario-test engine.

Reads a scenario-test package (see validate_input.py), and for each scenario computes,
against the target important business service:
  - severity / plausibility quality flags (severe-but-plausible rubric),
  - impact-tolerance test outcome (within / breach / not_evaluable) for downtime and data
    loss, with the recovery margin,
  - dependency-coverage completeness (which mapped dimensions were exercised),
  - decision-evidence completeness (owner + timestamp + evidence_ref per decision),
  - recovery-evidence presence,
and maps the full result set to a **suggested review disposition** band for a human.

IMPORTANT: This produces test evidence and a triage suggestion ONLY. It never produces a
resilience self-assessment sign-off, a compliance determination, a regulatory filing, an
attestation, or a case closure. Those require human adjudication (see references/controls.md
and references/domain-rules.md). The disposition mapping is deterministic and documented.

Usage:
  python calculate_or_transform.py package.json | --selftest
Prints the scenario-test JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "severity_levels": ["moderate", "severe", "extreme"],
    "plausibility_levels": ["implausible", "plausible", "highly_plausible"],
    "min_severity_for_test": "severe",
    "min_plausibility_for_test": "plausible",
    "margin_buffer_hours": 1.0,
    "dependency_dimensions": ["people", "process", "technology", "facilities", "third_parties", "data"],
}
DISCLAIMER = ("Scenario-test evidence and recommendations only; not a resilience "
              "self-assessment sign-off, compliance determination, regulatory filing, or "
              "attestation. Human adjudication required before any decision or submission.")
HIGH_LESSON = {"high", "severe", "critical"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _tolerance_leg(observed_hours, tolerance_hours):
    """Compute one leg (downtime or data loss) of the impact-tolerance test."""
    obs = _num(observed_hours)
    tol = _num(tolerance_hours)
    if obs is None or tol is None:
        return {"tolerance_hours": tolerance_hours, "observed_hours": observed_hours,
                "outcome": "not_evaluable", "margin_hours": None}
    margin = round(tol - obs, 4)
    return {"tolerance_hours": tol, "observed_hours": obs,
            "outcome": "within" if obs <= tol else "breach", "margin_hours": margin}


def _disposition(scenarios: list) -> str:
    """Deterministic mapping from the computed scenario set to a review disposition.

    Documented in references/domain-rules.md. Kept identical in validate_output.py.
    """
    outcomes = [s["outcome"] for s in scenarios]
    lesson_sev = [str(l.get("severity", "")).lower()
                  for s in scenarios for l in s.get("lessons", [])]
    if "breach" in outcomes or any(x in HIGH_LESSON for x in lesson_sev):
        return "Escalate"
    review = (
        any(s.get("coverage", {}).get("missing_dimensions") for s in scenarios)
        or any(x == "medium" for x in lesson_sev)
        or any(s.get("thin_margin") for s in scenarios)
        or any(s.get("quality_flags") for s in scenarios)
        or any(s.get("decision_gaps") for s in scenarios)
        or "not_evaluable" in outcomes
    )
    return "Review" if review else "Informational"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    sev_levels = cfg["severity_levels"]
    plaus_levels = cfg["plausibility_levels"]
    buffer = float(cfg["margin_buffer_hours"])
    dims_all = cfg["dependency_dimensions"]
    min_sev_i = sev_levels.index(cfg["min_severity_for_test"]) if cfg["min_severity_for_test"] in sev_levels else 0
    min_plaus_i = plaus_levels.index(cfg["min_plausibility_for_test"]) if cfg["min_plausibility_for_test"] in plaus_levels else 0

    services = {s["service_id"]: s for s in doc["important_business_services"]}
    out_scenarios = []
    not_evaluable = []
    remediation_actions = []

    for sc in doc["scenarios"]:
        svc = services.get(sc["service_id"], {})
        tol = svc.get("impact_tolerance") or {}
        obs = sc.get("observed") or {}

        # severe-but-plausible rubric quality flags
        quality_flags = []
        sev = sc.get("severity")
        plaus = sc.get("plausibility")
        if sev in sev_levels and sev_levels.index(sev) < min_sev_i:
            quality_flags.append("below_severe_threshold")
        if plaus in plaus_levels and plaus_levels.index(plaus) < min_plaus_i:
            quality_flags.append("below_plausibility_threshold")

        # impact-tolerance test (downtime + data loss)
        downtime = _tolerance_leg(obs.get("time_to_recover_hours"), tol.get("max_downtime_hours"))
        data_loss = _tolerance_leg(obs.get("data_loss_hours"), tol.get("max_data_loss_hours"))
        legs = [downtime, data_loss]
        outcomes = [leg["outcome"] for leg in legs]
        if "not_evaluable" in [downtime["outcome"]]:
            outcome = "not_evaluable"
        elif "breach" in outcomes:
            outcome = "breach"
        else:
            outcome = "within"
        thin_margin = outcome == "within" and any(
            leg["margin_hours"] is not None and leg["margin_hours"] < buffer for leg in legs)
        if outcome == "not_evaluable":
            not_evaluable.append({"scenario_id": sc["scenario_id"],
                                  "why": "observed.time_to_recover_hours missing"})

        # dependency coverage
        deps = svc.get("dependencies") or {}
        declared = [d for d in dims_all if deps.get(d)]
        exercised = [d for d in (sc.get("dimensions_exercised") or []) if d in declared]
        missing = [d for d in declared if d not in exercised]
        coverage = {"declared_dimensions": declared, "exercised_dimensions": exercised,
                    "missing_dimensions": missing,
                    "coverage_ratio": round(len(exercised) / len(declared), 3) if declared else None}

        # decision-evidence completeness
        decisions = []
        decision_gaps = []
        for d in (sc.get("decisions") or []):
            complete = bool(d.get("owner_role")) and bool(d.get("timestamp")) and bool(d.get("evidence_ref"))
            decisions.append({"decision_id": d.get("decision_id"), "description": d.get("description"),
                              "owner_role": d.get("owner_role"), "timestamp": d.get("timestamp"),
                              "evidence_ref": d.get("evidence_ref"), "complete": complete})
            if not complete:
                decision_gaps.append(d.get("decision_id"))

        recovery = sc.get("recovery_evidence") or []
        lessons = sc.get("lessons") or []
        for l in lessons:
            remediation_actions.append({
                "scenario_id": sc["scenario_id"], "lesson_id": l.get("lesson_id"),
                "description": l.get("description"), "severity": l.get("severity"),
                "remediation_owner_role": l.get("remediation_owner_role"),
                "evidence_ref": l.get("evidence_ref"),
                "status": "open_for_human_adjudication"})

        # evidence citations for the scenario
        evidence = []
        for d in decisions:
            if d.get("evidence_ref"):
                evidence.append({"kind": "decision", "ref": d["decision_id"], "citation": d["evidence_ref"]})
        for r in recovery:
            if r.get("source_ref"):
                evidence.append({"kind": "recovery", "ref": r.get("evidence_id"), "citation": r["source_ref"]})

        gaps = []
        if not recovery:
            gaps.append("no recovery evidence recorded")
        if missing:
            gaps.append(f"dependency dimensions not exercised: {', '.join(missing)}")
        if decision_gaps:
            gaps.append(f"incomplete decision records: {', '.join(str(x) for x in decision_gaps)}")
        if quality_flags:
            gaps.append(f"scenario rubric flags: {', '.join(quality_flags)}")

        out_scenarios.append({
            "scenario_id": sc["scenario_id"], "service_id": sc["service_id"],
            "title": sc.get("title"), "threat_type": sc.get("threat_type"),
            "severity": sev, "plausibility": plaus, "quality_flags": quality_flags,
            "tolerance_test": {"downtime": downtime, "data_loss": data_loss},
            "outcome": outcome, "thin_margin": thin_margin,
            "coverage": coverage,
            "decisions": decisions, "decision_gaps": decision_gaps,
            "recovery_evidence_count": len(recovery),
            "lessons": [{"lesson_id": l.get("lesson_id"), "severity": l.get("severity"),
                         "description": l.get("description")} for l in lessons],
            "evidence": evidence, "gaps": gaps,
        })

    disposition = _disposition(out_scenarios)
    return {
        "test_id": f"opres-{doc['programme_id']}-{doc['as_of']}-0001",
        "programme_id": doc["programme_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "scenarios": out_scenarios,
        "breaches": [s["scenario_id"] for s in out_scenarios if s["outcome"] == "breach"],
        "not_evaluable": not_evaluable,
        "suggested_disposition": disposition,
        "remediation_actions": remediation_actions,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "scenario_pack_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
