# Controls — fund-commentary-drafter

- **Risk tier:** R2 — analytical/drafting support. **Action mode:** Draft-only; no
  system-of-record change. The skill assembles a controlled draft; it never sends, files,
  publishes, or distributes.
- **Human approval:** `external-delivery` — **product** and **compliance** sign-off are
  required before the commentary is delivered externally or committed to a system of record.
  Internal analytical iteration may be reviewer-sampled.

## Prohibited (fail closed)

- **Unsupported claims** — any factual/performance statement not tied to a cited source.
  Claims that cannot be substantiated are flagged and removed, never asserted.
- **Unapproved forward/thematic language** — outlook and thematic statements must come only
  from the approved messaging library; non-`approved` messaging cannot be used.
- **Prohibited/misleading marketing language** — return guarantees, "risk-free", "will
  outperform", "assured returns", "cannot lose", "safe investment", and similar.
- **Numbers that do not tie out** — performance excess must equal fund − benchmark;
  attribution effects must sum to the total excess and equal the performance excess.
- **Missing required disclosures** for the fund/jurisdiction.
- **Sending, filing, publishing, or distributing** — outside this skill entirely.

## Delivery states (this skill may set only these)

`draft` → `approved-for-delivery` (after both sign-offs recorded). It may **not** set
`sent`, `submitted`, `distributed`, `published`, `filed`, `emailed`, or `released`.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present and non-empty
  (`performance_summary`, `attribution`, `positioning`, `flows`, `market_context`,
  `outlook`, `disclosures`).
- Performance and attribution tie-outs both `ok`.
- Every claim `supported` with ≥1 citation; `unsupported_claims` empty; claim
  `period_label` matches the commentary period.
- No prohibited/misleading marketing language in the claim narrative.
- `required_disclosures ⊆ disclosures_present`.
- Product **and** compliance approvals recorded with approver + date.
- `delivery_status` not in the sent/distributed set; draft-only standing note present.

## Segregation of duties

The drafter (this skill / its operator) does not self-approve. Product approves messaging
and positioning consistency; compliance approves disclosures and the prohibited-claim
screen. Both are distinct from the drafting step.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Commentary may reference holdings
  and flows that are material and non-public until published; treat the draft as MNPI.
- Retain the draft, claim ledger with citations, tie-out evidence, template/messaging/
  disclosure versions, and both sign-offs for the marketing-records retention period; log
  the drafter and approver identities.
