#!/usr/bin/env python3
"""Deterministic output validation for model-change-impact-analyzer.

Validates the final change-impact pack (the calculate_or_transform core + a narrative)
before it is presented or handed to a governance forum. Fails closed (R3 decision-support):
the skill may recommend, never decide. Checks:
  1. Every fired dimension has >= 1 cited evidence row.
  2. impact_band equals the deterministic banding of the fired dimensions, recomputed with
     the SAME versioned banding config the engine used (read from pack["config"], merged over
     the documented defaults) so a legitimately-tuned config validates instead of false-failing.
  3. recommended_revalidation_scope matches the band mapping.
  4. No approval / deployment / closure / waiver / attestation language (prohibited-decision
     screen for R3) in the narrative, notes, or dimension reasons.
  5. The standing disclaimer is present.
  6. adjudicator_prompts are included when any dimension fired.

Usage:
  python validate_output.py impact_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

CRITICAL_FLAGS = {
    "control_weakened", "oversight_removed", "autonomy_increased",
    "regulatory_surface_changed", "threshold_loosened",
}
HIGH_WEIGHT = {"data", "behavior", "scope", "regulatory"}
# Banding thresholds are configuration (versioned, owned by Model Risk Governance), not
# hard-coded judgments. These mirror calculate_or_transform.DEFAULT_CONFIG and are only used
# when the pack does not carry an explicit override.
DEFAULT_CONFIG = {
    "band_high_min_dims": 3,        # >= this many changed dimensions -> at least High
    "high_materiality_min_dims": 2, # high-materiality + high-weight + this many dims -> Critical
}
SCOPE_BY_BAND = {
    "Critical": "Full independent revalidation before deployment",
    "High": "Targeted independent revalidation of affected components before deployment",
    "Moderate": "Owner-led revalidation with independent model-risk review before deployment",
    "Low": "Revalidation not triggered under configured thresholds; record change and enhance monitoring",
}
DISCLAIMER = ("Impact assessment and revalidation recommendation only; not a change approval "
              "or deployment authorization. No model change has been approved, deployed, or attested.")

# Prohibited-decision assertions an R3 decision-support skill must never make. These catch
# the skill *asserting a decision has been made* (approve / deploy / waive / close / attest),
# not statements that a human must decide (e.g. "a human must approve before deployment").
DECISION_PATTERNS = [
    r"\bchange is approved\b", r"\bapproved for (deployment|production|release|go[- ]?live)\b",
    r"\bwe approve\b", r"\bi approve\b", r"\bapprove the change\b", r"\bfinal approval (granted|is complete)\b",
    r"\bauthoriz(e|ed) (the )?(deployment|release|change)\b",
    r"\bcleared (to|for) (deploy|deployment|release|production|go[- ]?live)\b",
    r"\bproceed with (the )?deployment\b", r"\bdeploy the (change|model) now\b",
    r"\bgo[- ]?live approved\b", r"\bwaive (the )?revalidation\b", r"\brevalidation (is )?waived\b",
    r"\bno revalidation (is )?required\b", r"\bsigned[- ]off\b", r"\bsign[- ]off (is )?complete\b",
    r"\battestation (is )?complete\b", r"\bself[- ]?certif", r"\bchange (is )?closed\b",
    r"\bclose (out )?the change\b", r"\bauto[- ]?approve", r"\bno further (review|validation) (is )?needed\b",
]


def expected_band(fired_dims, critical_flags, materiality, cfg=None):
    """Deterministic banding, mirrored from calculate_or_transform.expected_band.

    Thresholds come from ``cfg`` (the versioned banding config the engine used); missing
    keys fall back to DEFAULT_CONFIG so the validator honors a tuned config instead of a
    hard-coded threshold. Documented in references/domain-rules.md.
    """
    cfg = {**DEFAULT_CONFIG, **(cfg or {})}
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


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    dims = pack.get("dimensions") or []
    fired = [d for d in dims if d.get("fired")]
    fired_names = [d["dimension"] for d in fired]

    for d in fired:
        ev = d.get("evidence") or []
        if not ev:
            errors.append(f"fired dimension {d['dimension']} has no evidence")
        for row in ev:
            if not (str(row.get("citation") or "").strip()):
                errors.append(f"fired dimension {d['dimension']} evidence row missing citation")

    # recompute critical flags from the fired dimensions (do not trust the summary field)
    crit = sorted({f for d in fired for f in (d.get("risk_flags") or []) if f in CRITICAL_FLAGS})
    # honor the same versioned banding config the engine used (carried on the pack), merged
    # over documented defaults; do not re-derive the band from hard-coded thresholds.
    cfg = {**DEFAULT_CONFIG, **(pack.get("config") or {})}
    exp = expected_band(fired_names, crit, pack.get("model_materiality"), cfg)
    if pack.get("impact_band") != exp:
        errors.append(f"impact_band {pack.get('impact_band')!r} != deterministic {exp!r} for fired={fired_names}")

    band = pack.get("impact_band")
    if band in SCOPE_BY_BAND and pack.get("recommended_revalidation_scope") != SCOPE_BY_BAND[band]:
        errors.append(f"recommended_revalidation_scope does not match band {band!r} mapping")

    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(d.get("reason", "")) for d in dims])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited-decision language detected: {m.group(0)!r} (R3 recommends; it does not decide/approve/deploy)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if fired_names and not pack.get("adjudicator_prompts"):
        errors.append("dimensions fired but no adjudicator_prompts included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "impact_pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
