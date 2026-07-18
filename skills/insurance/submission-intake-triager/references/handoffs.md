# Adjacent-Skill Handoffs — submission-intake-triager

This skill produces a cited **intake triage packet** (`triage_id`) and stops. It does not
underwrite to a decision, price, bind, quote, decline, issue, or close.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `underwriting-workbench-assistant` | Submission is clean/triaged and needs the underwriter-ready risk profile + drafted decision rationale | `triage_id` + normalized fields |
| `catastrophe-exposure-monitor` | A catastrophe-zone flag fired and portfolio accumulation / modeled-loss review is needed | `triage_id` + location/TIV |
| `coverage-gap-analyzer` | The ask shifts to coverage adequacy of stated needs vs. terms/limits/exclusions | insured needs + exposure |
| `policy-wording-comparator` | Manuscript/endorsement wording needs clause-level comparison to filed forms | forms + endorsements |
| `premium-quote-comparator` | Post-quote comparison across markets (out of intake scope) | normalized quotes |
| `policy-renewal-reviewer` | The submission is a renewal needing expiring-vs-proposed term comparison | expiring + proposed terms |

## Upstream (may call this skill)

Broker-operations intake and `policy-renewal-reviewer` may hand a new-business or renewal
submission to this skill for normalization, reconciliation, and appetite triage. A scheduled
monitor is **not** used here (this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill **normalizes, reconciles, gaps, and triages only**; it must not build the
  underwriter risk profile, aggregate catastrophe exposure, compare wording, price, or
  decide — those belong to the human underwriter and the downstream skills above.
- Downstream skills reuse the `triage_id` packet (normalized fields + citations) rather than
  re-extracting from the raw documents or re-running appetite triage.
