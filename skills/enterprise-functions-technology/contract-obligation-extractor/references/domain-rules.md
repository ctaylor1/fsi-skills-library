# Domain Rules — contract-obligation-extractor

Orientation references: the organization's contract-management standard and its versioned
**obligation taxonomy** (the required categories a register must cover) and **review
requirements** (which human reviews must be recorded before delivery). These take precedence
and are versioned contracts. This skill applies the deterministic assembly rules below; it
does not exercise legal judgment.

## Obligation taxonomy (default categories)

Each required category maps to one register section. The taxonomy is configuration, not
judgment; deployments may extend it.

| Category | Register section | Captures |
| -------- | ---------------- | -------- |
| `obligation` | Obligations | Who must do what, by when (payment, delivery, reporting) |
| `key-date` | Key Dates | Effective dates, expiries, milestones, deadlines |
| `service-level` | Service Levels | SLAs, uptime, credits, remedies |
| `right` | Rights & Restrictions | Audit, exclusivity, IP, and other granted rights |
| `restriction` | Rights & Restrictions | Non-solicit, non-compete, confidentiality limits |
| `renewal` / `termination` | Renewal & Termination | Auto-renewal, non-renewal notice, termination rights/notice |
| `data-term` | Data Terms | Processing role, breach notice, sub-processor, residency |
| `dependency` | Dependencies | Cross-references, incorporated docs, third-party dependencies |

## Extraction status (deterministic, per extraction)

For each candidate extraction, resolve its source clause and assign a status. Precedence:
**unsourced → conflict → ambiguous → extracted** (the more serious flag wins).

| Status | Condition | Consequence |
| ------ | --------- | ----------- |
| `extracted` | A resolvable clause citation exists, the responsible party is resolvable where required, and no conflicting term exists in its category | Placed in its section, cited |
| `ambiguous` | Cited, but a party-bearing category (`obligation`, `service-level`, `restriction`, `right`) has no resolvable responsible party | Cited **and** listed as an open item (assign party) |
| `conflict` | Cited, but its category carries two or more distinct `terms.notice_days` across clauses (e.g. 90-day non-renewal vs 60-day termination notice) | Cited **and** listed as an open item (reconcile) — never resolved here |
| `unsourced` | No clause reference resolves and no citation is supplied | **Not asserted**; listed as a `needs-source` open item — never a citation-less obligation |
| `coverage-gap` | A taxonomy category has no extraction | Placeholder in its section + open item to **confirm** whether the contract addresses it — never asserted as silence |

Every asserted status (`extracted`/`ambiguous`/`conflict`) must carry a clause citation.

## Reviews capture (recorded, never assumed)

- Reviews with `status == "recorded"` are captured with `type`, `reviewer_role`, `reviewer`
  (masked), `date`, and `citation`.
- Every entry in `required_reviews` with no recorded review becomes an **outstanding** review
  and an open item. A review is never assumed done.
- `human_approval_required_before_delivery` is always `true` — the assembled register is a
  draft; a human must approve before delivery or reliance.

## Open-items taxonomy

`ambiguous-obligation` | `term-conflict` | `needs-source` | `coverage-gap` |
`outstanding-review`. Each open item names the item, its type, a required human action, and
(where a clause exists) its citation.

## Hard boundaries (fail closed)

- No **legal advice / interpretation** (enforceability, validity, breach, liability,
  recommendations).
- No **completeness / exhaustiveness** claim and no assertion that the contract is silent.
- No **unsupported assertion** (an obligation without a clause citation).
- No **delivery / execution** of the register or contract (draft-only).
- No **fabrication** of clauses, obligations, parties, dates, or terms.

## Register manifest — required contents

`register_id`, `contract_id`, `as_of_date`, `config_version`, `template_version`,
`assembly_status: draft-extracted`, `human_approval_required_before_delivery: true`, the
canonical `sections` (register summary, contract profile, obligations, key dates, service
levels, rights & restrictions, renewal & termination, data terms, dependencies, reviews, open
items, source index), the open-items list, and the standing note.
