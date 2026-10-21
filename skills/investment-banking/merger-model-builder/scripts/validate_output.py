#!/usr/bin/env python3
"""Deterministic output validation for merger-model-builder.

Validates the final pro forma model before it is presented or delivered. Independently
recomputes the reported figures from the model's own echoed primitives and driver components
so a mis-stated EPS, ownership split, or accretion figure cannot pass. Checks:

  1. Formula tie-outs — cash + stock consideration = offer value; new shares = stock
     consideration / acquirer price; pro forma shares = acquirer shares + new shares;
     pro forma EPS = pro forma NI / pro forma shares; accretion $/% recompute; ownership
     splits recompute and sum to 100%; verdict matches the sign of accretion.
  2. Assumption provenance — a non-empty assumptions list, every driver carries a citation,
     and the required drivers are present.
  3. Scenario behavior — base/upside/downside present; accretion is monotonic
     (upside >= base >= downside within tolerance), i.e. more synergies / lower premium is
     never less accretive.
  4. Reproducibility — model_id present and stamped with the assumptions_version; tie_outs
     block self-asserts true and is confirmed by the independent recompute above.
  5. No investment advice — no recommendation-to-transact, buy/sell, price-target, valuation
     opinion, or fairness-opinion language; standing disclaimer present.

Usage:
  python validate_output.py model.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REL_TOL = 1e-4   # relative tolerance for recomputed figures
ABS_TOL = 1e-4   # absolute floor for near-zero comparisons
DISCLAIMER = ("Illustrative pro forma model based on stated assumptions; not investment "
              "advice, a fairness opinion, or a recommendation to transact.")
REQUIRED_DRIVERS = {
    "consideration.cash_pct", "consideration.stock_pct", "consideration.offer_premium",
    "synergies.run_rate_pretax", "pro_forma_tax_rate", "financing.new_debt_rate",
}
# Investment-advice / recommendation / valuation-opinion language an R2 model must not use.
ADVICE_PATTERNS = [
    r"\bwe recommend\b", r"\brecommend (buying|acquiring|the acquisition|the deal|proceeding|the transaction)\b",
    r"\bshould (acquire|buy|proceed|pursue|do the deal)\b", r"\bwe advise\b",
    r"\battractive (acquisition|investment|deal|target|opportunity|entry)\b",
    r"\b(buy|sell|hold) rating\b", r"\b(over|under)weight\b", r"\bprice target\b",
    r"\bfair value is\b", r"\bintrinsic value is\b", r"\bunder-?valued\b", r"\bover-?valued\b",
    r"\bfair from a financial point of view\b", r"\bfairness opinion\b",
    r"\bgood (deal|investment|buy)\b", r"\bworth pursuing\b", r"\bcompelling (deal|value|investment)\b",
    r"\bstrong buy\b", r"\byou should (buy|sell|acquire|proceed|invest)\b",
]


def _close(a, b) -> bool:
    a = float(a); b = float(b)
    return abs(a - b) <= max(REL_TOL * abs(b), ABS_TOL)


def validate(model: dict) -> list[str]:
    errors: list[str] = []

    prim = model.get("primitives") or {}
    consid = model.get("consideration") or {}
    base = model.get("base_case") or {}
    own = model.get("pro_forma_ownership") or {}

    acq_ni = float(prim.get("acquirer_net_income", 0) or 0)
    acq_sh = float(prim.get("acquirer_shares", 0) or 0)
    acq_px = float(prim.get("acquirer_price", 0) or 0)
    tgt_sh = float(prim.get("target_shares", 0) or 0)

    # --- 1. formula tie-outs (independent recompute) ---
    offer_value = float(consid.get("offer_value", 0) or 0)
    cash_c = float(consid.get("cash_consideration", 0) or 0)
    stock_c = float(consid.get("stock_consideration", 0) or 0)
    new_shares = float(consid.get("new_shares_issued", 0) or 0)
    offer_px = float(consid.get("offer_price_per_share", 0) or 0)
    cash_pct = float(consid.get("cash_pct", 0) or 0)
    stock_pct = float(consid.get("stock_pct", 0) or 0)

    if not _close(cash_pct + stock_pct, 1.0):
        errors.append(f"consideration cash_pct + stock_pct != 1.0 ({cash_pct + stock_pct})")
    if not _close(offer_px * tgt_sh, offer_value):
        errors.append(f"offer_value {offer_value} != offer_price*target_shares {offer_px * tgt_sh}")
    if not _close(cash_c + stock_c, offer_value):
        errors.append(f"cash+stock consideration {cash_c + stock_c} != offer_value {offer_value}")
    if not _close(offer_value * cash_pct, cash_c):
        errors.append("cash_consideration != offer_value * cash_pct")
    if acq_px and not _close(stock_c / acq_px, new_shares):
        errors.append(f"new_shares_issued {new_shares} != stock_consideration/acquirer_price {stock_c / acq_px if acq_px else 0}")

    pf_shares = float(base.get("pro_forma_shares", 0) or 0)
    if not _close(acq_sh + new_shares, pf_shares):
        errors.append(f"pro_forma_shares {pf_shares} != acquirer_shares + new_shares {acq_sh + new_shares}")

    pf_ni = float(base.get("pro_forma_net_income", 0) or 0)
    pf_eps = float(base.get("pro_forma_eps", 0) or 0)
    if pf_shares and not _close(pf_ni / pf_shares, pf_eps):
        errors.append("pro_forma_eps != pro_forma_net_income / pro_forma_shares")

    std_eps = float(base.get("acquirer_standalone_eps", 0) or 0)
    if acq_sh and not _close(acq_ni / acq_sh, std_eps):
        errors.append("acquirer_standalone_eps != acquirer_net_income / acquirer_shares")

    acc_d = float(base.get("accretion_dilution_dollar", 0) or 0)
    if not _close(pf_eps - std_eps, acc_d):
        errors.append("accretion_dilution_dollar != pro_forma_eps - standalone_eps")
    acc_pct = float(base.get("accretion_dilution_pct", 0) or 0)
    if std_eps and not _close((pf_eps - std_eps) / std_eps * 100.0, acc_pct):
        errors.append("accretion_dilution_pct does not recompute from EPS")

    # verdict vs sign of accretion
    verdict = str(base.get("verdict", "")).lower()
    exp_verdict = "accretive" if acc_pct > 0.1 else ("dilutive" if acc_pct < -0.1 else "neutral")
    if verdict != exp_verdict:
        errors.append(f"verdict {verdict!r} inconsistent with accretion {acc_pct}% (expected {exp_verdict!r})")

    # ownership
    acq_pct = float(own.get("acquirer_pct", -1))
    tgt_pct = float(own.get("target_pct", -1))
    if pf_shares:
        if not _close(acq_sh / pf_shares * 100.0, acq_pct):
            errors.append("pro_forma_ownership.acquirer_pct does not recompute")
        if not _close(new_shares / pf_shares * 100.0, tgt_pct):
            errors.append("pro_forma_ownership.target_pct does not recompute")
    if not _close(acq_pct + tgt_pct, 100.0):
        errors.append(f"pro forma ownership does not sum to 100% ({acq_pct + tgt_pct})")

    # --- 2. assumption provenance ---
    assumptions = model.get("assumptions") or []
    if not assumptions:
        errors.append("assumptions list is empty — no driver provenance")
    drivers = set()
    for a in assumptions:
        drivers.add(a.get("driver"))
        if not str(a.get("citation", "")).strip():
            errors.append(f"assumption {a.get('driver')!r} missing citation")
    missing = REQUIRED_DRIVERS - drivers
    if missing:
        errors.append(f"assumptions missing required drivers: {sorted(missing)}")

    # --- 3. scenario behavior (monotonic in synergies/premium) ---
    scen = {s.get("name"): s for s in (model.get("scenarios") or [])}
    for nm in ("base", "upside", "downside"):
        if nm not in scen:
            errors.append(f"scenarios missing '{nm}'")
    if {"base", "upside", "downside"} <= set(scen):
        up = float(scen["upside"]["accretion_dilution_pct"])
        bs = float(scen["base"]["accretion_dilution_pct"])
        dn = float(scen["downside"]["accretion_dilution_pct"])
        if not (up >= bs - ABS_TOL and bs >= dn - ABS_TOL):
            errors.append(f"scenario accretion not monotonic (downside {dn} <= base {bs} <= upside {up} violated)")

    # --- 4. reproducibility ---
    model_id = str(model.get("model_id", ""))
    av = str(model.get("assumptions_version", ""))
    if not model_id:
        errors.append("model_id missing — model is not reproducibly identified")
    elif av and av not in model_id:
        errors.append("model_id does not embed assumptions_version — reproducibility stamp incomplete")
    tie = model.get("tie_outs") or {}
    for k in ("consideration_ties", "ownership_sums_to_one", "eps_recompute_matches"):
        if tie.get(k) is not True:
            errors.append(f"tie_outs.{k} is not asserted true")

    # --- 5. no investment advice + disclaimer ---
    # Scan free text for advice language, but strip the standing disclaimer first — the
    # disclaimer legitimately contains "investment advice" / "fairness opinion".
    text = " ".join([
        str(model.get("narrative", "")), str(model.get("notes", "")),
        *[str(s.get("reason", "")) for s in (model.get("scenarios") or [])],
    ])
    text = text.replace(DISCLAIMER, " ")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"investment-advice/opinion language detected: {m.group(0)!r} (R2 models do not advise)")
    if DISCLAIMER.lower() not in (str(model.get("narrative", "")) + " " + str(model.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_example.json"
        model = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        model = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        model = json.loads(sys.stdin.read())
    errors = validate(model)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
