# Changelog — voting-policy-consistency-checker

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`; Wave 5 — 2026 industry
expansion).

- **Scope:** compare a proxy-voting analyst's proposed vote per ballot item against the
  firm's versioned voting policy and analogous prior cases; surface deviations with policy
  and precedent citations. Read-only; R3 decision support.
- **HARD BOUNDARY:** evidences consistency only — never decides, changes, casts, submits, or
  finalizes a vote, treats the proposed vote as authoritative, or gives a merits opinion.
  Mandatory human adjudication before any vote is recorded.
- **Classification (deterministic):** per item `aligned` / `deviation` / `case_by_case` /
  `no_policy`, with effective-date policy selection (guideline `effective_date ≤ meeting_date`,
  latest; future/superseded guidelines excluded) and precedent concordance counts — each
  cited (see `scripts/calculate_or_transform.py`, `references/domain-rules.md`).
- **Controls:** R3; deterministic `validate_output` prohibited-decision screen (rejects
  vote-decision/action language, uncited findings, missing human-adjudication actions,
  disposition mismatch, missing disclaimer); versioned policy as the authority; durable
  `review_id` / `finding_id` and upstream `packet_id`.
- **Scripts:** `validate_input` (ballot/policy/precedent schema + evaluability warnings),
  the comparison engine, `validate_output` (cited-evidence, human-adjudication, deterministic
  disposition tie-out, decision-language screen, disclaimer). Each self-tests over a bundled
  fixture and prints an `N error(s)` line (exit 0 pass / 1 fail).
- **Evaluations:** trigger/routing, golden deviations case, no-precedent edge, deterministic
  script checks, no-decision safety fixture (fails closed) + injection, human-adjudication
  authorization.
- **Handoffs:** upstream `proxy-meeting-evidence-packet`; lateral `engagement-history-brief`
  and `mandate-compliance-monitor`; the vote decision/submission is a human/voting-committee
  action in the system of record (not a skill).

### Pending before release
- Domain SME (proxy voting / stewardship) + control-owner blind review; confirm the
  versioned voting-policy source, its owner, and the precedent-store schema.
- Confirm MNPI/client-confidential handling of voting intentions with compliance.
- Wire read-only MCP integrations (voting policy, voting-record/precedent, ballot,
  research-provider) at deployment.
