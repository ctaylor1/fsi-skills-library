# Domain Rules — fund-fact-sheet-builder

Orientation references: retail-communication / fund-marketing standards (FINRA Rule 2210 and
SEC advertising/performance-presentation rules in the US; KIID/KID and fund-marketing regimes
where configured), GIPS-aligned standardized performance presentation, and information-barrier /
MNPI controls. The firm's fact-sheet template, required-sections/approvals/disclosures config,
performance-presentation standard, and information-barrier policy take precedence and are
**versioned contracts**.

## Canonical fact-sheet sections (template contract)

The manifest and [assets/output-template.md](../assets/output-template.md) mirror these keys.
Content sections hold cited figure entries; `fund_summary`, `reconciliation`, and `sources` are
derived; `disclosures` is approved controlled content.

| Section key | Contents |
| ----------- | -------- |
| `fund_summary` | Header (fund, share class, ISIN, currency, benchmark, objective) + counts (derived) |
| `performance` | Standardized, **net-of-fees** returns (cumulative, annualized, calendar-year) vs benchmark, as-of dated |
| `holdings` | Top holdings, sector/geographic allocation |
| `risk` | Volatility, tracking error, Sharpe, drawdown, SRRI/risk indicator (as-of dated) |
| `fees` | Ongoing charges figure (OCF/TER), management fee, entry/exit charges |
| `esg` | Sustainability classification (e.g., SFDR article) and ESG metrics |
| `reconciliation` | Source-to-output tie-out for every numeric figure (derived) |
| `disclosures` | Required regulatory disclosures — approved, cited controlled content |
| `sources` | Deduplicated source index (derived) |

## Figure status assignment (deterministic)

Applied per figure by `scripts/calculate_or_transform.py`, in order:

| Status | Condition | Placement |
| ------ | --------- | --------- |
| `unsupported` | No `source_ref` | **Open item only** — never asserted |
| `restricted` | `mnpi` true **and** `intended_distribution` = `external` | **Open item only** — excluded from external sheet |
| reconcile-break | `value_numeric` vs `source_value_numeric` differ beyond `reconcile_tolerance` | **Open item only** — never asserted |
| `unresolved` | Figure `fund_id` ≠ fact-sheet `fund_id` | Asserted (cited) **and** open item — reconcile with a human |
| `stale` | `expires` earlier than `as_of_date` | Asserted (cited) **and** open item — refresh |
| `included` | Otherwise (cited, reconciled, fresh, identity-consistent) | Asserted (cited) |

Only `included` / `stale` / `unresolved` are asserted in a section, and every asserted entry
carries a citation — this is the **no-unsupported-assertion** guarantee. Every numeric figure
carrying a source value must also tie out within tolerance before it can be asserted — this is
the **source-to-output reconciliation** guarantee. A required section with zero asserted entries
yields a `section-incomplete` open item; it is never padded.

## Performance presentation (standardization)

Performance is presented **net-of-fees** over standardized periods (e.g., 1Y/3Y/5Y/10Y/since
inception, cumulative and annualized) alongside the stated benchmark, as of the reporting date.
A gross-only or non-standard-period figure is surfaced for review and never presented as the
headline. Past performance is not indicative of future results — the `past-performance`
disclosure is required on any sheet quoting returns.

## Disclosures (controlled content)

Each required disclosure is rendered as approved text from the controlled-content library, with
its citation and version. A disclosure with no citation or empty text is an **unsupported
disclosure** open item and is not rendered as satisfied. A `required_disclosure` not provided is
a `disclosure-outstanding` open item. Typical required set (configure per jurisdiction):
`past-performance`, `capital-at-risk`, `charges-reduce-returns`, `benchmark-disclosure`.

## Approvals (external-delivery posture)

Recorded approvals capture role + date + citation. Every `required_approval` not recorded is an
**outstanding** open item. External distribution requires performance verification,
compliance/marketing review, and registered-principal approval; the manifest always sets
`human_approval_required_before_delivery: true`.

## Hard boundaries (fail closed)

- No **distribution / delivery** (send, submit, email, publish, share).
- No **return promise or guarantee**; past performance is not indicative of future results.
- No **investment advice, rating, or recommendation**.
- No **unsupported assertion** — an uncited figure is an open item, not a section entry.
- No **unreconciled figure** — a number that does not tie to source is an open item.
- No **MNPI/embargoed content** in an external sheet absent documented wall-crossing / clearance.
- No **fabrication** of missing figures; no **auto-merge** of mismatched identities.

## Open-items taxonomy (required contents)

Durable `factsheet_id`; each gap typed as `unsupported-claim`, `mnpi-exclusion`,
reconcile-break, `identity-unresolved`, `stale-data`, `section-incomplete`,
`disclosure-unsupported`, `disclosure-outstanding`, or `outstanding-approval`, with the required
human action and (where a source exists) its citation.
