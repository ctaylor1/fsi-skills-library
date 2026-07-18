#!/usr/bin/env python3
"""Deterministic, source-linked leveraged-buyout (LBO) engine for lbo-model-builder.

Reads an LBO-input file (see validate_input.py), builds an explicit driver-based model for
base / upside / downside scenarios, and returns a fully tied-out model:

  1. Sources & Uses at entry (purchase EV, fees, new-debt tranches, sponsor-equity plug).
  2. An annual operating forecast (revenue -> EBITDA -> EBIT) over the holding period.
  3. A debt schedule per tranche: beginning balance, cash interest on the *beginning*
     balance (no circularity), mandatory amortization, and an optional cash sweep of
     excess free cash flow above a minimum-cash floor.
  4. A levered free-cash-flow build and a cash roll-forward.
  5. An exit (exit EV = exit EBITDA x exit multiple) walked to sponsor exit equity.
  6. Sponsor returns: MOIC and a single-cash-flow IRR.

Entry price and capital structure are fixed across scenarios; scenarios flex the operating
drivers and the exit multiple only. Every scenario carries its own formula tie-outs; every
assumption carries a provenance tag and citation; the model is reproducible from a hash of
its inputs.

IMPORTANT: This produces an *illustrative* LBO model only. It never issues investment
advice, an invest/pass/commit recommendation, a guaranteed return or IRR, or an
investment-committee approval. Scenario adjustments and entry/exit inputs are documented
assumptions, not the skill's judgment. See references/domain-rules.md.

Usage:
  python calculate_or_transform.py lbo_input.json | --selftest
Prints the model JSON to stdout.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

MONEY = 4            # money precision (units are typically millions)
RATIO = 6            # ratio / per-turn precision
TOL = 0.01           # tie-out tolerance
DISCLAIMER = ("Illustrative leveraged-buyout model for analytical purposes only; not "
              "investment advice, not a recommendation to make, hold, or exit any "
              "investment, not a guarantee of any return, IRR, or multiple, and not an "
              "investment-committee approval. Outputs depend entirely on the stated "
              "assumptions, which a qualified human must review.")

DRIVER_KEYS = ("revenue_base", "revenue_growth", "ebitda_margin", "da_pct_revenue",
               "capex_pct_revenue", "nwc_pct_of_revenue_change", "tax_rate",
               "cash_sweep_pct")
# operating drivers that scenarios may flex (revenue_base and structural terms are fixed)
SCENARIO_DRIVERS = ("revenue_growth", "ebitda_margin", "da_pct_revenue",
                    "capex_pct_revenue", "nwc_pct_of_revenue_change", "tax_rate",
                    "cash_sweep_pct")


def _v(node):
    """Numeric value from either a bare scalar or a {value, provenance, ...} dict."""
    if isinstance(node, dict):
        return float(node.get("value"))
    return float(node)


def _prov(node):
    return (node.get("provenance", "") if isinstance(node, dict) else "")


def _cite(node):
    return (node.get("citation", "") if isinstance(node, dict) else "")


def _resolve_drivers(doc: dict, name: str) -> dict:
    base = {k: _v(doc["drivers"][k]) for k in DRIVER_KEYS}
    if name == "base":
        return base
    adj = (doc.get("scenario_adjustments") or {}).get(name, {})
    for k, delta in adj.items():
        if k in base and k in SCENARIO_DRIVERS:
            base[k] = round(base[k] + float(delta), 8)
    return base


def _exit_multiple(doc: dict, name: str) -> float:
    em = _v(doc["exit"]["exit_multiple"])
    if name != "base":
        adj = (doc.get("scenario_adjustments") or {}).get(name, {})
        if "exit_multiple" in adj:
            em = round(em + float(adj["exit_multiple"]), 8)
    return em


def build_sources_and_uses(doc: dict) -> dict:
    """Entry sources & uses. Sponsor equity is the balancing plug -> sources == uses."""
    entry_ebitda = _v(doc["entry_ebitda"])
    entry_multiple = _v(doc["entry_multiple"])
    purchase_ev = round(entry_ebitda * entry_multiple, MONEY)

    fees = doc.get("fees") or {}
    txn_fee_pct = _v(fees.get("transaction_fee_pct", 0.0))
    fin_fee_pct = _v(fees.get("financing_fee_pct", 0.0))

    tranches = []
    total_new_debt = 0.0
    for tr in doc["debt_tranches"]:
        principal = round(_v(tr["turns"]) * entry_ebitda, MONEY)
        total_new_debt = round(total_new_debt + principal, MONEY)
        tranches.append({
            "name": tr["name"],
            "turns": _v(tr["turns"]),
            "rate": _v(tr["rate"]),
            "amort_pct": _v(tr.get("amort_pct", 0.0)),
            "cash_sweep": bool(tr.get("cash_sweep", False)),
            "principal": principal,
        })

    transaction_fees = round(txn_fee_pct * purchase_ev, MONEY)
    financing_fees = round(fin_fee_pct * total_new_debt, MONEY)
    total_uses = round(purchase_ev + transaction_fees + financing_fees, MONEY)
    sponsor_equity = round(total_uses - total_new_debt, MONEY)
    total_sources = round(total_new_debt + sponsor_equity, MONEY)

    su_ok = abs(total_sources - total_uses) <= TOL
    return {
        "purchase_enterprise_value": purchase_ev,
        "transaction_fees": transaction_fees,
        "financing_fees": financing_fees,
        "total_uses": total_uses,
        "tranches": tranches,
        "total_new_debt": total_new_debt,
        "sponsor_equity": sponsor_equity,
        "total_sources": total_sources,
        "entry_leverage": round(total_new_debt / entry_ebitda, RATIO) if entry_ebitda else None,
        "su_balanced_ok": su_ok,
    }


def project(doc: dict, su: dict, name: str) -> dict:
    d = _resolve_drivers(doc, name)
    hold = int(doc["hold_years"])
    tax = d["tax_rate"]
    sweep_pct = d["cash_sweep_pct"]
    min_cash = _v(doc.get("min_cash", 0.0))
    beginning_cash = _v(doc.get("opening_cash", 0.0))

    # per-tranche running balances, seeded from Sources & Uses
    balances = [t["principal"] for t in su["tranches"]]
    originals = [t["principal"] for t in su["tranches"]]
    rates = [t["rate"] for t in su["tranches"]]
    amort_pcts = [t["amort_pct"] for t in su["tranches"]]
    sweepable = [t["cash_sweep"] for t in su["tranches"]]
    tr_names = [t["name"] for t in su["tranches"]]

    prev_rev = d["revenue_base"]
    rows = []
    min_cash_ok = True
    for t in range(1, hold + 1):
        beg_tranche = list(balances)                 # per-tranche beginning balances
        rev = round(prev_rev * (1.0 + d["revenue_growth"]), MONEY)
        ebitda = round(rev * d["ebitda_margin"], MONEY)
        da = round(rev * d["da_pct_revenue"], MONEY)
        ebit = round(ebitda - da, MONEY)

        beg_debt = round(sum(beg_tranche), MONEY)
        interest = round(sum(rates[i] * beg_tranche[i] for i in range(len(balances))), MONEY)
        ebt = round(ebit - interest, MONEY)
        cash_taxes = round(tax * max(ebt, 0.0), MONEY)
        capex = round(rev * d["capex_pct_revenue"], MONEY)
        delta_nwc = round(d["nwc_pct_of_revenue_change"] * (rev - prev_rev), MONEY)

        # mandatory amortization (capped at the outstanding balance)
        mand = [round(min(amort_pcts[i] * originals[i], balances[i]), MONEY)
                for i in range(len(balances))]
        mandatory_amort = round(sum(mand), MONEY)

        fcf_before_sweep = round(ebitda - interest - cash_taxes - capex
                                 - delta_nwc - mandatory_amort, MONEY)

        # apply mandatory amortization first
        for i in range(len(balances)):
            balances[i] = round(balances[i] - mand[i], MONEY)

        # optional cash sweep of excess cash above the minimum-cash floor
        pre_sweep_cash = round(beginning_cash + fcf_before_sweep, MONEY)
        sweepable_cash = round(max(pre_sweep_cash - min_cash, 0.0), MONEY)
        sweep_budget = round(sweep_pct * sweepable_cash, MONEY)
        swept = [0.0] * len(balances)
        remaining = sweep_budget
        for i in range(len(balances)):
            if not sweepable[i] or remaining <= 0:
                continue
            pay = round(min(remaining, balances[i]), MONEY)
            swept[i] = pay
            balances[i] = round(balances[i] - pay, MONEY)
            remaining = round(remaining - pay, MONEY)
        optional_sweep = round(sum(swept), MONEY)
        ending_cash = round(pre_sweep_cash - optional_sweep, MONEY)
        if ending_cash < min_cash - TOL:
            min_cash_ok = False

        end_debt = round(sum(balances), MONEY)
        net_debt = round(end_debt - ending_cash, MONEY)
        leverage = round(net_debt / ebitda, RATIO) if ebitda else None
        coverage = round(ebitda / interest, RATIO) if interest else None

        rows.append({
            "year": t, "revenue": rev, "ebitda": ebitda, "da": da, "ebit": ebit,
            "beginning_debt": beg_debt, "interest": interest, "ebt": ebt,
            "cash_taxes": cash_taxes, "capex": capex, "delta_nwc": delta_nwc,
            "mandatory_amort": mandatory_amort, "fcf_before_sweep": fcf_before_sweep,
            "beginning_cash": beginning_cash, "optional_sweep": optional_sweep,
            "ending_cash": ending_cash, "ending_debt": end_debt, "net_debt": net_debt,
            "leverage": leverage, "interest_coverage": coverage,
            "tranches": [
                {"name": tr_names[i], "beginning": beg_tranche[i], "interest": round(rates[i] * beg_tranche[i], MONEY),
                 "mandatory_amort": mand[i], "sweep": swept[i], "ending": balances[i]}
                for i in range(len(balances))
            ],
        })
        beginning_cash = ending_cash
        prev_rev = rev

    # --- exit ---------------------------------------------------------------------------
    last = rows[-1]
    exit_ebitda = last["ebitda"]
    exit_mult = _exit_multiple(doc, name)
    exit_ev = round(exit_ebitda * exit_mult, MONEY)
    net_debt_exit = last["net_debt"]
    exit_equity = round(exit_ev - net_debt_exit, MONEY)

    sponsor_equity = su["sponsor_equity"]
    moic = round(exit_equity / sponsor_equity, RATIO) if sponsor_equity else None
    if moic is not None and moic > 0 and hold > 0:
        irr = round(moic ** (1.0 / hold) - 1.0, RATIO)
    else:
        irr = None

    # --- tie-outs (each re-checked independently in validate_output) --------------------
    interest_ok = True
    fcf_ok = True
    debt_rollforward_ok = True
    cash_rollforward_ok = True
    prev_cash = _v(doc.get("opening_cash", 0.0))
    for r in rows:
        exp_int = round(sum(tr["interest"] for tr in r["tranches"]), MONEY)
        if abs(exp_int - r["interest"]) > TOL:
            interest_ok = False
        exp_fcf = round(r["ebitda"] - r["interest"] - r["cash_taxes"] - r["capex"]
                        - r["delta_nwc"] - r["mandatory_amort"], MONEY)
        if abs(exp_fcf - r["fcf_before_sweep"]) > TOL:
            fcf_ok = False
        for tr in r["tranches"]:
            exp_end = round(tr["beginning"] - tr["mandatory_amort"] - tr["sweep"], MONEY)
            if abs(exp_end - tr["ending"]) > TOL:
                debt_rollforward_ok = False
        exp_end_cash = round(prev_cash + r["fcf_before_sweep"] - r["optional_sweep"], MONEY)
        if abs(exp_end_cash - r["ending_cash"]) > TOL:
            cash_rollforward_ok = False
        prev_cash = r["ending_cash"]

    exit_ok = (abs(exit_ev - round(exit_ebitda * exit_mult, MONEY)) <= TOL
               and abs(exit_equity - (exit_ev - net_debt_exit)) <= TOL)
    returns_ok = (moic is not None
                  and abs(moic * sponsor_equity - exit_equity) <= TOL
                  and (irr is None or abs((1.0 + irr) ** hold - moic) <= 1e-4))

    return {
        "name": name,
        "drivers_resolved": d,
        "exit_multiple": exit_mult,
        "years": rows,
        "exit": {
            "exit_ebitda": exit_ebitda, "exit_multiple": exit_mult,
            "exit_enterprise_value": exit_ev, "net_debt_at_exit": net_debt_exit,
            "exit_equity_value": exit_equity,
        },
        "returns": {
            "sponsor_equity": sponsor_equity, "exit_equity_value": exit_equity,
            "moic": moic, "irr": irr, "hold_years": hold,
        },
        "min_cash_ok": min_cash_ok,
        "tieouts": {
            "su_ok": su["su_balanced_ok"], "interest_ok": interest_ok, "fcf_ok": fcf_ok,
            "debt_rollforward_ok": debt_rollforward_ok,
            "cash_rollforward_ok": cash_rollforward_ok,
            "exit_ok": exit_ok, "returns_ok": returns_ok,
        },
    }


def _register(doc: dict) -> list:
    register = []
    for k in DRIVER_KEYS:
        node = doc["drivers"][k]
        register.append({"id": f"driver:{k}", "scope": "operating-driver", "value": _v(node),
                         "provenance": _prov(node), "citation": _cite(node)})
    for k in ("entry_ebitda", "entry_multiple"):
        register.append({"id": f"entry:{k}", "scope": "entry", "value": _v(doc[k]),
                         "provenance": _prov(doc[k]), "citation": _cite(doc[k])})
    fees = doc.get("fees") or {}
    for k in ("transaction_fee_pct", "financing_fee_pct"):
        if k in fees:
            register.append({"id": f"fees:{k}", "scope": "entry", "value": _v(fees[k]),
                             "provenance": _prov(fees[k]), "citation": _cite(fees[k])})
    for tr in doc["debt_tranches"]:
        for k in ("turns", "rate", "amort_pct"):
            if k in tr:
                register.append({"id": f"debt:{tr['name']}:{k}", "scope": "capital-structure",
                                 "value": _v(tr[k]), "provenance": _prov(tr[k]),
                                 "citation": _cite(tr[k])})
    register.append({"id": "exit:exit_multiple", "scope": "exit",
                     "value": _v(doc["exit"]["exit_multiple"]),
                     "provenance": _prov(doc["exit"]["exit_multiple"]),
                     "citation": _cite(doc["exit"]["exit_multiple"])})
    for k in ("opening_cash", "min_cash"):
        if k in doc:
            register.append({"id": f"liquidity:{k}", "scope": "liquidity", "value": _v(doc[k]),
                             "provenance": _prov(doc[k]), "citation": _cite(doc[k])})
    return register


def compute(doc: dict) -> dict:
    su = build_sources_and_uses(doc)
    scenarios = [project(doc, su, s) for s in ("base", "upside", "downside")]
    by = {s["name"]: s for s in scenarios}

    def _mono(*path):
        def get(s):
            node = s
            for p in path:
                node = node[p]
            return node
        dn, bs, up = get(by["downside"]), get(by["base"]), get(by["upside"])
        if None in (dn, bs, up):
            return True
        return dn <= bs + TOL and bs <= up + TOL

    returns_monotonic_ok = (_mono("exit", "exit_equity_value")
                            and _mono("returns", "moic")
                            and _mono("returns", "irr"))

    # --- reproducibility hash over the assumption inputs --------------------------------
    hash_src = json.dumps({
        "entry_ebitda": _v(doc["entry_ebitda"]), "entry_multiple": _v(doc["entry_multiple"]),
        "hold_years": int(doc["hold_years"]),
        "fees": {k: _v(v) for k, v in (doc.get("fees") or {}).items()},
        "tranches": [{"name": t["name"], "turns": _v(t["turns"]), "rate": _v(t["rate"]),
                      "amort_pct": _v(t.get("amort_pct", 0.0)),
                      "cash_sweep": bool(t.get("cash_sweep", False))}
                     for t in doc["debt_tranches"]],
        "drivers": {k: _v(doc["drivers"][k]) for k in DRIVER_KEYS},
        "opening_cash": _v(doc.get("opening_cash", 0.0)),
        "min_cash": _v(doc.get("min_cash", 0.0)),
        "exit_multiple": _v(doc["exit"]["exit_multiple"]),
        "scenario_adjustments": doc.get("scenario_adjustments") or {},
    }, sort_keys=True)
    inputs_hash = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()[:16]

    return {
        "model_id": f"lbo-{str(doc['company_id']).replace('*', '')}-{doc['entry_date']}-{inputs_hash}",
        "company_id": doc["company_id"],
        "as_of": doc["as_of"],
        "entry_date": doc["entry_date"],
        "currency": doc.get("currency"),
        "units": doc.get("units"),
        "config_version": doc.get("config_version"),
        "inputs_hash": inputs_hash,
        "hold_years": int(doc["hold_years"]),
        "entry_ebitda": _v(doc["entry_ebitda"]),
        "entry_multiple": _v(doc["entry_multiple"]),
        "sources_and_uses": su,
        "scenarios": scenarios,
        "assumptions_register": _register(doc),
        "model_checks": {
            "su_balanced_ok": su["su_balanced_ok"],
            "returns_monotonic_ok": returns_monotonic_ok,
            "all_tieouts_ok": all(all(s["tieouts"].values()) for s in scenarios),
            "min_cash_ok": all(s["min_cash_ok"] for s in scenarios),
        },
        "disclaimer": DISCLAIMER,
    }


def _selfcheck(pack: dict) -> list:
    """Internal tie-out check for --selftest: the built model must be internally consistent."""
    errors = []
    mc = pack.get("model_checks", {})
    for k in ("su_balanced_ok", "returns_monotonic_ok", "all_tieouts_ok"):
        if not mc.get(k):
            errors.append(f"model_checks.{k} is not true")
    for s in pack.get("scenarios", []):
        for name, ok in (s.get("tieouts") or {}).items():
            if not ok:
                errors.append(f"scenario {s.get('name')} tie-out {name} failed")
    if pack.get("inputs_hash") not in (pack.get("model_id") or ""):
        errors.append("model_id does not bind inputs_hash")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "lbo_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        pack = compute(doc)
        print(json.dumps(pack, indent=2))
        errors = _selfcheck(pack)
        for e in errors:
            print("ERROR", e)
        print(f"self-check: {len(errors)} error(s)")
        return 1 if errors else 0
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
