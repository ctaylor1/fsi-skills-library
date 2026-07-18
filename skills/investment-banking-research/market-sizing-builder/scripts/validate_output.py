#!/usr/bin/env python3
"""Deterministic output validation for market-sizing-builder.

Validates the final market-sizing pack (the calculate_or_transform core + a narrative) before
it is presented or delivered. Checks:
  1. Both methods (top_down, bottom_up) are present with every configured scenario.
  2. Formula tie-outs recomputed from the pack:
       - top_down: SAM == TAM * sam_ratio; SOM == SAM * som_ratio (per scenario).
       - bottom_up: method TAM/SAM/SOM == sum of segment TAM/SAM/SOM (per scenario).
  3. Containment per method per scenario: SOM <= SAM <= TAM.
  4. Scenario behavior: series ordered low <= base <= high for every level and method.
  5. Triangulation: recompute gap_pct from the two methods and confirm within_tolerance
     flags are correct (a formula tie-out on the reconciliation itself).
  6. Reported headline == the primary method's values for every scenario/level.
  7. Assumption provenance: every register entry carries provenance AND source_tier.
  8. No investment advice / securities recommendation / price-target / guarantee language.
  9. The standing disclaimer is present.

Usage:
  python validate_output.py market_sizing_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.5            # currency-unit tolerance for large-magnitude tie-outs
LEVELS = ("tam", "sam", "som")
DISCLAIMER = (
    "Market-size estimates for analytical purposes only; not investment advice, not a "
    "recommendation to buy, sell, or hold any security, and not a guarantee of revenue or "
    "market share. Estimates depend on the stated assumptions and sources and will vary."
)

# Affirmative investment-advice / recommendation / guarantee assertions an R2 market-sizing
# model must never make. Worded so the standing disclaimer above (which contains
# "recommendation to buy" and "guarantee of") does not self-trip.
ADVICE_PATTERNS = [
    r"\b(strong|conviction)?\s*buy rating\b",
    r"\bprice target\b",
    r"\boverweight\b", r"\bunderweight\b",
    r"\bwe (recommend|advise) (buying|selling|investing|that you (buy|sell|invest))\b",
    r"\byou should (buy|sell|invest|divest|allocate)\b",
    r"\bunder-?valued\b", r"\bover-?valued\b",
    r"\bguaranteed (return|revenue|growth|market share)\b",
    r"\brisk-free\b",
    r"\b(this|the) (stock|company|security) is a (buy|sell)\b",
    r"\bexpected return of\b",
]


def _sum_segments(bottom_up: dict, sc: str, level: str) -> float:
    segs = (bottom_up.get("segments") or {}).get(sc) or []
    return round(sum(float(s[level]) for s in segs), 2)


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    scenarios = pack.get("scenarios") or []
    td = pack.get("top_down") or {}
    bu = pack.get("bottom_up") or {}

    for name, block in (("top_down", td), ("bottom_up", bu)):
        rows = block.get("scenarios") or {}
        if not rows:
            errors.append(f"method '{name}' missing scenarios block")
            continue
        for sc in scenarios:
            if sc not in rows:
                errors.append(f"method '{name}' missing scenario '{sc}'")

    if errors:
        return errors

    # 2 + 3: tie-outs and containment per method/scenario
    for sc in scenarios:
        t = td["scenarios"][sc]
        exp_sam = round(t["tam"] * t["sam_ratio"], 2)
        exp_som = round(t["sam"] * t["som_ratio"], 2)
        if abs(exp_sam - t["sam"]) > TOL:
            errors.append(f"top_down[{sc}] SAM tie-out fails: TAM*sam_ratio={exp_sam} != SAM={t['sam']}")
        if abs(exp_som - t["som"]) > TOL:
            errors.append(f"top_down[{sc}] SOM tie-out fails: SAM*som_ratio={exp_som} != SOM={t['som']}")

        b = bu["scenarios"][sc]
        for level in LEVELS:
            exp = _sum_segments(bu, sc, level)
            if abs(exp - b[level]) > TOL:
                errors.append(f"bottom_up[{sc}] {level.upper()} tie-out fails: "
                              f"sum(segments)={exp} != {b[level]}")

        for name, r in (("top_down", t), ("bottom_up", b)):
            if not (r["som"] <= r["sam"] + TOL and r["sam"] <= r["tam"] + TOL):
                errors.append(f"{name}[{sc}] containment fails: expected SOM<=SAM<=TAM, "
                              f"got SOM={r['som']} SAM={r['sam']} TAM={r['tam']}")

    # 4: scenario ordering per method/level
    for name, block in (("top_down", td), ("bottom_up", bu)):
        for level in LEVELS:
            series = [block["scenarios"][sc][level] for sc in scenarios]
            if any(series[i] > series[i + 1] + TOL for i in range(len(series) - 1)):
                errors.append(f"{name} {level.upper()} not ordered across scenarios "
                              f"{dict(zip(scenarios, series))}")

    # 5: triangulation recomputation
    tol_pct = float(pack.get("triangulation_tolerance_pct", 0.20))
    for row in pack.get("triangulation") or []:
        a, bv = float(row["top_down"]), float(row["bottom_up"])
        denom = max(abs(a), abs(bv)) or 1.0
        gap = round(abs(a - bv) / denom, 4)
        if abs(gap - float(row.get("gap_pct", -1))) > 1e-4:
            errors.append(f"triangulation[{row.get('scenario')}/{row.get('level')}] gap_pct "
                          f"{row.get('gap_pct')} != recomputed {gap}")
        if bool(row.get("within_tolerance")) != bool(gap <= tol_pct):
            errors.append(f"triangulation[{row.get('scenario')}/{row.get('level')}] "
                          f"within_tolerance flag inconsistent with gap {gap} vs tol {tol_pct}")

    # 6: reported == primary method
    primary = pack.get("primary_method", "top_down")
    primary_block = td if primary == "top_down" else bu
    reported = pack.get("reported") or {}
    for sc in scenarios:
        for level in LEVELS:
            want = primary_block["scenarios"][sc][level]
            got = (reported.get(sc) or {}).get(level)
            if got is None or abs(float(got) - float(want)) > TOL:
                errors.append(f"reported[{sc}][{level}]={got} != primary '{primary}' value {want}")

    # 7: provenance + source tier on every assumption
    register = pack.get("assumptions_register") or []
    if not register:
        errors.append("assumptions_register missing (provenance must be recorded for every driver)")
    for a in register:
        if not (a.get("provenance") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing provenance")
        if not (a.get("source_tier") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing source_tier")

    # 8: advice/recommendation/guarantee scan over author free text (NOT the disclaimer field)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))])
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited investment-advice/recommendation/guarantee language detected: "
                          f"{m.group(0)!r} (R2 sizes markets; it does not advise, rate, or guarantee)")

    # 9: standing disclaimer present
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "market_sizing_pack_example.json"
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
