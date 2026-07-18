#!/usr/bin/env python3
"""Deterministic output validation for market-landscape-researcher.

Validates the final landscape brief (the calculate_or_transform core wrapped in a
narrative + limitations) before it is presented or delivered. Fails closed on any miss.

Checks:
  1. landscape_id present.
  2. All eight required dimensions present, each with >= 1 finding, every finding cited.
  3. Concentration tie-out: HHI, CR4, and band recomputed from `competitors` match the
     reported `concentration` block (deterministic, reproducible).
  4. R2 prohibited-decision/advice screen: NO investment advice, buy/sell/hold rating,
     price target, personalized recommendation, or guaranteed-return language anywhere in
     the narrative, notes, limitations, or dimension findings.
  5. Standing research disclaimer present.
  6. A non-empty limitations / uncertainty section is present.

Usage:
  python validate_output.py brief_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_DIMENSIONS = (
    "value_chain", "competitors", "customers", "regulation",
    "technology", "economics", "transactions", "strategic_implications",
)
HHI_MODERATE, HHI_HIGH = 1500.0, 2500.0
DISCLAIMER = ("Market research for informational purposes only; not investment advice, a "
              "recommendation, or an offer to buy or sell any security.")

# Investment advice / decision / rating language an R2 research skill must never produce.
PROHIBITED_PATTERNS = [
    r"\bwe recommend (buy|sell|to buy|to sell|buying|selling)",
    r"\bwe advise (clients|you) to (buy|sell|invest|divest)",
    r"\bour recommendation is to (buy|sell)",
    r"\byou should (buy|sell|invest|divest|purchase)",
    r"\bstrong buy\b", r"\bstrong sell\b",
    r"\bprice target\b",
    r"\brated? (a )?(buy|sell)\b",
    r"\brating[: ]+(buy|sell|hold|overweight|underweight)",
    r"\boverweight\b", r"\bunderweight\b",
    r"\bguaranteed (return|profit|gains?|to outperform)",
    r"\bwill outperform\b", r"\bwill beat the market\b",
    r"\bbuy (the |this )?(stock|shares|security)",
    r"\bsell (the |this )?(stock|shares|security)",
    r"\bconviction (buy|list)\b",
    r"\btable[- ]?pounding\b",
    r"\binvest in .{0,40}\b(now|today)\b",
]


def _band(hhi: float) -> str:
    if hhi >= HHI_HIGH:
        return "highly concentrated"
    if hhi >= HHI_MODERATE:
        return "moderately concentrated"
    return "unconcentrated"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    if not pack.get("landscape_id"):
        errors.append("missing landscape_id")

    # ---- dimensions + citations ----
    dims = pack.get("dimensions") or {}
    for d in REQUIRED_DIMENSIONS:
        rows = dims.get(d)
        if not isinstance(rows, list) or not rows:
            errors.append(f"dimension '{d}' missing or empty (all eight required)")
            continue
        for j, f in enumerate(rows):
            if not (str(f.get("citation") or "")).strip():
                errors.append(f"dimensions.{d}[{j}] finding is uncited")

    # ---- concentration tie-out ----
    comps = pack.get("competitors")
    con = pack.get("concentration") or {}
    if not comps:
        errors.append("missing competitors list — cannot tie out concentration")
    else:
        shares = sorted((float(c.get("revenue_share_pct", 0.0)) for c in comps), reverse=True)
        hhi = round(sum(s * s for s in shares), 2)
        cr4 = round(sum(shares[:4]), 2)
        if abs(float(con.get("hhi", -1)) - hhi) > 0.1:
            errors.append(f"HHI {con.get('hhi')!r} != deterministic recompute {hhi}")
        if abs(float(con.get("cr4", -1)) - cr4) > 0.1:
            errors.append(f"CR4 {con.get('cr4')!r} != deterministic recompute {cr4}")
        if con.get("hhi_band") != _band(hhi):
            errors.append(f"hhi_band {con.get('hhi_band')!r} != deterministic {_band(hhi)!r}")

    # ---- prohibited advice/decision screen ----
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    lim = pack.get("limitations")
    text_parts.append(" ".join(lim) if isinstance(lim, list) else str(lim or ""))
    for d in REQUIRED_DIMENSIONS:
        for f in (dims.get(d) or []):
            text_parts.append(str(f.get("finding", "")))
    text = " ".join(text_parts)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited investment-advice/decision language: {m.group(0)!r} "
                          f"(R2 researches and evidences; it does not advise or rate)")

    # ---- disclaimer ----
    disc_text = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in disc_text:
        errors.append("missing standing research disclaimer text")

    # ---- limitations present ----
    if not lim or (isinstance(lim, list) and not any(str(x).strip() for x in lim)):
        errors.append("missing limitations/uncertainty section")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "landscape_pack_example.json"
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
