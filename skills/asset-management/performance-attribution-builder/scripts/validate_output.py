#!/usr/bin/env python3
"""Deterministic output validation for performance-attribution-builder.

Enforces the Draft & package guardrails before the performance-attribution analysis is presented:
  1. All required template sections are present (mirrors assets/output-template.md).
  2. No unsupported/unapproved claims: every segment row carries a citation; every attributed
     segment ties out (allocation + selection + interaction + currency == the stated total); the
     effect totals sum to the stated attributed active return; and the stated active return equals
     portfolio_return - benchmark_return (an asserted number that does not reconcile is treated as
     an unsupported claim and fails closed).
  3. Required human approvals are recorded (role + date + citation) and delivery approval is
     flagged; missing required approvals appear as outstanding open items.
  4. No investment-recommendation/advice, forward-looking or guaranteed-performance, GIPS-
     compliance, unsubstantiated-marketing, or send/deliver language.
  5. build_status is 'draft-attribution' (never final / approved / delivered).
  6. The standing note is present.

Usage: python validate_output.py attribution.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "attribution_summary", "portfolio_benchmark", "segment_attribution", "effect_totals",
    "currency_attribution", "reconciliation", "methodology", "qa_checks", "open_items",
    "approvals", "source_index",
]
STANDING_NOTE = (
    "Draft performance-attribution analysis for human review only. It is not investment advice "
    "and not a recommendation; it makes no forward-looking or guaranteed-performance claim and "
    "asserts no GIPS compliance; the effects are an ex-post decomposition of realized return, and "
    "this draft has not been reviewed, approved, or delivered."
)
TOL = 1e-6  # tie-out tolerance in return space (decimals)

# Claims a performance-attribution builder must NEVER make.
RECOMMENDATION_PATTERNS = [
    r"\bwe recommend\b", r"\bour recommendation\b", r"\brecommend (increasing|reducing|adding|"
    r"trimming|buying|selling|overweighting|underweighting)\b",
    r"\byou should (buy|sell|increase|reduce|add|trim)\b",
    r"\bshould (overweight|underweight)\b", r"\brating:\s*(buy|sell|hold)\b",
    r"\binvestment advice\b", r"\bsuitable for your\b",
]
PERFORMANCE_PATTERNS = [
    r"\bguaranteed return\b", r"\bguaranteed to outperform\b", r"\bwill outperform\b",
    r"\bwill continue to outperform\b", r"\bexpected to outperform\b",
    r"\bprojected to return\b", r"\bfuture returns will\b", r"\bassures? a return\b",
]
GIPS_PATTERNS = [
    r"\bgips[- ]compliant\b", r"\bgips verified\b", r"\bcompliant with gips\b",
    r"\bclaims? gips compliance\b",
]
MARKETING_PATTERNS = [
    r"\btop[- ]decile\b", r"\btop[- ]quartile fund\b", r"\bbest[- ]in[- ]class returns\b",
    r"\bnumber[- ]one performing\b",
]
DELIVERY_PATTERNS = [
    r"\bsent to the client\b", r"\bsent to investors\b", r"\bdistributed to investors\b",
    r"\bdelivered to the client\b", r"\bposted to the fact ?sheet\b", r"\bpublished to\b",
    r"\bwe have sent\b", r"\bemailed to the (client|investor)\b",
]


def _has_citation(entry):
    if not isinstance(entry, dict):
        return False
    return bool(entry.get("citation")) or bool(entry.get("citations"))


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections")
    if not isinstance(sections, dict):
        return ["attribution output has no 'sections' object"]

    # 1. required sections present
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required section '{sec}'")

    # 2. segment rows: citation + attributed rows tie out
    seg_total_sum = 0.0
    for row in sections.get("segment_attribution") or []:
        seg = row.get("segment", "?")
        if not _has_citation(row):
            errors.append(f"unsupported claim: segment {seg} has no citation")
        if row.get("status") == "attributed":
            comps = [row.get("allocation"), row.get("selection"), row.get("interaction"),
                     row.get("currency_effect")]
            if not all(_num(x) for x in comps) or not _num(row.get("total")):
                errors.append(f"segment {seg} attributed but missing numeric effect components")
                continue
            recomputed = sum(float(x) for x in comps)
            if abs(recomputed - float(row["total"])) > TOL:
                errors.append(f"tie-out failed: segment {seg} total {row['total']} != "
                              f"allocation+selection+interaction+currency {round(recomputed, 10)}")
            seg_total_sum += float(row["total"])

    # 2. effect totals reconcile to the stated attributed active return
    et = sections.get("effect_totals") or {}
    recon = sections.get("reconciliation") or {}
    pb = sections.get("portfolio_benchmark") or {}
    if et:
        for k in ("allocation", "selection", "interaction", "currency", "total_attributed"):
            if not _num(et.get(k)):
                errors.append(f"effect_totals missing numeric '{k}'")
        if all(_num(et.get(k)) for k in ("allocation", "selection", "interaction", "currency",
                                         "total_attributed")):
            s = float(et["allocation"]) + float(et["selection"]) + float(et["interaction"]) + float(et["currency"])
            if abs(s - float(et["total_attributed"])) > TOL:
                errors.append(f"tie-out failed: effect_totals sum {round(s, 10)} != "
                              f"total_attributed {et['total_attributed']}")
            if abs(seg_total_sum - float(et["total_attributed"])) > TOL:
                errors.append(f"tie-out failed: sum of segment totals {round(seg_total_sum, 10)} != "
                              f"total_attributed {et['total_attributed']}")

    # 2. active return consistent with stated portfolio/benchmark returns and the reconciliation
    if all(_num(pb.get(k)) for k in ("portfolio_return", "benchmark_return", "active_return")):
        if abs((float(pb["portfolio_return"]) - float(pb["benchmark_return"])) - float(pb["active_return"])) > TOL:
            errors.append("tie-out failed: active_return != portfolio_return - benchmark_return")
    if _num(recon.get("active_return")) and _num(recon.get("attributed_active_return")) and _num(recon.get("residual")):
        r = float(recon["active_return"]) - float(recon["attributed_active_return"])
        if abs(r - float(recon["residual"])) > TOL:
            errors.append(f"reconciliation residual {recon['residual']} is not "
                          f"active_return - attributed_active_return ({round(r, 10)})")
    if _num(recon.get("active_return")) and _num(pb.get("active_return")):
        if abs(float(recon["active_return"]) - float(pb["active_return"])) > TOL:
            errors.append("reconciliation active_return inconsistent with portfolio_benchmark active_return")

    # 3. approvals recorded well-formed; delivery approval flagged
    approvals = sections.get("approvals")
    if not isinstance(approvals, dict) or "recorded" not in approvals:
        errors.append("approvals section missing or lacks a 'recorded' list")
    else:
        for rec in approvals.get("recorded") or []:
            for field in ("type", "approver_role", "date", "citation"):
                if not rec.get(field):
                    errors.append(f"recorded approval {rec.get('type','?')!r} missing '{field}'")
    if doc.get("human_approval_required_before_delivery") is not True:
        errors.append("human_approval_required_before_delivery must be true (external-delivery posture)")

    # 4. forbidden language (scan everything except the disclaimer standing note)
    scan = json.dumps({k: v for k, v in doc.items() if k != "standing_note"})
    for label, patterns in (("investment-recommendation/advice", RECOMMENDATION_PATTERNS),
                            ("forward-looking/guaranteed-performance", PERFORMANCE_PATTERNS),
                            ("GIPS-compliance", GIPS_PATTERNS),
                            ("unsubstantiated-marketing", MARKETING_PATTERNS),
                            ("delivery/submission", DELIVERY_PATTERNS)):
        for pat in patterns:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {label} language detected: {m.group(0)!r} "
                              f"(attribution builder only assembles a draft ex-post decomposition)")

    # 5. build status must be draft
    if doc.get("build_status") != "draft-attribution":
        errors.append(f"build_status must be 'draft-attribution', got {doc.get('build_status')!r}")

    # 6. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "attribution_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
