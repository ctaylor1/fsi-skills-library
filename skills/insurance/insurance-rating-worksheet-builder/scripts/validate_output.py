#!/usr/bin/env python3
"""Deterministic output validation for insurance-rating-worksheet-builder.

Enforces the R3 guardrails before the worksheet is presented:
  1. Per coverage: premium_before_fees == base_rate * factor_product (within tolerance).
  2. indicated_premium == Sum coverage_total + policy_fees_total (within tolerance).
  3. No bind / quote-issuance / offer language.
  4. Standing disclaimer present.

Usage: python validate_output.py worksheet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_RE = re.compile(r"not a bound quote", re.I)
PROHIBITED = [
    r"\bbound the coverage\b", r"\bcoverage is bound\b", r"\bwe issue the quote\b",
    r"\bpolicy issued\b", r"\bquote is final\b", r"\bwe bind\b", r"\boffer of coverage extended\b",
    r"\bwe(?:'ve| have) bound\b",
]
TOL = 0.05


def validate(p: dict) -> list[str]:
    errors = []
    from insurance_contract import validate_artifact
    errors.extend(validate_artifact(p.get("artifact"), input_doc=p.get("calculation_inputs"), output=p))
    covs = p.get("coverages") or []
    subtotal = 0.0
    for c in covs:
        base, prod, pbf = c.get("base_rate"), c.get("factor_product"), c.get("premium_before_fees")
        if None not in (base, prod, pbf) and abs(base * prod - pbf) > max(TOL, abs(pbf) * 1e-6):
            errors.append(f"{c.get('coverage')}: premium_before_fees {pbf} != base*factor_product {round(base * prod, 2)}")
        if c.get("coverage_total") is not None:
            subtotal += c["coverage_total"]
    ind = p.get("indicated_premium")
    pf = p.get("policy_fees_total") or 0.0
    if ind is not None and abs((subtotal + pf) - ind) > max(TOL, abs(ind) * 1e-6):
        errors.append(f"indicated_premium {ind} != Sum coverage_total {round(subtotal, 2)} + policy_fees {pf}")
    try:
        from calculate_or_transform import compute
        expected = compute(p["calculation_inputs"])
        for key in ('coverages', 'policy_fees', 'policy_fees_total', 'indicated_premium'):
            if p.get(key) != expected[key]:
                errors.append(f"{key} does not reproduce calculation_inputs")
    except (KeyError, ValueError, TypeError) as exc:
        errors.append(f"missing or invalid calculation_inputs: {exc}")
    scan = json.dumps({k: v for k, v in p.items() if k not in {"disclaimer", "calculation_inputs", "artifact"}}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"bind/quote-issuance language detected: {m.group(0)!r} (R3 indicates, underwriting binds/quotes)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (indicated premium only / not a bound quote)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "worksheet_example.json"
        p = json.loads(pth.read_text(encoding="utf-8"))
    elif argv:
        p = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        p = json.loads(sys.stdin.read())
    errors = validate(p)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
