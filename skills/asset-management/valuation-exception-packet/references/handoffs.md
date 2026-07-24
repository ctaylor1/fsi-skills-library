# Adjacent-Skill Handoffs — valuation-exception-packet

Exception **investigation/packaging** (this skill), feed **reconciliation** (upstream), and the
**price decision / NAV striking** (downstream, human) are separate control activities with
different entitlements, evidence depth, and outputs. This skill emits a durable `case_id` +
evidence bundle; it must not perform the reconciler's matching or the committee's decision.

## Upstream (feeds this skill)

| Upstream source | When it routes here | Handoff artifact |
| --------------- | ------------------- | ---------------- |
| `investment-vendor-feed-reconciler` | A field-level internal-vs-vendor **price** discrepancy is found | Discrepancy record (both marks + as-of times) |
| `investment-data-quality-exception-detector` | A feed-level stale/absent/implausible **price** signal is raised | Flagged instrument + signal |
| `nav-preparation-tie-out` | A price issue/break surfaces during NAV tie-out | Instrument + break context |

These upstreams **surface** candidates; they do not choose canonical values. This skill
investigates and packages them for adjudication.

## Downstream (this skill hands to — human adjudication)

| Downstream (human) | When | Handoff artifact |
| ------------------ | ---- | ---------------- |
| **Valuation Committee** | Any `exception-confirmed` case needing a price decision | `case_id` + cited evidence bundle + `recommended_next_step` |
| **Fund accounting / NAV oversight** (working `nav-preparation-tie-out`) | Once the committee resolves the price, NAV tie-out/striking proceeds | Adjudicated price + `case_id` reference |

Price selection/override and NAV certification/striking are **human** decisions — no skill in
the catalog makes them, so these are human/ops handoffs, not skill-to-skill routing.

## Duplicate-execution prevention

- This skill **does not** reconcile feeds (that is `investment-vendor-feed-reconciler`) or
  run feed-wide detection (`investment-data-quality-exception-detector`); it investigates a
  named instrument's price and packages evidence.
- It **does not** choose the canonical value or certify NAV — those stay with the human
  committee and fund accounting.
- The committee and `nav-preparation-tie-out` consume this skill's `case_id`/bundle rather than
  re-investigating; the deterministic `case_id` prevents duplicate cases for the same
  instrument/date.
