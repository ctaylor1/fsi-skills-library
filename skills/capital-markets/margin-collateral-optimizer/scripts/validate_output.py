#!/usr/bin/env python3
"""Deterministic output validation for margin-collateral-optimizer.

Validates the final collateral-recommendation pack (the calculate_or_transform core plus a
plain-language narrative) before it is presented or delivered. Fails closed. Checks:
  1. Every recommended allocation line carries a non-empty source citation.
  2. Coverage math ties out per call: each line's post_haircut_value == posted_market_value
     * (1 - haircut); the lines sum to total_post_haircut_value; coverage_ratio and
     shortfall are consistent with required_amount.
  3. Surfacing (no silent gaps): any call with a shortfall or a concentration-limit breach
     must appear in unresolved_items — the pack may not hide an uncovered call.
  4. No prohibited execution / binding-decision / dispute / investment-advice language
     (R2 recommends; treasury and operations decide and act).
  5. The standing disclaimer is present.
  6. approval_required is True.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.05
DISCLAIMER = ("Recommendation only; not a collateral instruction. No collateral has been "
              "pledged, moved, substituted, or settled, and no margin call has been "
              "disputed or accepted. Treasury and operations approval is required before "
              "any action.")

# Affirmative execution / binding-decision / dispute / advice assertions R2 must not make.
# The `disclaimer` field is NOT scanned (it legitimately negates these verbs).
PROHIBITED_PATTERNS = [
    r"\bpledg(?:e|ed|ing) the (?:collateral|securities|asset)",
    r"\bwe(?:'ve| have| will|'ll)?\s+pledg",
    r"\b(?:has|have) been (?:pledged|posted|moved|transferred|settled|wired)\b",
    r"\b(?:moved|transferred|wired|settled) the collateral\b",
    r"\bexecute[d]? the (?:substitution|movement|transfer|pledge|allocation)\b",
    r"\bsettle[d]? the (?:movement|collateral|call)\b",
    r"\bdisput(?:e|ed|ing) the (?:margin )?call\b",
    r"\b(?:reject|accept)(?:ed)? the (?:margin )?call\b",
    r"\bno approval (?:is )?(?:needed|required)\b",
    r"\bproceed(?:ing)? without (?:approval|sign-?off)\b",
    r"\bguaranteed (?:return|profit|yield)\b",
    r"\byou should (?:buy|sell|invest|allocate)\b",
]


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    calls = pack.get("calls")
    if not isinstance(calls, list):
        return ["pack has no 'calls' list"]

    unresolved_ids = {u.get("call_id") for u in pack.get("unresolved_items") or []}

    for c in calls:
        cid = c.get("call_id", "?")
        required = float(c.get("required_amount") or 0.0)
        lines = c.get("allocation") or []
        line_sum = 0.0
        for l in lines:
            if not str(l.get("citation") or "").strip():
                errors.append(f"call {cid}: allocation line {l.get('asset_id','?')} missing citation")
            pmv = float(l.get("posted_market_value") or 0.0)
            hc = float(l.get("haircut") or 0.0)
            phv = float(l.get("post_haircut_value") or 0.0)
            expected_phv = round(pmv * (1.0 - hc), 2)
            if abs(expected_phv - phv) > TOL:
                errors.append(f"call {cid}: {l.get('asset_id','?')} post_haircut_value {phv} != "
                              f"posted_market_value*(1-haircut) {expected_phv}")
            line_sum += phv

        total_phv = float(c.get("total_post_haircut_value") or 0.0)
        if abs(round(line_sum, 2) - total_phv) > TOL:
            errors.append(f"call {cid}: allocation lines sum {round(line_sum,2)} != "
                          f"total_post_haircut_value {total_phv}")

        exp_cov = round(total_phv / required, 2) if required else 0.0
        if abs(exp_cov - float(c.get("coverage_ratio") or 0.0)) > 0.02:
            errors.append(f"call {cid}: coverage_ratio {c.get('coverage_ratio')} != "
                          f"total/required {exp_cov}")

        exp_short = round(max(0.0, required - total_phv), 2)
        if abs(exp_short - float(c.get("shortfall") or 0.0)) > TOL:
            errors.append(f"call {cid}: shortfall {c.get('shortfall')} != "
                          f"required-covered {exp_short}")

        breaches = c.get("concentration_breaches") or []
        if (exp_short > TOL or breaches) and cid not in unresolved_ids:
            errors.append(f"call {cid}: shortfall/breach not surfaced in unresolved_items")

    # prohibited-language scan over free text (never the disclaimer field)
    parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    for c in calls:
        parts.append(str(c.get("rationale", "")))
        parts.append(str(c.get("note", "")))
    text = " ".join(parts)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited action/decision language detected: {m.group(0)!r} "
                          f"(R2 recommends; treasury/operations decide and act)")

    disc_scope = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in disc_scope:
        errors.append("missing standing disclaimer text")

    if pack.get("approval_required") is not True:
        errors.append("approval_required must be true (treasury + operations approval gate)")

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
