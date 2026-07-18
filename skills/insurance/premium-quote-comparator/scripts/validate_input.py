#!/usr/bin/env python3
"""Deterministic input validation for premium-quote-comparator.

Validates a quotes file before normalization/comparison. Fails closed on structural
problems; warns on data-quality gaps that make a like-for-like comparison unsafe (mixed
currencies, mismatched terms, a coverage with neither limit nor deductible, a single quote).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  as_of (YYYY-MM-DD), config_version, risk_type, currency,
  quotes[{quote_id, carrier, product, term_months,
          premium{amount, frequency}, fees[{name, amount}],
          coverages[{code, name, limit, deductible}],
          exclusions[], endorsements[{code, name}], service_factors{...},
          currency, source_ref}]

Usage:
  python validate_input.py quotes.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("as_of", "config_version", "risk_type", "quotes")
REQUIRED_QUOTE = ("quote_id", "carrier", "premium", "term_months", "coverages")
FREQUENCIES = {"annual", "semiannual", "quarterly", "monthly"}


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

    quotes = doc.get("quotes") or []
    if not isinstance(quotes, list) or not quotes:
        errors.append("quotes must be a non-empty list")
        return errors, warnings
    if len(quotes) < 2:
        warnings.append("only one quote supplied — there is nothing to compare against")

    ids, currencies, terms = set(), set(), set()
    doc_ccy = doc.get("currency")
    for i, q in enumerate(quotes):
        tag = f"quotes[{i}] ({q.get('quote_id','?')})"
        for k in REQUIRED_QUOTE:
            if k not in q or q[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        qid = q.get("quote_id")
        if qid in ids:
            errors.append(f"{tag}: duplicate quote_id")
        ids.add(qid)

        prem = q.get("premium") or {}
        if not isinstance(prem, dict):
            errors.append(f"{tag}: premium must be an object with amount + frequency")
        else:
            if _num(prem.get("amount")) is None:
                errors.append(f"{tag}: premium.amount not numeric")
            if prem.get("frequency") not in FREQUENCIES:
                errors.append(f"{tag}: premium.frequency must be one of {sorted(FREQUENCIES)}")

        term = _num(q.get("term_months"))
        if term is None or term <= 0:
            errors.append(f"{tag}: term_months must be a positive number")
        else:
            terms.add(term)

        covs = q.get("coverages")
        if not isinstance(covs, list):
            errors.append(f"{tag}: coverages must be a list")
        elif not covs:
            warnings.append(f"{tag}: no coverages listed — comparison grid will be empty for this quote")
        else:
            for j, c in enumerate(covs):
                if not c.get("code"):
                    errors.append(f"{tag}: coverages[{j}] missing 'code'")
                if c.get("deductible") is not None and _num(c.get("deductible")) is None:
                    errors.append(f"{tag}: coverages[{j}] ({c.get('code','?')}) deductible not numeric")
                if c.get("limit") in (None, "") and c.get("deductible") in (None, ""):
                    warnings.append(f"{tag}: coverage {c.get('code','?')} has neither limit nor deductible — not comparable")

        for f in q.get("fees") or []:
            if _num(f.get("amount")) is None:
                errors.append(f"{tag}: fee {f.get('name','?')!r} amount not numeric")

        currencies.add(q.get("currency") or doc_ccy)
        if not q.get("source_ref"):
            warnings.append(f"{tag}: no source_ref — figures will not be citable to a quote of record")

    if len([c for c in currencies if c]) > 1:
        warnings.append(f"quotes span multiple currencies {sorted(c for c in currencies if c)} — not directly comparable; normalize FX before relying on cost figures")
    if len(terms) > 1:
        warnings.append(f"quotes have different policy terms (months) {sorted(terms)} — premiums are annualized but limits/exclusions may not be term-equivalent")
    if not doc.get("config"):
        warnings.append("no 'config' block — default normalization settings will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "quotes_example.json"
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
