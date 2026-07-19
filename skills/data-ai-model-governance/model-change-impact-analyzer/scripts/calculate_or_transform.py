#!/usr/bin/env python3
"""Deterministic, explainable change-impact assessment for model-change-impact-analyzer.

Reads a proposed model/agent change record (see validate_input.py), evaluates each change
dimension against the configured rules, attaches evidence + citations to every fired
dimension, maps the fired set to an impact band, and derives a recommended revalidation
scope and governance path.

IMPORTANT: This produces explainable *findings and a recommendation for human adjudication*
only. It never approves, deploys, releases, waives revalidation for, closes, or attests a
change, and never makes an autonomous regulated decision. Banding is deterministic and
documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py change_record.json     # prints the assessment JSON
  python calculate_or_transform.py --selftest             # runs on the bundled fixture,
                                                           # prints JSON + a self-check line
Prints the assessment JSON to stdout. Under --selftest also validates internal invariants
and prints "compute self-check: N error(s)" (exit 1 if any invariant fails).
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Flags that, when attached to a *changed* dimension, force the highest impact band because
# they weaken a control, broaden autonomy, or move the regulatory surface.
CRITICAL_FLAGS = {
    "control_weakened", "oversight_removed", "autonomy_increased",
    "regulatory_surface_changed", "threshold_loosened",
}
# Dimensions whose change tends to require independent revalidation on a material model.
HIGH_WEIGHT = {"data", "behavior", "scope", "regulatory"}
KNOWN_DIMENSIONS = ["scope", "data", "tools", "behavior", "controls",
                    "testing", "users", "regulatory"]

SCOPE_BY_BAND = {
    "Critical": "Full independent revalidation before deployment",
    "High": "Targeted independent revalidation of affected components before deployment",
    "Moderate": "Owner-led revalidation with independent model-risk review before deployment",
    "Low": "Revalidation not triggered under configured thresholds; record change and enhance monitoring",
}
GOVERNANCE_BY_BAND = {
    "Critical": "Independent model validation and change-governance adjudication required before any deployment",
    "High": "Independent model-risk review and change-governance adjudication required before any deployment",
    "Moderate": "Model-risk notification and owner review required before any deployment",
    "Low": "Record in model inventory and monitor; route to periodic review",
}
DISCLAIMER = ("Impact assessment and revalidation recommendation only; not a change approval "
              "or deployment authorization. No model change has been approved, deployed, or attested.")

DEFAULT_CONFIG = {
    "band_high_min_dims": 3,        # >= this many changed dimensions -> at least High
    "high_materiality_min_dims": 2, # high-materiality + high-weight + this many dims -> Critical
}


def expected_band(fired_dims: list[str], critical_flags: list[str], materiality: str,
                  cfg: dict) -> str:
    """Deterministic banding (mirrored in validate_output.py). Documented in domain-rules.md."""
    n = len(fired_dims)
    high_weight_hit = bool(set(fired_dims) & HIGH_WEIGHT)
    if critical_flags or (materiality == "high" and high_weight_hit
                          and n >= cfg["high_materiality_min_dims"]):
        return "Critical"
    if n >= cfg["band_high_min_dims"] or (materiality == "high" and high_weight_hit):
        return "High"
    if n >= 1:
        return "Moderate"
    return "Low"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    model = doc["model"]
    materiality = model["materiality"]
    supplied = {d.get("dimension"): d for d in doc["dimensions"]}

    findings, not_evaluable = [], []
    critical_flags_fired: list[str] = []

    for name in KNOWN_DIMENSIONS:
        d = supplied.get(name)
        if d is None:
            not_evaluable.append({"dimension": name, "why": "not supplied in change record"})
            continue
        changed = bool(d.get("changed"))
        flags = [f for f in (d.get("risk_flags") or []) if isinstance(f, str)]
        crit = sorted(set(flags) & CRITICAL_FLAGS)
        if changed:
            critical_flags_fired.extend(crit)
        evidence = []
        if changed:
            evidence = [{
                "field": name,
                "before": d.get("before", ""),
                "after": d.get("after", ""),
                "citation": str(d.get("evidence_ref", "")).strip(),
            }]
        reason = _reason(name, changed, flags, crit)
        findings.append({
            "dimension": name,
            "fired": changed,
            "reason": reason,
            "risk_flags": flags,
            "critical": bool(crit),
            "high_weight": name in HIGH_WEIGHT,
            "evidence": evidence,
        })

    fired_dims = [f["dimension"] for f in findings if f["fired"]]
    critical_flags_fired = sorted(set(critical_flags_fired))
    band = expected_band(fired_dims, critical_flags_fired, materiality, cfg)

    adjudicator_prompts = []
    if fired_dims:
        adjudicator_prompts = [
            "Confirm the change is within the model's approved use; a net-new use case is an intake, not a change.",
            "Verify independent validation coverage for each changed component before deployment.",
            "Confirm fair-lending / adverse-action impact of any threshold or cutoff change.",
            "Confirm data-lineage and provenance review for any changed data source.",
            "Confirm monitoring and rollback are in place for the changed behavior.",
            "Record the human adjudication decision and rationale in the change record.",
        ]

    return {
        "assessment_id": f"mcia-{model['model_id']}-{doc['as_of']}-0001",
        "change_id": doc["change_id"],
        "model_id": model["model_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "config": cfg,
        "model_materiality": materiality,
        "regulated_use": bool(model.get("regulated_use")),
        "is_agent": bool(model.get("is_agent")),
        "dimensions": findings,
        "fired_dimensions": fired_dims,
        "critical_flags_fired": critical_flags_fired,
        "impact_band": band,
        "recommended_revalidation_scope": SCOPE_BY_BAND[band],
        "recommended_governance_path": GOVERNANCE_BY_BAND[band],
        "not_evaluable": not_evaluable,
        "adjudicator_prompts": adjudicator_prompts,
        "disclaimer": DISCLAIMER,
    }


def _reason(name: str, changed: bool, flags: list[str], crit: list[str]) -> str:
    if not changed:
        return f"{name}: no change declared"
    base = f"{name} changed"
    if crit:
        return f"{base}; critical flag(s) {crit} weaken a control / broaden autonomy / move regulatory surface (finding only, not a decision)"
    if flags:
        return f"{base}; risk flag(s) {flags} noted"
    return f"{base}; no critical risk flag"


def _selfcheck(pack: dict) -> list[str]:
    """Internal invariants used by --selftest; independent of validate_output.py."""
    errs = []
    # recompute the band with the effective config the pack was produced under
    cfg = {**DEFAULT_CONFIG, **(pack.get("config") or {})}
    exp = expected_band(pack["fired_dimensions"], pack["critical_flags_fired"],
                        pack["model_materiality"], cfg)
    if pack["impact_band"] != exp:
        errs.append(f"impact_band {pack['impact_band']!r} != recomputed {exp!r}")
    if pack["recommended_revalidation_scope"] != SCOPE_BY_BAND[pack["impact_band"]]:
        errs.append("recommended_revalidation_scope does not match band mapping")
    for f in pack["dimensions"]:
        if f["fired"]:
            if not f["evidence"] or not (f["evidence"][0].get("citation") or "").strip():
                errs.append(f"fired dimension {f['dimension']} missing cited evidence")
    return errs


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "change_record_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    pack = compute(doc)
    print(json.dumps(pack, indent=2))
    if selftest:
        errs = _selfcheck(pack)
        for e in errs:
            print("ERROR", e)
        print(f"compute self-check: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
