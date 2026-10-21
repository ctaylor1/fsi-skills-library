# Adjacent-Skill Handoffs - investment-banking-pitch-builder

This skill **assembles and packages** a pitch-book draft from already-approved components.
It does not build the analyses/models, and it never delivers. Content construction is
upstream; control clearance and delivery are separate activities.

## Upstream (produce approved components this skill assembles)

| Upstream skill | Provides |
| -------------- | -------- |
| `comps-analysis-builder` | Trading-comps pages, multiples, peer rationale |
| `dcf-modeler` | DCF valuation pages, WACC, EV-to-equity bridge |
| `three-statement-model-builder` | Integrated operating model outputs |
| `merger-model-builder` | Accretion/dilution and pro forma pages |
| `lbo-model-builder` | LBO returns / sources-and-uses pages |
| `scenario-sensitivity-generator` | Sensitivity and scenario exhibits |
| `company-profile-builder` | Company profiles and strip pages |
| `market-landscape-researcher` | Industry/theme landscape pages |
| `market-sizing-builder` | TAM/SAM/SOM pages |
| `earnings-results-analyzer` | Post-earnings results context |
| `buyer-investor-list-builder` | Buyer/investor universe pages |
| `coverage-meeting-preparer` | Client/prospect context and objectives |
| `due-diligence-packager` | Diligence-sourced facts and open-item context |

When a page is stale, unsourced, or needs rebuilding, route the **page** back to the
relevant upstream skill above; do not edit the underlying figures inside the pitch.

## Adjacent control / compliance (clear before external use)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `conflicts-of-interest-reviewer` | Conflicts / control-room clearance for the engagement | engagement_id + parties |
| `communications-compliance-reviewer` | Review of required disclosures, prohibited claims, supervision on the materials | assembled draft + source map |

## Human / operations handoffs (no catalog skill performs these)

- **Deal-captain MD sign-off**, **control-room/compliance clearance** (MNPI, wall-cross,
  information barriers), and **legal/disclaimer review** are recorded as approvals.
- **External delivery** to the client/board is performed by a **person** through the firm's
  approved channel - never by this skill.

## Duplicate-execution prevention

- This skill does **not** build comps/DCF/models/profiles/market pages (upstream) and does
  **not** adjudicate conflicts, run the communications-compliance review, or deliver.
- It consumes approved components and emits a single assembled draft keyed by
  `engagement_id`; re-runs replace the draft rather than creating parallel decks.
