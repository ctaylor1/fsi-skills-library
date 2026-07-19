#!/usr/bin/env python3
"""Deterministic output validation for sanctions-match-adjudicator.

Fails CLOSED before an evidence bundle / disposition recommendation is presented. Enforces
the R3 "Investigate & casework" guardrails:
  1. Every case carries a DURABLE case_id of the form SANC-<alert_id>.
  2. Screening provenance is present (screening_engine + screening_run_id) — adjudication
     consumes a documented screening hit; it does not self-generate matches.
  3. disposition_recommendation is a RECOMMENDATION only (from the allowed set); the skill
     never emits a confirm/discount/block/release/file disposition.
  4. Every evidence item is cited: each chronology event, each match_factor, and each party
     carries a citation, and the bundle exposes a non-empty citation list and a chronology.
  5. disposition_basis is consistent with the evidence: score-band ties out to match_score;
     ownership/strong-id overrides require the corroborating factor; the conflict guard
     requires a discriminating factor.
  6. No autonomous match confirmation/discount, payment block/reject/release, account
     block/unblock, or blocking/OFAC-report filing language anywhere in the output (a bad
     fixture with such language MUST fail closed).
  7. The standing note is present.

Usage: python validate_output.py adjudication.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {
    "recommend-true-match-escalate",
    "recommend-potential-match-l2-review",
    "recommend-false-positive-discount",
    "needs-data",
    "possible-duplicate",
}
SCORE_BASED = {
    "recommend-true-match-escalate",
    "recommend-potential-match-l2-review",
    "recommend-false-positive-discount",
}
ALLOWED_BASES = {"score-band", "ownership-override", "strong-id-override",
                 "conflict-guard", "needs-data", "possible-duplicate"}
CASE_ID_RE = re.compile(r"^SANC-.+")
DEFAULT_BANDS = {"true_match_min": 6, "review_min": 2}
DISCRIMINATOR_NAMES = {"dob_mismatch", "strong_id_mismatch", "nationality_mismatch",
                       "entity_type_mismatch"}
STANDING_NOTE = (
    "Sanctions adjudication decision-support only; no match has been confirmed or discounted, "
    "no payment has been blocked, rejected, or released, no account has been blocked or "
    "unblocked, and no blocking/OFAC report has been filed. An authorized sanctions officer "
    "must adjudicate every disposition."
)

# Affirmative confirmation / discount / block / release / filing language — a skill that only
# RECOMMENDS must never assert that any of these actions was taken. Phrased to match the
# affirmative/past-tense action (not the standing note's negations or "recommend ..." text).
PROHIBITED_PATTERNS = [
    r"\bcase (is |was )?closed\b", r"\bclosed the case\b",
    r"\b(true |positive )?match (is |was )?confirmed\b", r"\bconfirmed (a |the )?(true |positive )?match\b",
    r"\bconfirmed as (a )?false positive\b", r"\bfalse positive confirmed\b",
    r"\bcleared the (customer|payment|account|hit|alert|name|subject)\b",
    r"\bdiscounted the (hit|match|alert|name)\b",
    r"\b(we )?blocked the (payment|account|funds|transaction)\b",
    r"\brejected the (payment|transaction)\b", r"\breleased the (payment|funds|transaction)\b",
    r"\bunblocked the (account|payment|funds)\b",
    r"\bfiled (a |the )?(blocking|ofac|sanctions) report\b",
    r"\bsubmitted (a |the )?(blocking|ofac) report\b",
    r"\breported to (the )?ofac that\b",
    r"\bsanctions determination (is|was|has been) (made|reached)\b",
    r"\bexonerat", r"\bno further action taken\b",
]


def _expected_band(score, bands):
    if score >= bands["true_match_min"]:
        return "recommend-true-match-escalate"
    if score >= bands["review_min"]:
        return "recommend-potential-match-l2-review"
    return "recommend-false-positive-discount"


def _factor_names(bundle):
    return {f.get("name") for f in (bundle.get("match_factors") or [])}


def validate(doc: dict, bands=None) -> list[str]:
    bands = bands or DEFAULT_BANDS
    errors: list[str] = []
    cases = doc.get("cases") or []
    if not cases:
        return ["adjudication output has no cases"]

    for c in cases:
        aid = c.get("alert_id", "?")
        cid = c.get("case_id")
        if not cid or not CASE_ID_RE.match(str(cid)):
            errors.append(f"{aid}: case_id {cid!r} is not a durable SANC-<id> identifier")
        elif cid != f"SANC-{aid}":
            errors.append(f"{aid}: case_id {cid!r} != expected durable id 'SANC-{aid}'")

        prov = c.get("screening_provenance") or {}
        if not prov.get("screening_engine") or not prov.get("screening_run_id"):
            errors.append(f"{aid}: missing screening provenance (screening_engine + screening_run_id)")

        disp = c.get("disposition_recommendation")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{aid}: disallowed disposition {disp!r} "
                          "(recommendations only; adjudication never confirms/discounts/blocks/releases/files)")

        basis = c.get("disposition_basis")
        if basis not in ALLOWED_BASES:
            errors.append(f"{aid}: disposition_basis {basis!r} not in {sorted(ALLOWED_BASES)}")

        b = c.get("evidence_bundle") or {}
        if not b:
            errors.append(f"{aid}: missing evidence_bundle")
        else:
            if not b.get("citations"):
                errors.append(f"{aid}: evidence_bundle has no citations")
            chrono = b.get("chronology") or []
            if not chrono:
                errors.append(f"{aid}: evidence_bundle has no chronology")
            for i, ev in enumerate(chrono):
                if not ev.get("citation"):
                    errors.append(f"{aid}: chronology event {i} ({ev.get('type')}) missing citation")
            facs = b.get("match_factors") or []
            if not facs:
                errors.append(f"{aid}: evidence_bundle has no match_factors")
            for f in facs:
                if not f.get("citations"):
                    errors.append(f"{aid}: match_factor {f.get('name')!r} missing citation")
            for j, party in enumerate(b.get("parties") or []):
                if not party.get("citations"):
                    errors.append(f"{aid}: party {j} ({party.get('role')}) missing citation")

        names = _factor_names(b)
        if basis == "score-band" and disp in SCORE_BASED:
            exp = _expected_band(c.get("match_score", 0), bands)
            if disp != exp:
                errors.append(f"{aid}: score-band disposition {disp!r} != expected {exp!r} "
                              f"for match_score {c.get('match_score')}")
        elif basis == "ownership-override":
            if disp != "recommend-true-match-escalate":
                errors.append(f"{aid}: ownership-override must recommend-true-match-escalate, got {disp!r}")
            if "ownership_nexus" not in names:
                errors.append(f"{aid}: ownership-override without an 'ownership_nexus' match_factor")
        elif basis == "strong-id-override":
            if disp != "recommend-true-match-escalate":
                errors.append(f"{aid}: strong-id-override must recommend-true-match-escalate, got {disp!r}")
            if "strong_id_match" not in names or not ({"name_primary_match", "alias_match"} & names):
                errors.append(f"{aid}: strong-id-override requires a 'strong_id_match' plus a name/alias factor")
        elif basis == "conflict-guard":
            if disp != "recommend-potential-match-l2-review":
                errors.append(f"{aid}: conflict-guard must recommend-potential-match-l2-review, got {disp!r}")
            if not (DISCRIMINATOR_NAMES & names):
                errors.append(f"{aid}: conflict-guard without any discriminating match_factor")

    scan = json.dumps(cases) + " " + str(doc.get("narrative", ""))
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited confirmation/discount/block/release/filing language detected: "
                          f"{m.group(0)!r} (adjudication recommends only; a sanctions officer decides)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing or altered standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "adjudication_example.json"
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
