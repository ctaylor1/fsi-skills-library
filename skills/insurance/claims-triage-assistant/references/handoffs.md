# Adjacent-Skill Handoffs — claims-triage-assistant

Triaging a claim is a **separate control activity** from adjudicating it, adjusting it,
analyzing coverage, and paying it. This skill produces a review-ready draft triage package;
humans and other skills own the coverage decision, the reserve, the assignment, the payment,
and any regulatory filing.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `claim-readiness-checker` | FNOL/loss-notice completeness and document readiness | A validated claim record ready to triage |
| `catastrophe-exposure-monitor` | Read-only catastrophe-event flags and exposure context | `catastrophe_code` used to raise urgency and route to the CAT unit |

## Downstream / lateral (this skill routes to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `coverage-gap-analyzer` | Triage surfaced a coverage question (period mismatch, lapse, possible exclusion) | `claim_id` + the open coverage questions (human coverage analysis; no determination here) |
| `claims-fraud-referral-assistant` | Fraud indicators present | `claim_id` + indicator evidence (SIU referral; triage concludes no fraud) |
| `subrogation-opportunity-screener` | Possible recovery from an at-fault third party | `claim_id` + party/liability context |
| `claims-file-reviewer` | Complex / large-loss claim (S1) needing a deeper file review | `claim_id` + triage package |
| `reserving-analysis-assistant` | A reserve needs to be analyzed and set (never by triage) | `claim_id` + severity/exposure context (human-owned) |
| `policy-document-explainer` | The claimant/handler needs the policy wording explained | policy reference (explanation only) |

## Human / specialist handoffs (no catalog skill)

- **Adjudication & assignment** — the coverage determination, liability assessment, reserve,
  and adjuster/queue assignment are made by the claims supervisor and adjuster of record, not
  this skill.
- **Catastrophe / major-loss handling** — CAT-coded claims route to the catastrophe /
  major-loss unit; the upstream monitor only flags exposure.
- **Litigation** — matters in suit route to claims litigation / legal counsel.
- **Vulnerable claimant** — a vulnerability indicator routes to the accommodation / support
  team for review before any contact.
- **Regulatory reporting** — any statutory or DOI report is handled by claims compliance;
  this skill only flags that a deadline or report may be relevant.

## Duplicate-execution prevention

- This skill **does not** decide coverage, set a reserve, assign, pay, close, or file — those
  belong to the human owner or the named specialist skill under approval.
- Downstream consumers act on the emitted `claim_id` triage package rather than re-triaging.
- A `refer-specialist` route is resolved by the named owner, not auto-actioned here.
