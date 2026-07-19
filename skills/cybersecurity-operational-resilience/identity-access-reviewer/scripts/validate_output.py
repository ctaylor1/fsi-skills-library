#!/usr/bin/env python3
"""Deterministic output validation for identity-access-reviewer (R3 fail-closed screen).

Validates the final access-review pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks:
  1. Every fired finding has >= 1 cited evidence row.
  2. suggested_priority equals the deterministic mapping from fired_findings.
  3. No access-decision / execution / closure / filing / certification language in the
     narrative, notes, or finding reasons (R3 stages recommendations; it never decides/acts).
  4. Every staged revocation is a candidate marked "staged_for_approval" and references a
     fired finding — never an executed/completed action (fail closed on autonomous action).
  5. The standing disclaimer is present.
  6. context_prompts are included when any finding fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"sod_conflict", "dormant_privileged", "orphaned_account", "privileged_without_mfa"}
STAGED_OK = {"staged_for_approval", "pending_approval", "recommended"}
DISCLAIMER = ("Access-review evidence and staged recommendations only; not an access "
              "decision. No entitlement has been revoked, disabled, or certified.")

# Prohibited: language asserting the skill decided/executed/closed/filed/certified. R3
# decision-support stages recommendations for a human control owner; it never acts.
DECISION_PATTERNS = [
    r"\brevoked\b", r"\bhas been (revoked|removed|disabled|deprovisioned|certified)\b",
    r"\bdeprovisioned\b", r"\bderprovisioned\b",
    r"\baccount(s)? (was|were|has been|have been|is|are) disabled\b",
    r"\bdisabled the account\b", r"\bwe disabled\b",
    r"\bremoved the entitlement\b", r"\bentitlement(s)? removed\b",
    r"\bauto-?remediat", r"\bremediation (was |has been )?applied\b",
    r"\bcertification (is )?complete\b", r"\bre-?certified\b",
    r"\bcertified and closed\b", r"\battestation signed\b", r"\bsigned the attestation\b",
    r"\bclosed the (review|case)\b", r"\b(review|case) closed\b",
    r"\baccess (is |was )?approved\b", r"\bapproved the revocation\b",
    r"\bdenied the (request|access)\b", r"\bwe (have )?(revoked|disabled|removed)\b",
]


def _expected_priority(fired: list[str]) -> str:
    if len(fired) >= 3 or (ESCALATORS & set(fired)):
        return "Elevated"
    return "Review" if fired else "Informational"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    fired = [f["finding"] for f in findings if f.get("fired")]

    # 1. evidence + citations on every fired finding
    for f in findings:
        if f.get("fired"):
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"fired finding {f['finding']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired finding {f['finding']} evidence row missing citation")

    # 2. deterministic priority tie-out
    exp = _expected_priority(fired)
    if pack.get("suggested_priority") != exp:
        errors.append(f"suggested_priority {pack.get('suggested_priority')!r} != deterministic {exp!r} for fired={fired}")

    # 3. no decision/execution/closure language (scan narrative + notes + finding reasons,
    #    NOT the disclaimer field which legitimately names those actions as negatives)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"decision/action language detected: {m.group(0)!r} (R3 stages recommendations; it does not decide/act)")

    # 4. staged revocations must be candidates only, tied to a fired finding
    for sr in pack.get("staged_revocations") or []:
        gid = sr.get("grant_id", "?")
        status = str(sr.get("status", "")).lower()
        if status not in STAGED_OK:
            errors.append(f"staged_revocation {gid} status {sr.get('status')!r} is not a staged candidate "
                          f"(autonomous action is prohibited; must be one of {sorted(STAGED_OK)})")
        rf = sr.get("related_finding")
        if rf not in fired:
            errors.append(f"staged_revocation {gid} related_finding {rf!r} is not a fired finding")

    # 5. standing disclaimer present
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    # 6. context prompts when findings fired
    if fired and not pack.get("context_prompts"):
        errors.append("findings fired but no context_prompts included")

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
