# Approved Template — Claims Triage Summary (DRAFT)

This is the controlled template the skill assembles into `draft_summary.body`. Every draft
MUST include the `DRAFT` marker, all six required section headings (verbatim), the
recommended (not decided) bands, and the standing note. `scripts/validate_output.py` enforces
the section list, the DRAFT marker, the recorded approvals, band tie-out, and the
no-regulated-conclusion / no-executed-action screens.

The summary is **draft-only**: it is prepared for internal review and is never sent, and it
never determines coverage, sets a reserve, approves/denies/pays/closes/assigns a claim, or
concludes fraud or liability.

---

DRAFT - CLAIMS TRIAGE SUMMARY, FOR INTERNAL REVIEW - NOT A COVERAGE OR LIABILITY DECISION

Claim: {claim_id} | Policy: {policy_id_masked} | Product: {product}

## Claim summary
{Claim type in plain language, reported date, loss date, estimated exposure, and party count —
taken from the claim record. Triage support only; no assertions beyond the record.}

## Severity and complexity
{Recommended severity band (S1 Complex / S2 Moderate / S3 Standard) with the score and the
explainable drivers. This is a handling-complexity recommendation, not an exposure or reserve
figure.}

## Urgency and service level
{Recommended urgency band (U1 Immediate / U2 Prompt / U3 Routine), the suggested first-touch
service level, and the drivers (injury, fatality, catastrophe, statutory deadline, business
interruption, vulnerability).}

## Coverage questions to resolve
{The open coverage QUESTIONS the triage screens surfaced (policy-period mismatch, lapsed
status, possible exclusion) for a human to resolve — OR a clear statement that none were
surfaced. The skill never answers a coverage question or determines coverage.}

## Recommended routing
{The recommended specialist referrals and/or the standard queue, each with a reason. Skill
referrals name a catalog skill; human referrals name the responsible team. Routing is a
recommendation a human confirms.}

## Human adjudication required
Coverage determination, liability assessment, reserve setting, queue and adjuster assignment,
and any payment remain with the claims supervisor and adjuster of record. This triage
recommends only and decides nothing.

Draft claims triage only: severity, urgency, coverage questions, and routing are
recommendations for human review. No coverage decision, reserve, payment, assignment, or
claim closure has been made.

---

## Required approvals (recorded, must be present)

| Approval | Role | Recorded when |
| -------- | ---- | ------------- |
| `triage_lead_review` | Claims triage lead | Triage lead has reviewed the recommended bands, coverage questions, and routing |
| `claims_supervisor_approval` | Claims supervisor / adjuster of record | Sign-off required before any queue/adjuster assignment, reserve, coverage decision, payment, or system-of-record change |

Both approvals start `pending`. Coverage determination, reserve setting, adjuster assignment,
payment, closure, and any regulatory filing happen **outside** this skill (the adjuster of
record and claims supervisor, or the named specialist skill under human approval).
