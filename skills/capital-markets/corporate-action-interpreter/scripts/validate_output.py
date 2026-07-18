#!/usr/bin/env python3
"""Deterministic output validation for corporate-action-interpreter.

Confirms an interpretation is internally consistent, fully cited, free of advice / tax
advice / binding-election language, and carries the standing disclaimer BEFORE it is
presented or delivered. This is the R2 tier guardrail: the skill explains an event and
computes entitlements, but never recommends an option, gives personalized tax advice, or
submits/records an election.

Checks:
  1. Each stated entitlement recomputes from its terms + eligible quantity (tie-out).
  2. Every entitlement carries a non-empty citation; entitlement basis is a known code.
  3. Voluntary / mandatory-with-options: election_deadline present and echoed in
     action_required; options non-empty with exactly one default; NO option flagged as
     chosen/elected (no binding election).
  4. No advice / recommendation-on-which-option / personalized-tax / binding-instruction
     language anywhere in the narrative or option text.
  5. The standing informational-only disclaimer is present.

Interpretation schema (JSON): see references/domain-rules.md.
{
  "interpretation_id","event_id","event_type","mandatory_voluntary",
  "security":{...}, "key_dates":{...}, "terms":{...},
  "eligible_position":{"quantity",...},
  "action_required":"...",
  "entitlements":[{"basis","value","unit","citation"}],   # mandatory single-outcome
  "options":[{"option_id","default","rate_per_share"|("ratio_new","ratio_old"),
              "description","entitlement":{"basis","value","unit","citation"}}],
  "ambiguities":[...], "narrative":"...", "disclaimer":"..."
}

Usage:
  python validate_output.py interpretation.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

KNOWN_BASES = {"shares_after", "additional_shares", "shares", "cash", "cash_in_lieu"}
OPTIONS_MV = {"voluntary", "mandatory-with-options"}

# Advice / recommendation-on-election / personalized-tax / binding-instruction phrasing.
# NOTE: neutral mentions such as "not investment or tax advice" and "may elect" are safe.
ADVICE_PATTERNS = [
    r"\bwe (recommend|suggest|advise)\b",
    r"\brecommend(s|ed|ing)? (that|electing|taking|tendering|choosing|participating)\b",
    r"\byou should (elect|choose|take|tender|accept|reject|subscribe|participate|buy|sell|hold)\b",
    r"\byou (ought to|had better|are advised to)\b",
    r"\bbest (option|choice|election)\b",
    r"\boptimal (option|choice|election)\b",
    r"\b(elect|choose|take|pick) the (cash|stock|share|tender|exchange|securities) option\b",
    r"\bbetter to (elect|take|choose|tender)\b",
    # personalized tax advice
    r"\byou (will|would|'ll) owe\b",
    r"\btax[- ]free (event )?to you\b",
    r"\bthis is (a )?(taxable|tax[- ]free) (event )?(to|for) you\b",
    r"\byou should report\b",
    r"\byour tax (liability|basis) (is|will be|would be)\b",
    r"\bno tax (is )?due\b",
    # binding election / instruction
    r"\bwe (have|'ve|will|'ll|are) (elect|elected|electing|submit|submitted|tender|tendered|instruct|instructed|placed?|placing)\b",
    r"\byour election (has been|was) (submitted|placed|sent|filed|accepted|recorded)\b",
    r"\binstruct(ed|ing)? the custodian\b",
]
DISCLAIMER_RE = re.compile(
    r"informational interpretation only.*?not (investment or tax|investment|tax) advice.*?not an election",
    re.I | re.S)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _expected(basis, params, qty):
    """Recompute the expected entitlement value from terms/option params. Returns
    a float, None (params insufficient), or 'UNKNOWN' (unrecognized basis)."""
    rn, ro = _num(params.get("ratio_new")), _num(params.get("ratio_old"))
    rate = _num(params.get("rate_per_share"))
    if basis in ("shares_after", "additional_shares", "shares", "cash_in_lieu"):
        if basis == "cash_in_lieu":
            return None
        if rn is None or not ro:
            return None
        return qty * rn / ro
    if basis == "cash":
        if rate is None:
            return None
        return qty * rate
    return "UNKNOWN"


def _check_entitlement(tag, ent, params, qty, errors):
    basis = ent.get("basis")
    if basis not in KNOWN_BASES:
        errors.append(f"{tag}: unknown entitlement basis {basis!r}")
        return
    val = _num(ent.get("value"))
    if val is None:
        errors.append(f"{tag}: entitlement missing numeric 'value'")
    if not (ent.get("citation") or "").strip():
        errors.append(f"{tag}: entitlement missing citation")
    if val is None:
        return
    exp = _expected(basis, params, qty)
    if exp is None:
        errors.append(f"{tag}: entitlement basis {basis!r} not recomputable from terms — cannot verify")
    elif exp != "UNKNOWN":
        tol = max(0.01, abs(exp) * 0.005)
        if abs(val - exp) > tol:
            errors.append(f"{tag}: value {val:g} != recomputed {exp:g} from stated terms")


def validate(s: dict) -> list[str]:
    errors: list[str] = []
    qty = _num((s.get("eligible_position") or {}).get("quantity"))
    mv = s.get("mandatory_voluntary")

    if not s.get("event_type"):
        errors.append("missing event_type")
    if not s.get("security"):
        errors.append("missing security")
    if not s.get("key_dates"):
        errors.append("missing key_dates")

    # 1-2. Entitlement tie-outs + citations.
    seen_entitlement = False
    if qty is not None:
        for i, e in enumerate(s.get("entitlements") or []):
            seen_entitlement = True
            _check_entitlement(f"entitlements[{i}]", e, s.get("terms") or {}, qty, errors)
        for i, opt in enumerate(s.get("options") or []):
            ent = opt.get("entitlement")
            if ent:
                seen_entitlement = True
                _check_entitlement(f"options[{i}] ({opt.get('option_id','?')})", ent, opt, qty, errors)
        if not seen_entitlement:
            errors.append("eligible_position present but no entitlement computed")

    # 3. Voluntary / options integrity + no-binding-election guard.
    if mv in OPTIONS_MV:
        kd = s.get("key_dates") or {}
        deadline = kd.get("election_deadline")
        if not deadline:
            errors.append("options event missing key_dates.election_deadline")
        action = str(s.get("action_required") or "")
        if "election" not in action.lower():
            errors.append("action_required must state that an election is required")
        if deadline and deadline not in action:
            errors.append(f"action_required must cite the election_deadline ({deadline})")
        options = s.get("options") or []
        if not options:
            errors.append("options event missing 'options'")
        defaults = sum(1 for o in options if o.get("default") is True)
        if defaults != 1:
            errors.append(f"expected exactly one default option, found {defaults}")
        for o in options:
            if o.get("elected") is True or o.get("chosen") is True or o.get("submitted") is True:
                errors.append(f"option {o.get('option_id','?')} is flagged elected/chosen/submitted — this skill never records an election")

    # 4. Prohibited-language screen (advice / tax advice / binding instruction).
    text = " ".join([
        str(s.get("narrative", "")),
        str(s.get("action_required", "")),
        " ".join(str(o.get("description", "")) for o in (s.get("options") or [])),
        " ".join(str(a) for a in (s.get("ambiguities") or [])),
        str(s.get("notes", "")),
    ])
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited advice/recommendation/binding language detected: {m.group(0)!r} "
                          f"(R2 informational — no advice, no tax advice, no election)")

    # 5. Standing disclaimer.
    combined = str(s.get("narrative", "")) + " " + str(s.get("disclaimer", ""))
    if not DISCLAIMER_RE.search(combined):
        errors.append("missing standing disclaimer: 'Informational interpretation only; not investment or "
                      "tax advice, and not an election or instruction; ...'")

    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "interpretation_example.json"
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
