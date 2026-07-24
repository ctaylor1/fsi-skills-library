# Changelog — engagement-history-brief

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`). A Draft & package
(Artifact-creation) skill for the 2026 industry-expansion cohort that assembles a single
issuer's stewardship engagement history into a cited, draft brief for a stewardship analyst.

- **Scope:** reverse-chronological engagement timeline; issuer commitments matched to
  disclosed progress with a factual, date-based status; attendee roll-up by role; deduplicated
  source documents; unresolved follow-ups. Draft-only; no system-of-record write.
- **Controls (R3):** HARD BOUNDARY — never chooses an engagement objective
  (`engagement_objective.selected` stays `null`), never represents a firm position
  (`firm_position.represented` stays `false`), and never casts/proposes/recommends a vote.
  Deterministic `validate_output` fails closed on any uncited item, chosen objective /
  represented position, prohibited-decision / vote language, non-draft status, or missing
  approver roles. Versioned `brief_version` / `source_hierarchy_version`; durable `brief_id`
  and carried-through `engagement_id` / `commitment_id` / `follow_up_id` / `doc_id`.
- **Scripts:** `validate_input` (engagement-log schema; data-quality warnings for missing
  owners, uncited progress, overdue commitments, future-dated entries), `calculate_or_transform`
  (chronology + commitment↔progress matching + attendee roll-up + source dedup + open
  follow-ups, with `--selftest` invariant checks), `validate_output` (draft-only, template
  sections, citation coverage, hard-boundary + language screen, approvals, standing note).
  Python stdlib-only, self-contained, de-identified fixtures.
- **Assets:** `output-template.md` — the controlled Engagement History Brief template with the
  Engagement objective and Firm position sections left deliberately unset.
- **Evaluations:** trigger/routing (history vs. vote/objective/commentary), a golden 4-engagement
  fixture exercising every commitment status and follow-up state, deterministic script checks,
  and a fail-closed safety check running `validate_output` on a non-compliant brief (exit 1),
  plus injection / fabricate-citation / vote / SoR-write refusals.
- **Handoffs:** vote-decision evidence → `proxy-meeting-evidence-packet`; human-proposed vote
  vs. policy → `voting-policy-consistency-checker`; external firm-attributed commentary →
  `fund-commentary-drafter`; objective/position/vote decisions → human (stewardship lead /
  committee).

### Pending before release
- Stewardship control-owner + compliance (MNPI handling / Stewardship Code disclosure) blind
  review; segregation-of-duties review (assembly vs. objective/position/vote decisions).
- Confirm the controlled brief template + source-hierarchy config source, owner, and versioning.
- Wire read-only MCP integrations (engagement log / stewardship CRM, document intelligence,
  entity resolution, approved-source retrieval) at deployment.
