# Changelog

## 2026-09-20 — Phase 1 explicit-mode merge (unreleased)

- Consolidated the two named entrypoints without merging their native schemas or professional responsibilities.
- Added whitelist dispatch, validation before compute, detached native/outer reconstruction and mode-isolation regressions.
- Preserved native fixtures and evaluation declarations under mode-prefixed script and case identifiers.
- No automatic cross-mode mapping, source connector or execution authority added.
- Updated routing identifiers to canonical package names; self-handoffs require explicit modes and reviewed native-input preparation. Added detached wrapper fixtures and standalone/mode-isolation regressions.

## evidence mode: proxy-meeting-evidence-packet

# Changelog — proxy-meeting-evidence-packet

## Unreleased — Phase 1 source fidelity

- Future/invalid evidence is excluded with explicit needs. Policy evidence with a conflicting mandate is ineligible; policy_version is required for a complete packet. Entitlement compares supplied account, record date and share count to an entitlement_ledger with source_ref. Missing or discrepant ledgers and future record dates require reconciliation. packet_id identifies the packet. This comparison does not authenticate custody records or cast votes.
- Added detached original-input reconstruction and independent adverse-case regressions. Validation remains draft-only and does not authenticate sources or approvals.


## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to separate
proxy-meeting **evidence collection/packaging** from **policy-consistency review** of a
human-proposed instruction (`voting-policy-consistency-checker`) and from the **vote decision /
ballot submission** (downstream, human), which carry distinct entitlements, evidence depth, and
outputs.

- **Scope:** for a shareholder meeting's agenda, collect the agenda item, issuer disclosure and
  board recommendation, ownership / record-date entitlement, the voting-policy clause,
  research-provider inputs (e.g., ISS / Glass Lewis), and analogous precedent; tag every collected
  item as an observed fact or a hypothesis; check completeness and entitlement integrity; score a
  documented review-priority band; and assemble a cited evidence bundle with a durable `case_id`.
  Read-only; recommendation-only disposition.
- **Controls:** R3; never casts, proposes, or recommends a vote, submits a ballot, closes a case,
  or overrides entitlement/record-date data; no hypothesis may be presented as an observed fact; a
  cited board/provider/precedent direction is an observed fact, not a proposed vote; versioned
  evidence/policy config; MNPI / client-confidential and research-provider licensing handling.
- **Scripts:** `validate_input` (meeting/agenda schema, needs-data & entitlement warnings), the
  evidence engine (`calculate_or_transform`: observation/hypothesis tagging, required-category and
  record-date entitlement checks, contested detection, deterministic review-priority band, evidence
  bundle), and `validate_output` (durable IDs, allowed dispositions only, prohibited-field &
  vote-action/entitlement-override language screens, observation/hypothesis integrity, citation
  completeness, review-priority tie-out, standing note). Each script has a `--selftest` over a
  bundled fixture and prints a line ending in `N error(s)`.
- **Evaluations:** trigger/routing, golden 6-item agenda exercising every disposition (assembled,
  entitlement-flagged, needs-data), contested detection, and observed/hypothesis tagging;
  deterministic script checks; a no-decision safety check running `validate_output` on a
  non-compliant packet (fails closed on vote-cast, prohibited field, mislabelled hypothesis, and
  vote/override language); vote-cast and entitlement-override refusals; a disposition-authorization
  refusal.
- **Handoffs:** upstream from the meeting-notice/vote-agent feed and `engagement-history-brief`;
  adjacent to `voting-policy-consistency-checker` (tests a human-proposed instruction against
  policy); downstream to the human proxy committee / stewardship (vote decision) and the custodian
  / proxy operations (entitlement correction).

### Pending before release
- Stewardship / proxy-voting control-owner review; segregation-of-duty review (packaging vs. voting
  vs. entitlement correction).
- Confirm the approved proxy-evidence config and voting-policy source, owner, and versioning;
  confirm the business-day/holiday calendar used for deadline proximity.
- Confirm firm-level vote-disclosure / N-PX recordkeeping obligations at deployment.
- Wire read-only MCP integrations (meeting notice/vote agent, issuer disclosures, custodian/record-
  date entitlement, voting policy, research providers, prior-vote record) at deployment.


## policy mode: voting-policy-consistency-checker

# Changelog — voting-policy-consistency-checker

## Unreleased — Phase 1 source fidelity

- Mandate-specific eligible policies override firm-wide policies; equally current competing policies produce no_policy. Policy availability is limited to the review as-of, with meeting-date expiration checks. Precedent requires matching mandate_id and an explicit comparability_key; category alone is insufficient. This is literal consistency with supplied policy, not adjudication of policy conditions or vote merits.
- Added detached original-input reconstruction and independent adverse-case regressions. Validation remains draft-only and does not authenticate sources or approvals.


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
