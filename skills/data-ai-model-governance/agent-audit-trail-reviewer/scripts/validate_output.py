#!/usr/bin/env python3
"""Deterministic output validation for agent-audit-trail-reviewer.

Validates the final review pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. This is the R3 prohibited-decision screen: it fails closed if the
pack asserts an autonomous control decision, closure, filing, attestation, or a
system-of-record write — none of which this skill may do.

Checks:
  1. Every finding has >= 1 cited evidence row.
  2. Each finding's severity equals the deterministic severity for its type.
  3. disposition equals the deterministic mapping from the (recomputed) severity counts.
  4. reproducibility block is coherent (incomplete <=> missing_fields non-empty).
  5. human_adjudication_required is true.
  6. The standing disclaimer is present.
  7. No autonomous-decision / closure / filing / attestation language in the free text.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Control-review evidence only; not a control attestation or adjudication. No "
              "finding has been closed, filed, or written to a system of record; human "
              "adjudication is required.")

TYPE_SEVERITY = {
    "prohibited_autonomous_action": "high",
    "unauthorized_override": "high",
    "self_approval": "high",
    "missing_approval": "medium",
    "after_the_fact_approval": "medium",
    "out_of_scope_tool": "medium",
    "retention_gap": "medium",
    "evidence_traceability_gap": "low",
    "reproducibility_gap": "low",
    "logging_gap": "low",
}

# Declarative / completed assertions this R3 skill must NOT make. These target the skill
# claiming it decided/closed/filed/attested — advisory future-tense recommendations ("route
# to an adjudicator to decide whether to close the finding") are intentionally not matched.
PROHIBITED_PATTERNS = [
    r"\bcontrol(s)? (is|are|was|were) (effective|ineffective)\b",
    r"\bpass(ed|es)? the audit\b",
    r"\bfail(ed|s)? the audit\b",
    r"\bthe agent (is|was) (compliant|non-?compliant)\b",
    r"\bwe (closed|close) (the|this) (finding|issue|case|review)\b",
    r"\b(finding|issue|case|review) (has been|is|was) closed\b",
    r"\bclosing (the|this) (finding|issue|case|review)\b",
    r"\bmarked (as )?(resolved|remediated|closed)\b",
    r"\bfiled (the|an|a) (issue|finding|report|complaint)\b",
    r"\blogged (the|an|a) (issue|finding) in\b",
    r"\bwrote (it )?to the (audit|risk|issue)",
    r"\brecorded the attestation\b",
    r"\bopened (issue|finding) [A-Z0-9]",
    r"\bcertif(y|ied|ies)\b",
    r"\bsigned off\b",
    r"\bautonomously (approved|closed|decided|remediated)\b",
    r"\battest(ed) that\b",
]


def _disposition(counts: dict) -> str:
    if counts.get("high", 0) >= 1 or counts.get("medium", 0) >= 3:
        return "Escalate"
    if sum(counts.values()) >= 1:
        return "Review"
    return "No exceptions noted"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    # 1. evidence + citation
    for f in findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('finding_id')} ({f.get('type')}) has no evidence")
        for row in ev:
            if not str(row.get("citation") or "").strip():
                errors.append(f"finding {f.get('finding_id')} evidence row missing citation")

    # 2. severity matches deterministic map; recompute counts from the map (tamper-resistant)
    counts = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        ftype = f.get("type")
        exp_sev = TYPE_SEVERITY.get(ftype)
        if exp_sev is None:
            errors.append(f"finding {f.get('finding_id')} has unknown type {ftype!r}")
            continue
        if f.get("severity") != exp_sev:
            errors.append(f"finding {f.get('finding_id')} severity {f.get('severity')!r} != deterministic {exp_sev!r} for type {ftype}")
        counts[exp_sev] += 1

    # 3. disposition maps deterministically
    exp_disp = _disposition(counts)
    if pack.get("disposition") != exp_disp:
        errors.append(f"disposition {pack.get('disposition')!r} != deterministic {exp_disp!r} for counts {counts}")

    # 4. reproducibility coherence
    repro = pack.get("reproducibility")
    if not isinstance(repro, dict):
        errors.append("missing reproducibility block")
    else:
        complete = bool(repro.get("complete"))
        missing = repro.get("missing_fields") or []
        if complete and missing:
            errors.append("reproducibility.complete is true but missing_fields is non-empty")
        if not complete and not missing:
            errors.append("reproducibility.complete is false but missing_fields is empty")

    # 5. human adjudication flag
    if pack.get("human_adjudication_required") is not True:
        errors.append("human_adjudication_required must be true (R3 mandates human adjudication)")

    # 6. disclaimer present
    joined_disc = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in joined_disc:
        errors.append("missing standing disclaimer text")

    # 7. prohibited-decision screen over free text (narrative + notes + finding descriptions);
    #    the structured disclaimer/disposition fields are excluded by design. The standing
    #    disclaimer itself is a negated phrasing ("No finding has been closed...") so it is
    #    stripped before scanning to avoid a self-inflicted false positive.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("description", "")) for f in findings])
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing/attestation language detected: {m.group(0)!r} "
                          f"(R3 evidences and recommends; it does not decide, close, file, or attest)")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_pack_example.json"
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
