# Domain Rules — policy-document-assistant

The firm's **policy-management standard** governs how controlled policies and procedures are
structured, versioned, reviewed, and approved. The rules below are the default encoding used
by `scripts/calculate_or_transform.py` and enforced by `scripts/validate_output.py`; the
deployed values come from the versioned `config:policy-std` contract.

## Required template sections (order fixed)

`document-control` → `purpose` → `scope` → `policy-statements` →
`roles-responsibilities` → `related-documents` → `review-version-history` → `approvals`.
Optional sections `definitions` and `exceptions-escalation` are inserted only when the
request supplies clauses for them. A missing required section fails output validation.

## Clause sourcing rule (no unsupported assertions)

- A clause marked `normative` (a "shall/must" statement) **must** cite one or more
  `req_ids` that each resolve to a requirements-register entry with `status: "approved"`
  **and** a non-empty authoritative `source`.
- A normative clause with no such mapping is recorded in `unsupported_clauses` and blocks
  release. The skill never fabricates a requirement to clear the block.
- Informational clauses (purpose, scope, roles, exceptions) need no citation.

## Version-bump rule

Versions are `X.Y`. From the current version and the requested `change_type`:

| change_type | Result |
| ----------- | ------ |
| `major` | `(X+1).0` — material change to obligations/scope |
| `minor` | `X.(Y+1)` — clarifications, added/refined statements |
| `editorial` | `X.Y` unchanged — typo/formatting only, logged in history |

The computed `new_version` must equal this rule; a mismatch fails validation.

## Review cadence (by tier)

`next_review_date = proposed_effective_date + interval`, where the interval is:

| Tier | Review interval |
| ---- | --------------- |
| `tier-1` | 12 months |
| `tier-2` | 24 months |
| `tier-3` | 36 months |
| unknown | 12 months (conservative default) |

The computed `next_review_date` must tie out; a mismatch fails validation. The **real**
effective date is set by the owner at activation — the draft carries only a proposed date.

## Required-approval matrix

`approvals_required` lists the roles that must be recorded `approved` (with approver + date)
before external delivery. Default when unspecified: `owner`, `legal`, `compliance`. A
higher-tier policy may add roles (e.g., `risk`, `board-committee`) per the policy standard.
Recording an approval is a human action; the skill only opens the slots and verifies they
are filled.

## Change summary (compare mode)

Against the prior version's clauses (by `clause_id` + text), the draft reports `added`,
`modified`, and `removed` clause IDs plus normative/informational counts. This supports the
"compare two policy versions" use case and feeds the Review and Version History section.

## Hard boundaries (fail closed)

- No **publishing, activating, filing, or making effective** — draft-only.
- No **unsupported normative statement** — every "shall/must" cites an approved requirement.
- No **invented, paraphrased, superseded, or non-approved requirement** as a source.
- No **personalized legal advice** or binding regulatory interpretation.
- No **self-recorded or backdated approvals**.
