#!/usr/bin/env python3
"""Deterministic input validation for lbo-model-builder.

Validates an LBO-input file before the model is built. Fails closed on structural problems
(missing entry terms, empty capital structure, non-numeric assumptions, missing drivers or
exit multiple); warns on data-quality gaps that weaken the model (missing provenance/
citation, entry EBITDA inconsistent with revenue x margin, out-of-range rates/weights, very
high entry leverage, very long holds, missing scenario adjustments).

Input schema (JSON): see references/source-map.md. Key fields:
  company_id, as_of (YYYY-MM-DD), entry_date (YYYY-MM-DD), config_version, currency, units,
  entry_ebitda (> 0), entry_multiple (> 0), hold_years (int > 0),
  fees{transaction_fee_pct, financing_fee_pct},
  debt_tranches[ {name, turns (>= 0), rate (>= 0), amort_pct (0..1), cash_sweep(bool)} ],
  drivers{revenue_base(>0), revenue_growth, ebitda_margin, da_pct_revenue, capex_pct_revenue,
  nwc_pct_of_revenue_change, tax_rate, cash_sweep_pct -> {value, provenance, citation}},
  opening_cash, min_cash, exit{exit_multiple (> 0)},
  scenario_adjustments{upside{...}, downside{...}}

Usage:
  python validate_input.py lbo_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("company_id", "as_of", "entry_date", "config_version", "entry_ebitda",
                "entry_multiple", "hold_years", "debt_tranches", "drivers", "exit")
DRIVER_KEYS = ("revenue_base", "revenue_growth", "ebitda_margin", "da_pct_revenue",
               "capex_pct_revenue", "nwc_pct_of_revenue_change", "tax_rate",
               "cash_sweep_pct")
HIGH_LEVERAGE = 7.0     # entry net-debt / EBITDA above which we warn


def _v(node):
    try:
        return float(node.get("value") if isinstance(node, dict) else node)
    except (TypeError, ValueError, AttributeError):
        return None


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _prov_cite(node):
    if isinstance(node, dict):
        return (node.get("provenance") or "").strip(), (node.get("citation") or "").strip()
    return "", ""


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if not DATE_RE.match(str(doc["entry_date"])):
        errors.append(f"entry_date must start YYYY-MM-DD, got {doc['entry_date']!r}")

    entry_ebitda = _v(doc["entry_ebitda"])
    if entry_ebitda is None or entry_ebitda <= 0:
        errors.append(f"entry_ebitda must be > 0, got {doc['entry_ebitda']!r}")
    entry_multiple = _v(doc["entry_multiple"])
    if entry_multiple is None or entry_multiple <= 0:
        errors.append(f"entry_multiple must be > 0, got {doc['entry_multiple']!r}")
    for k in ("entry_ebitda", "entry_multiple"):
        prov, cite = _prov_cite(doc[k])
        if not prov or not cite:
            warnings.append(f"{k} has no provenance/citation — validate_output will reject the pack")

    hy = _int(doc["hold_years"])
    if hy is None or hy <= 0:
        errors.append(f"hold_years must be a positive integer, got {doc['hold_years']!r}")
    elif hy > 10:
        warnings.append(f"hold_years {hy} > 10 — very long holds are low-confidence")

    # debt tranches
    tranches = doc.get("debt_tranches") or []
    if not isinstance(tranches, list) or not tranches:
        errors.append("debt_tranches must be a non-empty list")
    total_turns = 0.0
    for i, tr in enumerate(tranches if isinstance(tranches, list) else []):
        tag = tr.get("name", f"#{i}") if isinstance(tr, dict) else f"#{i}"
        if not isinstance(tr, dict) or "name" not in tr:
            errors.append(f"debt_tranches[{i}] must be an object with a 'name'")
            continue
        for k in ("turns", "rate"):
            if k not in tr:
                errors.append(f"debt_tranches[{tag}].{k} is required")
            elif _v(tr[k]) is None:
                errors.append(f"debt_tranches[{tag}].{k} value is not numeric")
        turns = _v(tr.get("turns"))
        if turns is not None:
            if turns < 0:
                errors.append(f"debt_tranches[{tag}].turns must be >= 0, got {turns}")
            total_turns += turns
        amort = _v(tr.get("amort_pct"))
        if amort is not None and not (0.0 <= amort <= 1.0):
            warnings.append(f"debt_tranches[{tag}].amort_pct {amort} is outside [0,1] — check the term")
        for k in ("turns", "rate", "amort_pct"):
            if k in tr:
                prov, cite = _prov_cite(tr[k])
                if not prov or not cite:
                    warnings.append(f"debt_tranches[{tag}].{k} has no provenance/citation — "
                                    f"validate_output will reject the pack")
    if entry_ebitda and total_turns and total_turns > HIGH_LEVERAGE:
        warnings.append(f"entry leverage {round(total_turns, 2)}x EBITDA exceeds {HIGH_LEVERAGE}x — "
                        f"aggressive capital structure; confirm the debt terms")

    # drivers
    drivers = doc.get("drivers") or {}
    for k in DRIVER_KEYS:
        if k not in drivers:
            errors.append(f"drivers.{k} is required")
            continue
        if _v(drivers[k]) is None:
            errors.append(f"drivers.{k} value is not numeric")
        prov, cite = _prov_cite(drivers[k])
        if not prov:
            warnings.append(f"drivers.{k} has no provenance — validate_output will reject the pack")
        if not cite:
            warnings.append(f"drivers.{k} has no citation — validate_output will reject the pack")
    rev_base = _v(drivers.get("revenue_base"))
    if rev_base is not None and rev_base <= 0:
        errors.append(f"drivers.revenue_base must be > 0, got {rev_base}")
    tax = _v(drivers.get("tax_rate"))
    if tax is not None and not (0.0 <= tax < 1.0):
        warnings.append(f"drivers.tax_rate {tax} is outside [0,1) — check the input")
    sweep = _v(drivers.get("cash_sweep_pct"))
    if sweep is not None and not (0.0 <= sweep <= 1.0):
        warnings.append(f"drivers.cash_sweep_pct {sweep} is outside [0,1] — check the input")
    margin = _v(drivers.get("ebitda_margin"))
    if None not in (entry_ebitda, rev_base, margin) and rev_base and entry_ebitda:
        implied = rev_base * margin
        if abs(implied - entry_ebitda) > 0.01 * entry_ebitda:
            warnings.append(f"entry_ebitda {entry_ebitda} is inconsistent with revenue_base x ebitda_margin "
                            f"({round(implied, 4)}); confirm the LTM figures reconcile")

    # exit
    ex = doc.get("exit") or {}
    if "exit_multiple" not in ex:
        errors.append("exit.exit_multiple is required")
    elif _v(ex["exit_multiple"]) is None or _v(ex["exit_multiple"]) <= 0:
        errors.append(f"exit.exit_multiple must be > 0, got {ex.get('exit_multiple')!r}")
    else:
        prov, cite = _prov_cite(ex["exit_multiple"])
        if not prov or not cite:
            warnings.append("exit.exit_multiple has no provenance/citation — validate_output will reject the pack")

    # liquidity
    min_cash = _v(doc.get("min_cash"))
    if min_cash is not None and min_cash < 0:
        warnings.append(f"min_cash {min_cash} is negative — check the liquidity floor")

    # scenario adjustments (optional but expected for a 3-case model)
    sa = doc.get("scenario_adjustments") or {}
    for scen in ("upside", "downside"):
        if scen not in sa:
            warnings.append(f"no scenario_adjustments.{scen} — {scen} will equal the base case")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "lbo_input_example.json"
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
