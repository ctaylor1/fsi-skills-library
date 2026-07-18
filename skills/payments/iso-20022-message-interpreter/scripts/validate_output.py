#!/usr/bin/env python3
"""Deterministic output validation for iso-20022-message-interpreter.

Confirms an interpretation object (see calculate_or_transform.py) is internally consistent,
fully cited, free of remediation/advice or regulated-determination language, and carries the
standing disclaimer BEFORE it is presented or delivered. This is the fail-closed gate for the
Explain & summarize archetype: a non-compliant interpretation exits non-zero.

Checks:
  1. Required fields present (message_type, message_name, transactions, narrative, disclaimer).
  2. Control totals tie: summary.nb_of_txs == len(transactions); summed amounts == summary.total_amount.
  3. Citation coverage: every transaction AND every finding carries a non-empty citation.
  4. No-advice / prohibited-claim screen: narrative + finding messages + notes contain no
     remediation directive (resubmit / repair / release funds / retry / approve / you should /
     we recommend) and no regulated determination (fraud / sanctions / AML / compliant /
     guaranteed to settle). Any hit FAILS CLOSED.
  5. Standing disclaimer present.
  6. Rejected-status coverage: any rejected/returned transaction must carry a reason or an
     explicit finding noting the missing reason (no silent rejection interpretation).

Usage:
  python validate_output.py interpretation.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

AMOUNT_TOL = 0.01
REQUIRED = ("message_type", "message_name", "transactions", "narrative", "disclaimer")

# Remediation directives and regulated determinations this R2 interpreter must never make.
PROHIBITED = [
    r"\byou (should|must|need to|ought to)\b",
    r"\bwe (recommend|advise|suggest)\b",
    r"\bi (recommend|advise|suggest)\b",
    r"\b(please )?resubmit\b", r"\bre-?send\b", r"\bre-?submit the\b",
    r"\bretry (the|this) (payment|transaction)\b",
    r"\brepair (the|this) (payment|message|transaction)\b",
    r"\brelease (the )?funds\b", r"\bsafe to release\b",
    r"\bforce[- ]settle\b", r"\bmanually post\b", r"\boverride the\b",
    r"\bapprove(d)? (the|this) (payment|repair|resubmission)\b",
    r"\bsanctions[- ]clear(ed)?\b", r"\baml[- ]clear(ed)?\b",
    r"\bno fraud\b", r"\bis (not )?fraud(ulent)?\b",
    r"\b(is|are) (fully )?compliant\b",
    r"\bguaranteed to settle\b", r"\bwill (definitely )?settle\b",
]
DISCLAIMER_RE = re.compile(
    r"interpretation and explanation only.*not a payment instruction.*"
    r"(repair authorization|compliance/fraud determination|determination)", re.I | re.S)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(s: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(s, dict):
        return ["interpretation must be a JSON object"]
    for k in REQUIRED:
        if k not in s or s[k] in (None, "", []):
            errors.append(f"missing required field '{k}'")
    txs = s.get("transactions") or []
    if not txs:
        errors.append("interpretation has no transactions")

    # Control totals
    summary = s.get("summary") or {}
    nb = summary.get("nb_of_txs")
    if nb is not None and _num(nb) is not None and int(_num(nb)) != len(txs):
        errors.append(f"summary.nb_of_txs {nb} != transactions listed {len(txs)}")
    ta = _num(summary.get("total_amount"))
    if ta is not None:
        summed = sum(_num((t.get('amount') or {}).get('value')) or 0.0 for t in txs)
        if abs(summed - ta) > max(AMOUNT_TOL, abs(ta) * 0.0001):
            errors.append(f"summary.total_amount {ta} != summed transaction amounts {summed:.2f}")

    # Citation coverage
    for t in txs:
        if not (t.get("citation") or "").strip():
            errors.append(f"transaction {t.get('end_to_end_id', '?')}: missing citation")
        si = t.get("status_interpretation") or {}
        cat = str(si.get("category", ""))
        if cat in ("rejected", "returned"):
            has_reason = bool(si.get("reason_code") or si.get("reason_plain") or si.get("reason_text"))
            has_finding = any(f.get("code") in ("REJECT_NO_REASON",) for f in s.get("findings", []))
            if not has_reason and not has_finding:
                errors.append(f"transaction {t.get('end_to_end_id', '?')}: rejected status with no "
                              "reason and no explicit missing-reason finding (fail closed)")
    for f in s.get("findings", []):
        if not (f.get("citation") or "").strip():
            errors.append(f"finding {f.get('code', '?')}: missing citation")

    # No-advice / prohibited-claim screen
    scanned = " ".join([str(s.get("narrative", "")), str(s.get("notes", ""))]
                       + [str(f.get("message", "")) for f in s.get("findings", [])])
    for pat in PROHIBITED:
        m = re.search(pat, scanned, re.I)
        if m:
            errors.append(f"prohibited action/determination language detected: {m.group(0)!r} "
                          "(R2 interpreter is explanatory only; route action to the appropriate skill)")

    # Standing disclaimer
    if not DISCLAIMER_RE.search(str(s.get("disclaimer", "")) + " " + str(s.get("narrative", ""))):
        errors.append("missing standing disclaimer: 'Interpretation and explanation only; not a "
                      "payment instruction, repair authorization, or compliance/fraud determination.'")

    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "interpretation_valid.json"
        s = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        s = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        s = json.loads(sys.stdin.read())
    errors = validate(s)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
