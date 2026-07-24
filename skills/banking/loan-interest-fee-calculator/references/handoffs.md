# Adjacent-Skill Handoffs — loan-interest-fee-calculator

This skill produces a source-linked **recalculation workbook** (`calc_id`) — interest, fees,
amortization, settlement, participation allocations, a variance report, and a reconciliation
to the approved engine — and stops. It **never posts, approves, or executes** an adjustment,
and it never delivers the workbook or a payoff quote anywhere on its own.

## Upstream (feed this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `credit-application-packager` | Organized, source-linked borrower/collateral/approval package with the executed agreement | Executed terms + source map |
| `loan-package-completeness-checker` | Certification that closing conditions are satisfied, so the terms are reliable to recalculate from | Completeness result + open conditions |

## Parallel / cross-check

| Skill | Why |
| ----- | --- |
| `covenant-compliance-monitor` | Consumes recomputed interest and fees as inputs to covenant tests and headroom tracking |
| `fee-and-charge-reviewer` | Consumer-facing explanation/comparison of account fees against disclosed terms (different user and scope from a servicing recalculation) |

## Downstream / routing (consume this skill's `calc_id`)

| Trigger | Route to | Handoff artifact |
| ------- | -------- | ---------------- |
| **Closing conditions incomplete** — collateral, legal, signature, or expiration items still open before the terms can be relied on | `loan-package-completeness-checker` | `case_id` + list of unreliable/missing terms |
| **Substantive servicing exception** — a material variance (e.g. a booked fee or interest materially off) needing root-cause investigation and a staged correction | `loan-servicing-exception-resolver` | `calc_id` + variance report (material lines) |

## Human / authorized-workflow handoff (no skill substitutes for it)

**Posting, approving, waiving, or reversing** any interest, fee, or adjustment — and
**delivering** a payoff quote or workbook to a borrower, participant, or counterparty — is
**out of scope** and belongs to an **authorized servicing officer and the approval /
execution workflow** (`loan-servicing-exception-resolver` stages the change for authorized
execution). This skill routes those actions to those humans and workflows; it never performs
them. Personalized financial, legal, or tax advice is likewise out of scope.

## Duplicate-execution prevention

- This skill recalculates and reports the **workbook only**; it must not investigate the
  root cause of an exception, stage or approve a correction, deliver the workbook, or post
  anything — those belong to the routed skills, authorized workflows, and humans.
- Downstream skills and humans reuse the `calc_id` (with its `inputs_hash`,
  `config_version`, and `rate_table_version`) rather than recomputing, so the same inputs
  produce the same numbers everywhere the workbook is cited.
