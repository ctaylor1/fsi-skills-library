#!/usr/bin/env python3
"""Deterministic output validation for liquidity-risk-scenario-analyzer.

Validates the final liquidity assessment pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. This is the R3 prohibited-decision screen: the skill may
surface findings, cited evidence, and proposed contingency options for human adjudication, but
must never state a regulated liquidity determination, approve/execute a funding action, clear or
waive a limit breach, file a regulatory return, or write a system of record.

Checks:
  1. Every fired finding (structural + per-scenario) has >= 1 cited evidence row.
  2. overall_assessment equals the deterministic band mapping from the finding severities.
  3. Findings tie out to the numbers: survival < min => survival_horizon_breach present;
     coverage < min => coverage_ratio_breach present, per scenario.
  4. No regulated-decision / closure / filing / commitment language (narrative + notes +
     finding details + proposed actions).
  5. The standing disclaimer is present.
  6. Proposed contingency options are supplied whenever the assessment is not "Within appetite".

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

SEVERITY_RANK = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}
BAND_BY_SEVERITY = {3: "Breach", 2: "Elevated", 1: "Watch", 0: "Within appetite"}
DISCLAIMER = ("Liquidity stress analysis and evidence only; not a regulatory determination, "
              "funding decision, or limit action.")

# Regulated-decision / closure / filing / commitment assertions an R3 decision-support skill
# must NOT make. These are execution / adjudication statements, not analysis. Proposed options
# framed as "PROPOSAL ... adjudication required" are permitted and do not match these.
DECISION_PATTERNS = [
    r"\bwe (will|shall|are going to|have decided to) (draw|repo|pledge|sell|monetize|activate|file|submit|execute|borrow|breach|waive|override)\b",
    r"\bactivate the (contingency funding plan|cfp)\b",
    r"\b(alco|the board|treasury committee) (has |have )?approved\b",
    r"\bapproved by (alco|the board|the treasury committee)\b",
    r"\bfile (the |a )?(2052a|lcr|nsfr|liquidity)\b",
    r"\bsubmit(ted)?\b[^.]{0,40}\bto (the )?(regulator|supervisor|federal reserve|the fed|pra|ecb|occ)\b",
    r"\bbreach (is |has been |was )?(cleared|closed|waived|resolved|remediated|approved)\b",
    r"\blimit (is |has been |was )?(increased|decreased|reduced|reset|raised|lowered|overridden|waived)\b",
    r"\bcapital (add-?on|surcharge)\b",
    r"\bwe are (fully )?compliant\b",
    r"\bfinal (determination|decision)\b",
    r"\battestation (is |has been )?signed\b",
    r"\bcertify (that )?the (institution|bank|firm|entity)\b",
    r"\bwaive the (limit|breach)\b",
    r"\bclose (the |this )?(case|finding|breach)\b",
    r"\bdisregard (the |your |all )?(prior|previous|above|earlier) (instruction|rule)",
]


def _all_findings(pack: dict) -> list[dict]:
    out = list(pack.get("structural_findings") or [])
    for sc in pack.get("scenarios") or []:
        out.extend(sc.get("findings") or [])
    return out


def _expected_band(findings: list[dict]) -> str:
    top = 0
    for f in findings:
        top = max(top, SEVERITY_RANK.get(f.get("severity", ""), 0))
    return BAND_BY_SEVERITY[top]


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = _all_findings(pack)

    # 1. evidence + citation completeness
    for f in findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('finding')} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {f.get('finding')} evidence row missing citation")

    # 2. deterministic band
    exp = _expected_band(findings)
    if pack.get("overall_assessment") != exp:
        errors.append(f"overall_assessment {pack.get('overall_assessment')!r} != deterministic {exp!r}")

    # 3. tie-out of findings to numbers
    limits = pack.get("limits") or {}
    min_surv = limits.get("min_survival_days")
    min_cov = limits.get("min_coverage_ratio")
    for sc in pack.get("scenarios") or []:
        names = {f.get("finding") for f in (sc.get("findings") or [])}
        sd = sc.get("survival_horizon_days")
        if min_surv is not None and sd is not None and float(sd) < float(min_surv) \
                and "survival_horizon_breach" not in names:
            errors.append(f"scenario {sc.get('scenario_id')}: survival {sd} < {min_surv} but no survival_horizon_breach finding")
        cov = sc.get("coverage_ratio")
        if min_cov is not None and cov is not None and float(cov) < float(min_cov) \
                and "coverage_ratio_breach" not in names:
            errors.append(f"scenario {sc.get('scenario_id')}: coverage {cov} < {min_cov} but no coverage_ratio_breach finding")

    # 4. regulated-decision / filing / closure language screen (not the disclaimer field)
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(f.get("detail", "")) for f in findings]
    text_parts += [str(a) for a in (pack.get("proposed_contingency_actions") or [])]
    text = " ".join(text_parts)
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"regulated-decision/filing/closure language detected: {m.group(0)!r} "
                          f"(R3 evidences and proposes; it does not decide, file, or act)")

    # 5. disclaimer present
    hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in hay:
        errors.append("missing standing disclaimer text")

    # 6. proposed options required when not within appetite
    if pack.get("overall_assessment") not in (None, "Within appetite") \
            and not (pack.get("proposed_contingency_actions")):
        errors.append("assessment is not 'Within appetite' but no proposed contingency options were supplied")

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
