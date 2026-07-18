#!/usr/bin/env python3
"""Deterministic fee-vs-disclosed-terms comparison for fee-and-charge-reviewer.

Reads a fee-review file (see validate_input.py), matches each posted fee to its disclosed
term, classifies the comparison, attaches evidence + citations (posted ref AND disclosed
term ref), maps the finding set to a deterministic review outcome, and drafts neutral
questions plus a remediation *request* for human review.

IMPORTANT: This produces a factual comparison and neutral questions ONLY. It never asserts a
legal or regulatory violation, never decides a refund/adjustment, never reverses or credits a
charge, and never provides legal advice. Those are human/authorized-system actions. The
outcome mapping is deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py fee_review.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path

DEFAULT_CONFIG = {"amount_tolerance": 0.0}
DISCLAIMER = ("Fee review and questions only; not a legal conclusion, refund decision, or "
              "legal advice, and not a reversal or credit of any charge.")

# Statuses that represent a discrepancy for human review.
DISCREPANCY_STATUSES = {"exceeds_disclosed", "frequency_cap_exceeded", "not_in_schedule"}
# Statuses that represent a question (softer than a discrepancy).
QUESTION_STATUSES = {"waiver_condition_may_apply"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _cite_fee(f: dict) -> str:
    return f"fees:{f.get('source_ref', '?')}@{f.get('date', '?')}"


def _cite_term(t: dict) -> str:
    return f"terms:{t.get('source_ref', '?')}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    tol = float(cfg["amount_tolerance"])
    terms = {t["fee_code"]: t for t in doc["disclosed_terms"]}
    ctx = doc.get("account_context") or {}
    waivers_met = {str(w).lower() for w in ctx.get("waivers_met", [])}
    fees = sorted(doc["posted_fees"], key=lambda f: (str(f.get("date")), str(f.get("fee_id"))))

    # Pre-compute frequency-cap overflow (per fee_code per day and per period).
    by_code_day = defaultdict(list)
    by_code_period = defaultdict(list)
    for f in fees:
        code = f.get("fee_code")
        if code and code in terms:
            by_code_day[(code, str(f["date"]))].append(f["fee_id"])
            by_code_period[code].append(f["fee_id"])
    over_cap = set()
    for code, term in terms.items():
        cpd = term.get("cap_per_day")
        cpp = term.get("cap_per_period")
        if cpd is not None:
            for (c, _day), fids in by_code_day.items():
                if c == code and len(fids) > cpd:
                    for fid in fids[int(cpd):]:
                        over_cap.add(fid)
        if cpp is not None:
            fids = by_code_period.get(code, [])
            if len(fids) > cpp:
                for fid in fids[int(cpp):]:
                    over_cap.add(fid)

    findings = []
    for f in fees:
        fid = f["fee_id"]
        code = f.get("fee_code")
        amount = _num(f.get("amount"))
        term = terms.get(code) if code else None
        posted_ev = {"type": "posted", "fee_id": fid, "amount": amount,
                     "citation": _cite_fee(f)}

        if term is None:
            status = "not_in_schedule"
            reason = "no matching disclosed term in the provided fee schedule"
            evidence = [posted_ev]
            disc = amount
        else:
            disclosed = _num(term.get("disclosed_amount"))
            term_ev = {"type": "disclosed", "fee_code": code,
                       "disclosed_amount": disclosed, "citation": _cite_term(term)}
            wc = {str(w).lower() for w in (term.get("waiver_conditions") or [])}
            met = sorted(wc & waivers_met)
            if fid in over_cap:
                cap = term.get("cap_per_day", term.get("cap_per_period"))
                status = "frequency_cap_exceeded"
                reason = f"count of '{code}' fees exceeds the disclosed cap ({cap})"
                evidence = [posted_ev, term_ev]
                disc = amount
            elif amount > disclosed + tol:
                status = "exceeds_disclosed"
                reason = f"posted amount {amount:.2f} exceeds disclosed {disclosed:.2f}"
                evidence = [posted_ev, term_ev]
                disc = round(amount - disclosed, 2)
            elif met:
                status = "waiver_condition_may_apply"
                reason = (f"account meets waiver condition(s) {met} the schedule lists for "
                          f"'{code}'; ask whether the waiver should have applied")
                evidence = [posted_ev, term_ev]
                disc = 0.0
            else:
                status = "matches_disclosed"
                reason = f"posted amount {amount:.2f} matches disclosed {disclosed:.2f}"
                evidence = [posted_ev, term_ev]
                disc = 0.0

        findings.append({
            "fee_id": fid, "fee_code": code, "category": (term or {}).get("category"),
            "label": f.get("label") or (term or {}).get("label"),
            "amount": amount, "currency": f.get("currency", "USD"),
            "disclosed_amount": (_num(term.get("disclosed_amount")) if term else None),
            "status": status, "discrepancy_amount": disc,
            "reason": reason, "evidence": evidence,
        })

    flagged = [x for x in findings if x["status"] in (DISCREPANCY_STATUSES | QUESTION_STATUSES)]
    discrepancies = [x for x in findings if x["status"] in DISCREPANCY_STATUSES]
    questions_findings = [x for x in findings if x["status"] in QUESTION_STATUSES]

    # Deterministic review-outcome mapping (see references/domain-rules.md).
    if discrepancies:
        outcome = "discrepancies_found"
    elif questions_findings:
        outcome = "questions_to_raise"
    else:
        outcome = "no_discrepancies"

    counts = defaultdict(int)
    for x in findings:
        counts[x["status"]] += 1

    questions = []
    for x in flagged:
        if x["status"] == "exceeds_disclosed":
            questions.append(
                f"{x['label']} ({x['fee_id']}) posted at {x['amount']:.2f} but the disclosed "
                f"schedule lists {x['disclosed_amount']:.2f}; ask servicing to confirm the "
                f"applicable fee-schedule version.")
        elif x["status"] == "frequency_cap_exceeded":
            questions.append(
                f"{x['label']} ({x['fee_id']}) appears beyond the disclosed frequency cap; "
                f"ask servicing to confirm whether this item should stand.")
        elif x["status"] == "not_in_schedule":
            questions.append(
                f"{x['label']} ({x['fee_id']}) of {x['amount']:.2f} has no matching entry in "
                f"the provided fee schedule; request the disclosed term or the charge basis.")
        elif x["status"] == "waiver_condition_may_apply":
            questions.append(
                f"{x['label']} ({x['fee_id']}): the account meets a waiver condition the "
                f"schedule lists; ask servicing whether the waiver should have applied.")

    remediation_request_draft = ""
    if flagged:
        remediation_request_draft = (
            f"Requesting a review of {len(flagged)} charge(s) on account {doc['account_id']} "
            f"for the {doc['statement_period']['start']} to {doc['statement_period']['end']} "
            f"statement period against the disclosed fee schedule. Please confirm the "
            f"applicable schedule version and whether any waiver conditions apply. This is a "
            f"request for review, not an assertion that any charge was improper. "
            f"(Draft for human review before any delivery.)")

    return {
        "review_id": f"fcr-{str(doc['account_id']).replace('*', '')}-{doc['as_of']}-0001",
        "account_id": doc["account_id"],
        "as_of": doc["as_of"],
        "statement_period": doc["statement_period"],
        "config_version": doc.get("config_version"),
        "findings": findings,
        "flagged_fee_ids": [x["fee_id"] for x in flagged],
        "summary": {
            "status_counts": dict(counts),
            "total_posted": round(sum(x["amount"] for x in findings), 2),
            "total_flagged_for_review": round(sum(x["discrepancy_amount"] for x in discrepancies), 2),
        },
        "review_outcome": outcome,
        "questions": questions,
        "remediation_request_draft": remediation_request_draft,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "fee_review_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
