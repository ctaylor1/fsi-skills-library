# Adjacent-Skill Handoffs — credit-surveillance-packet

This skill **gathers and packages** issuer credit-surveillance evidence from inputs other skills
and humans produce. It does not ingest raw feeds, extract covenant terms, monitor the thesis, or
make any rating / thesis / position decision. All skill names below exist in
`catalog/skills-catalog.json`.

## Upstream (feeds this skill — produce the inputs the packet consumes)

| Upstream skill | Produces | Handoff artifact |
| -------------- | -------- | ---------------- |
| `investment-source-ingester` | Ingested filings / market / rating feeds | raw source documents + refs |
| `holdings-transaction-normalizer` | Normalized positions/instruments | issuer/instrument identity |
| `security-master-enricher` | Instrument reference data | issuer/security resolution |
| `investment-vendor-feed-reconciler` | Reconciled vendor spread/rating feeds | approved market/rating inputs |

The packet **ties out** to these sources; it never re-derives or re-scopes them. If a required
financial, spread, or rating input is missing or unapproved, this skill returns `needs-data` and
routes to the producing skill/human rather than inventing the figure.

## Downstream / adjacent (this skill routes to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `credit-terms-covenant-extractor` | A covenant is flagged as changed and term-level detail (definitions, baskets, step-downs) is needed | issuer_id + changed covenant IDs + credit-agreement ref |
| `investment-thesis-monitor` | Ongoing thesis KPI / catalyst tracking for the issuer is needed | issuer_id + surveillance packet |
| `counterparty-exposure-monitor` | The issuer is also a counterparty and exposure/limit monitoring is needed | issuer_id + exposure context |
| `fund-commentary-drafter` | Surveillance findings roll into periodic fund commentary | draft-ready packet |

The mandated covenant handoff is **`credit-terms-covenant-extractor`**: this skill flags *that* a
covenant changed; the extractor pulls the covenant *terms*. The two do not duplicate each other —
surveillance never extracts or interprets covenant terms, and the extractor never builds the
surveillance metrics or tracks period-over-period change.

## Peer skill (do not duplicate)

- **Covenant-term extraction / interpretation** is `credit-terms-covenant-extractor`, not this
  skill. This skill is issuer-level *surveillance* (metrics + change tracking + citations).

## Human / licensed-specialist handoffs (no catalog skill)

- The **credit rating** (assignment/derivation) is made by the rating process / committee /
  agency — never by this skill. `rating_action` stays `reported-only`.
- Any **investment-thesis change** is made by the research analyst / PM — never by this skill.
  `thesis_action` stays `unchanged`.
- Any **position or trade decision** is made by the PM / trading desk — never by this skill (and
  is a prohibited action). `position_action` stays `none`.
- **Covenant compliance / headroom determination**, **MNPI / wall-crossing sign-off**, and any
  regulatory review go to compliance / a human before delivery.

## Duplicate-execution prevention

- This skill does **not** ingest feeds, extract covenant terms, monitor the thesis, or record any
  rating / thesis / position — those belong to the upstream/downstream skills and to humans.
- It emits a single draft-ready packet keyed by `issuer_id` + `as_of`; downstream consumers reuse
  that packet rather than re-assembling it.
- If inputs are incomplete or unapproved it stops at `needs-data` and names the producing skill,
  instead of filling the gap with an unsourced figure.
