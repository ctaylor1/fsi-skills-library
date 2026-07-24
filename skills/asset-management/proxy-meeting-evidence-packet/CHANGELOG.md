# Changelog — proxy-meeting-evidence-packet

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
