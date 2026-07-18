# Adjacent-Skill Handoffs — relationship-manager-client-briefer

This skill is **prep-time drafting only**. It assembles a source-cited relationship brief for
a human RM to review and, if they choose, use or deliver. It does not send, submit, or file
the brief, write the CRM, make any credit / covenant / pricing / risk-rating decision, or give
advice — those are separate activities with distinct entitlements and systems of record.

## Upstream (feeds this skill)

| Upstream source | Provides | Handoff artifact |
| --------------- | -------- | ---------------- |
| Commercial CRM | Client identity, contacts, pipeline, relationship notes, open actions | `crm:party/contacts/opp/action` refs |
| Core banking / servicing | Facility exposures and product holdings | `core-banking:exposures/products` refs |
| Covenant tracking | Covenant definitions and latest test status | `covenants:test` refs |
| Profitability / RAROC | Revenue-to-bank and return metrics | `profitability:*` refs |
| Service / case management | Open service cases | `service:case` refs |
| News / media | Recent news and adverse-media flags | `news:item` refs |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| Drafting the underwriting / credit memo for a new facility, renewal, or increase | `credit-memo-drafter` |
| Testing covenants or working a covenant breach/cure beyond surfacing status | `covenant-compliance-monitor` |
| Designing a treasury / cash-management solution or proposal | `commercial-cash-management-advisor` |
| Onboarding a new entity or product (document collection/checks) | `customer-onboarding-document-checker` |
| Delinquency / collections treatment for a past-due client | `collections-treatment-planner` |
| A loan-servicing exception (billing, payment, boarding error) | `loan-servicing-exception-resolver` |
| Investigating adverse media / negative news on the client | `adverse-media-investigator` |
| Refreshing KYC / customer due diligence | `kyc-customer-due-diligence-screener` |
| Recalculating or reviewing the customer risk rating | `customer-risk-rating-reviewer` |
| Resolving a customer complaint | `complaint-resolution-assistant` |
| Tracking / closing the meeting's follow-up actions afterward | `meeting-action-tracker` |
| Sending / delivering the brief, or writing it to the CRM | an authorized human (out of scope; this skill never delivers or writes a system of record) |

Note: this skill is for **commercial-banking relationship coverage**. Investment-banking deal
coverage prep is a different activity (`coverage-meeting-preparer`).

## Downstream (human, not a skill)

The reviewed and approved brief is used or delivered by an **authorized human**, who also
performs any CRM write and any credit / covenant / pricing decision the brief may inform. This
skill emits a `client_id`-keyed draft brief plus a `reviewer_signoff_required` flag and a
recorded `approvals` block; it must not perform delivery, a CRM write, or any decision.

## Duplicate-execution prevention

- This skill **does not** underwrite credit, adjudicate covenants, design cash-management
  solutions, onboard, investigate adverse media, or write the CRM — those belong to the routes
  above or to a human.
- A brief carries the `client_id` and `as_of_date` so a reviewer works one authored draft
  rather than re-assembling.
- A `needs-data`, `unresolved-entity`, `unsupported-content`, or `stale-source` record is
  resolved by a human (supply data, confirm identity, substantiate, or refresh), never
  force-packaged.
