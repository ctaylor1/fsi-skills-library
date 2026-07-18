#!/usr/bin/env python3
"""Deterministic output validation for submission-intake-triager.

Validates the final triage packet (the calculate_or_transform core + a narrative) before it
is presented to an underwriter or routed. This is the R3 prohibited-decision screen: it
fails closed if the packet asserts a bind/quote/price/decline/issue/closure — those are
regulated decisions reserved for a licensed human underwriter.

Checks:
  1. routing_recommendation is one of the four documented bands.
  2. routing_recommendation equals the deterministic mapping from appetite_findings + gaps.
  3. Every refer/out appetite finding has >= 1 cited evidence row.
  4. Every reconciliation 'mismatch' carries >= 2 cited source values (surfaced, not hidden).
  5. Follow-up requests exist whenever gaps exist.
  6. No prohibited decision/bind/quote/decline/issue/closure language (narrative + notes +
     finding reasons + follow-up text).
  7. The standing disclaimer is present.

Usage:
  python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

BAND_OUT = "Out-of-appetite (recommend decline — underwriter adjudicates)"
BAND_INCOMPLETE = "Incomplete — pending broker information"
BAND_REFER = "Refer to underwriter"
BAND_IN = "In-appetite — route to underwriter for standard handling"
BANDS = {BAND_OUT, BAND_INCOMPLETE, BAND_REFER, BAND_IN}

DISCLAIMER = ("Triage evidence and routing recommendation only; not a bind, quote, price, "
              "or coverage decision. A licensed underwriter adjudicates; no coverage has "
              "been bound, quoted, priced, declined, or issued.")

# Affirmative regulated-decision / action assertions an R3 triage skill must never make.
# Phrased to catch affirmative statements, not negated disclaimers.
PROHIBITED_PATTERNS = [
    r"\bwe (are )?(bind|binding|will bind)\b", r"\bcoverage is bound\b", r"\bbinding coverage\b",
    r"\bwe (are )?(quote|quoting|will quote)\b", r"\bquoted premium\b", r"\bpremium is \$",
    r"\bwe (are )?(decline|declining|will decline)\b", r"\bthe (risk|submission) is declined\b",
    r"\bcoverage is (declined|denied|bound)\b", r"\bpolicy (has been |is )?issued\b",
    r"\bwe approve the (risk|submission)\b", r"\b(risk|submission) is (approved|accepted|bound)\b",
    r"\bwe are issuing (the )?policy\b", r"\bcase closed\b", r"\bclose the submission\b",
    r"\bsubmission (is )?closed\b",
]


def _expected_band(findings: list, gaps: list) -> str:
    statuses = [f.get("status") for f in findings]
    critical_gap = any(g.get("severity") == "critical" for g in gaps)
    if "out" in statuses:
        return BAND_OUT
    if critical_gap:
        return BAND_INCOMPLETE
    if "refer" in statuses:
        return BAND_REFER
    return BAND_IN


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("appetite_findings") or []
    gaps = pack.get("gaps") or []
    recon = pack.get("reconciliation") or []

    band = pack.get("routing_recommendation")
    if band not in BANDS:
        errors.append(f"routing_recommendation {band!r} is not one of the documented bands")
    else:
        exp = _expected_band(findings, gaps)
        if band != exp:
            errors.append(f"routing_recommendation {band!r} != deterministic {exp!r} "
                          f"for statuses={[f.get('status') for f in findings]}")

    for f in findings:
        if f.get("status") in ("refer", "out"):
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"appetite finding {f.get('rule')} ({f.get('status')}) has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"appetite finding {f.get('rule')} evidence row missing citation")

    for r in recon:
        if r.get("status") == "mismatch":
            vals = r.get("values") or []
            if len(vals) < 2:
                errors.append(f"reconciliation mismatch on {r.get('field')} must carry >= 2 source values")
            for v in vals:
                if not (v.get("citation") or "").strip():
                    errors.append(f"reconciliation mismatch on {r.get('field')} value missing citation")

    if gaps and not (pack.get("follow_up_requests")):
        errors.append("gaps present but no follow_up_requests drafted")

    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
        + [str(f.get("reason", "")) for f in findings]
        + [str(fu.get("request", "")) for fu in (pack.get("follow_up_requests") or [])]
    )
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/bind/quote/decline language detected: {m.group(0)!r} "
                          f"(R3 recommends + evidences; a licensed underwriter decides)")

    combined = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in combined:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
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
