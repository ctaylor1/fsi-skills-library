#!/usr/bin/env python3
"""Deterministic output validation for client-review-preparer.

Enforces the R3 "Draft & package" guardrails before a client-review pack is handed to a
licensed human for adjudication and (their own, separate) use:
  1. Template fidelity: a packageable pack has the required sections and no unfilled
     `{{placeholder}}` tokens.
  2. No unsupported claims: a packageable record is entity-resolved and fully source-cited;
     every listed content item (and every holding) carries a citation; citations non-empty.
  3. Client & account identity: only draft-review is packageable, and it carries resolved
     accounts with type/registration and a citation each.
  4. Performance & holdings tie-out: per-account holdings sum to the reported value, accounts
     sum to the household total, and any household_reported_value matches.
  5. Disclosure coverage: the required disclosures for the review type are all present
     (disclosure_check.missing is empty).
  6. Required approvals recorded: reviewer_signoff_required=true and a non-empty approvals
     block are present (human adjudication is mandatory before use).
  7. No unauthorized recommendation / suitability decision / trade, and no decision, closure,
     or filing / system-of-record write language (R3: recommendations & evidence only).
  8. No send / submit / deliver language (this skill never delivers).
  9. No personalized investment, legal, or tax advice.
 10. The standing note is present.

Fails closed on any miss so a defective or overreaching pack cannot be presented as
ready-to-use.

Usage: python validate_output.py review.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

STANDING_NOTE = (
    "Client-review preparation draft for internal advisor use only; this skill does not make "
    "or communicate any investment recommendation, suitability decision, trade, closure, or "
    "filing, does not send, submit, or deliver the pack, and does not write any CRM or system "
    "of record; it gives no investment, legal, or tax advice; every item must be verified "
    "against its cited source and adjudicated by a licensed human before use."
)
# Sections that must exist and be non-empty for a packageable pack.
REQUIRED_NONEMPTY = ("client_id", "household_name", "advisor", "review_type", "as_of_date",
                     "accounts", "portfolio_summary", "goals", "discussion_agenda",
                     "disclosures", "citations", "approvals")
# Sections whose key must be present (may be an empty list for a given client).
REQUIRED_PRESENT = ("performance", "plan_items", "prior_notes", "service_history",
                    "life_events", "open_actions", "routing", "disclosure_check")
# Content lists whose every entry must carry a non-empty citation (no unsupported claims).
CITED_LISTS = ("performance", "goals", "plan_items", "prior_notes", "service_history",
               "life_events", "open_actions", "discussion_agenda", "disclosures")
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")

# R3: no unauthorized recommendation / suitability decision / trade instruction.
RECOMMENDATION_PATTERNS = [
    r"\bwe recommend (that )?(you |the client )?(buy|sell|purchase|liquidate|allocate|invest|switch|reallocate|move)\b",
    r"\byou should (buy|sell|purchase|liquidate|invest|switch|reallocate|move|rebalance)\b",
    r"\b(recommended|suggested) (trade|allocation|purchase|sale|reallocation) (is|:)\b",
    r"\bplace (the|a|this) (trade|order)\b",
    r"\bexecute the (trade|order|reallocation|rebalance)\b",
    r"\bthis (recommendation|trade) is (suitable|approved)\b",
    r"\bguarantee(s|d)? (a )?(return|performance|outcome|gain|profit)\b",
]
# R3: no decision, closure, or filing / system-of-record write.
DECISION_PATTERNS = [
    r"\bmark(ed|ing)? the review (complete|closed|final)\b",
    r"\bclose (the|this) (case|review)\b",
    r"\bcase closed\b",
    r"\bfil(e|ed|ing) (it|the review|the pack|the form) (in|to|with) the (system of record|crm|book of record)\b",
    r"\bwrit(e|ing|ten) (it )?(to|into) the (crm|system of record|book of record)\b",
    r"\bpost(ed|ing)? (it )?(to|into) the (system of record|crm|book of record)\b",
    r"\bupdat(e|ed|ing) the crm\b",
]
# Draft-only: never send / submit / deliver.
DELIVERY_PATTERNS = [
    r"\bpack (has been |was )?(sent|emailed|delivered|distributed|submitted)\b",
    r"\bi (have |'ve )?(sent|emailed|delivered|distributed|submitted) (it|the pack|the review|the deck)\b",
    r"\b(send|deliver|submit) (the|this) (pack|review|deck|brief) to the (client|customer|household)\b",
]
ADVICE_PATTERNS = [
    r"\b(personalized|personalised) (investment|financial|tax|legal) advice\b",
    r"\byou should (invest|refinance|hedge|restructure|contribute|withdraw)\b",
    r"\bas your (financial advisor|advisor|attorney|lawyer|cpa|accountant)\b",
]


def _round2(x):
    try:
        return round(float(x or 0), 2)
    except Exception:
        return None


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    reviews = doc.get("reviews") or []
    if not reviews:
        return ["review output has no records"]

    for b in reviews:
        cid = b.get("client_id", "?")
        if not b.get("packageable"):
            continue

        if b.get("status") != "draft-review":
            errors.append(f"{cid}: packageable but status is {b.get('status')!r} (only 'draft-review' is packageable)")
        if not b.get("citations"):
            errors.append(f"{cid}: packageable but citations list is empty")

        pack = b.get("review_pack") or {}
        if not pack:
            errors.append(f"{cid}: packageable but no review_pack object")
            continue

        for sec in REQUIRED_NONEMPTY:
            if sec not in pack or pack.get(sec) in (None, "", [], {}):
                errors.append(f"{cid}: pack missing required section {sec!r} (template fidelity)")
        for sec in REQUIRED_PRESENT:
            if sec not in pack:
                errors.append(f"{cid}: pack missing required section {sec!r} (template fidelity)")
        if not pack.get("reviewer_signoff_required"):
            errors.append(f"{cid}: pack missing reviewer_signoff_required=true (required approvals not recorded)")
        appr = pack.get("approvals") or {}
        if not appr.get("required"):
            errors.append(f"{cid}: pack missing recorded approvals (approvals.required) before use")
        if PLACEHOLDER_RE.search(json.dumps(pack)):
            errors.append(f"{cid}: pack contains unfilled '{{{{placeholder}}}}' tokens (template fidelity)")

        # no unsupported claims: every listed content item must carry a citation
        for lst in CITED_LISTS:
            for k, item in enumerate(pack.get(lst) or []):
                if not (isinstance(item, dict) and item.get("citation")):
                    errors.append(f"{cid}: {lst}[{k}] has no citation (unsupported claim)")

        # client & account identity
        for k, a in enumerate(pack.get("accounts") or []):
            if not (a.get("account_id") and a.get("type") and a.get("registration")):
                errors.append(f"{cid}: accounts[{k}] missing identity (account_id/type/registration)")

        # performance & holdings tie-out
        ps = pack.get("portfolio_summary") or {}
        acct_lines = ps.get("accounts") or []
        roll = 0.0
        for k, a in enumerate(acct_lines):
            hv = _round2(sum(_round2(h.get("market_value")) or 0 for h in a.get("holdings") or []))
            rv = _round2(a.get("reported_value"))
            roll += rv or 0
            if hv != rv:
                errors.append(f"{cid}: holdings tie-out mismatch on account {a.get('account_id')} ({hv} != {rv})")
            if not a.get("citation"):
                errors.append(f"{cid}: portfolio_summary.accounts[{k}] has no citation (unsupported claim)")
            for j, h in enumerate(a.get("holdings") or []):
                if not h.get("citation"):
                    errors.append(f"{cid}: portfolio_summary.accounts[{k}].holdings[{j}] has no citation (unsupported claim)")
        roll = _round2(roll)
        if _round2(ps.get("total_value")) != roll:
            errors.append(f"{cid}: household tie-out mismatch (total_value {ps.get('total_value')} != sum of accounts {roll})")
        hrv = ps.get("household_reported_value")
        if hrv is not None and _round2(hrv) != roll:
            errors.append(f"{cid}: household_reported_value {hrv} != sum of accounts {roll} (tie-out)")

        # disclosure coverage
        dc = pack.get("disclosure_check") or {}
        if dc.get("missing"):
            errors.append(f"{cid}: required disclosures missing {dc.get('missing')} (disclosure coverage)")

    scan = json.dumps(reviews) + " " + str(doc.get("narrative", ""))
    for pat in RECOMMENDATION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited recommendation/advice language detected: {m.group(0)!r} "
                          "(this skill surfaces discussion points, it never recommends, approves, or trades)")
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing language detected: {m.group(0)!r} "
                          "(R3: no autonomous decision, closure, filing, or system-of-record write)")
    for pat in DELIVERY_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited delivery/submission language detected: {m.group(0)!r} "
                          "(this skill never sends, submits, or delivers the pack)")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited advice language detected: {m.group(0)!r}")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_example.json"
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
