#!/usr/bin/env python3
"""Deterministic output validation for settlement-report-summarizer.

Confirms the computed settlement summary is internally consistent, fully cited, and free
of advice / optimization / determination language BEFORE it is presented or delivered.

Checks:
  1. Gross-to-net tie-out: sum(category signed amounts) == net_settlement (+/- tolerance).
  2. net_settlement == funding.expected_net (+/- tolerance) when funding is present.
  3. total_fees == sum of the magnitudes of the fee categories (+/- tolerance).
  4. effective_fee_rate_pct == total_fees / gross_sales * 100 (+/- tolerance) when present.
  5. by_card_brand values tie to gross_sales (+/- tolerance) when present.
  6. Every category line carries a non-empty citation.
  7. Narrative/notes contain no advice, fee-optimization, or settlement-determination
     phrasing (R1 is informational only).
  8. The standing informational-only disclaimer is present.

Summary schema (JSON):
{
  "snapshot_id","merchant_id","report_id","as_of_date","settlement_currency",
  "gross_sales","total_fees","net_settlement","effective_fee_rate_pct"(opt),
  "categories":[{"category","amount","citation"}],
  "by_card_brand":{"Visa":amount,...}(opt),
  "funding":{"expected_net":num,...}(opt),
  "narrative":"...","disclaimer":"..."
}

Usage:
  python validate_output.py summary.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

MONEY_TOL = 0.5   # currency units

# Advice / recommendation / fee-optimization language (R1 gives none of it).
ADVICE_PATTERNS = [
    r"\brecommend(s|ed|ing)?\b", r"\bwe (suggest|advise|recommend|propose)\b",
    r"\byou (should|ought to|must|need to|might want to|could)\b",
    r"\bshould (switch|negotiate|renegotiate|dispute|contest|reduce|lower|move|consider|review|renew|cancel|shop)\b",
    r"\b(too|overly) (high|expensive|costly|low|much)\b",
    r"\b(fees?|rates?|pricing|markup|reserve) (are|is|seem|seems|look|looks|appear|appears) (high|low|expensive|excessive|competitive|reasonable|fair|unfair)\b",
    r"\bbetter (rate|processor|deal|option|pricing|terms)\b",
    r"\bswitch(ing)? (processor|provider|providers|to|away)\b",
    r"\brenegotiat", r"\bnegotiate (a|your|better)\b",
    r"\bover-?charg", r"\bshop around\b", r"\bexcessive\b",
]
# Determination / reconciliation-confirmation language (that is a control decision, not a summary).
DETERMINATION_PATTERNS = [
    r"\breconcil(e|es|ed|ing)\b", r"\bties? out (to|with|against) your\b",
    r"\bmatches your (ledger|books|records|bank)\b",
    r"\bsettlement is (correct|accurate|verified|valid|right)\b",
    r"\b(confirmed|verified) (correct|accurate|against)\b",
    r"\bno (discrepanc|error|errors|break|breaks|issue|issues)\b",
    r"\b(deposit|funding|settlement) (is|was) (confirmed|verified|correct)\b",
]
DISCLAIMER_RE = re.compile(r"informational (summary )?only.*not\b.*\b(advice|reconciliation|confirmation)", re.I)

FEE_CATEGORIES = {"interchange_fees", "scheme_fees", "processor_fees", "other_fees", "fees"}


def _close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def validate(s: dict) -> list[str]:
    errors: list[str] = []
    net = s.get("net_settlement")
    cats = s.get("categories") or []
    if net is None or not cats:
        return ["summary missing net_settlement or categories"]

    signed_sum = 0.0
    fee_magnitude = 0.0
    for c in cats:
        cat = c.get("category", "?")
        amt = c.get("amount")
        if amt is None:
            errors.append(f"category {cat}: missing amount")
            continue
        signed_sum += amt
        if cat in FEE_CATEGORIES:
            fee_magnitude += abs(amt)
        if not (c.get("citation") or "").strip():
            errors.append(f"category {cat}: missing citation")

    if not _close(signed_sum, net, MONEY_TOL):
        errors.append(f"tie-out failed: sum(category amounts) {signed_sum:.2f} != net_settlement {net:.2f}")

    funding = s.get("funding") or {}
    exp = funding.get("expected_net")
    if exp is not None and not _close(net, exp, MONEY_TOL):
        errors.append(f"net_settlement {net:.2f} != funding.expected_net {exp:.2f}")

    total_fees = s.get("total_fees")
    if total_fees is not None and not _close(total_fees, fee_magnitude, MONEY_TOL):
        errors.append(f"total_fees {total_fees:.2f} != sum of fee categories {fee_magnitude:.2f}")

    gross = s.get("gross_sales")
    eff = s.get("effective_fee_rate_pct")
    if eff is not None and total_fees is not None and gross:
        expected_eff = total_fees / gross * 100.0
        if not _close(eff, expected_eff, max(0.05, abs(expected_eff) * 0.01)):
            errors.append(f"effective_fee_rate_pct {eff} != total_fees/gross_sales {expected_eff:.2f}")

    brands = s.get("by_card_brand") or {}
    if brands and gross is not None:
        bsum = sum(brands.values())
        if not _close(bsum, gross, MONEY_TOL):
            errors.append(f"by_card_brand sums to {bsum:.2f}, expected gross_sales {gross:.2f}")

    # Language screen over narrative/notes only (not the disclaimer, which names the boundary).
    text = " ".join(str(s.get(k, "")) for k in ("narrative", "notes"))
    text += " " + json.dumps(s.get("data_gaps", ""))
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"advice/optimization language detected: {m.group(0)!r} (R1 is informational only)")
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"settlement-determination language detected: {m.group(0)!r} (no reconciliation/confirmation here)")

    if not DISCLAIMER_RE.search(str(s.get("narrative", "")) + " " + str(s.get("disclaimer", ""))):
        errors.append("missing standing disclaimer: 'Informational summary only; ... not ... advice/reconciliation/confirmation'")

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
