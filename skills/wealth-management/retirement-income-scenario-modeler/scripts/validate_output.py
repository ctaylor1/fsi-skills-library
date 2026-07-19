#!/usr/bin/env python3
"""Deterministic output validation for retirement-income-scenario-modeler.

Validates the final retirement-income projection pack (the calculate_or_transform core plus
an author narrative) before it is presented or handed off. Checks, in the order of the
archetype's validation focus, and fails closed on any miss:

  1. Formula tie-outs (per scenario, re-derived independently, NOT trusted from the pack):
       - each account's balance roll-forward: end == (begin - gross_withdrawal) * (1 + return)
       - the begin balance of year j+1 equals the end balance of year j (continuity)
       - funding identity: guaranteed_income_net + net_withdrawal + shortfall - surplus == spending
       - tax identity: net_withdrawal == gross_withdrawal_total - tax_portfolio;
         tax_total == tax_portfolio + tax_guaranteed
       - portfolio totals: begin/end_portfolio == sum of the account begins/ends
       - non-negativity: no negative balance; no withdrawal exceeding the begin balance
       - and, on top of that independent re-derivation, fail closed if the pack SELF-REPORTS a
         tie-out failure (model_checks.all_tieouts_ok is false, or any scenario
         tieouts.*_ok is false): a model that flags its own formula tie-outs as broken must
         never be presented.
  2. Scenario behaviour: base / favorable / adverse present; terminal portfolio value is
     monotonic (adverse <= base <= favorable) and total shortfall is monotonic
     (favorable <= base <= adverse).
  3. Assumption provenance: every entry in the assumptions register carries a non-empty
     provenance AND citation.
  4. Reproducibility: model_id and inputs_hash are present.
  5. R3 hard boundary: NO advice / recommendation to adopt a strategy, NO guarantee of income
     or that assets will last, and NO regulated-decision / case-closure / filing / system-of-
     record-write language in the author free text (regex screen).
  6. Standing disclaimer present.

Usage:
  python validate_output.py retirement_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.02
DISCLAIMER = ("Illustrative retirement-income projection for planning purposes only, "
              "expressed as a range across deterministic scenarios; not a guarantee of "
              "future income, returns, or that assets will last, and not a probability of "
              "success. Not investment, tax, insurance, or legal advice and not a "
              "recommendation to adopt any withdrawal, claiming, or product strategy. "
              "Outputs depend entirely on the stated assumptions, which a qualified human "
              "must review; any recommendation or decision requires licensed-advisor and "
              "client adjudication.")

# Affirmative advice / guarantee / regulated-decision assertions an R3 model must NOT make.
# Worded as directed/affirmative forms so the standing disclaimer's negated phrases
# ("not a guarantee", "not a recommendation to adopt...") do not self-trip.
ADVICE_PATTERNS = [
    # personalized advice / recommendation to act
    r"\byou should (retire|claim|delay|buy|purchase|annuitize|convert|withdraw|roll over|move|invest)\b",
    r"\bwe recommend (retiring|claiming|delaying|buying|purchasing|annuitizing|converting|the annuity|you|that you)\b",
    r"\bi recommend (retiring|claiming|delaying|buying|purchasing|annuitizing|converting)\b",
    r"\b(our|the|my) recommendation is\b",
    r"\bthe (best|right|optimal|recommended) (strategy|option|choice|withdrawal rate|claiming age) (is|would be)\b",
    r"\byou (can|will) safely (retire|withdraw|spend)\b",
    # guarantees
    r"\bguaranteed (income|return|to last|not to run out|for life)\b",
    r"\b(your|the) (money|portfolio|assets|savings|plan) (will|are guaranteed to) (last|never run out|not run out)\b",
    r"\byou (will|are guaranteed to) (never run out|not run out|have enough)\b",
    r"\brisk-free (income|return|retirement)\b",
    r"\b\d{1,3}% (probability|chance) of success\b",
    # regulated decision / closure / filing / system-of-record write
    r"\b(recommendation|strategy|plan|withdrawal rate) (is|has been) approved\b",
    r"\b(suitability|reg ?bi|reg bi) (approved|cleared|signed off)\b",
    r"\b(case|review|plan) (closed|is closed|has been closed)\b",
    r"\b(filed|submitted|posted|executed|placed the trade|booked) (with|to|the|in)\b",
    r"\b(written|saved|committed) to the (crm|system of record|book of record|custodian)\b",
    r"\bi have (executed|placed|submitted|filed|booked|rebalanced)\b",
]


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _check_scenario(s: dict) -> list[str]:
    errors = []
    name = s.get("name", "?")
    rows = s.get("years") or []
    if not rows:
        return [f"scenario {name}: no projection years"]

    prev_end = None            # per-account end of the prior year -> continuity check
    total_shortfall = 0.0
    for r in rows:
        yr = r.get("year")
        spending = _num(r.get("spending_need"))
        g_net = _num(r.get("guaranteed_income_net"))
        net_wd = _num(r.get("net_withdrawal"))
        gross_total = _num(r.get("gross_withdrawal_total"))
        tax_pf = _num(r.get("tax_portfolio"))
        tax_g = _num(r.get("tax_guaranteed"))
        tax_total = _num(r.get("tax_total"))
        shortfall = _num(r.get("shortfall"))
        surplus = _num(r.get("surplus"))
        funded = _num(r.get("funded"))
        begin_pf = _num(r.get("begin_portfolio"))
        end_pf = _num(r.get("end_portfolio"))
        accts = r.get("accounts") or []
        if None in (spending, g_net, net_wd, gross_total, tax_pf, tax_g, tax_total,
                    shortfall, surplus, funded, begin_pf, end_pf):
            errors.append(f"scenario {name} year {yr}: missing numeric fields")
            continue

        # per-account roll-forward + continuity + non-negativity
        sum_begin = sum_end = sum_gross = 0.0
        cur_end = {}
        for a in accts:
            aid = a.get("id")
            begin = _num(a.get("begin")); gross = _num(a.get("gross_withdrawal"))
            ret = _num(a.get("return_applied")); end = _num(a.get("end"))
            if None in (begin, gross, ret, end):
                errors.append(f"scenario {name} year {yr} account {aid}: missing numeric fields")
                continue
            after = begin - gross
            if after < 0:
                after = 0.0
            if abs(round(after * (1.0 + ret), 2) - end) > TOL:
                errors.append(f"scenario {name} year {yr} account {aid}: roll-forward tie-out fails "
                              f"((begin {begin} - gross {gross}) * (1+{ret}) != end {end})")
            if begin < -TOL or end < -TOL or gross > begin + TOL:
                errors.append(f"scenario {name} year {yr} account {aid}: negative balance or "
                              f"withdrawal exceeds balance")
            if prev_end is not None and aid in prev_end and abs(prev_end[aid] - begin) > TOL:
                errors.append(f"scenario {name} year {yr} account {aid}: begin {begin} != prior "
                              f"year end {prev_end[aid]} (continuity)")
            sum_begin += begin; sum_end += end; sum_gross += gross
            cur_end[aid] = end
        prev_end = cur_end

        # portfolio totals
        if abs(round(sum_begin, 2) - begin_pf) > TOL:
            errors.append(f"scenario {name} year {yr}: begin_portfolio {begin_pf} != sum of account begins {round(sum_begin,2)}")
        if abs(round(sum_end, 2) - end_pf) > TOL:
            errors.append(f"scenario {name} year {yr}: end_portfolio {end_pf} != sum of account ends {round(sum_end,2)}")
        if abs(round(sum_gross, 2) - gross_total) > TOL:
            errors.append(f"scenario {name} year {yr}: gross_withdrawal_total {gross_total} != sum of account grosses {round(sum_gross,2)}")

        # tax identity
        if abs(net_wd - (gross_total - tax_pf)) > TOL:
            errors.append(f"scenario {name} year {yr}: net_withdrawal tie-out fails "
                          f"(gross {gross_total} - tax_portfolio {tax_pf} != net {net_wd})")
        if abs(tax_total - (tax_pf + tax_g)) > TOL:
            errors.append(f"scenario {name} year {yr}: tax_total tie-out fails "
                          f"(tax_portfolio {tax_pf} + tax_guaranteed {tax_g} != tax_total {tax_total})")

        # funding identity
        if abs(funded - (g_net + net_wd)) > TOL:
            errors.append(f"scenario {name} year {yr}: funded tie-out fails "
                          f"(guaranteed_net {g_net} + net_withdrawal {net_wd} != funded {funded})")
        if abs((funded + shortfall - surplus) - spending) > TOL:
            errors.append(f"scenario {name} year {yr}: funding identity fails "
                          f"(funded {funded} + shortfall {shortfall} - surplus {surplus} != spending {spending})")
        total_shortfall += shortfall

    # scenario total shortfall tie-out
    reported_short = _num(s.get("total_shortfall"))
    if reported_short is not None and abs(reported_short - round(total_shortfall, 2)) > TOL:
        errors.append(f"scenario {name}: total_shortfall {reported_short} != sum of yearly shortfalls {round(total_shortfall,2)}")
    return errors


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    scenarios = pack.get("scenarios") or []
    by = {s.get("name"): s for s in scenarios}

    for req in ("base", "favorable", "adverse"):
        if req not in by:
            errors.append(f"missing required scenario '{req}'")

    for s in scenarios:
        errors += _check_scenario(s)

    # scenario behaviour: terminal monotonic (adverse <= base <= favorable),
    # shortfall monotonic (favorable <= base <= adverse)
    if all(n in by for n in ("base", "favorable", "adverse")):
        d = _num(by["adverse"].get("terminal_portfolio_value"))
        b = _num(by["base"].get("terminal_portfolio_value"))
        u = _num(by["favorable"].get("terminal_portfolio_value"))
        if None not in (d, b, u) and not (d <= b + TOL and b <= u + TOL):
            errors.append(f"terminal portfolio values not monotonic (expected adverse <= base <= favorable): "
                          f"adverse={d}, base={b}, favorable={u}")
        sd = _num(by["adverse"].get("total_shortfall"))
        sb = _num(by["base"].get("total_shortfall"))
        su = _num(by["favorable"].get("total_shortfall"))
        if None not in (sd, sb, su) and not (su <= sb + TOL and sb <= sd + TOL):
            errors.append(f"total shortfall not monotonic (expected favorable <= base <= adverse): "
                          f"favorable={su}, base={sb}, adverse={sd}")

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

    # Self-reported tie-out integrity. The engine independently re-derives each scenario's
    # tie-outs and rolls them into scenario["tieouts"] and model_checks.all_tieouts_ok. Those
    # flags are NOT trusted in place of the independent re-derivation above, but a pack that
    # flags its OWN formula tie-outs as broken must never be presented — fail closed.
    mc = pack.get("model_checks") or {}
    if "all_tieouts_ok" in mc and not mc.get("all_tieouts_ok"):
        errors.append("model_checks.all_tieouts_ok is false (the model reports its own formula "
                      "tie-outs do not hold)")
    for s in scenarios:
        for flag, ok in (s.get("tieouts") or {}).items():
            if ok is False:
                errors.append(f"scenario {s.get('name')!r}: reported tie-out {flag} is false "
                              f"(the model's own integrity self-check failed)")

    # R3 hard-boundary scan over author free text — NOT the disclaimer.
    # The standing disclaimer contains negated phrases ("not a guarantee", "not a
    # recommendation to adopt..."); strip it first so it cannot self-trip.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("note", "")) for s in scenarios])
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited advice/guarantee/decision language detected: {m.group(0)!r} "
                          f"(R3 models and explains a RANGE; it does not advise, guarantee, decide, "
                          f"close, or file — those require licensed-human adjudication)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "retirement_pack_example.json"
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
