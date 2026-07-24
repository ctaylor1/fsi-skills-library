#!/usr/bin/env python3
"""Deterministic output validation for voting-policy-consistency-checker.

Screens the final consistency review (the calculate_or_transform core + a narrative) before
it is presented to the analyst. This is the R3 prohibited-decision gate: the skill evidences
deviations, it NEVER decides, changes, casts, or submits a vote. A non-compliant review
(decision/action language, missing disclaimer, or a tampered disposition) MUST fail closed.

Checks:
  1. Structural: findings present; each finding has an item_id and a known status.
  2. Cited evidence: every aligned/deviation/case_by_case finding cites a policy; every
     deviation/case_by_case/no_policy finding carries a human-adjudication required_action.
  3. overall_disposition equals the deterministic mapping from the findings.
  4. No vote-decision / vote-action language in the free text (narrative, notes, reasons).
  5. The standing disclaimer is present.

Usage:
  python validate_output.py review.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

VALID_STATUSES = {"aligned", "deviation", "case_by_case", "no_policy"}
DISCLAIMER = (
    "Consistency findings and cited evidence only; not a voting decision or instruction. "
    "This review does not cast, change, or submit any vote; a human analyst adjudicates and "
    "records the vote in the system of record.")

# Assertions an R3 consistency review must never make: that a vote was/will be decided,
# cast, changed, submitted, or otherwise actioned. Phrased to catch completed/imperative
# actions, not neutral descriptions of the human's downstream responsibility.
DECISION_PATTERNS = [
    r"\bwe will vote\b", r"\bi will vote\b", r"\bwe are voting\b",
    r"\bcast(ing)? (the |this |a |our )?vote\b",
    r"\bcast(ing)? (the |this |a )?ballot\b",
    r"\bsubmit(ted|ting)? (the |this |a |our )?(vote|ballot|voting instruction|proxy)\b",
    r"\bchang(e|ed|ing) (the |this |our |my )?vote\b",
    r"\boverrid(e|den|ing) (the |this )?(vote|proposed vote)\b",
    r"\bfinal(iz|is)(e|ed|ing) (the |this )?(vote|ballot)\b",
    r"\bvote (has been|was) (cast|submitted|finalized|finalised|changed|recorded|filed|sent)\b",
    r"\bballot (has been |was )?(submitted|cast|filed|sent)\b",
    r"\bvoting instruction(s)? (submitted|sent|filed|issued|recorded)\b",
    r"\binstruct(ing|ed)? the (ballot|proxy|vote)\b",
    r"\bthe (final )?decision is to vote\b",
]


def expected_disposition(findings: list[dict]) -> str:
    statuses = {f.get("status") for f in findings}
    if "deviation" in statuses:
        return "deviations_present"
    if ({"case_by_case", "no_policy"} & statuses
            or any(f.get("precedent_discordant") for f in findings)):
        return "review_recommended"
    return "consistent"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    if not findings:
        errors.append("no findings present — nothing to review")

    for f in findings:
        tag = f.get("item_id") or f.get("finding_id") or "?"
        status = f.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"finding {tag}: invalid status {status!r}")
            continue
        if status in ("aligned", "deviation", "case_by_case") and not (f.get("policy_citation") or "").strip():
            errors.append(f"finding {tag} ({status}) missing policy_citation (cited evidence required)")
        if status in ("deviation", "case_by_case", "no_policy") and not (f.get("required_action") or "").strip():
            errors.append(f"finding {tag} ({status}) missing required_action (human adjudication required)")

    exp = expected_disposition(findings)
    if pack.get("overall_disposition") != exp:
        errors.append(
            f"overall_disposition {pack.get('overall_disposition')!r} != deterministic "
            f"{exp!r} for findings")

    # Free-text screen: narrative + notes + finding reasons. Strip the disclaimer first so
    # its own controlled wording is never mistaken for an assertion.
    narrative = str(pack.get("narrative", "")).replace(DISCLAIMER, " ")
    text = " ".join([narrative, str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(
                f"decision/action language detected: {m.group(0)!r} "
                f"(R3 evidences deviations; it never decides, changes, or submits a vote)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_example.json"
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
