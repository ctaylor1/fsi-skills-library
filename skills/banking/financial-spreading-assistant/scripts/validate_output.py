#!/usr/bin/env python3
"""Deterministic output validation for financial-spreading-assistant.

Validates the final spread pack (the calculate_or_transform core + a narrative) before it is
presented or delivered. It re-derives the checks from the pack rather than trusting the
`ok` flags in it. Checks:
  1. Formula tie-outs: for every period the balance sheet balances (assets == liabilities +
     equity), each computed subtotal reconciles to the borrower's reported total, and the
     computed income-statement net income ties to the reported net income (within tolerance).
  2. Assumption provenance: every adjustment in the register carries a non-empty provenance
     AND a citation; the template + classification-map versions are recorded.
  3. Scenario behaviour (as-reported vs normalized): the normalized income statement differs
     from the as-reported income statement ONLY by the documented adjustments — every changed
     line equals the signed sum of adjustments to that line, and no undocumented change slips
     in (a phantom add-back).
  4. Ambiguous-mapping escalation: if any mapping is ambiguous, requires_human_mapping is true
     and every ambiguous entry carries a citation (the spread is not silently completed).
  5. Reproducibility: spread_id, template_version, classification_map_version present.
  6. NO credit decision / NO investment advice language in the free text.
  7. The standing disclaimer is present.

Usage:
  python validate_output.py spread_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

IS_CODES = ("revenue", "cogs", "operating_expenses", "depreciation_amortization",
            "interest_expense", "taxes", "other_income_expense")
DISCLAIMER_KEY = "not a credit decision, credit rating, eligibility determination, or investment advice"

# Affirmative credit-decision / advice assertions an R2 spread must never make. Worded so the
# standing disclaimer (which says what the spread is *not*) does not self-trip; the disclaimer
# is also excluded from the scanned text below.
DECISION_PATTERNS = [
    r"\bapprove (the |this )?(loan|facility|credit|application|line|request)\b",
    r"\bdecline (the |this )?(loan|facility|credit|application|line|request)\b",
    r"\bdeny (the |this )?(loan|facility|credit|application|line|request)\b",
    r"\brecommend (approv|declin|denial|denying|extending|granting)\b",
    r"\bthe borrower (is|has|represents) (a )?(strong|good|sound|solid|poor|weak|bad|acceptable) credit\b",
    r"\bcreditworth(y|iness)\b",
    r"\bqualif(y|ies|ied) for\b",
    r"\bwe (should |will )?(extend|grant|approve) (the )?(loan|facility|credit|line)\b",
    r"\binvest in\b",
    r"\bbuy (this|the) (stock|share|security|bond|note)\b",
    r"\b(strong|good|great) investment\b",
    r"\b(strong buy|strong sell)\b",
]


def _f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    tol = _f(pack.get("tolerance"), 1.0) or 1.0
    spreads = pack.get("spreads") or []
    if not spreads:
        errors.append("no spreads present")

    # signed adjustment effect per (period, code) from the register
    adj = {}
    register = pack.get("adjustments_register") or []
    for a in register:
        if not (a.get("provenance") or "").strip():
            errors.append(f"adjustment {a.get('id')!r} missing provenance")
        if not (a.get("citation") or "").strip():
            errors.append(f"adjustment {a.get('id')!r} missing citation")
        signed = _f(a.get("amount")) * (1.0 if a.get("direction") == "add" else -1.0)
        adj[(a.get("period"), a.get("code"))] = adj.get((a.get("period"), a.get("code")), 0.0) + signed

    for s in spreads:
        p = s.get("period")
        bs = s.get("balance_sheet") or {}
        sub = bs.get("subtotals") or {}
        assets = _f(sub.get("total_assets"))
        liab_eq = _f(sub.get("total_liabilities")) + _f(sub.get("total_equity"))
        if abs(assets - liab_eq) > tol:
            errors.append(f"{p} balance_sheet does not balance: assets {assets} != liabilities+equity {liab_eq}")
        reported = bs.get("reported") or {}
        for key in ("total_assets", "total_liabilities", "total_equity"):
            rep = reported.get(key)
            if rep is not None and abs(_f(sub.get(key)) - _f(rep)) > tol:
                errors.append(f"{p} balance_sheet computed {key} {_f(sub.get(key))} != reported {_f(rep)}")

        is_ = s.get("income_statement") or {}
        asrep = is_.get("as_reported") or {}
        norm = is_.get("normalized_components") or {}
        base = is_.get("components") or {}
        rep_ni = is_.get("reported_net_income")
        if rep_ni is not None and abs(_f(asrep.get("net_income")) - _f(rep_ni)) > tol:
            errors.append(f"{p} income_statement computed net_income {_f(asrep.get('net_income'))} != reported {_f(rep_ni)}")

        # scenario behaviour: normalized == as-reported + documented adjustments, nothing else
        for code in IS_CODES:
            delta = _f(norm.get(code)) - _f(base.get(code))
            expected = adj.get((p, code), 0.0)
            if abs(delta - expected) > tol:
                errors.append(f"{p} normalized {code} change {round(delta, 2)} != documented adjustments {round(expected, 2)} (phantom or missing add-back)")

        # cash-flow proxy recompute when evaluable
        cf = s.get("cash_flow") or {}
        if cf.get("evaluable"):
            c = cf.get("components") or {}
            recomputed = round(_f(c.get("net_income")) + _f(c.get("depreciation_amortization"))
                               - _f(c.get("change_in_working_capital")), 2)
            if abs(recomputed - _f(cf.get("operating_cash_flow_proxy"))) > tol:
                errors.append(f"{p} cash-flow proxy {cf.get('operating_cash_flow_proxy')} != recomputed {recomputed}")

    # ambiguous-mapping escalation
    ambiguous = pack.get("ambiguous_mappings") or []
    if ambiguous and not pack.get("requires_human_mapping"):
        errors.append("ambiguous_mappings present but requires_human_mapping is not true (spread must not be silently completed)")
    for a in ambiguous:
        if not (a.get("citation") or "").strip():
            errors.append(f"ambiguous mapping {a.get('raw_label')!r} missing citation")

    # reproducibility
    for key in ("spread_id", "template_version", "classification_map_version"):
        if not (pack.get(key) or ""):
            errors.append(f"missing {key}")

    # credit-decision / advice scan over author free text — NOT the disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("note", "")) for s in spreads])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited credit-decision/advice language detected: {m.group(0)!r} "
                          f"(R2 spreads and calculates; it does not decide credit or advise)")

    disc = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER_KEY not in disc:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "spread_pack_example.json"
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
