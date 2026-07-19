#!/usr/bin/env python3
"""Deterministic input validation for retirement-income-scenario-modeler.

Validates a retirement-plan input file before the projection is built. Fails closed on
structural problems (missing ages, non-numeric assumptions, no accounts, unsupported
withdrawal strategy, incoherent age ordering); warns on data-quality gaps that weaken the
model (missing provenance/citation, unusually high spending relative to assets, real return
below inflation, very long horizons, no adverse scenario).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  household_id, as_of (YYYY-MM-DD), valuation_date (YYYY-MM-DD), config_version, currency,
  units, current_age, retirement_age (>= current_age), horizon_age (> retirement_age),
  spending{annual_need(>0), inflation, guaranteed_income_tax_rate} each -> {value,provenance,
  citation}, accounts[]{id, type, balance(>=0), expected_return, effective_tax_rate in [0,1)},
  guaranteed_income[]{id, annual_amount, start_age, cola}, withdrawal{strategy('spending_gap'
  |'fixed_pct'), order[], fixed_pct}, scenario_adjustments{favorable{...}, adverse{...}}.

Usage:
  python validate_input.py retirement_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("household_id", "as_of", "valuation_date", "config_version",
                "retirement_age", "horizon_age", "spending", "accounts")
SPENDING_KEYS = ("annual_need", "inflation", "guaranteed_income_tax_rate")
STRATEGIES = ("spending_gap", "fixed_pct")


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


def _check_prov(node, label, warnings):
    prov, cite = _prov_cite(node)
    if not prov:
        warnings.append(f"{label} has no provenance — validate_output will reject the pack")
    if not cite:
        warnings.append(f"{label} has no citation — validate_output will reject the pack")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if not DATE_RE.match(str(doc["valuation_date"])):
        errors.append(f"valuation_date must start YYYY-MM-DD, got {doc['valuation_date']!r}")

    cur = _int(doc.get("current_age", doc["retirement_age"]))
    ret = _int(doc["retirement_age"])
    hor = _int(doc["horizon_age"])
    if ret is None:
        errors.append(f"retirement_age must be an integer, got {doc['retirement_age']!r}")
    if hor is None:
        errors.append(f"horizon_age must be an integer, got {doc['horizon_age']!r}")
    if None not in (ret, hor):
        if hor <= ret:
            errors.append(f"horizon_age ({hor}) must be greater than retirement_age ({ret})")
        elif hor - ret > 45:
            warnings.append(f"planning horizon {hor - ret} years (to age {hor}) is very long — "
                            f"confirm the longevity assumption")
    if None not in (cur, ret) and ret < cur:
        errors.append(f"retirement_age ({ret}) must be >= current_age ({cur})")

    # spending
    sp = doc.get("spending") or {}
    for k in SPENDING_KEYS:
        if k not in sp:
            errors.append(f"spending.{k} is required")
            continue
        if _v(sp[k]) is None:
            errors.append(f"spending.{k} value is not numeric")
        _check_prov(sp[k], f"spending.{k}", warnings)
    need = _v(sp.get("annual_need"))
    if need is not None and need <= 0:
        errors.append(f"spending.annual_need must be > 0, got {need}")
    infl = _v(sp.get("inflation"))
    if infl is not None and not (-0.10 <= infl <= 0.25):
        warnings.append(f"spending.inflation {infl} is outside a plausible [-0.10, 0.25] range")
    grate = _v(sp.get("guaranteed_income_tax_rate"))
    if grate is not None and not (0.0 <= grate < 1.0):
        errors.append(f"spending.guaranteed_income_tax_rate must be in [0,1), got {grate}")

    # accounts
    accounts = doc.get("accounts") or []
    if not accounts:
        errors.append("accounts must contain at least one account")
    seen_ids = set()
    total_balance = 0.0
    for i, a in enumerate(accounts):
        aid = a.get("id") or f"#{i}"
        if aid in seen_ids:
            errors.append(f"duplicate account id {aid!r}")
        seen_ids.add(aid)
        for field in ("balance", "expected_return", "effective_tax_rate"):
            if field not in a:
                errors.append(f"account {aid}: {field} is required")
                continue
            if _v(a[field]) is None:
                errors.append(f"account {aid}: {field} is not numeric")
            _check_prov(a[field], f"account {aid}.{field}", warnings)
        bal = _v(a.get("balance"))
        if bal is not None:
            if bal < 0:
                errors.append(f"account {aid}: balance must be >= 0, got {bal}")
            else:
                total_balance += bal
        rate = _v(a.get("effective_tax_rate"))
        if rate is not None and not (0.0 <= rate < 1.0):
            errors.append(f"account {aid}: effective_tax_rate must be in [0,1), got {rate}")
        ret_a = _v(a.get("expected_return"))
        if ret_a is not None and infl is not None and ret_a < infl:
            warnings.append(f"account {aid}: expected_return {ret_a} is below inflation {infl} "
                            f"(negative real return) — confirm the assumption")

    # withdrawal
    wd = doc.get("withdrawal") or {}
    strat = wd.get("strategy", "spending_gap")
    if strat not in STRATEGIES:
        errors.append(f"withdrawal.strategy must be one of {STRATEGIES}, got {strat!r}")
    if strat == "fixed_pct" and _v(wd.get("fixed_pct")) is None:
        errors.append("withdrawal.fixed_pct is required for the fixed_pct strategy")
    order = wd.get("order") or []
    for oid in order:
        if oid not in seen_ids:
            errors.append(f"withdrawal.order references unknown account id {oid!r}")

    # guaranteed income
    for i, s in enumerate(doc.get("guaranteed_income") or []):
        sid = s.get("id") or f"#{i}"
        for field in ("annual_amount", "cola"):
            if field not in s:
                errors.append(f"guaranteed_income {sid}: {field} is required")
            elif _v(s[field]) is None:
                errors.append(f"guaranteed_income {sid}: {field} is not numeric")
            else:
                _check_prov(s[field], f"guaranteed_income {sid}.{field}", warnings)
        if _int(s.get("start_age")) is None:
            errors.append(f"guaranteed_income {sid}: start_age must be an integer")

    # spending-vs-assets sanity (first-year gross draw as a % of assets)
    if need is not None and total_balance > 0:
        rate0 = need / total_balance
        if rate0 > 0.06:
            warnings.append(f"first-year spending need is ~{rate0:.1%} of investable assets "
                            f"before guaranteed income — high depletion risk; confirm inputs")

    # scenarios
    sa = doc.get("scenario_adjustments") or {}
    for scen in ("favorable", "adverse"):
        if scen not in sa:
            warnings.append(f"no scenario_adjustments.{scen} — {scen} will equal the base case; "
                            f"a range needs both a favorable and an adverse case")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "retirement_input_example.json"
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
