# Domain Rules — policy-wording-comparator

How wording **findings** are classified for materiality and mapped to a **review track**. Thresholds
and clause taxonomies are configuration (versioned, owned by the product / compliance team), not
per-form judgements, and are never tuned to reach a desired answer. A licensed human adjudicates the
coverage, compliance, and filing questions the findings raise.

## Finding types

| Finding type | Fires when | Evidence attached |
| ------------ | ---------- | ----------------- |
| `added` | A `clause_id` is present in the subject form but not the baseline | Subject clause |
| `removed` | A `clause_id` is present in the baseline form but not the subject | Baseline clause |
| `modified` | Same `clause_id` in both, but the `text` differs (text-change ratio recorded) | Both clauses |
| `dangling_reference` | A subject clause `references` a term/clause not defined or present in the subject form (a **conflict**) | Subject clause |
| `missing_required_clause` | A `required_clause_types` entry has no clause of that type in the subject form (a **gap**) | The requirement |

Alignment is by stable `clause_id`. Unchanged clauses are counted but not reported as findings.

## Materiality (deterministic)

- A change to a clause whose `clause_type` is in the **material set** is `material`:
  `insuring_agreement`, `exclusion`, `condition`, `condition_precedent`, `definition`, `limit`,
  `sublimit`, `deductible`, `coverage_trigger`, `cancellation`, `subrogation`, `other_insurance`.
- A `modified` clause of any other type is `material` when its text-change ratio
  `>= material_text_change` (default **0.15** = 15% of the wording changed by `difflib` ratio).
- `dangling_reference` and `missing_required_clause` are always `material` (conflicts and gaps).

## Escalation (deterministic)

A material finding also `escalate`s when **any** of:

- its `clause_type` is in the **escalation set**: `insuring_agreement`, `exclusion`, `limit`,
  `sublimit`, `deductible`, `coverage_trigger`, `condition_precedent`; **or**
- it deviates from a **filed / approved** baseline (`filed_deviation`) — the subject changes a
  material clause relative to a form of record, raising a filing-review question; **or**
- it is a `dangling_reference` (conflict) or `missing_required_clause` (gap).

## Review-track mapping (deterministic, documented)

| Suggested track | Rule |
| --------------- | ---- |
| **No material changes** | No `material` findings |
| **Standard review** | One or more `material` findings, none of which `escalate` |
| **Legal/compliance review required** | Any `escalate` finding (escalation clause type, filed-form deviation, conflict, or gap) |

The track is a **triage suggestion for a human reviewer**. It is not a coverage determination, a
compliance sign-off, an approval to file, or a review closure, and it never files, approves, or binds
a form.

## Reviewer questions

Each material finding produces a neutral reviewer **question** (e.g., "Exclusion `C-EXC-3` was added
in the subject form — confirm the intended narrowing of coverage and the filing implications."). The
skill asks; it does not answer the coverage/compliance/filing question itself.

## Hard boundaries (fail closed)

- Never state or imply that coverage **applies / is granted / is denied**, or that an exclusion does
  or does not apply.
- Never state a form **is compliant**, certify compliance, approve a form, clear it **for filing**,
  say it is **ready to file**, file it, or bind coverage.
- Never **close the review** or state that no further review is required.
- Never tune materiality thresholds to the individual form or deal; use only the versioned config.
- `filed_deviation` raises a **filing-review question**; it is not a statement of (non-)compliance.
