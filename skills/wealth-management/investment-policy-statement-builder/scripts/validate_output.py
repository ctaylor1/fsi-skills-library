#!/usr/bin/env python3
"""Deterministic output validation for investment-policy-statement-builder.

Enforces the draft-and-package guardrails before an IPS draft is presented:
  1. All 13 required template sections are present (template fidelity).
  2. Every material section and every allocation line carries a citation
     (no unsupported / unapproved assertions).
  3. Strategic allocation is internally consistent (targets sum to 100% +/-0.1; within bands).
  4. Overall risk tolerance = most conservative of ability/willingness/capacity.
  5. Advisor / Compliance / Client approvals are recorded and still `pending`.
  6. draft_status == "draft" and delivery_status == "not-delivered" (draft-only; never sent).
  7. No prohibited language: suitability-approval, trade/execution, filing/delivery/
     finalization, or guarantee/performance claims (regex families, case-insensitive).
  8. The standing note is present.
Any failure exits non-zero so the draft fails closed.

Usage: python validate_output.py draft.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

RISK_SCALE = ["Conservative", "Moderate-Conservative", "Moderate",
              "Moderate-Aggressive", "Aggressive"]
REQUIRED_SECTIONS = [
    ("purpose-and-scope", "Purpose and Scope"),
    ("governance-and-roles", "Governance and Roles"),
    ("investment-objectives", "Investment Objectives"),
    ("risk-tolerance", "Risk Tolerance"),
    ("time-horizon", "Time Horizon"),
    ("liquidity-requirements", "Liquidity Requirements"),
    ("tax-considerations", "Tax Considerations"),
    ("constraints-and-restrictions", "Constraints and Restrictions"),
    ("strategic-asset-allocation", "Strategic Asset Allocation"),
    ("rebalancing-policy", "Rebalancing Policy"),
    ("benchmarks-and-monitoring", "Benchmarks and Monitoring"),
    ("approvals-and-effective-date", "Approvals and Effective Date"),
    ("disclosures", "Disclosures"),
]
MATERIAL_SECTIONS = {
    "investment-objectives", "risk-tolerance", "time-horizon",
    "liquidity-requirements", "tax-considerations", "constraints-and-restrictions",
    "strategic-asset-allocation",
}
APPROVAL_ROLES = ("Advisor", "Compliance", "Client")
STANDING_NOTE = ("Draft IPS for human review only; no allocation approved as suitable, no "
                 "suitability determination made, and nothing finalized, filed, delivered, or traded.")

PROHIBITED = {
    "approval-as-done": [
        r"\bsuitability approved\b", r"\brecommendation approved\b", r"\bdeemed suitable\b",
        r"\bwe hereby approve\b", r"\bis approved for the client\b",
        r"\bbest[- ]interest determination made\b",
    ],
    "trade-execution": [
        r"\bexecute the trade\b", r"\btrades? executed\b", r"\border placed\b",
        r"\bplace the order\b", r"\brebalance executed\b", r"\bsent to the custodian\b",
    ],
    "filing-delivery-final": [
        r"\bfile the\b", r"\bsubmitted to\b", r"\bfinal and binding\b",
        r"\bdelivered to the (client|custodian)\b", r"\bsigned and executed\b",
    ],
    "guarantee-performance": [
        r"\bguaranteed returns?\b", r"\bguarantees? to\b", r"\brisk-free\b",
        r"\bwill outperform\b", r"\bno downside\b",
    ],
}


def _expected_overall(risk):
    idxs = []
    for dim in ("ability", "willingness", "capacity"):
        v = (risk or {}).get(dim)
        if v not in RISK_SCALE:
            return None
        idxs.append(RISK_SCALE.index(v))
    return RISK_SCALE[min(idxs)]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    # 1 + 2: required sections present + material sections cited
    sections = {s.get("key"): s for s in (doc.get("sections") or [])}
    for key, title in REQUIRED_SECTIONS:
        s = sections.get(key)
        if not s:
            errors.append(f"missing required section '{key}' ({title})")
            continue
        if s.get("title") != title:
            errors.append(f"section '{key}': title {s.get('title')!r} != required {title!r}")
        if not s.get("present", False):
            errors.append(f"section '{key}': not present")
        if key in MATERIAL_SECTIONS and not s.get("citations"):
            errors.append(f"section '{key}': material assertion has no citation (unsupported)")

    # 3: allocation consistency (recomputed, not trusted)
    alloc = doc.get("strategic_asset_allocation") or []
    if not alloc:
        errors.append("strategic_asset_allocation is empty")
    else:
        total = 0.0
        for line in alloc:
            ac = line.get("asset_class", "?")
            if not line.get("citation"):
                errors.append(f"allocation line {ac!r}: missing citation (unsupported assertion)")
            try:
                t = float(line.get("target_pct")); lo = float(line.get("min_pct")); hi = float(line.get("max_pct"))
            except (TypeError, ValueError):
                errors.append(f"allocation line {ac!r}: non-numeric band")
                continue
            total += t
            if lo > hi:
                errors.append(f"allocation line {ac!r}: min {lo} > max {hi}")
            elif not (lo <= t <= hi):
                errors.append(f"allocation line {ac!r}: target {t} outside band [{lo}, {hi}]")
        if abs(total - 100.0) > 0.1:
            errors.append(f"allocation targets sum to {total:g}, expected 100")

    # 4: risk tolerance reconciliation
    risk = doc.get("risk_tolerance") or {}
    exp = _expected_overall(risk)
    if exp is None:
        errors.append("risk_tolerance: ability/willingness/capacity incomplete or off-scale")
    elif risk.get("overall") != exp:
        errors.append(f"risk_tolerance.overall {risk.get('overall')!r} != most-conservative {exp!r}")

    # 5: approvals recorded and pending
    appr = {a.get("role"): a for a in (doc.get("approvals") or [])}
    for role in APPROVAL_ROLES:
        a = appr.get(role)
        if not a:
            errors.append(f"approvals: missing '{role}' entry")
        elif str(a.get("status", "")).lower() != "pending":
            errors.append(f"approvals: '{role}' status {a.get('status')!r} must be 'pending' (draft-only)")

    # 6: draft-only status flags
    if doc.get("draft_status") != "draft":
        errors.append(f"draft_status {doc.get('draft_status')!r} must be 'draft' (never final/approved)")
    if doc.get("delivery_status") != "not-delivered":
        errors.append(f"delivery_status {doc.get('delivery_status')!r} must be 'not-delivered' (never sent/submitted)")

    # 7: prohibited language (scan everything EXCEPT the standing_note field)
    scan_doc = {k: v for k, v in doc.items() if k != "standing_note"}
    scan = json.dumps(scan_doc) + " " + str(doc.get("narrative", ""))
    for family, pats in PROHIBITED.items():
        for pat in pats:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {family} language detected: {m.group(0)!r} (draft never "
                              f"approves/trades/files/guarantees)")

    # 8: standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ips_draft_example.json"
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
