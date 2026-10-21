#!/usr/bin/env python3
"""Deterministic output validation for lbo-model-builder.

Validates the final LBO model pack (the calculate_or_transform core + an author narrative)
before it is presented or delivered. Checks, in order of the archetype's validation focus:

  1. Formula tie-outs, re-derived independently (not trusted from the pack):
       - Sources & Uses balance: total_sources == total_uses; sponsor_equity ==
         total_uses - total_new_debt; total_new_debt == sum(tranche principals);
         purchase EV == entry_ebitda * entry_multiple.
       - Per scenario, per year: interest == sum(rate * beginning balance);
         fcf_before_sweep == EBITDA - interest - cash taxes - capex - dNWC - mandatory amort;
         debt roll-forward ending == beginning - mandatory - sweep (per tranche);
         cash roll-forward ending == beginning + fcf_before_sweep - optional sweep;
         year-1 tranche beginning == the tranche's S&U principal.
       - Exit: exit EV == exit EBITDA * exit multiple; exit equity == exit EV - net debt.
       - Returns: MOIC == exit equity / sponsor equity; (1 + IRR)^hold == MOIC.
  2. Scenario behaviour: base / upside / downside present; exit equity, MOIC, and IRR
     monotonic (downside <= base <= upside).
  3. Assumption provenance: every register entry carries a non-empty provenance AND citation.
  4. Reproducibility: model_id and inputs_hash present.
  5. No investment advice: no invest/acquire/commit recommendation, no guaranteed return/IRR,
     and no investment-committee approval language in author free text.
  6. Standing disclaimer present.

Usage:
  python validate_output.py lbo_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.01
DISCLAIMER = ("Illustrative leveraged-buyout model for analytical purposes only; not "
              "investment advice, not a recommendation to make, hold, or exit any "
              "investment, not a guarantee of any return, IRR, or multiple, and not an "
              "investment-committee approval. Outputs depend entirely on the stated "
              "assumptions, which a qualified human must review.")

# Affirmative advice / recommendation / return-guarantee / IC-approval assertions an R2
# model must NOT make. Worded so the standing disclaimer above (which uses negated forms:
# "not investment advice", "not a recommendation to make, hold, or exit any investment",
# "not a guarantee of any return, IRR, or multiple", "not an investment-committee approval")
# does not self-trip: the patterns require an affirmative directed form, not the negation.
ADVICE_PATTERNS = [
    r"\byou should (invest|acquire|buy|pass on|proceed|commit|walk away|do this deal|approve)\b",
    r"\bwe recommend (investing|acquiring|proceeding|committing|the investment|this deal|the deal|approving|approval)\b",
    r"\bi recommend (investing|acquiring|proceeding|committing|this deal|the deal)\b",
    r"\b(approve|approving) (the|this) (deal|investment|transaction)\b",
    r"\b(strong|clear|compelling|attractive) (buy|investment recommendation)\b",
    r"\bguaranteed (return|irr|moic|multiple|upside)\b",
    r"\b(returns?|irr|moic) (of [\d.]+%?\s*)?(is|are) guaranteed\b",
    r"\bthe deal (will|is guaranteed to) (return|deliver|generate|produce)\b",
    r"\brisk-free (return|irr|investment)\b",
    r"\brated (a )?(buy|strong buy)\b",
]


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _check_sources_uses(pack: dict) -> list[str]:
    errors = []
    su = pack.get("sources_and_uses") or {}
    ts = _num(su.get("total_sources"))
    tu = _num(su.get("total_uses"))
    if ts is None or tu is None:
        errors.append("sources_and_uses missing total_sources/total_uses")
        return errors
    if abs(ts - tu) > TOL:
        errors.append(f"sources & uses do not balance (sources {ts} != uses {tu})")

    tranches = su.get("tranches") or []
    sum_principal = round(sum(_num(t.get("principal"), 0.0) for t in tranches), 4)
    tnd = _num(su.get("total_new_debt"))
    if tnd is not None and abs(tnd - sum_principal) > TOL:
        errors.append(f"total_new_debt {tnd} != sum of tranche principals {sum_principal}")
    se = _num(su.get("sponsor_equity"))
    if se is not None and tnd is not None and abs(se - (tu - tnd)) > TOL:
        errors.append(f"sponsor_equity tie-out fails (total_uses {tu} - total_new_debt {tnd} != {se})")

    ee = _num(pack.get("entry_ebitda")); em = _num(pack.get("entry_multiple"))
    pev = _num(su.get("purchase_enterprise_value"))
    if None not in (ee, em, pev) and abs(pev - round(ee * em, 4)) > TOL:
        errors.append(f"purchase EV tie-out fails (entry_ebitda {ee} * entry_multiple {em} != {pev})")
    return errors


def _check_scenario(name: str, s: dict, su: dict) -> list[str]:
    errors = []
    rate_by_name = {t.get("name"): _num(t.get("rate")) for t in (su.get("tranches") or [])}
    principal_by_name = {t.get("name"): _num(t.get("principal")) for t in (su.get("tranches") or [])}
    rows = s.get("years") or []
    if not rows:
        return [f"scenario {name}: no forecast years"]

    prev_cash = None
    prev_ending = {}       # tranche name -> prior-year ending balance
    for idx, r in enumerate(rows):
        y = r.get("year")
        ebitda = _num(r.get("ebitda")); interest = _num(r.get("interest"))
        taxes = _num(r.get("cash_taxes")); capex = _num(r.get("capex"))
        dnwc = _num(r.get("delta_nwc")); mand = _num(r.get("mandatory_amort"))
        fcf = _num(r.get("fcf_before_sweep")); sweep = _num(r.get("optional_sweep"))
        beg_cash = _num(r.get("beginning_cash")); end_cash = _num(r.get("ending_cash"))

        # per-tranche interest + debt roll-forward
        tr_interest_sum = 0.0
        for tr in r.get("tranches") or []:
            tn = tr.get("name")
            b = _num(tr.get("beginning")); a = _num(tr.get("mandatory_amort"), 0.0)
            sw = _num(tr.get("sweep"), 0.0); e = _num(tr.get("ending")); ti = _num(tr.get("interest"))
            if None in (b, e):
                errors.append(f"scenario {name} year {y} tranche {tn}: missing beginning/ending")
                continue
            if abs((b - a - sw) - e) > TOL:
                errors.append(f"scenario {name} year {y} tranche {tn}: debt roll-forward fails "
                              f"(beginning {b} - amort {a} - sweep {sw} != ending {e})")
            rate = rate_by_name.get(tn)
            if rate is not None and ti is not None and abs(round(rate * b, 4) - ti) > TOL:
                errors.append(f"scenario {name} year {y} tranche {tn}: interest tie-out fails "
                              f"(rate {rate} * beginning {b} != {ti})")
            if ti is not None:
                tr_interest_sum += ti
            # year-1 beginning must equal the tranche's S&U principal
            if idx == 0 and tn in principal_by_name and principal_by_name[tn] is not None \
                    and abs(b - principal_by_name[tn]) > TOL:
                errors.append(f"scenario {name} tranche {tn}: year-1 beginning {b} != S&U principal "
                              f"{principal_by_name[tn]}")
            # continuity: this year's beginning == last year's ending
            if tn in prev_ending and prev_ending[tn] is not None and abs(b - prev_ending[tn]) > TOL:
                errors.append(f"scenario {name} year {y} tranche {tn}: beginning {b} != prior ending "
                              f"{prev_ending[tn]}")
            prev_ending[tn] = e

        if interest is not None and abs(round(tr_interest_sum, 4) - interest) > TOL:
            errors.append(f"scenario {name} year {y}: interest tie-out fails "
                          f"(sum of tranche interest {round(tr_interest_sum,4)} != {interest})")

        # fcf build
        if None not in (ebitda, interest, taxes, capex, dnwc, mand, fcf):
            exp_fcf = round(ebitda - interest - taxes - capex - dnwc - mand, 4)
            if abs(exp_fcf - fcf) > TOL:
                errors.append(f"scenario {name} year {y}: fcf tie-out fails "
                              f"(ebitda {ebitda} - interest - taxes - capex - dNWC - amort {exp_fcf} != {fcf})")

        # cash roll-forward
        if None not in (beg_cash, fcf, sweep, end_cash):
            if abs(round(beg_cash + fcf - sweep, 4) - end_cash) > TOL:
                errors.append(f"scenario {name} year {y}: cash roll-forward fails "
                              f"(beginning {beg_cash} + fcf {fcf} - sweep {sweep} != ending {end_cash})")
        if prev_cash is not None and beg_cash is not None and abs(beg_cash - prev_cash) > TOL:
            errors.append(f"scenario {name} year {y}: beginning cash {beg_cash} != prior ending {prev_cash}")
        prev_cash = end_cash

    # exit
    ex = s.get("exit") or {}
    xe = _num(ex.get("exit_ebitda")); xm = _num(ex.get("exit_multiple"))
    xev = _num(ex.get("exit_enterprise_value")); nd = _num(ex.get("net_debt_at_exit"))
    xeq = _num(ex.get("exit_equity_value"))
    if None not in (xe, xm, xev) and abs(round(xe * xm, 4) - xev) > TOL:
        errors.append(f"scenario {name}: exit tie-out fails (exit_ebitda {xe} * multiple {xm} != EV {xev})")
    if None not in (xev, nd, xeq) and abs((xev - nd) - xeq) > TOL:
        errors.append(f"scenario {name}: exit tie-out fails (exit EV {xev} - net debt {nd} != equity {xeq})")

    # returns
    rr = s.get("returns") or {}
    se = _num(rr.get("sponsor_equity")); xq = _num(rr.get("exit_equity_value"))
    moic = _num(rr.get("moic")); irr = _num(rr.get("irr")); hold = _num(rr.get("hold_years"))
    if None not in (se, xq, moic) and se:
        if abs(moic * se - xq) > TOL:
            errors.append(f"scenario {name}: returns tie-out fails "
                          f"(moic {moic} * sponsor_equity {se} != exit_equity {xq})")
    if None not in (moic, irr, hold) and moic > 0:
        if abs((1.0 + irr) ** hold - moic) > 1e-3:
            errors.append(f"scenario {name}: IRR tie-out fails ((1+irr {irr})^{hold} != moic {moic})")
    return errors


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    errors += _check_sources_uses(pack)

    scenarios = pack.get("scenarios") or []
    by = {s.get("name"): s for s in scenarios}
    su = pack.get("sources_and_uses") or {}

    for req in ("base", "upside", "downside"):
        if req not in by:
            errors.append(f"missing required scenario '{req}'")

    for s in scenarios:
        errors += _check_scenario(s.get("name", "?"), s, su)

    # scenario behaviour: monotonic across exit equity, MOIC, and IRR
    if all(n in by for n in ("base", "upside", "downside")):
        checks = [("exit_equity_value", lambda s: (s.get("exit") or {}).get("exit_equity_value")),
                  ("moic", lambda s: (s.get("returns") or {}).get("moic")),
                  ("irr", lambda s: (s.get("returns") or {}).get("irr"))]
        for label, get in checks:
            d = _num(get(by["downside"])); b = _num(get(by["base"])); u = _num(get(by["upside"]))
            if None in (d, b, u):
                continue
            if not (d <= b + TOL and b <= u + TOL):
                errors.append(f"scenario {label}s not monotonic (expected downside <= base <= upside): "
                              f"downside={d}, base={b}, upside={u}")

    # assumption provenance
    register = pack.get("assumptions_register") or []
    if not register:
        errors.append("assumptions_register missing (provenance must be recorded for every assumption)")
    for a in register:
        if not (a.get("provenance") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing provenance")
        if not (a.get("citation") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing citation")

    # reproducibility
    if not (pack.get("model_id") or "").strip():
        errors.append("missing model_id (reproducibility)")
    if not (pack.get("inputs_hash") or "").strip():
        errors.append("missing inputs_hash (reproducibility)")

    # advice/recommendation/return-guarantee scan over author free text — NOT the disclaimer.
    # The standing disclaimer itself contains negated phrases; strip it first so it cannot
    # self-trip, even when an author embeds it inside the narrative.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("note", "")) for s in scenarios])
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited investment-advice/recommendation language detected: {m.group(0)!r} "
                          f"(R2 models and explains; it does not advise, recommend, guarantee a return, "
                          f"or approve a deal)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "lbo_pack_example.json"
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
