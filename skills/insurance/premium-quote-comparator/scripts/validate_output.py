#!/usr/bin/env python3
"""Deterministic output validation for premium-quote-comparator.

Validates the final comparison pack (the calculate_or_transform core + a narrative) before
it is presented or delivered. Checks:
  1. Every normalized quote figure is citable to a source quote.
  2. lowest_annualized_total_cost_quote_id equals the deterministic argmin over the
     normalized quotes (factual tie-out; the pack never invents a "winner").
  3. No advice / recommendation / suitability language and no coverage-or-eligibility
     determination (the R2 hard boundary — this skill compares, it does not advise or decide).
  4. The standing disclaimer is present.
  5. When material differences exist, comparability_flags are present (cost is never
     surfaced without the caveats that make quotes non-like-for-like).

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Comparison of quotes only; not insurance advice, a coverage determination, or a "
              "recommendation to purchase. Coverage selection is the customer's decision, made "
              "with a licensed producer.")

# Advice / recommendation / suitability the R2 comparator must never make:
ADVICE_PATTERNS = [
    r"\bwe recommend\b", r"\bi recommend\b", r"\brecommend(?:ing|ed)? (?:that )?(?:you|the customer)\b",
    r"\byou should (?:buy|choose|select|pick|purchase|go with|get|switch|drop|cancel)\b",
    r"\bthe best (?:policy|quote|option|value|choice|carrier|coverage|deal)\b",
    r"\bbest (?:value|option|choice|deal|policy|fit) for you\b",
    r"\bright (?:policy|coverage|option|fit) for you\b",
    r"\bbest coverage\b", r"\bchoose (?:carrier|quote|policy|option) [a-z0-9]", r"\bselect (?:carrier|quote|policy|option) [a-z0-9]",
    r"\bsuitable for you\b", r"\bsuitab(?:le|ility) (?:for|assessment)\b",
    r"\byour best (?:bet|option)\b", r"\bmy advice\b",
]
# Coverage / eligibility determinations the comparator must never make:
DETERMINATION_PATTERNS = [
    r"\byou are covered\b", r"\byou'?re covered\b", r"\byou will be covered\b",
    r"\bthis policy (?:will )?covers? you\b", r"\bcoverage is (?:approved|denied|confirmed)\b",
    r"\byou qualify\b", r"\byou are eligible\b", r"\beligible for coverage\b",
    r"\b(?:the )?claim will be (?:paid|covered)\b", r"\bguaranteed (?:coverage|to be covered)\b",
    r"\bwe will (?:pay|cover) (?:your|the) claim\b",
]


def _argmin_quote(normalized: list[dict]) -> str | None:
    if not normalized:
        return None
    return min(normalized, key=lambda n: (n.get("annualized_total_cost", float("inf")), str(n.get("quote_id"))))["quote_id"]


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    normalized = pack.get("normalized_quotes") or []
    if not normalized:
        errors.append("normalized_quotes is empty — nothing to compare")

    for n in normalized:
        if not (n.get("citation") or "").strip():
            errors.append(f"normalized quote {n.get('quote_id')} missing citation to source quote")
        if n.get("annualized_total_cost") is None:
            errors.append(f"normalized quote {n.get('quote_id')} missing annualized_total_cost")

    exp = _argmin_quote(normalized)
    if normalized and pack.get("lowest_annualized_total_cost_quote_id") != exp:
        errors.append(
            f"lowest_annualized_total_cost_quote_id {pack.get('lowest_annualized_total_cost_quote_id')!r} "
            f"!= deterministic argmin {exp!r}")

    # scan author-controlled free text only (narrative + notes + flag details); never the disclaimer.
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
        + [str(f.get("detail", "")) for f in pack.get("comparability_flags") or []])
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"advice/recommendation language detected: {m.group(0)!r} (R2 compares; it does not advise or select)")
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"coverage/eligibility determination language detected: {m.group(0)!r} (R2 does not decide coverage)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer")

    diffs = pack.get("differences") or {}
    has_material_diff = any(bool(v) for v in diffs.values())
    if has_material_diff and not (pack.get("comparability_flags")):
        errors.append("material differences exist but no comparability_flags surfaced (cost shown without caveats)")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "comparison_example.json"
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
