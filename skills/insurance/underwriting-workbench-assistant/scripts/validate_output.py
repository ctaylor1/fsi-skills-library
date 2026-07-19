#!/usr/bin/env python3
"""Deterministic output validation for underwriting-workbench-assistant.

Enforces the R3 draft-and-package guardrails before a compiled workbench is presented:
  1. Only advisory dispositions appear (no bind/quote/decline/issue/close states).
  2. Every rule finding carries evidence; the decision rationale is framed for HUMAN
     adjudication and carries no unsupported/unapproved claims.
  3. human_adjudication is recorded and PENDING — no autonomous underwriting decision.
  4. The packaged deliverable contains every required output-template section.
  5. No coverage-binding / decision / filing / system-of-record language anywhere in the
     profiles.
  6. The standing note is present.

Any miss fails closed (exit 1). See references/controls.md and assets/output-template.md.

Usage: python validate_output.py profile.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {"needs-data", "refer-to-underwriter", "ready-for-underwriter-review"}
REQUIRED_TEMPLATE = ["Risk Summary", "Data Completeness", "Source Freshness",
                     "Rule Findings & Exceptions", "Draft Decision Rationale",
                     "Human Adjudication", "Standing Note"]
STANDING_NOTE_KEY = "no coverage has been bound, quoted, declined, or issued"

# Language that would assert an actual underwriting decision or system-of-record write.
DECISION_PATTERNS = [
    r"\bpolicy (is |has been )?bound\b", r"\bcoverage (is |has been )?bound\b",
    r"\bbind the risk\b", r"\bwe (will )?bind\b", r"\bbound as quoted\b",
    r"\bapproved for binding\b",
    r"\brisk (is |has been )?declined\b", r"\bwe (will )?decline\b", r"\bdecline the risk\b",
    r"\bdeclinature (issued|approved)\b",
    r"\bpolicy (is |has been )?issued\b", r"\bissue the policy\b",
    r"\bquote (is |has been )?issued\b", r"\bwe will insure\b",
    r"\bcoverage (is |has been )?granted\b",
    r"\bunderwriting decision:? (approved|declined|bound)\b", r"\bfinal (underwriting )?decision\b",
    r"\bfiled to (the )?policy admin", r"\bposted to (the )?policy admin",
    r"\bsystem of record (is |has been )?updated\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    profiles = doc.get("profiles") or []
    if not profiles:
        return ["workbench output has no profiles"]

    for p in profiles:
        sid = p.get("submission_id", "?")
        disp = p.get("recommended_disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{sid}: disallowed disposition {disp!r} "
                          "(draft-only decision support; no bind/quote/decline/issue/close)")

        for f in p.get("rule_findings") or []:
            if not f.get("evidence"):
                errors.append(f"{sid}: rule finding {f.get('rule_id')} missing evidence citation")

        dr = p.get("decision_rationale") or {}
        if dr.get("unsupported_claims"):
            errors.append(f"{sid}: decision_rationale.unsupported_claims must be empty, "
                          f"found {dr.get('unsupported_claims')}")
        if "underwriter adjudication" not in str(dr.get("recommendation", "")).lower():
            errors.append(f"{sid}: recommendation must be framed for human underwriter adjudication")

        ha = p.get("human_adjudication") or {}
        if ha.get("status") != "pending":
            errors.append(f"{sid}: human_adjudication.status must be 'pending' (draft-only), "
                          f"got {ha.get('status')!r}")
        if ha.get("decision") is not None:
            errors.append(f"{sid}: human_adjudication.decision must be null until a human "
                          f"underwriter decides, got {ha.get('decision')!r}")
        if not ha.get("required_approver"):
            errors.append(f"{sid}: human_adjudication missing required_approver")

        comp = p.get("completeness") or {}
        if disp == "ready-for-underwriter-review" and comp.get("complete") is not True:
            errors.append(f"{sid}: ready-for-underwriter-review requires a complete profile")
        if disp == "refer-to-underwriter" and not (p.get("rule_findings")):
            errors.append(f"{sid}: refer-to-underwriter requires at least one rule finding")

    # Coverage-decision / filing language screen (profiles only; note/template are constant).
    scan = json.dumps(profiles)
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"binding/decision language detected: {m.group(0)!r} "
                          "(draft-only; the decision belongs to a human underwriter)")

    present = doc.get("template_sections_present") or []
    miss = [s for s in REQUIRED_TEMPLATE if s not in present]
    if miss:
        errors.append("missing required template section(s): " + ", ".join(miss))

    if STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "profile_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
