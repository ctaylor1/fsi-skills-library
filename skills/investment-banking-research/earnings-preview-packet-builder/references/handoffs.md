# Adjacent-Skill Handoffs - earnings-preview-packet-builder

This skill **compiles and packages** a source-backed, pre-event preview brief from already-
sourced facts and third-party-attributed debate points. It is strictly **pre-event**, it
never sets a forecast/rating/target/trade view, and it never publishes or distributes.
Content sourcing is upstream; the post-event analysis, control clearance, and distribution
are separate activities.

## Downstream / adjacent by lifecycle stage

| Skill | When | Boundary |
| ----- | ---- | -------- |
| `earnings-results-analyzer` | **After** the company reports - beat/miss vs consensus, guidance revision, KPI drivers, transcript changes, thesis impact | Post-event analysis is a different skill; this preview stops at the print. The preview `packet_id` + `job_id` hand context to it. |
| `investment-thesis-monitor` | Ongoing thesis/estimate tracking between events | Not a per-event compilation; separate cadence. |

## Upstream (produce sourced components this skill compiles)

| Upstream skill | Provides |
| -------------- | -------- |
| `investment-source-ingester` | Ingested filings, transcripts, IR-calendar events |
| `investment-vendor-feed-reconciler` | Reconciled consensus / estimates feed values |
| `investment-data-quality-exception-detector` | Data-quality exceptions on cited figures |
| `company-profile-builder` | Company profile and historical KPI series |
| `scenario-sensitivity-generator` | Full driver sensitivity / scenario exhibits (beyond disclosed sensitivities) |
| `adverse-media-investigator` | In-depth controversy / adverse-media investigation |
| `coverage-meeting-preparer` | Coverage context and management-meeting objectives |
| `coverage-initiation-researcher` | Coverage-initiation background where relevant |

When a figure is stale, unsourced, or disputed, route the **item** back to the relevant
upstream skill above; do not edit or back-fill the underlying number inside the packet.

## Adjacent control / compliance (clear before distribution)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `communications-compliance-reviewer` | Review of required disclosures, prohibited-claim screen, and supervision on the materials | assembled packet + source map |
| `conflicts-of-interest-reviewer` | Conflicts / control-room clearance for the coverage | `packet_id` + issuer + parties |

## Human / operations handoffs (no catalog skill performs these)

- **Supervisory-analyst sign-off**, **research-compliance / control-room clearance** (MNPI,
  wall-cross, information barriers), and **legal/disclaimer review** are recorded as approvals.
- **Distribution** of the packet to the desk or any external party is performed by a
  **person** through the firm's approved channel - never by this skill.

## Duplicate-execution prevention

- This skill does **not** build sensitivity/scenario exhibits, reconcile feeds, investigate
  controversies in depth, run the post-event results analysis, adjudicate conflicts, run the
  communications-compliance review, or distribute (all above).
- It consumes sourced components and emits a single assembled packet keyed by `packet_id`
  (with a durable `job_id`); re-runs replace the packet rather than creating parallel briefs.
