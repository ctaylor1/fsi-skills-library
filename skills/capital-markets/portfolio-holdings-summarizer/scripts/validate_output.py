#!/usr/bin/env python3
"""Deterministic output validation for portfolio-holdings-summarizer.

Confirms the computed summary is internally consistent, fully cited, and free of
advice/recommendation language BEFORE it is presented or delivered.

Checks:
  1. Position weights tie to 100% (+/- tolerance).
  2. Each position weight == market_value / total_market_value (within tolerance).
  3. Allocation buckets (by_asset_class) tie to 100% (+/- tolerance).
  4. Every position carries a non-empty citation.
  5. Narrative/any text contains no advice or recommendation phrasing.
  6. The standing informational-only disclaimer is present.

Summary schema (JSON):
{
  "snapshot_id","account_id","as_of_date","base_currency","total_market_value",
  "positions":[{"instrument_id","market_value","weight_pct","citation"}],
  "allocation":{"by_asset_class":{"Equity":pct,...},"cash_pct":pct},
  "narrative":"..."
}

Usage:
  python validate_output.py summary.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

WEIGHT_TOL = 0.5   # percentage points
ADVICE_PATTERNS = [
    r"\brecommend(s|ed|ing)?\b", r"\bshould (buy|sell|hold|consider|rebalance|reduce|increase)\b",
    r"\byou (should|ought to|might want to)\b", r"\bwe (suggest|advise|recommend)\b",
    r"\b(buy|sell) (this|these|more|now)\b", r"\bover-?weight\b", r"\bunder-?weight\b",
    r"\btoo (risky|concentrated|aggressive|conservative)\b", r"\bwell[- ]diversified\b",
    r"\b(is|looks) (risky|safe|suitable|unsuitable|appropriate)\b", r"\brebalanc",
    r"\bgood investment\b", r"\bbad investment\b", r"\bbetter (option|choice)\b",
]
DISCLAIMER_RE = re.compile(r"informational (summary )?only.*(not (investment )?advice|not a recommendation)", re.I)


def _close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def validate(s: dict) -> list[str]:
    errors: list[str] = []
    total = s.get("total_market_value")
    positions = s.get("positions") or []
    if not total or not positions:
        return ["summary missing total_market_value or positions"]

    wsum = 0.0
    for p in positions:
        w = p.get("weight_pct")
        mv = p.get("market_value")
        if w is None or mv is None:
            errors.append(f"position {p.get('instrument_id','?')}: missing weight_pct or market_value")
            continue
        wsum += w
        expected = mv / total * 100.0
        if not _close(w, expected, max(0.1, abs(expected) * 0.01)):
            errors.append(f"position {p.get('instrument_id','?')}: weight_pct {w} != mv/total {expected:.2f}")
        if not (p.get("citation") or "").strip():
            errors.append(f"position {p.get('instrument_id','?')}: missing citation")
    if not _close(wsum, 100.0, WEIGHT_TOL):
        errors.append(f"position weights sum to {wsum:.2f}%, expected 100% (+/-{WEIGHT_TOL})")

    alloc = (s.get("allocation") or {}).get("by_asset_class") or {}
    if alloc:
        asum = sum(alloc.values()) + (s.get("allocation") or {}).get("cash_pct", 0)
        if not _close(asum, 100.0, WEIGHT_TOL):
            errors.append(f"allocation (by_asset_class + cash) sums to {asum:.2f}%, expected 100%")

    text = " ".join(str(s.get(k, "")) for k in ("narrative", "notes")) + " " + json.dumps(s.get("top_holdings", ""))
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"advice/recommendation language detected: {m.group(0)!r} (R1 is informational only)")
    if not DISCLAIMER_RE.search(str(s.get("narrative", "")) + " " + str(s.get("disclaimer", ""))):
        errors.append("missing standing disclaimer: 'Informational summary only; not investment advice or a recommendation.'")

    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "summary_example.json"
        s = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        s = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        s = json.loads(sys.stdin.read())
    errors = validate(s)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
