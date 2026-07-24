#!/usr/bin/env python3
"""Deterministic vote-vs-policy-and-precedent comparison for
voting-policy-consistency-checker.

Reads a ballot file (see validate_input.py), and for each agenda item:
  1. Selects the applicable policy guideline for the item's category — the guideline whose
     effective_date is on or before the meeting_date, latest such (version/effective-date
     rule in references/domain-rules.md). Not-yet-effective guidelines are ignored.
  2. Derives the policy-implied position and compares it to the HUMAN analyst's
     proposed_vote, classifying the item: aligned | deviation | case_by_case | no_policy.
  3. Compares the proposed_vote against analogous prior firm votes (same category, earlier
     meetings) and reports concordant/discordant precedent counts with citations.
  4. Emits a cited finding per item and a deterministic overall_disposition.

IMPORTANT: This produces consistency *findings and cited evidence* only. It NEVER decides,
changes, casts, or submits a vote, and never treats the proposed_vote as authoritative.
Every deviation / case_by_case / no_policy finding carries a mandatory human-adjudication
action. The disposition mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py ballot.json   # prints the review JSON to stdout
  python calculate_or_transform.py --selftest     # checks bundled fixture, prints N error(s)
"""
from __future__ import annotations
import json, sys
from pathlib import Path

VOTE_VALUES = {"For", "Against", "Abstain", "Withhold"}
DISCLAIMER = (
    "Consistency findings and cited evidence only; not a voting decision or instruction. "
    "This review does not cast, change, or submit any vote; a human analyst adjudicates and "
    "records the vote in the system of record.")


def _select_guideline(category: str, meeting_date: str, guides: list[dict]) -> dict | None:
    """Latest guideline for the category effective on/before the meeting date."""
    eligible = [g for g in guides
                if g.get("category") == category
                and str(g.get("effective_date", "")) <= str(meeting_date)]
    if not eligible:
        return None
    return max(eligible, key=lambda g: str(g.get("effective_date", "")))


def _policy_citation(g: dict) -> str:
    return f"policy:{g.get('policy_ref', '?')}@{g.get('version', '?')};eff={g.get('effective_date', '?')}"


def _prec_citation(p: dict) -> str:
    return f"precedent:{p.get('case_id', '?')}@{p.get('meeting_date', '?')}"


def compute(doc: dict) -> dict:
    meeting_date = str(doc["meeting_date"])
    guides = doc.get("policy_guidelines") or []
    precs = doc.get("precedents") or []
    findings: list[dict] = []

    for idx, item in enumerate(doc["agenda_items"], start=1):
        category = item.get("category")
        proposed = item.get("proposed_vote")
        finding_id = f"{doc['meeting_id']}-F{idx:03d}"
        g = _select_guideline(category, meeting_date, guides)

        # Analogous prior firm votes: same category, strictly earlier meetings.
        analogous = [p for p in precs
                     if p.get("category") == category
                     and str(p.get("meeting_date", "")) < meeting_date]
        concordant = [p for p in analogous if p.get("vote_cast") == proposed]
        discordant = [p for p in analogous if p.get("vote_cast") != proposed]
        precedent_evaluable = bool(analogous)
        precedent_discordant = precedent_evaluable and len(discordant) > len(concordant)
        precedent = {
            "evaluable": precedent_evaluable,
            "concordant": len(concordant),
            "discordant": len(discordant),
            "citations": [_prec_citation(p) for p in analogous],
        }

        if g is None:
            status = "no_policy"
            policy_position = None
            policy_citation = None
            reason = (f"no policy guideline effective as of {meeting_date} for category "
                      f"'{category}'; consistency cannot be assessed (coverage gap)")
            required_action = (
                "Route to policy owner to confirm the applicable guideline, then re-run; "
                "a human analyst must document rationale before any vote is recorded.")
        else:
            policy_position = g.get("default_position")
            policy_citation = _policy_citation(g)
            if policy_position == "Case-by-case":
                status = "case_by_case"
                reason = (f"policy is case-by-case for '{category}' ({policy_citation}); "
                          f"proposed vote '{proposed}' needs documented rationale, not a "
                          f"mechanical match")
                required_action = (
                    "Attach documented case-by-case rationale; a human analyst adjudicates "
                    "before the vote is recorded.")
            elif proposed == policy_position:
                status = "aligned"
                reason = (f"proposed vote '{proposed}' matches policy position "
                          f"'{policy_position}' ({policy_citation})")
                required_action = None
            else:
                status = "deviation"
                reason = (f"proposed vote '{proposed}' conflicts with policy position "
                          f"'{policy_position}' ({policy_citation})")
                required_action = (
                    "Document the deviation rationale and obtain voting-committee "
                    "adjudication before any vote is recorded; the deviation is not "
                    "resolved by this review.")

        findings.append({
            "finding_id": finding_id,
            "item_id": item.get("item_id"),
            "category": category,
            "title": item.get("title"),
            "proposed_vote": proposed,
            "policy_position": policy_position,
            "policy_citation": policy_citation,
            "status": status,
            "precedent": precedent,
            "precedent_discordant": precedent_discordant,
            "required_action": required_action,
            "reason": reason,
        })

    counts = {s: sum(1 for f in findings if f["status"] == s)
              for s in ("aligned", "deviation", "case_by_case", "no_policy")}
    disposition = expected_disposition(findings)

    return {
        "review_id": f"vpcc-{doc['meeting_id']}-{meeting_date}-0001",
        "packet_id": doc.get("packet_id"),
        "meeting_id": doc["meeting_id"],
        "issuer": doc.get("issuer"),
        "meeting_date": meeting_date,
        "policy_version": doc.get("policy_version"),
        "as_of": doc.get("as_of"),
        "findings": findings,
        "counts": counts,
        "overall_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def expected_disposition(findings: list[dict]) -> str:
    """Deterministic roll-up (see references/domain-rules.md).

    deviations_present  -> any hard policy deviation.
    review_recommended  -> no deviation, but a case-by-case, a no_policy gap, or a
                           precedent discordance needs documented human review.
    consistent          -> every item aligned with policy and precedent.
    """
    statuses = {f["status"] for f in findings}
    if "deviation" in statuses:
        return "deviations_present"
    if ({"case_by_case", "no_policy"} & statuses
            or any(f.get("precedent_discordant") for f in findings)):
        return "review_recommended"
    return "consistent"


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ballot_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = compute(doc)
    by_item = {f["item_id"]: f for f in out["findings"]}
    errors: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            errors.append(msg)

    check(out["overall_disposition"] == "deviations_present",
          f"disposition {out['overall_disposition']!r} != 'deviations_present'")
    check(by_item["ITEM-1"]["status"] == "aligned", "ITEM-1 should be aligned")
    check(by_item["ITEM-2"]["status"] == "case_by_case", "ITEM-2 should be case_by_case")
    check(by_item["ITEM-3"]["status"] == "deviation", "ITEM-3 should be deviation")
    check(by_item["ITEM-4"]["status"] == "deviation", "ITEM-4 should be deviation")
    check(by_item["ITEM-5"]["status"] == "no_policy", "ITEM-5 should be no_policy")
    check(out["counts"]["deviation"] == 2, f"expected 2 deviations, got {out['counts']['deviation']}")
    # Effective-date selection: ITEM-4 must resolve to the 2025 (For) guideline, not 2023.
    check(by_item["ITEM-4"]["policy_position"] == "For",
          "ITEM-4 must select the effective 2025 climate guideline (position 'For')")
    check("PXY-POL-2025" in (by_item["ITEM-4"]["policy_citation"] or ""),
          "ITEM-4 policy citation should reference the effective PXY-POL-2025 guideline")
    # ITEM-3 must ignore the not-yet-effective 2027 'Against' guideline.
    check(by_item["ITEM-3"]["policy_position"] == "For",
          "ITEM-3 must ignore the not-yet-effective 2027 guideline (position stays 'For')")
    # Every deviation / case_by_case / no_policy carries a human-adjudication action.
    for f in out["findings"]:
        if f["status"] in ("deviation", "case_by_case", "no_policy"):
            check(bool(f["required_action"]), f"{f['item_id']} missing required_action")
        if f["status"] in ("deviation", "aligned", "case_by_case"):
            check(bool(f["policy_citation"]), f"{f['item_id']} missing policy_citation")
    # Precedent discordance surfaced for the auditor item (firm historically voted For).
    check(by_item["ITEM-3"]["precedent_discordant"] is True,
          "ITEM-3 should be precedent_discordant (prior votes were 'For')")

    for e in errors:
        print("ERROR", e)
    print(f"compute selftest: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
