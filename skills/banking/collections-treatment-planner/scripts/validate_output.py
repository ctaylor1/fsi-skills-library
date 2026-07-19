#!/usr/bin/env python3
"""Deterministic output validation for collections-treatment-planner.

Validates the final treatment-plan pack (the calculate_or_transform core + a narrative)
before it is presented to the collections/hardship specialist. This is the R3 fail-closed
screen: a plan that asserts a decision, closes/files/reports, threatens the consumer,
ignores a suppression flag, or exceeds the call-frequency cap must NOT pass.

Checks:
  1. requires_human_adjudication is true AND the standing disclaimer is present.
  2. Every treatment marked eligible carries >= 1 cited evidence row.
  3. recommended_treatments equals exactly the set of eligible treatments (deterministic
     tie-out to the engine — no injected/ineligible option).
  4. No regulated-decision language — neither approval-side (approve/grant/settle/close/file/
     report) NOR denial-side (deny/decline/reject a forbearance/modification/hardship/
     arrangement/request). The skill recommends; a human adjudicates and acts either way.
  5. No FDCPA/UDAAP-prohibited threat language.
  6. Suppression honored: if outreach is suppressed, no outreach channel may be eligible.
  7. Call cap honored: 'phone' may be an eligible channel only if phone_outreach_eligible.

Usage:
  python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_KEY = "requires human adjudication and authorization"

# Regulated-decision / closure / filing / reporting / commitment assertions an R3
# decision-support skill must NEVER make (it recommends; a human adjudicates and acts).
DECISION_PATTERNS = [
    r"\bwe (have |hereby )?approv(e|ed)\b", r"\bapproved\b", r"\bis approved\b",
    r"\bforbearance (is |has been )?granted\b", r"\bmodification (is |has been )?(approved|granted)\b",
    r"\bwe (have )?(closed|close) (the )?(case|account)\b", r"\bcase (is )?closed\b",
    r"\bcharged?[- ]off\b", r"\bwrite[ -]?off the (balance|debt)\b",
    r"\bwe (have )?waiv(e|ed) the (balance|debt)\b",
    r"\bwe (have )?(set up|established|activated) (the )?(payment )?(plan|arrangement)\b",
    r"\barrangement is (now )?in place\b", r"\bhas been re-?aged\b", r"\bwe (have )?re-?aged\b",
    r"\bwe (have )?filed\b", r"\bfiled suit\b", r"\blawsuit (has been|is) filed\b",
    r"\breferred (the account )?to legal for filing\b",
    r"\bwe (have )?reported (this )?(to|the) (the )?(credit )?bureau", r"\breported to the bureau",
    r"\bwe (have )?settled\b", r"\bsettlement (is )?agreed\b",
]

# Denial-side adverse decisions are equally prohibited: an R3 decision-support skill never
# denies/declines/rejects a treatment, hardship accommodation, or consumer request — that
# adverse decision belongs to the human adjudicator. Matched in BOTH word orders (verb->subject
# "we have denied the forbearance" and subject->verb "the modification request is rejected") so
# the screen can't be side-stepped by rephrasing.
_DENY_VERB = r"(den(?:y|ies|ied|ying)|declin(?:e|es|ed|ing)|reject(?:s|ed|ing)?)"
_DECISION_SUBJECT = (
    r"(forbearance|modification|hardship|arrangement|repayment plan|payment plan|"
    r"promise[ -]?to[ -]?pay|settlement|re-?age|due[ -]?date change|counseling referral|"
    r"application|request|accommodation|treatment|option)"
)
DENIAL_PATTERNS = [
    rf"\b{_DENY_VERB}\b[^.]{{0,40}}\b{_DECISION_SUBJECT}\b",  # verb then subject
    rf"\b{_DECISION_SUBJECT}\b[^.]{{0,40}}\b{_DENY_VERB}\b",  # subject then verb
]

# FDCPA/UDAAP-prohibited conduct / threats (never in a recommendation pack).
THREAT_PATTERNS = [
    r"\bwe will sue you\b", r"\byou will be (arrested|jailed)\b", r"\bcriminal charges\b",
    r"\bgarnish (your )?wages\b", r"\bseize your\b", r"\bwe will take your (home|car|property)\b",
    r"\bface arrest\b", r"\bif you do not pay we will\b",
]


def _text_fields(pack: dict) -> str:
    parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    for t in pack.get("eligible_treatments") or []:
        parts.append(str(t.get("rationale", "")))
    op = pack.get("outreach_plan") or {}
    parts += [str(op.get("cadence_note", "")), str(op.get("tone", ""))]
    parts += [str(x) for x in (pack.get("care_prompts") or [])]
    return " ".join(parts)


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    # 1. mandatory human adjudication + disclaimer
    if pack.get("requires_human_adjudication") is not True:
        errors.append("requires_human_adjudication must be true (R3 mandatory human adjudication)")
    if DISCLAIMER_KEY not in str(pack.get("disclaimer", "")).lower():
        errors.append("missing standing human-adjudication disclaimer")

    treatments = pack.get("eligible_treatments") or []
    eligible = [t for t in treatments if t.get("eligible")]

    # 2. eligible treatment must be evidenced/cited
    for t in eligible:
        ev = t.get("evidence") or []
        if not any((row.get("citation") or "").strip() for row in ev):
            errors.append(f"eligible treatment {t.get('treatment')!r} has no cited evidence")

    # 3. deterministic tie-out: recommended == eligible set
    rec = set(pack.get("recommended_treatments") or [])
    exp = {t.get("treatment") for t in eligible}
    if rec != exp:
        errors.append(f"recommended_treatments {sorted(rec)} != eligible set {sorted(exp)} (deterministic tie-out failed)")

    # 4 & 5. prohibited decision / threat language
    text = _text_fields(pack)
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"regulated-decision/closure/filing language detected: {m.group(0)!r} (R3 recommends; it does not decide or act)")
    for pat in DENIAL_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"regulated adverse-decision (deny/decline/reject) language detected: {m.group(0)!r} (R3 recommends; a human adjudicates and issues any denial)")
    for pat in THREAT_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited threat/conduct language detected: {m.group(0)!r}")

    # 6. suppression honored
    sup = pack.get("suppression") or {}
    op = pack.get("outreach_plan") or {}
    channels = op.get("eligible_channels") or []
    if sup.get("outreach_suppressed") and channels:
        errors.append(f"outreach is suppressed but eligible_channels is non-empty: {channels}")

    # 7. call cap honored
    caps = pack.get("contact_caps") or {}
    if "phone" in channels and not caps.get("phone_outreach_eligible"):
        errors.append("'phone' is an eligible channel but phone_outreach_eligible is false (call-cap/suppression breach)")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "plan_example.json"
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
