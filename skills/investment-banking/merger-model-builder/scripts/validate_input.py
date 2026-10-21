#!/usr/bin/env python3
"""Deterministic input validation for merger-model-builder.

Validates a de-identified deal file before the pro forma engine runs. Fails closed on
structural or arithmetic-integrity problems (bad shares/price, consideration mix that does
not sum to 100%, missing offer basis). Warns on data-quality gaps that make the model less
meaningful (missing synergies, no scenarios, thin provenance).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Keys:
  deal_id, as_of (YYYY-MM-DD), assumptions_version, currency, pro_forma_tax_rate,
  acquirer{net_income,shares_diluted,share_price,tax_rate,source_ref},
  target{net_income,shares_diluted,share_price,source_ref},
  consideration{offer_price_per_share|premium_pct, cash_pct, stock_pct, source_ref},
  financing{new_debt_rate,cash_yield_foregone,cash_on_hand_used,financing_fees,
            financing_fee_amort_years,source_ref},
  synergies{run_rate_pretax,phasing_pct,source_ref},
  purchase_accounting{intangible_writeup,intangible_amort_years,amort_tax_deductible,
                      transaction_fees,source_ref},
  scenarios{base,upside,downside}

Usage:
  python validate_input.py deal.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("deal_id", "as_of", "assumptions_version", "acquirer", "target",
                "consideration", "pro_forma_tax_rate")
REQUIRED_PARTY = ("net_income", "shares_diluted", "share_price", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(deal: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in deal:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(deal["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {deal['as_of']!r}")

    for side in ("acquirer", "target"):
        party = deal.get(side) or {}
        if not isinstance(party, dict):
            errors.append(f"{side} must be an object")
            continue
        for k in REQUIRED_PARTY:
            if k not in party or party[k] in (None, ""):
                errors.append(f"{side}: missing '{k}'")
        for k in ("net_income", "shares_diluted", "share_price"):
            if _num(party.get(k)) is None:
                errors.append(f"{side}.{k} not numeric")
        if _num(party.get("shares_diluted")) is not None and _num(party["shares_diluted"]) <= 0:
            errors.append(f"{side}.shares_diluted must be > 0")
        if _num(party.get("share_price")) is not None and _num(party["share_price"]) <= 0:
            errors.append(f"{side}.share_price must be > 0")

    t = _num(deal.get("pro_forma_tax_rate"))
    if t is None or not (0.0 <= t < 1.0):
        errors.append(f"pro_forma_tax_rate must be in [0,1), got {deal.get('pro_forma_tax_rate')!r}")

    consid = deal.get("consideration") or {}
    cash = _num(consid.get("cash_pct"))
    stock = _num(consid.get("stock_pct"))
    if cash is None or stock is None:
        errors.append("consideration.cash_pct and stock_pct are required numerics")
    elif abs((cash + stock) - 1.0) > 1e-6:
        errors.append(f"consideration cash_pct + stock_pct must equal 1.0, got {cash + stock}")
    if cash is not None and (cash < 0 or cash > 1):
        errors.append("consideration.cash_pct must be in [0,1]")
    if consid.get("offer_price_per_share") in (None, "") and consid.get("premium_pct") in (None, ""):
        errors.append("consideration needs either offer_price_per_share or premium_pct")
    if _num(consid.get("offer_price_per_share")) is not None and _num(consid["offer_price_per_share"]) <= 0:
        errors.append("consideration.offer_price_per_share must be > 0 when provided")
    if not consid.get("source_ref"):
        warnings.append("consideration has no source_ref — offer terms lack provenance")

    # data-quality warnings (do not block, but flag reduced meaning)
    fin = deal.get("financing") or {}
    if not deal.get("financing"):
        warnings.append("no 'financing' block — new debt/foregone-interest effects default to 0")
    else:
        if _num(fin.get("new_debt_rate")) is None:
            warnings.append("financing.new_debt_rate missing — incremental interest treated as 0")
        coh = _num(fin.get("cash_on_hand_used"))
        if coh is not None and consid.get("offer_price_per_share") and _num(deal["target"].get("shares_diluted")) is not None:
            cash_consid = _num(consid["offer_price_per_share"]) * _num(deal["target"]["shares_diluted"]) * (cash or 0.0)
            if coh > cash_consid + 1e-6:
                warnings.append("financing.cash_on_hand_used exceeds base-case cash consideration — new debt floored at 0")

    syn = deal.get("synergies") or {}
    if not syn or _num(syn.get("run_rate_pretax")) in (None, 0.0):
        warnings.append("no run-rate synergies — accretion reflects financing/structure only")
    elif not syn.get("source_ref"):
        warnings.append("synergies have no source_ref — synergy provenance is thin")

    pa = deal.get("purchase_accounting") or {}
    if pa.get("intangible_writeup") and not _num(pa.get("intangible_amort_years")):
        warnings.append("intangible_writeup set but intangible_amort_years missing/0 — amortization treated as 0")

    if not deal.get("scenarios"):
        warnings.append("no 'scenarios' block — default base/upside/downside drivers will be used")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "deal_example.json"
        deal = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        deal = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        deal = json.loads(sys.stdin.read())
    errors, warnings = validate(deal)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
