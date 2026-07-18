# Controls — financial-statement-audit-assistant

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The output is a working-paper **draft**, not audit evidence relied
  upon until reviewed.
- **Human approval:** `external-delivery` — preparer and engagement-reviewer sign-off are
  recorded on the draft; **partner approval is required before any reliance or external
  delivery** (issuing to the client, the file of record, a regulator, or a group/component
  auditor). Internal analytical iteration may be reviewer-sampled.

## Prohibited (fail closed)

- **Expressing or implying an audit opinion**, or any conclusion that the statements
  "present fairly" / are "true and fair" / are "free from material misstatement" / obtain
  "reasonable assurance".
- **Concluding** on fair presentation, materiality sufficiency, or **going concern**.
- **ICFR / SOX** control-effectiveness opinions.
- **Signing off** on behalf of a human, or manufacturing an approval.
- **Delivering, filing, submitting, or issuing** anything as final (draft-only).
- **Unsupported assertions** — any tie-out, selection, or finding without a citation.

## Working-paper states (this skill may set only these)

`draft` → `preparer-signed` (carried from input) → `reviewer-pending` / `reviewer-signed`
(carried from input). It may **not** set `final`, `delivered`, `filed`, `issued`, or
`opinion-formed`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity** — all eight required sections present and non-empty.
- **No unsupported assertions** — every tie-out and finding carries a citation.
- **No opinion / assurance language** (regex: `in our opinion`, `present(s) fairly`,
  `true and fair`, `reasonable assurance`, `free from material misstatement`,
  `going concern … is appropriate`, qualified/unqualified/adverse/disclaimer opinion).
- **Draft-only** — no `filed with`, `submitted to the SEC/regulator/PCAOB`, `delivered as
  final`, `issued … as final`, or `this report is final`.
- **Tie-out arithmetic** — `difference == fs_amount − tb_sum`; status matches the
  clearly-trivial threshold.
- **Required approvals recorded** — `Preparer` and `Reviewer` roles present, each with a
  name and a status.
- **Standing note** present.

## Segregation of duties

Preparer, reviewer, and the partner who authorizes reliance/delivery are distinct roles. The
same person (or this skill) must not both prepare and approve the working paper. This skill
prepares a draft; humans review and approve.

## Data classification, privacy, records

- **Confidential (financial records).** Restrict to the engagement team; apply data
  minimization on any customer/employee identifiers pulled into support.
- Retain the working-paper draft, cited sources, and the **planning-parameter version** per
  the firm's audit documentation retention policy; log preparer identity and every source
  read. The audit file of record is maintained by the engagement's system, not by this skill.
