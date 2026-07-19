#!/usr/bin/env python3
"""Deterministic output validation for stress-test-scenario-designer.

Validates the final scenario-design pack (the calculate_or_transform core + a narrative)
before it is presented or handed off. This is the R3 fail-closed screen. Checks:
  1. Structural completeness — every scenario has transmission channels + assumptions;
     every stress scenario also has management actions; each impact has a numeric
     distance_to_breach.
  2. Coverage — no scenario carries coverage_gaps.
  3. Reverse stress — present, names a constraint, and reports a scaling_multiple
     (or an explicit "not reachable" interpretation).
  4. Readiness tie-out — readiness_band equals the deterministic mapping from the pack's
     own structural/coverage/monotonicity/plausibility flags (see references/domain-rules.md).
  5. Prohibited decision/adoption/filing/advice language is absent (narrative + notes +
     scenario free-text), enforcing the R3 boundary.
  6. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Scenario design evidence and recommendations only; not an approved stress "
              "scenario, a capital or liquidity decision, a set limit, or a regulatory "
              "submission. Human adjudication (risk committee / model risk / board) is "
              "required before adoption.")

# Affirmative regulated-decision / adoption / filing / advice assertions an R3
# decision-support skill must NEVER make. Phrased to catch positive assertions while
# leaving factual/cautionary narration ("... before adoption", "not a decision") alone.
PROHIBITED_PATTERNS = [
    r"\bis adopted\b", r"\bare adopted\b", r"\bwe adopt\b", r"\badopt this scenario\b",
    r"\badopted as (the |our )?official\b",
    r"\bis approved\b", r"\bhas been approved\b", r"\bboard has approved\b",
    r"\bboard-approved\b", r"\bapprove(d)? the (scenario|capital plan|distribution|dividend)\b",
    r"\bwe will (file|submit)\b", r"\bfil(e|ing) (the |our )?(ccar|dfast|stress|results|submission)\b",
    r"\bsubmit(ted)? to the regulator\b", r"\bfinal capital plan\b",
    r"\bcapital is adequate\b", r"\bcapital adequacy is confirmed\b",
    r"\bdistribution is approved\b", r"\bdividend is approved\b",
    r"\bpass(es|ed) the stress test\b", r"\bfail(ed|s) the stress test\b",
    r"\bcertif(y|ies|ied) (the )?(model|scenario|soundness|results)\b",
    r"\bbreach is confirmed\b", r"\bconfirmed breach\b",
    r"\bset the (limit|threshold|reverse-stress trigger)\b", r"\bwe recommend buying\b",
]
SEVERITY_ORDER = {"baseline": 0, "adverse": 1, "severely_adverse": 2}


def _expected_readiness(pack: dict) -> str:
    scenarios = pack.get("scenarios") or []
    any_missing = any(s.get("components_missing") for s in scenarios)
    any_coverage = any(s.get("coverage_gaps") for s in scenarios)
    any_plausibility = any(s.get("plausibility_flags") for s in scenarios)
    monotonic = pack.get("severity_monotonic", False)
    ready = not (any_missing or any_coverage or any_plausibility) and monotonic
    return "Ready-for-review" if ready else "Not-ready"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    scenarios = pack.get("scenarios") or []
    if not scenarios:
        errors.append("pack has no scenarios")

    for s in scenarios:
        tag = f"scenario '{s.get('name','?')}'"
        if not s.get("transmission_channels"):
            errors.append(f"{tag}: no transmission_channels")
        if not s.get("assumptions"):
            errors.append(f"{tag}: no assumptions")
        if s.get("severity") != "baseline" and not s.get("management_actions"):
            errors.append(f"{tag}: stress scenario has no management_actions")
        if s.get("coverage_gaps"):
            errors.append(f"{tag}: coverage_gaps present: {s['coverage_gaps']}")
        for imp in s.get("impacts") or []:
            if not isinstance(imp.get("distance_to_breach"), (int, float)):
                errors.append(f"{tag}: impact on {imp.get('constraint')} missing numeric distance_to_breach")

    rs = pack.get("reverse_stress")
    if not rs:
        errors.append("missing reverse_stress result")
    else:
        if not rs.get("constraint"):
            errors.append("reverse_stress does not name a target constraint")
        if rs.get("scaling_multiple") is None and "not reachable" not in str(rs.get("interpretation", "")).lower():
            errors.append("reverse_stress has no scaling_multiple and no 'not reachable' interpretation")

    exp = _expected_readiness(pack)
    if pack.get("readiness_band") != exp:
        errors.append(f"readiness_band {pack.get('readiness_band')!r} != deterministic {exp!r}")

    # prohibited-language screen over free text (NOT the disclaimer field)
    parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    for s in scenarios:
        parts.append(str(s.get("design_notes", "")))
        parts.extend(str(x) for x in s.get("transmission_channels") or [])
        parts.extend(str(x) for x in s.get("assumptions") or [])
        parts.extend(str(x) for x in s.get("management_actions") or [])
    text = " ".join(parts)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"decision/adoption/filing language detected: {m.group(0)!r} "
                          f"(R3 designs and recommends; it does not decide, adopt, or file)")

    combined = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in combined:
        errors.append("missing standing disclaimer")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
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
