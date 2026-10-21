#!/usr/bin/env python3
"""Deterministic output validation for portfolio-risk-contribution-analyzer.

Validates the final risk-contribution packet (the calculate_or_transform core + an author
narrative) before it is presented or delivered. Checks, in order of the archetype's
validation focus:

  1. Formula tie-outs, re-derived INDEPENDENTLY from the pack's weights + covariance (not
     trusted from the emitted contributions):
       - portfolio variance == w' * Sigma * w ; total risk == sqrt(variance)
       - marginal contribution MCR_i == (Sigma * w)_i / total_risk
       - total contribution   TRC_i == w_i * MCR_i
       - Euler identity: sum(TRC_i) == total_risk
       - sum(PCR_i) == 1 ; PCR_i == TRC_i / total_risk
       - group aggregation: sum of group TRC == total_risk ; sum of group PCR == 1
  2. Variance guard: portfolio variance > 0 (else the decomposition is undefined).
  3. Reconciliation to the approved risk engine total: the recorded `reconciled` flag must
     equal (rel_diff <= tolerance), and rel_diff is re-derived from the totals.
  4. Assumption/version provenance: methodology name + version present; every assumptions
     register entry carries a non-empty provenance AND citation.
  5. Reproducibility: packet_id and inputs_hash present.
  6. Tier boundary (R2 fail-closed): no risk-limit-setting, no mandate/trade/rebalance/hedge
     directive, and no buy/sell/hold investment advice in the author free text.
  7. Standing disclaimer present.

Usage:
  python validate_output.py risk_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, math, re, sys
from pathlib import Path

TOL = 1e-4
DISCLAIMER = ("Illustrative risk-contribution analysis for analytical purposes only; not a "
              "risk limit, not a mandate to trade, rebalance, or hedge, and not investment "
              "advice. Risk contributions are conditional on the stated methodology, "
              "weights, and covariance inputs, which a qualified human and the approved risk "
              "engine must review.")

# Affirmative decisions/actions/advice an R2 model must NOT make. Worded so the standing
# disclaimer above (which says "not a risk limit", "not a mandate to trade, rebalance, or
# hedge", "not investment advice") does not self-trip: the disclaimer is stripped first, and
# the patterns require affirmative directed forms, not the negated disclaimer form.
PROHIBITED_PATTERNS = [
    # setting or changing a risk limit
    r"\bset(ting)? (the |a |an )?(risk |var |volatility |exposure )?limit(s)? (to|at|of)\b",
    r"\b(raise|raising|lower|lowering|reduce|reducing|increase|increasing|tighten|tightening|"
    r"loosen|loosening|adjust|adjusting|change|changing|revise|revising) (the |a |an )?"
    r"(risk |var |volatility |exposure )?limit(s)?\b",
    r"\b(risk |var |volatility )?limit(s)? should be (set )?(to|at|higher|lower|reduced|increased|raised|lowered)\b",
    r"\bimpose (a |an )?(new )?(risk )?limit\b",
    # mandating trades / rebalances / hedges / position actions
    r"\b(you|the pm|the fund|the desk|management) (must|should|need to|needs to|have to|has to) "
    r"(sell|buy|trim|cut|reduce|hedge|rebalance|de-?risk|divest|liquidate|unwind|add to|increase|overweight|underweight)\b",
    r"\b(sell|trim|cut|reduce|hedge|rebalance|de-?risk|divest|liquidate|unwind) (the |this |that )?"
    r"(position|holding|exposure|portfolio|book|name|weight|allocation)\b",
    r"\bwe recommend (selling|buying|trimming|cutting|reducing|hedging|rebalancing|divesting|a (buy|sell|reduction))\b",
    r"\b(i|we) recommend (that )?(you |the pm )?(sell|buy|trim|cut|reduce|hedge|rebalance|divest)\b",
    r"\brebalance (to|toward|towards|into)\b",
    r"\bmandat(e|es|ing) (a |an |the )?(sale|trade|reduction|rebalanc\w*|hedge|action|change)\b",
    # investment advice / rating / target / guarantee
    r"\byou should (buy|sell|hold|short|avoid|overweight|underweight)\b",
    r"\b(our|the) (buy|sell|hold|overweight|underweight) (rating|call|recommendation)\b",
    r"\brated (a )?(buy|sell|hold)\b",
    r"\bprice target (of|is|:)\b",
    r"\bguaranteed (to reduce|to lower|return|risk reduction|reduction)\b",
]


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _recompute(pack: dict) -> tuple[dict, list[str]]:
    """Independently re-derive risk, MCR, TRC, PCR from weights + covariance."""
    errors: list[str] = []
    contribs = pack.get("contributions") or []
    cov = pack.get("covariance") or {}
    order = cov.get("order")
    matrix = cov.get("matrix")
    w_by = {c.get("position_id"): _num(c.get("weight")) for c in contribs}
    if not order or not matrix or any(w_by.get(pid) is None for pid in (order or [])):
        return {}, ["cannot re-derive tie-outs: missing covariance.order/matrix or a position weight"]
    n = len(order)
    if len(matrix) != n or any(len(r) != n for r in matrix):
        return {}, [f"covariance.matrix is not square {n}x{n}"]
    w = [w_by[pid] for pid in order]
    sigma_w = [sum(_num(matrix[i][j], 0.0) * w[j] for j in range(n)) for i in range(n)]
    var_p = sum(w[i] * sigma_w[i] for i in range(n))
    if var_p <= 0:
        return {"var_p": var_p}, ["portfolio variance is not > 0 (risk decomposition undefined)"]
    sigma_p = math.sqrt(var_p)
    mcr = {order[i]: sigma_w[i] / sigma_p for i in range(n)}
    trc = {order[i]: w[i] * mcr[order[i]] for i in range(n)}
    pcr = {order[i]: trc[order[i]] / sigma_p for i in range(n)}
    return {"var_p": var_p, "sigma_p": sigma_p, "mcr": mcr, "trc": trc, "pcr": pcr}, errors


def _validate_legacy(pack: dict) -> list[str]:
    errors: list[str] = []
    contribs = pack.get("contributions") or []
    if not contribs:
        errors.append("contributions missing (no per-position risk contributions to validate)")

    total_risk = _num(pack.get("total_risk"))
    if total_risk is None:
        errors.append("missing total_risk")

    derived, derr = _recompute(pack)
    errors += derr

    if derived.get("sigma_p") is not None and total_risk is not None:
        if abs(derived["sigma_p"] - total_risk) > 1e-3:
            errors.append(f"total_risk tie-out fails: recomputed sqrt(w'Sigma w) "
                          f"{round(derived['sigma_p'], 6)} != total_risk {total_risk}")
        var_emit = _num(pack.get("portfolio_variance"))
        if var_emit is not None and abs(derived["var_p"] - var_emit) > 1e-3:
            errors.append(f"portfolio_variance tie-out fails: recomputed {round(derived['var_p'], 6)} "
                          f"!= emitted {var_emit}")

    # per-position tie-outs (MCR, TRC, PCR) against the independent re-derivation
    if derived.get("trc"):
        for c in contribs:
            pid = c.get("position_id")
            if pid not in derived["trc"]:
                errors.append(f"position {pid}: not present in covariance order; cannot verify")
                continue
            for key, dmap in (("mcr", derived["mcr"]), ("trc", derived["trc"]), ("pcr", derived["pcr"])):
                emitted = _num(c.get(key))
                if emitted is None:
                    errors.append(f"position {pid}: missing {key}")
                elif abs(emitted - dmap[pid]) > 1e-3:
                    errors.append(f"position {pid}: {key} tie-out fails "
                                  f"(emitted {emitted} != recomputed {round(dmap[pid], 6)})")

    # Euler identity + percentage sum from the emitted contributions
    if contribs and total_risk is not None:
        sum_trc = round(sum(_num(c.get("trc"), 0.0) for c in contribs), 6)
        if abs(sum_trc - total_risk) > 1e-3:
            errors.append(f"Euler tie-out fails: sum of total risk contributions {sum_trc} "
                          f"!= total_risk {total_risk} (homogeneity requires equality)")
        sum_pcr = round(sum(_num(c.get("pcr"), 0.0) for c in contribs), 6)
        if abs(sum_pcr - 1.0) > 1e-3:
            errors.append(f"percentage contributions do not sum to 1 (sum_pcr {sum_pcr})")

    # group aggregation tie-outs
    groups = pack.get("group_contributions") or []
    if groups and total_risk is not None:
        g_trc = round(sum(_num(g.get("trc"), 0.0) for g in groups), 6)
        g_pcr = round(sum(_num(g.get("pcr"), 0.0) for g in groups), 6)
        if abs(g_trc - total_risk) > 1e-3:
            errors.append(f"group total-risk aggregation fails: sum of group TRC {g_trc} != total_risk {total_risk}")
        if abs(g_pcr - 1.0) > 1e-3:
            errors.append(f"group percentage aggregation fails: sum of group PCR {g_pcr} != 1")

    # variance guard
    if pack.get("var_guard_ok") is False:
        errors.append("var_guard_ok is false (portfolio variance not positive; decomposition undefined)")

    # reconciliation to the approved risk engine total
    rec = pack.get("reconciliation")
    if rec is None:
        errors.append("reconciliation to approved-engine total is missing (required)")
    else:
        approved = _num(rec.get("approved_engine_total"))
        computed = _num(rec.get("computed_total"))
        tol_rel = _num(rec.get("tolerance_rel"), 0.01)
        reconciled = rec.get("reconciled")
        if approved is None or computed is None:
            errors.append("reconciliation missing approved_engine_total or computed_total")
        else:
            rel = abs(computed - approved) / abs(approved) if approved else None
            expect = (rel is not None and rel <= tol_rel)
            if bool(reconciled) != expect:
                errors.append(f"reconciliation flag inconsistent: reconciled={reconciled} but "
                              f"rel_diff {None if rel is None else round(rel, 6)} vs tolerance {tol_rel}")
            if reconciled and rel is not None and rel > tol_rel:
                errors.append(f"reconciliation claims tie but computed risk {computed} does not match "
                              f"approved engine total {approved} within tolerance {tol_rel}")
            if total_risk is not None and computed is not None and abs(total_risk - computed) > 1e-6:
                errors.append(f"reconciliation.computed_total {computed} != pack total_risk {total_risk}")

    # methodology / version provenance
    method = pack.get("methodology") or {}
    if not (method.get("name") or "").strip():
        errors.append("methodology.name missing (methodology provenance required)")
    if not (method.get("version") or "").strip():
        errors.append("methodology.version missing (version provenance required)")

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
    if not (pack.get("packet_id") or "").strip():
        errors.append("missing packet_id (reproducibility)")
    if not (pack.get("inputs_hash") or "").strip():
        errors.append("missing inputs_hash (reproducibility)")

    # tier boundary: no limit-setting / mandate / advice in author free text (NOT the disclaimer)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(g.get("note", "")) for g in groups])
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited risk-limit/mandate/advice language detected: {m.group(0)!r} "
                          f"(R2 models and explains; it never sets a limit, mandates an action, or advises)")

    # standing disclaimer
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def validate(pack: dict, source_doc: dict | None = None) -> list[str]:
    """Require detached original input; do not authenticate it or approve narrative."""
    import runpy
    try:
        errors = _validate_legacy(pack)
    except (TypeError, ValueError, KeyError, AttributeError, OverflowError) as exc:
        return [f"malformed output: {exc}"]
    engine = runpy.run_path(str(Path(__file__).with_name("calculate_or_transform.py")))
    integrity = runpy.run_path(str(Path(__file__).with_name("native_integrity.py")))
    integrity["validate_reconstruction"](pack, engine["compute"], errors, original_input=source_doc)
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "risk_pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    source_doc = None
    if "--input" in argv:
        source_doc = json.loads(Path(argv[argv.index("--input") + 1]).read_text(encoding="utf-8"))
    errors = validate(pack, source_doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
