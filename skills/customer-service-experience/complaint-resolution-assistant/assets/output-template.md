# Approved Template — Complaint Final-Response Letter (DRAFT)

This is the controlled template the skill assembles into `draft_response.body`. Every draft
MUST include the `DRAFT` marker, all six required section headings (verbatim), the proposed
(not final) outcome, and the standing note. `scripts/validate_output.py` enforces the section
list, the DRAFT marker, the recorded approvals, and the no-unsupported-claim / no-send screens.

The letter is **draft-only**: it is prepared for internal review and is never sent, and it
never admits legal liability, guarantees a result, gives legal advice, or states that a
payment has been made.

---

DRAFT - FOR INTERNAL REVIEW, NOT SENT

Dear {customer_name_masked},

## Summary of your complaint
{What the customer complained about, the product, and the date received — one or two plain
sentences, taken from the complaint record.}

## What we looked into
{The records reviewed and the standards the complaint was assessed against (cited). Do not
overstate scope.}

## What we found
{The root cause on the evidence reviewed, stated factually against the standards. No
admission of legal liability; no guarantees.}

## Putting things right
{The proposed remediation breakdown — refund, interest, distress-and-inconvenience band, and
capped goodwill — with a proposed total, OR a clear statement that no financial redress is
proposed. Figures come only from the deterministic engine and must tie out.}

## Our decision
Proposed outcome (DRAFT, pending internal approval): your complaint is {upheld /
partially upheld / not upheld}. This wording is a recommendation for the complaints handler
and approver and is not a final decision.

## How to escalate
{The customer's right to escalate to the relevant external dispute-resolution scheme or
ombudsman, and the applicable time limit — from the configured jurisdiction pack. Confirm
before finalising.}

How to contact us: {handler contact / case reference}.

Draft complaint response only: proposed classification, remediation, and outcome are
recommendations for human review. Nothing has been sent to the customer or reported to a
regulator.

---

## Required approvals (recorded, must be present)

| Approval | Role | Recorded when |
| -------- | ---- | ------------- |
| `complaints_handler_review` | Complaints handler | Handler has reviewed the draft and the proposed outcome |
| `final_response_approver` | Complaints manager / conduct-risk approver | Sign-off required before any external delivery or system-of-record change |

Both approvals start `pending`. External delivery, redress payment, account change, and any
regulatory return happen **outside** this skill (human owner, or
`omnichannel-case-orchestrator` under approval).
