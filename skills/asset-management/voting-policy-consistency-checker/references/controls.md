# Controls — voting-policy-consistency-checker

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only
  analysis.
- **Human approval:** `required` — mandatory human adjudication before any vote is decided,
  changed, recorded, or submitted. This skill produces findings and evidence only.

## Prohibited (fail closed)

- No **vote decision, change, casting, submission, or finalization** — of a vote, ballot,
  proxy, or voting instruction. The skill evidences deviations; the human/voting committee
  decides and the proxy-voting system of record records.
- No treating the `proposed_vote` as authoritative or "approved".
- No **case closure** or suppression of a deviation; each `deviation` / `case_by_case` /
  `no_policy` finding carries a mandatory human-adjudication `required_action`.
- No **personalized investment advice** or merits opinion on a proposal.
- No **system-of-record write** (proxy-voting platform, ballot, voting-record store).
- No overriding **entitlement / record-date / share-count** data (owned upstream by
  `proxy-meeting-evidence-packet`).

## Required output screens (`scripts/validate_output.py`)

- Findings present; each finding has a known status (`aligned` / `deviation` /
  `case_by_case` / `no_policy`).
- Every `aligned` / `deviation` / `case_by_case` finding cites a policy guideline
  (`policy_citation`).
- Every `deviation` / `case_by_case` / `no_policy` finding carries a human-adjudication
  `required_action`.
- `overall_disposition` equals the deterministic mapping from the findings
  (references/domain-rules.md).
- No vote-decision / vote-action language in the free text (regex screen: "we will vote",
  "cast the vote", "submit the ballot", "vote has been cast/submitted/recorded", "override
  the vote", "finalize the vote", etc.).
- Standing disclaimer present: "Consistency findings and cited evidence only; not a voting
  decision or instruction. This review does not cast, change, or submit any vote; a human
  analyst adjudicates and records the vote in the system of record."

A non-compliant review (see `evals/files/review_with_decision.json`) MUST fail closed
(exit 1).

## Conflicts / fairness

- Cite firm policy as the authority; a proxy-advisor recommendation is context, never an
  override.
- Describe deviations factually; take no position on the merits of the proposal or the
  issuer.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Voting intentions can be
  market-sensitive and are client-confidential; minimize free-text and never disclose a
  client's voting intention outside the authorized workflow.
- Retain the review, its citations, and the `policy_version` per records policy; log the
  read and any human adjudication that follows. Never exfiltrate ballot or client data.

## Reproducibility

`review_id` binds the output to the exact ballot, `policy_version`, precedent set, and the
effective-date selection; re-running with the same inputs reproduces the findings and
disposition.
