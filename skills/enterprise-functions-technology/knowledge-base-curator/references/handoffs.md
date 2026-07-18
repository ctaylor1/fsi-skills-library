# Adjacent-Skill Handoffs — knowledge-base-curator

Curation (this skill) identifies knowledge-health issues and **drafts** the recommended
fixes. Substantive downstream work — rewriting a policy, composing an answer, analyzing a
control gap or a regulatory change — belongs to other skills. **Applying** a change (publish,
merge, assign owner, retire, delete) is a **human / operations action** in the CMS, not a
skill.

## Downstream (this skill routes to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `policy-document-assistant` | A `review-update` or `conflicting` finding needs the substantive body of a policy/procedure document rewritten | `article_id` + finding + cited source-of-truth |
| `knowledge-answer-composer` | The request is really "answer this question from the KB", not curate it | topic/query + relevant `article_id`s |
| `policy-procedure-gap-analyzer` | A `missing` gap is a policy/procedure control gap, not just an absent article | `topic_id` + coverage evidence |
| `regulatory-change-impact-analyzer` | An article is `stale`/`conflicting` because a regulation changed | `article_id` + source-of-truth delta |

## Human / operations handoffs (no skill executes these)

- **Content owner** — reviews and approves each `review-update`, `merge`, or `assign-owner`
  proposal, then publishes/merges/assigns in the CMS.
- **Records / retention owner** — reviews each `retire` recommendation and performs
  retirement/deletion under the records policy.
- **Knowledge governance** — owns the required-topic registry and adjudicates `ownerless`
  findings and new-topic (`create`) proposals.

## Upstream (feeds this skill)

The KB/CMS export and the controlled-content library populate the article inventory and
metadata; the required-topic registry defines expected coverage. This skill is **interactive**
(`aws-fsi-scheduled-agent: no`); a read-only monitor may *populate* an inventory but must not
curate or act.

## Duplicate-execution prevention

- This skill **does not** rewrite policy bodies, compose answers, or perform gap/impact
  analysis — those route downstream.
- The content owner consumes the `pack_id`/finding rather than re-triaging the KB.
- A `duplicate` links to its canonical for human confirmation; it is never auto-merged here.
