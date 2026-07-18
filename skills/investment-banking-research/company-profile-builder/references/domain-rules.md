# Domain Rules — company-profile-builder

Orientation references: SEC filings (10-K/10-Q/8-K, proxy) as authoritative issuer sources;
FINRA/SEC research and communications standards (a factual profile is not research with a
rating/recommendation); information-barrier / MNPI controls. The firm's profile template,
required-sections/approvals config, and information-barrier policy take precedence and are
**versioned contracts**.

## Canonical profile sections (template contract)

The profile manifest and [assets/output-template.md](../assets/output-template.md) mirror
these keys. Content sections hold cited fact entries; `profile_summary` and `sources` are
derived.

| Section key | Contents |
| ----------- | -------- |
| `profile_summary` | Header + counts (derived) |
| `business_overview` | What the company does, segments, geography |
| `key_financials` | KPIs and operating/financial metrics (revenue, growth, margin, etc.) |
| `ownership` | Major holders, insider/institutional split, share structure |
| `management` | Key executives and board |
| `trading_data` | Price, market cap, EV, multiples, 52-week range (**as-of dated**) |
| `transactions` | Precedent M&A / financing history |
| `sources` | Deduplicated source index (derived) |

## Fact status assignment (deterministic)

Applied per fact by `scripts/calculate_or_transform.py`, in order:

| Status | Condition | Placement |
| ------ | --------- | --------- |
| `unsupported` | No `source_ref` | **Open item only** — never asserted |
| `restricted-mnpi` | `mnpi` true **and** `intended_distribution` = `external` | **Open item only** — excluded from external profile |
| `unresolved` | Fact `company_id` ≠ profile `company_id` | Asserted (cited) **and** open item — reconcile with a human |
| `stale` | `expires` earlier than `as_of_date` | Asserted (cited) **and** open item — refresh |
| `included` | Otherwise (cited, fresh, identity-consistent) | Asserted (cited) |

Only `included` / `stale` / `unresolved` are asserted in a section, and every asserted entry
carries a citation — this is the **no-unsupported-assertion** guarantee. A required section
with zero asserted entries yields a `section-incomplete` open item; it is never padded.

## Approvals (external-delivery posture)

Recorded approvals capture role + date + citation. Every `required_approval` not recorded is
an **outstanding** open item. External distribution requires supervisory/research-analyst and
compliance (control-room) approval; the manifest always sets
`human_approval_required_before_delivery: true`.

## Hard boundaries (fail closed)

- No **distribution / delivery** (send, submit, email, publish, share).
- No **investment advice, rating, recommendation, or price-target opinion**.
- No **unsupported assertion** — an uncited fact is an open item, not a section entry.
- No **MNPI** in an external profile absent documented wall-crossing / compliance clearance.
- No **fabrication** of missing facts; no **auto-merge** of mismatched identities.

## Open-items taxonomy (required contents)

Durable `profile_id`; each gap typed as `unsupported-claim`, `mnpi-exclusion`,
`identity-unresolved`, `stale-data`, `section-incomplete`, or `outstanding-approval`, with the
required human action and (where a source exists) its citation.
