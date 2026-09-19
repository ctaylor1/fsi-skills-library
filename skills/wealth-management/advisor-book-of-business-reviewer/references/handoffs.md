# Household handoffs from a book review

This skill owns book-level triage and draft capacity planning. It does not repeat
the household work of the receiving skills or execute their resulting actions.

| Need identified in the book | Receiving skill | Substantive packet |
| --- | --- | --- |
| Household review is due | client-review-preparer | Actual household ID, engagement, due date, source-linked review history, documented signals and open issues. |
| A meeting occurred and follow-up needs drafting | advisor-follow-up-assistant | Actual household meeting evidence and agreed actions; this queue alone is not evidence a meeting occurred. |
| A life event changes goals or cash requirements | household-financial-planning-assistant | Sourced client event, affected goals and known cash needs; preserve missing amounts and dates. |
| Client requests a consolidation or new managed-account discussion | investment-recommendation-evidence-reviewer | Exact client request and interest evidence, current household facts and capacity; no recommendation inferred from a growth task. |
| A relationship is being established | wealth-onboarding-packager | Actual household and engagement facts, source links and unresolved authority or documentation issues. |
| A documented concern may involve exploitation | senior-investor-protection-screener | Exact observations, transaction lifecycle and source dates; no age-based inference or automatic hold. |
| Risk information needs refresh | investment-risk-profile-reviewer | Changed household circumstances and originating evidence; no invented risk appetite. |

For each household action, create a new receiving request with a new request_id,
the **actual household_id** in that row, the applicable engagement and as-of date,
the necessary source registry and source-bound substantive records. Carry the
book artifact_id and action_id as origins and retain unresolved issue origin IDs.
`book:<book_id>` identifies a collection and must never become the receiving client.
Book-level issues with no household ID remain with the practice review owner until
a human determines the affected households; do not choose one automatically.

The receiving skill must validate its own required schema. Preserve the book's
complete source context in the handoff archive; select the minimum necessary client
records for the new input. Map compatible upstream issues to required
`upstream_issues: [{artifact_id, code, message, status, source_ids, resolution?}]`.
If the recipient instead requires `unresolved_issues`, perform an explicit documented
mapping without dropping origin IDs or unresolved status. An empty list is an
explicit reviewed inventory, not a default inferred from omitted evidence.

Incoming household findings should be aggregated with source and originating
artifact references before review. A book-level resolution cannot silently resolve
the originating household artifact. Proposed work allocations never authorize a
send, appointment, reassignment, recommendation adoption or record update.
