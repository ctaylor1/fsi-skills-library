# Earnings Preview Packet - Output Template

> DRAFT - pre-event research preview for internal analyst, supervisory-analyst, and
> compliance review only. Not for distribution until the required approvals are recorded.
> Contains no forecast, rating, price target, or trade recommendation. This skill never
> publishes, sends, distributes, or files materials.

Fill every field from **approved sources**. Do not originate figures or state a house view;
cite the source and attribute every forward-looking number to a third party (consensus
provider or company guidance/disclosure). Any item missing a takeaway, a source, an approved
data point, or content approval is **blocked** (not `ready`). Required template sections must
all be present.

---

## Header

- **Packet:** `{packet_id}`  ·  **Job:** `{job_id}`  ·  **As of:** `{as_of_date}`
- **Issuer:** `{issuer.name}` (`{issuer.ticker}`)  ·  **Sector:** `{issuer.sector}`
- **Event:** `{event.fiscal_period}` - reports `{event.report_date}` `{event.report_time}`
  (call `{event.call_datetime_utc}`)  ·  **Comparable:** `{event.comparable_period}`
- **Template:** `{template_id}@{template_version}`
- **Data classification:** Highly Confidential (MNPI / client-confidential)
- **Packet status:** `{draft | hold-for-approval | ready-for-distribution}`  *(never a distributed state)*

## Required sections (template fidelity)

Present: `{sections_present}`  ·  Missing: `{sections_missing}` *(must be empty to distribute)*

Default required sections: `cover`, `event-calendar`, `consensus-snapshot`, `prior-guidance`,
`historical-kpis`, `controversies-and-debates`, `sensitivities`, `open-questions`, `disclaimer`.

## Consensus vs. prior guidance (descriptive - sourced figures only)

| Metric | Consensus (cited) | Guidance range (as issued, cited) | Midpoint | Position | Gap to midpoint |
| ------ | ----------------- | --------------------------------- | -------- | -------- | --------------- |
| `{metric}` | `{consensus_value}` `{unit}` | `{guidance_low}`-`{guidance_high}` | `{guidance_midpoint}` | `below/within/above-range` | `{gap_to_midpoint}` |

*Consensus is third-party; guidance is company-issued. This table states where two sourced
numbers sit relative to each other - it is not a forecast of the print.*

## Historical KPI trend (reported figures only)

| KPI | Latest period | Latest | Prior (QoQ) | QoQ delta | Year-ago (YoY) | YoY delta | Source |
| --- | ------------- | ------ | ----------- | --------- | -------------- | --------- | ------ |
| `{kpi}` | `{latest_period}` | `{latest_value}` | `{prior_value}` | `{qoq_delta}` | `{yoy_value}` | `{yoy_delta}` | `{source}` |

## Items

For each item, in template-section order:

| Field | Content |
| ----- | ------- |
| Item ID | `{item_id}` |
| Section | `{section}` |
| Title | `{title}` |
| Source component | `{source_component}` (upstream skill or `manual`) |
| Takeaway (factual "what to watch") | `{takeaway}` |
| Data points | each: `{label}` = `{value}` - kind `{kind}`, attribution `{attribution}`, `source_ref` `{ref@date}` (approved: yes) |
| Sources | `{[system:ref@date, ...]}` |
| Content approval | `{approver}` on `{date}` (status: approved) |
| Status | `ready` \| `needs-source` \| `unsupported-claim` \| `needs-approval` |

## Controversies, debates, and open questions

- **Known controversies** - each cited to its source; the packet takes no side.
- **Debate points** - bull/bear items each **attributed** (sell-side note, trade press,
  filing); the packet states the debate, it does not resolve it or recommend.
- **Open questions** - for the print and for management; open items only, with no implied
  answer, forecast, or recommendation.

## Unsupported / blocked items

List every item whose status is not `ready`, every data point lacking an approved
`source_ref`, and every forward-looking figure lacking a third-party attribution. Resolve
these (route to the upstream data/research skill) before distribution - **never** back-fill
with an estimated figure or a house view.

## Required approvals (recorded before external distribution)

| Role | Owner | Status | Approver | Date |
| ---- | ----- | ------ | -------- | ---- |
| `supervisory_analyst` | Registered supervisory analyst | approved / pending | | |
| `research_compliance` | Research compliance / control room | approved / pending | | |
| `legal_disclaimers` | Legal | approved / pending | | |

`ready-for-distribution` requires **all** rows `approved`.

## Standing note (required)

> Pre-event preview compilation only; no forecast, price target, rating, or trade view has
> been set, and no packet has been published or distributed. Consensus and guidance figures
> are third-party sourced, not the skill's estimates. External distribution requires the
> recorded supervisory-analyst, research-compliance, and legal approvals and is performed by
> a person, not this skill.
