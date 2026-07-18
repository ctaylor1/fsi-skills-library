#!/usr/bin/env python3
"""Deterministic input validation for fund-commentary-drafter.

Validates a commentary-inputs file before drafting. Fails closed on structural problems;
warns on data-quality gaps that must be resolved (or will force claims to be flagged
`unsupported`) before a package is release-ready.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  template_version, fund{fund_id,fund_name,benchmark,currency,share_class},
  period{type,label,from,to},
  reconciled_performance{fund_return_pct,benchmark_return_pct,excess_return_pct,reconciled,source_ref},
  attribution{total_excess_pct,reconciled,source_ref,effects[{name,contribution_pct,source_ref}]},
  positioning[], flows{}, market_context[], approved_messaging[{id,text,owner,status}],
  disclosures[], required_disclosures[], draft_claims[], prior_commentary_ref

Usage: python validate_input.py commentary_inputs.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

PERF_TOL = 0.011
ATTRIB_TOL = 0.10
REQUIRED_TOP = ("template_version", "fund", "period", "reconciled_performance", "attribution")
REQUIRED_FUND = ("fund_id", "fund_name", "benchmark", "currency")
REQUIRED_PERIOD = ("type", "label", "from", "to")
REQUIRED_PERF = ("fund_return_pct", "benchmark_return_pct", "excess_return_pct", "source_ref")
REQUIRED_ATTR = ("total_excess_pct", "source_ref", "effects")


def _f(x):
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

    fund = doc.get("fund") or {}
    for k in REQUIRED_FUND:
        if not fund.get(k):
            errors.append(f"fund: missing '{k}'")
    period = doc.get("period") or {}
    for k in REQUIRED_PERIOD:
        if not period.get(k):
            errors.append(f"period: missing '{k}'")

    rp = doc.get("reconciled_performance") or {}
    for k in REQUIRED_PERF:
        if rp.get(k) in (None, ""):
            errors.append(f"reconciled_performance: missing '{k}'")
    att = doc.get("attribution") or {}
    for k in REQUIRED_ATTR:
        if att.get(k) in (None, "", []):
            errors.append(f"attribution: missing '{k}'")
    effects = att.get("effects") or []
    if not isinstance(effects, list) or not effects:
        errors.append("attribution.effects must be a non-empty list")
    else:
        for i, e in enumerate(effects):
            if not e.get("name") or e.get("contribution_pct") is None or not e.get("source_ref"):
                errors.append(f"attribution.effects[{i}]: needs name, contribution_pct, source_ref")
    if errors:
        return errors, warnings

    # --- data-quality tie-out warnings (must be clean before release, not structural) ---
    fund_r, bench_r, excess_r = _f(rp.get("fund_return_pct")), _f(rp.get("benchmark_return_pct")), _f(rp.get("excess_return_pct"))
    if rp.get("reconciled") is not True:
        warnings.append("reconciled_performance.reconciled != true -> reconcile performance before drafting")
    if None not in (fund_r, bench_r, excess_r) and abs(round(fund_r - bench_r, 4) - excess_r) > PERF_TOL:
        warnings.append("performance excess does not tie to fund - benchmark -> fix before drafting")
    total_excess = _f(att.get("total_excess_pct"))
    eff_sum = round(sum(_f(e.get("contribution_pct")) or 0 for e in effects), 4)
    if att.get("reconciled") is not True:
        warnings.append("attribution.reconciled != true -> reconcile attribution before drafting")
    if total_excess is not None and abs(eff_sum - total_excess) > ATTRIB_TOL:
        warnings.append(f"attribution effects sum {eff_sum} != total_excess {total_excess} -> reconcile")
    if total_excess is not None and excess_r is not None and abs(total_excess - excess_r) > PERF_TOL:
        warnings.append("attribution total_excess != performance excess -> sources disagree")

    req = set(doc.get("required_disclosures") or [])
    have = set(doc.get("disclosures") or [])
    for d in sorted(req - have):
        warnings.append(f"required disclosure not provided: {d} -> package will fail output validation")

    for m in doc.get("approved_messaging") or []:
        if m.get("status") != "approved":
            warnings.append(f"messaging {m.get('id')!r} status={m.get('status')!r} -> cannot be used as a claim basis")

    for d in doc.get("draft_claims") or []:
        if not (d.get("source_refs")):
            warnings.append(f"draft_claim {d.get('id')!r} has no source_refs -> will be flagged unsupported")

    if not doc.get("prior_commentary_ref"):
        warnings.append("no prior_commentary_ref -> period-over-period consistency check limited")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "commentary_inputs.json"
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
