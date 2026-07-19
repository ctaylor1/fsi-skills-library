#!/usr/bin/env python3
"""Deterministic input validation for investment-policy-statement-builder.

Validates an IPS build/refresh request before the draft is assembled. Fails closed on
structural problems (missing top-level fields, malformed allocation table). Warns on data
gaps that force a `needs-data` disposition (uncited material assertions, missing profile
blocks) so the drafter surfaces them instead of guessing.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version, template_version, tax_version, ips_id, author_id,
  governance{parties[],decision_authority,standard_of_care,citation},
  objectives{primary_goal,return_objective,spending_need,citation},
  risk_tolerance{ability,willingness,capacity,citation},
  time_horizon{years,stage,citation}, liquidity{reserve_amount,annual_distribution,citation},
  tax{marginal_rate,approved_assumptions_ref,account_types[],citation},
  constraints{legal_regulatory,restrictions[{type,detail,citation}],citation},
  target_allocation[{asset_class,target_pct,min_pct,max_pct,benchmark,citation}],
  rebalancing{method,threshold_pct,review_frequency,citation},
  benchmarks{portfolio,review_cadence,citation}, disclosures{ref,citation},
  approvals[{role,name_masked,status}]

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "ips_id", "target_allocation")
RISK_SCALE = ["Conservative", "Moderate-Conservative", "Moderate",
              "Moderate-Aggressive", "Aggressive"]
ALLOC_KEYS = ("asset_class", "target_pct", "min_pct", "max_pct", "benchmark", "citation")
# material assertion blocks -> the field that must carry a citation
MATERIAL_BLOCKS = ("objectives", "risk_tolerance", "time_horizon", "liquidity",
                   "tax", "constraints")
APPROVAL_ROLES = ("Advisor", "Compliance", "Client")


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    # --- allocation table (structural = error) ---
    alloc = doc.get("target_allocation") or []
    if not isinstance(alloc, list) or not alloc:
        errors.append("target_allocation must be a non-empty list")
    else:
        total = 0.0
        for i, line in enumerate(alloc):
            tag = f"target_allocation[{i}] ({line.get('asset_class','?')})"
            for k in ALLOC_KEYS:
                if k not in line or line[k] in (None, ""):
                    errors.append(f"{tag}: missing '{k}'")
            t, lo, hi = _num(line.get("target_pct")), _num(line.get("min_pct")), _num(line.get("max_pct"))
            if None in (t, lo, hi):
                continue
            total += t
            if lo > hi:
                errors.append(f"{tag}: min_pct {lo} > max_pct {hi}")
            if not (lo <= t <= hi):
                errors.append(f"{tag}: target_pct {t} outside band [{lo}, {hi}]")
        if abs(total - 100.0) > 0.1:
            errors.append(f"target_allocation targets sum to {total:g}, expected 100")

    # --- material assertion blocks (missing/uncited = needs-data warning) ---
    for blk in MATERIAL_BLOCKS:
        b = doc.get(blk)
        if not b:
            warnings.append(f"missing '{blk}' block -> needs-data")
            continue
        if not b.get("citation"):
            warnings.append(f"'{blk}' missing citation -> needs-data (unsupported assertion)")

    # --- risk tolerance scale sanity ---
    rt = doc.get("risk_tolerance") or {}
    for dim in ("ability", "willingness", "capacity"):
        v = rt.get(dim)
        if v is None:
            warnings.append(f"risk_tolerance.{dim} missing -> needs-data")
        elif v not in RISK_SCALE:
            errors.append(f"risk_tolerance.{dim}={v!r} not on scale {RISK_SCALE}")

    # --- tax must reference the approved set ---
    tax = doc.get("tax") or {}
    if tax and not tax.get("approved_assumptions_ref"):
        warnings.append("tax.approved_assumptions_ref missing -> tax figures unsupported (needs-data)")

    # --- versions present ---
    if not doc.get("template_version"):
        warnings.append("template_version missing -> record the versioned template contract")
    if not doc.get("tax_version"):
        warnings.append("tax_version missing -> record the versioned tax-assumptions contract")

    # --- approvals must not be pre-granted in the request ---
    approvals = doc.get("approvals") or []
    seen_roles = {a.get("role") for a in approvals}
    for role in APPROVAL_ROLES:
        if role not in seen_roles:
            warnings.append(f"approvals: no '{role}' entry -> will be added as pending")
    for a in approvals:
        st = str(a.get("status", "")).lower()
        if st and st != "pending":
            errors.append(f"approvals: '{a.get('role')}' status {a.get('status')!r} is not 'pending' "
                          f"(this skill drafts; approvals are granted by humans out-of-band)")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ips_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
