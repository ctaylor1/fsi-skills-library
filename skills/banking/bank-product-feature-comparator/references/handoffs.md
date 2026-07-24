# Adjacent-Skill Handoffs — bank-product-feature-comparator

This skill produces a neutral, cited **product comparison** (`request_id`) and the
outstanding **discovery questions** the banker must confirm — then it stops. It never
assesses needs or suitability, and never recommends, ranks, or selects a product. Those are
human decisions and, where a skill exists, adjacent skills.

## Downstream (route the human/banker to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `suitability-reg-bi-reviewer` | The banker/advisor has formed a recommendation and needs it reviewed for customer profile, costs, alternatives, conflicts, and disclosures (Reg BI / suitability). This comparator never forms that recommendation. | `request_id` + comparison + citation index |
| `commercial-cash-management-advisor` | A commercial customer needs treasury/cash-management **services recommended** from operating cash-flow analysis (advisory, needs-based). Out of scope here. | customer context (handled by that skill) |
| `fee-and-charge-reviewer` | The user wants a **specific existing account's** posted fees identified, categorized, and compared to disclosed terms — not a comparison of published product sheets. | account + statement/fee data |
| `customer-onboarding-document-checker` | The customer has (via a human decision) chosen a product and onboarding begins; check the package for required documents and exceptions. | chosen `product_id` |
| `advisor-follow-up-assistant` | After the human decision, draft client-facing meeting notes, action items, and disclosures for advisor approval. | meeting context |

## Upstream (may call this skill)

A relationship banker (or a service/branch workflow) requests a factual side-by-side of two
or more **approved** products during a client conversation. This skill is interactive
(`aws-fsi-scheduled-agent: no`); no scheduled monitor calls it.

## Human / ops handoff (no skill — route to a person)

- **Stale or unapproved product content** (fail-closed): route to the **product-content
  owner / marketing-compliance content-library owner** to refresh, re-approve, or supersede
  the record in the approved catalog. Do not compare against unapproved or stale content and
  do not "work around" the block.
- **A needs or suitability question** the banker cannot answer factually: route to the
  licensed banker/advisor and, for documented recommendations, to `suitability-reg-bi-reviewer`.

## Duplicate-execution prevention

- This skill **compares approved facts and lists discovery questions only**. It must not
  assess needs, judge suitability, recommend/rank, or open a product — those belong to the
  human and the downstream skills above.
- Downstream skills reuse the `request_id` comparison + `citation_index` rather than
  re-pulling and re-comparing product content.
