#!/usr/bin/env python3
"""Deterministic input validation for portfolio-proposal-comparator.

Validates a comparison file before metrics are computed. Fails closed on structural problems;
warns on data-quality gaps that limit which dimensions are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  client_id, as_of (YYYY-MM-DD), config_version, stated_objective (optional),
  config{...thresholds/tax-assumptions...},
  proposals[{proposal_id,label,source_ref,objective,advisory_fee_bps,assumed_turnover,
             revenue_sharing,surrender_period_months,
             holdings[{holding_id,name,asset_class,sector,issuer,diversified,weight,
                       expense_ratio_bps,illiquid,liquidity_days,share_class,proprietary,
                       cheaper_share_class_available,source_ref}]}]

Usage:
  python validate_input.py comparison.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("client_id", "as_of", "config_version", "proposals")
REQUIRED_PROP = ("proposal_id", "label", "advisory_fee_bps", "holdings")
REQUIRED_HOLD = ("holding_id", "asset_class", "weight", "expense_ratio_bps", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    proposals = doc.get("proposals") or []
    if not isinstance(proposals, list) or len(proposals) < 2:
        errors.append("proposals must be a list of at least 2 proposals to compare")
        return errors, warnings

    seen_pids = set()
    for i, p in enumerate(proposals):
        ptag = f"proposals[{i}] ({p.get('proposal_id','?')})"
        for k in REQUIRED_PROP:
            if k not in p or p[k] in (None, ""):
                errors.append(f"{ptag}: missing '{k}'")
        if _num(p.get("advisory_fee_bps")) is None:
            errors.append(f"{ptag}: advisory_fee_bps not numeric")
        pid = p.get("proposal_id")
        if pid in seen_pids:
            errors.append(f"{ptag}: duplicate proposal_id")
        seen_pids.add(pid)

        holdings = p.get("holdings") or []
        if not isinstance(holdings, list) or not holdings:
            errors.append(f"{ptag}: holdings must be a non-empty list")
            continue

        seen_hids, wsum = set(), 0.0
        for j, h in enumerate(holdings):
            htag = f"{ptag} holdings[{j}] ({h.get('holding_id','?')})"
            for k in REQUIRED_HOLD:
                if k not in h or h[k] in (None, ""):
                    errors.append(f"{htag}: missing '{k}'")
            w = _num(h.get("weight"))
            if w is None:
                errors.append(f"{htag}: weight not numeric")
            else:
                wsum += w
            if _num(h.get("expense_ratio_bps")) is None:
                errors.append(f"{htag}: expense_ratio_bps not numeric")
            hid = h.get("holding_id")
            if hid in seen_hids:
                errors.append(f"{htag}: duplicate holding_id")
            seen_hids.add(hid)
            if not h.get("diversified") and not str(h.get("issuer") or "").strip():
                warnings.append(f"{htag}: single-name holding with no issuer — concentration_issuer not evaluable for this row")
            if not h.get("sector"):
                warnings.append(f"{htag}: no sector — concentration_sector not evaluable for this row")

        if abs(wsum - 1.0) > 0.02:
            warnings.append(f"{ptag}: holding weights sum to {wsum:.4f} (expected ~1.0) — normalize before comparing")
        if _num(p.get("assumed_turnover")) is None:
            warnings.append(f"{ptag}: no assumed_turnover — tax-drag estimate not evaluable for this proposal")

    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds/tax assumptions used; record the config_version")
    if not doc.get("stated_objective"):
        warnings.append("no stated_objective — objective_mismatch not evaluated")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "proposals_example.json"
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
