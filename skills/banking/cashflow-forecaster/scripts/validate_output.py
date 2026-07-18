#!/usr/bin/env python3
"""Deterministic output validation for cashflow-forecaster.

Validates the final forecast pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. Checks:
  1. All three scenarios (base, upside, downside) are present.
  2. Each scenario ties out: opening_balance + sum(period net) == ending_balance, and the
     ending equals the last period's running balance (within tolerance).
  3. Scenario endings are monotonic: downside <= base <= upside (scenario behaviour sanity).
  4. Every assumption in the register carries a provenance tag.
  5. No financial/investment/tax/credit advice, no credit decision, no guarantee of a future
     balance (R2 is a transparent planning model, not advice and not a decision).
  6. The standing disclaimer is present.
  7. Drivers are reported when history exists.

Usage:
  python validate_output.py forecast_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.01
DISCLAIMER = ("Forecast for planning purposes only; not financial, investment, tax, or "
              "credit advice, and not a guarantee of future account balances. Assumptions "
              "are estimates and actual results will vary.")

# Affirmative advice / guarantee / credit-decision assertions an R2 forecast must not make.
# Worded so the standing disclaimer above (which contains "guarantee of" and "credit advice")
# does not self-trip: only "guaranteed" and directed "guarantee <you/your/...>" match.
ADVICE_PATTERNS = [
    r"\byou should (invest|buy|sell|refinance|borrow|take out|open|withdraw|move your money|pay off)\b",
    r"\bwe recommend (that )?you\b",
    r"\bi recommend (that )?you\b",
    r"\bguaranteed\b",
    r"\bguarantee (you|your|a positive|future returns|no overdraft)\b",
    r"\brisk-free\b",
    r"\bpre-?approved\b",
    r"\b(you|they) qualif(y|ies|ied) for\b",
    r"\bapproved for (a |an )?(loan|line of credit|mortgage|overdraft|credit)\b",
    r"\b(will not|won'?t) overdraft\b",
    r"\byou will have (at least|\$|a balance of)\b",
]


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    scenarios = pack.get("scenarios") or []
    by = {s.get("name"): s for s in scenarios}
    opening = float(pack.get("opening_balance", 0.0))

    for req in ("base", "upside", "downside"):
        if req not in by:
            errors.append(f"missing required scenario '{req}'")

    for s in scenarios:
        name = s.get("name")
        rows = s.get("periods") or []
        if not rows:
            errors.append(f"scenario {name} has no periods")
            continue
        sum_net = round(sum(float(r.get("net", 0.0)) for r in rows), 2)
        ending = float(s.get("ending_balance"))
        if abs(opening + sum_net - ending) > TOL:
            errors.append(f"scenario {name} tie-out fails: opening {opening} + sum_net {sum_net} "
                          f"!= ending {ending}")
        if abs(float(rows[-1].get("balance")) - ending) > TOL:
            errors.append(f"scenario {name} ending_balance {ending} != last period balance "
                          f"{rows[-1].get('balance')}")

    if all(n in by for n in ("base", "upside", "downside")):
        d = float(by["downside"]["ending_balance"])
        b = float(by["base"]["ending_balance"])
        u = float(by["upside"]["ending_balance"])
        if not (d <= b + TOL and b <= u + TOL):
            errors.append(f"scenario endings not monotonic (expected downside <= base <= upside): "
                          f"downside={d}, base={b}, upside={u}")

    register = pack.get("assumptions_register") or []
    if not register:
        errors.append("assumptions_register missing (provenance must be recorded for every assumption)")
    for a in register:
        if not (a.get("provenance") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing provenance")

    # advice/guarantee/decision scan over author free text — NOT the disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("note", "")) for s in scenarios])
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited advice/guarantee/decision language detected: {m.group(0)!r} "
                          f"(R2 models and explains; it does not advise, decide, or guarantee)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if (pack.get("history") or {}).get("periods") and not pack.get("drivers"):
        errors.append("history present but no drivers reported")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "forecast_pack_example.json"
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
