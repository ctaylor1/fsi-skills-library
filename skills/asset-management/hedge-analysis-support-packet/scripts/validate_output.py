#!/usr/bin/env python3
"""Deterministic output validation for hedge-analysis-support-packet.

Validates the final hedge-analysis packet (the calculate_or_transform core + an author
narrative) before it is presented or delivered. Checks, in order of the archetype's
validation focus:

  1. Formula tie-outs, re-derived independently from the packet's own stated sensitivities
     and scenario shocks (never trusted from the packet):
       - residual[f] == portfolio_sensitivity[f] + hedge_sensitivity[f] for every factor
       - residual_gross == sum(|residual[f]|); coverage_overall == (gross_p - residual_gross)/gross_p
       - portfolio scenario P&L == sum(portfolio_sensitivity[f] * shock[f])
       - hedge scenario P&L == sum(hedge_sensitivity[f] * shock[f])
       - hedged scenario P&L == portfolio + hedge (linearity) == sum(residual[f] * shock[f])
  2. Reconciliation: when approved-engine totals are present, the portfolio gross sensitivity
     and each scenario P&L reconcile to them within tolerance.
  3. Provenance: every assumptions_register entry carries a non-empty provenance AND citation;
     the approved model records id + version + effective_date.
  4. Reproducibility: packet_id and inputs_hash present.
  5. Completeness: every candidate hedge carries residual, coverage, and scenario P&L.
  6. Tier boundary (R2): no hedge-selection / recommendation / execution / advice language in
     author free text, and no overstated-efficacy ("guaranteed", "fully eliminates all risk").
  7. Standing disclaimer present.

Usage:
  python validate_output.py hedge_packet.json | --selftest
Prints a line ending "N error(s)"; exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.01
RECON_ABS = 0.01
RECON_REL = 0.005
DISCLAIMER = ("Illustrative hedge-analysis support packet for analytical purposes only. It "
              "calculates exposures, sensitivities, coverage, and scenario P&L for a "
              "human-defined set of candidate hedges under supplied, approved-model "
              "assumptions; it does not select, recommend, rank, or endorse any hedge, is "
              "not a recommendation to enter, adjust, or unwind any position, is not "
              "investment, legal, or tax advice, and does not authorize or execute any "
              "trade. Hedge selection and execution are human decisions; results are only "
              "as good as the stated assumptions, which a qualified human must review.")

# Affirmative, directed hedge-selection / recommendation / execution / advice assertions an
# R2 packet must NOT make. Worded as affirmative directed forms so the standing disclaimer
# (negated: "does not select, recommend, rank...") and negated limitations ("does not
# recommend a hedge") do not self-trip. The disclaimer is stripped before scanning anyway.
BOUNDARY_PATTERNS = [
    r"\b(we|i) recommend (hedging|the hedge|this hedge|adding|putting on|executing|entering|buying|selling|using hedge|hedge h\d|the overlay)\b",
    r"\brecommended hedge (is|would be|:)\b",
    r"\bthe (best|optimal|preferred|recommended|superior|right|correct) hedge (is|would be|to use|to put on|:)\b",
    r"\b(best|optimal|preferred|recommended) choice (is|would be)\b",
    r"\byou should (hedge|use|adopt|implement|put on|execute|enter|select|choose|pick|buy|sell|divest)\b",
    r"\bwe (select|choose|pick|advise|suggest) (hedge|hedging|adopting|implementing|executing|entering)\b",
    r"\b(select|choose|pick|adopt|implement|go with|opt for|execute|enter into|put on) hedge h\d\b",
    r"\bexecute (the |this )?(hedge|trade|overlay|order|position)\b",
    r"\bplace (the |this )?(hedge|trade|order)\b",
    r"\bproceed with (the |this )?(hedge|trade|overlay|position)\b",
    r"\bguaranteed (protection|hedge|return|to (offset|eliminate|remove|protect))\b",
    r"\b(fully|completely|entirely) (eliminat\w*|remov\w*|neutraliz\w*|offset\w*) (all |the )?(risk|exposure|downside)\b",
    r"\byou should (buy|sell|invest|divest)\b",
]


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _recon_tol(approved: float) -> float:
    return max(RECON_ABS, RECON_REL * abs(approved))


def _check_hedge(c: dict, p_sens: dict, gross_p: float, factors: list,
                 scen_shocks: dict, port_pnl: dict) -> list[str]:
    errors = []
    hid = c.get("hedge_id", "?")
    residual = c.get("residual") or {}
    h_sens = c.get("sensitivities") or {}
    if not residual:
        return [f"hedge {hid}: missing residual exposure"]

    # residual tie-out
    for f in factors:
        rf = _num(residual.get(f))
        exp = _num(p_sens.get(f, 0.0), 0.0) + _num(h_sens.get(f, 0.0), 0.0)
        if rf is None:
            errors.append(f"hedge {hid}: residual missing factor {f}")
        elif abs(rf - exp) > TOL:
            errors.append(f"hedge {hid} factor {f}: residual tie-out fails "
                          f"(portfolio {p_sens.get(f, 0.0)} + hedge {h_sens.get(f, 0.0)} != residual {rf})")

    # gross + coverage tie-out
    rg = _num(c.get("residual_gross"))
    exp_rg = round(sum(abs(_num(residual.get(f), 0.0)) for f in factors), 4)
    if rg is None or abs(rg - exp_rg) > TOL:
        errors.append(f"hedge {hid}: residual_gross tie-out fails (expected {exp_rg}, got {rg})")
    cov = _num(c.get("coverage_overall"))
    if gross_p and cov is not None:
        exp_cov = (gross_p - (rg if rg is not None else exp_rg)) / gross_p
        if abs(cov - exp_cov) > 1e-4:
            errors.append(f"hedge {hid}: coverage_overall tie-out fails (expected {round(exp_cov, 6)}, got {cov})")

    # scenario P&L tie-outs
    rows = c.get("scenario_pnl") or {}
    for sid, shocks in scen_shocks.items():
        row = rows.get(sid)
        if not row:
            errors.append(f"hedge {hid}: missing scenario P&L for '{sid}'")
            continue
        exp_pf = round(sum(_num(p_sens.get(f, 0.0), 0.0) * shocks.get(f, 0.0) for f in factors), 4)
        exp_h = round(sum(_num(h_sens.get(f, 0.0), 0.0) * shocks.get(f, 0.0) for f in factors), 4)
        exp_res = round(sum(_num(residual.get(f, 0.0), 0.0) * shocks.get(f, 0.0) for f in factors), 4)
        pf, h_pnl, hedged = _num(row.get("portfolio")), _num(row.get("hedge")), _num(row.get("hedged"))
        if pf is None or h_pnl is None or hedged is None:
            errors.append(f"hedge {hid} scenario {sid}: missing portfolio/hedge/hedged P&L")
            continue
        if abs(pf - exp_pf) > TOL or abs(h_pnl - exp_h) > TOL:
            errors.append(f"hedge {hid} scenario {sid}: scenario P&L tie-out fails "
                          f"(portfolio {pf} vs {exp_pf}, hedge {h_pnl} vs {exp_h})")
        if abs(hedged - (pf + h_pnl)) > TOL or abs(hedged - exp_res) > TOL:
            errors.append(f"hedge {hid} scenario {sid}: scenario P&L tie-out fails "
                          f"(hedged {hedged} != portfolio+hedge {round(pf + h_pnl, 4)} / residual {exp_res})")
        if port_pnl.get(sid) is not None and abs(_num(port_pnl[sid], 0.0) - exp_pf) > TOL:
            errors.append(f"hedge {hid} scenario {sid}: portfolio_scenario_pnl inconsistent "
                          f"({port_pnl[sid]} != {exp_pf})")
    return errors


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    factors = pack.get("factors") or list((pack.get("portfolio") or {}).get("sensitivities", {}).keys())
    port = pack.get("portfolio") or {}
    p_sens = port.get("sensitivities") or {}
    gross_p = round(sum(abs(_num(p_sens.get(f, 0.0), 0.0)) for f in factors), 4)

    # portfolio gross tie-out
    stated_gross = _num(port.get("gross_sensitivity"))
    if stated_gross is None or abs(stated_gross - gross_p) > TOL:
        errors.append(f"portfolio gross_sensitivity tie-out fails (expected {gross_p}, got {stated_gross})")

    scen_shocks = {s["id"]: {k: _num(v, 0.0) for k, v in (s.get("shocks") or {}).items()}
                   for s in (pack.get("scenarios") or [])}
    port_pnl = pack.get("portfolio_scenario_pnl") or {}

    comparison = pack.get("comparison") or []
    if not comparison:
        errors.append("comparison table is empty — no candidate hedges to compare")
    for c in comparison:
        errors += _check_hedge(c, p_sens, gross_p, factors, scen_shocks, port_pnl)

    # reconciliation to approved-engine totals (only checked when present in the packet)
    recon = pack.get("reconciliation") or {}
    if recon.get("supplied"):
        g = recon.get("gross") or {}
        if "approved" in g:
            a, comp = _num(g.get("approved")), _num(g.get("computed"))
            if comp is None or abs(comp - gross_p) > TOL:
                errors.append(f"reconciliation gross computed value is inconsistent with the packet ({comp} != {gross_p})")
            if a is not None and comp is not None and abs(comp - a) > _recon_tol(a):
                errors.append(f"reconciliation to approved-engine gross fails (approved {a}, computed {comp})")
        for sid, r in (recon.get("scenarios") or {}).items():
            a, comp = _num(r.get("approved")), _num(r.get("computed"))
            if a is not None and comp is not None and abs(comp - a) > _recon_tol(a):
                errors.append(f"reconciliation to approved-engine scenario '{sid}' fails (approved {a}, computed {comp})")

    # model provenance (version + effective date)
    model = pack.get("model") or {}
    for k in ("id", "version", "effective_date"):
        if not str(model.get(k, "")).strip():
            errors.append(f"model.{k} missing (approved-model version/effective-date provenance required)")

    # assumption provenance
    register = pack.get("assumptions_register") or []
    if not register:
        errors.append("assumptions_register missing (provenance must be recorded for every assumption)")
    for a in register:
        if not str(a.get("provenance", "")).strip():
            errors.append(f"assumption {a.get('id')!r} missing provenance")
        if not str(a.get("citation", "")).strip():
            errors.append(f"assumption {a.get('id')!r} missing citation")

    # reproducibility
    if not str(pack.get("packet_id", "")).strip():
        errors.append("missing packet_id (reproducibility)")
    if not str(pack.get("inputs_hash", "")).strip():
        errors.append("missing inputs_hash (reproducibility)")

    # tier-boundary scan over author free text — NOT the disclaimer. Strip the standing
    # disclaimer first so its negated phrasing cannot self-trip even if embedded in narrative.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(x) for x in (pack.get("limitations") or [])]
                    + [str(c.get("note", "")) for c in comparison])
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in BOUNDARY_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited hedge-selection/recommendation language detected: {m.group(0)!r} "
                          f"(R2 calculates and compares; it does not select, recommend, or execute a hedge)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "hedge_packet_example.json"
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
