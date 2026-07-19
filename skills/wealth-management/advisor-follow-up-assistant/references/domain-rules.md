# Domain Rules — advisor-follow-up-assistant

Orientation references: SEC/FINRA books-and-records, FINRA Rule 2210 (communications with the
public — principal approval and content standards), FINRA Rule 3110 (supervision), Reg BI Care
Obligation context, and the 2026 FINRA Annual Regulatory Oversight Report. The **firm's own**
approved follow-up template, disclosures library, and communications-supervision policy take
precedence and are **versioned contracts**. Nothing here is investment advice; it defines how a
draft follow-up package is assembled and screened, not what a client should do.

## Required follow-up sections (template fidelity)

Every draft must contain all of these sections. `scripts/calculate_or_transform.py` lays inputs
into them and `scripts/validate_output.py` fails closed if any is missing or mistitled.

| # | Section key | Title |
| - | ----------- | ----- |
| 1 | `meeting-summary` | Meeting Summary |
| 2 | `action-items` | Action Items |
| 3 | `client-communication` | Client Communication (Draft) |
| 4 | `disclosures` | Disclosures |
| 5 | `crm-update` | CRM Update (Proposed) |
| 6 | `next-meeting` | Next-Meeting Reminder |
| 7 | `approvals-and-delivery` | Approvals and Delivery |

## Disclosure completeness (deterministic)

Each recommendation discussed carries two flags. The draft is `needs-data` (and the output screen
fails) unless both are satisfied:

| Flag | Requirement |
| ---- | ----------- |
| `requires_disclosure` | A disclosure entry whose `covers_recommendation` equals the recommendation `id` must be present (drawn from the versioned disclosures library). |
| `requires_suitability_review` | A route to `suitability-reg-bi-reviewer` referencing the recommendation `id` must be recorded. The draft **never** states the recommendation is suitable or approved. |

A missing disclosure or a missing route is a **hard error** — the drafter never invents a disclosure
or resolves suitability itself.

## Action-item completeness (deterministic)

| Rule | Requirement |
| ---- | ----------- |
| Owner | Every action item names an `owner` (advisor, client, or operations). |
| Due date | Every action item carries a `due_date`. |
| Citation | Every action item carries a `citation` to the meeting record or source. |
| Client items | Items assigned to the client are framed as requests to consider, never commitments made on the client's behalf. |

A missing owner, due date, or citation makes the item `needs-data`.

## Material assertions require a source (no unsupported claims)

Each of these is a *material assertion* and must carry a citation, or the draft is `needs-data` and
the output screen fails:

- the meeting summary (meeting record + each discussion point)
- each action item
- the client communication key points
- each disclosure (or, when no recommendation requires one, the meeting record basis for "none required")
- each proposed CRM field change
- the next-meeting reminder

## Hard boundaries (fail closed)

- **No sending / delivering.** The client communication is a draft; never "sent," "emailed," or
  "delivered to the client." Sending is a human/operations step after approval.
- **No CRM / system-of-record write.** CRM changes are *proposed*; never "updated," "written," or
  "posted." `crm_write_status` stays `not-written`.
- **No trading or staging.** No order, trade list, or execution language — that is
  `portfolio-rebalancing-assistant` (R4, approval-gated).
- **No suitability / Reg BI determination.** The draft never states a recommendation is "suitable,"
  "approved," or "in the client's best interest as determined" — that is `suitability-reg-bi-reviewer`
  plus a human supervisor.
- **No guarantees or performance promises.** No "guaranteed return," "risk-free," "will outperform,"
  or "no downside."
- **No personalized advice beyond documented inputs.** The draft reflects the documented meeting; it
  does not invent discussion points, action items, or figures the sources do not support.

## Prohibited-language screen (regex families in `validate_output.py`)

The output validator rejects, case-insensitive:

1. **Execution-as-done:** `execute the trade`, `trade(s)? executed`, `order placed`, `place the
   order`, `funds transferred`, `have rebalanced`, `rebalance executed`, `trade has been placed`.
2. **Sent/delivered-as-done:** `email sent`, `sent to the client`, `have notified the client`,
   `delivered to the client`, `message has been sent`, `submitted to compliance`.
3. **CRM-write-as-done:** `updated the crm`, `crm updated`, `record(s)? updated`, `written to the
   system of record`, `saved to salesforce`/`saved to the crm`, `posted to the account`.
4. **Guarantee/performance:** `guaranteed return`, `guarantee[ds]? to`, `risk-free`, `will
   outperform`, `no downside`.
5. **Suitability/advice-as-done:** `suitability approved`, `deemed suitable`, `best-interest
   determination made`, `we hereby approve`, `approved as suitable`, `this is suitable for you`.

Any match is a hard error. These screens are deliberate belt-and-suspenders on top of the structural
draft-status, delivery-status, CRM-write-status, and approval checks.
