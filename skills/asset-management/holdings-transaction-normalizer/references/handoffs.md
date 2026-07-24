# Adjacent-Skill Handoffs — holdings-transaction-normalizer

This skill produces a **canonical pack** (`job_id`) with lineage, plus a **rejected-record
queue**, and stops. It does not resolve identities, choose canonical values, reconcile, or tie
out NAV — those are distinct skills with distinct entitlements.

## Downstream / route-to (all exist in `catalog/skills-catalog.json`)

| Skill | When (which reject code or request) | Handoff artifact |
| ----- | ----------------------------------- | ---------------- |
| `security-master-enricher` | `AMBIGUOUS_IDENTITY` reject, or a request to merge/resolve identities or create a master security | reject rows + both source records (never pre-merged) |
| `investment-vendor-feed-reconciler` | Sources disagree on a *value* (price, rating, attribute, corporate-action term) and the user wants the canonical value chosen | the differing canonical records + `job_id` |
| `investment-data-quality-exception-detector` | Detect stale prices, implausible moves, duplicate instruments, broken mappings across feeds | canonical records + `job_id` |
| `position-cash-reconciliation-assistant` | Match internal positions/cash to custodian/prime-broker/administrator and classify breaks | canonical positions/cash + lineage |
| `nav-preparation-tie-out` | Tie out positions/prices/accruals/cash across books, custodian, and administrator | canonical records + `job_id` |

## Upstream (may call this skill)

Investment-data operations pipelines and fund-operations analysts call this skill to standardize
multi-source extracts **before** reconciliation or NAV work. Raw source extraction itself is a
read-only feed operation, not a separate skill in this library.

## Duplicate-execution prevention

- This skill normalizes **shape and codes** only; it must not resolve identities, select canonical
  values, reconcile, or tie out — those belong to the skills above.
- Downstream skills consume the canonical records + lineage keyed by `job_id`; they do not re-run
  normalization.
- The reject queue's `reason_code` names the correct owner, so a conflict is routed once, to one
  place, without this skill attempting the resolution itself.

> Handoff fidelity: every skill named here is present in `catalog/skills-catalog.json` (Wave 5,
> 2026 industry-expansion cohort). Reason codes route to a human/next skill; they are never a
> disposition made by this skill.
