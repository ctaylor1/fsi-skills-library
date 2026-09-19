# Native input and output contract

Top level: `case_id`, calendar `as_of`, `context` with capacity, represented_party,
object_id, jurisdiction and line_of_business, versioned `sources`, explicit
`unresolved_issues`, optional `upstream_artifacts`, `rule_profile`, and native `data`.
Each source has source_ref and version, with optional source as_of. Duplicate source
IDs reject; distinguish versions explicitly. All domain evidence rows reference the
source registry through source_refs. Missing business amounts are JSON null; numeric
strings or numbers must be finite. Booleans are not monetary numbers.

Rule profile: profile_id, version, source_refs, effective_from, effective_to,
jurisdictions and lines_of_business. The profile is supplied reviewed evidence, not
a built-in legal opinion. Dates must be YYYY-MM-DD. The complete example documents
native field names and supported enums alongside the method reference.

Output: standardized case/context/as_of, source_document, findings, native results,
status, completeness, evaluability, unresolved_issues and insurance artifact. Status
ready-for-review is a draft readiness state only. Null means unknown/unavailable,
not zero. Review findings may exist in an otherwise evaluable draft. No output
selects a professional outcome or executes an action.

## Native `data.tasks` contract

`data.tasks` is an array of task objects. Supply an explicit empty array when tasks
are not yet available; omission also becomes empty and creates a task gap. Null is
not a valid task-list shape. Each task contains:

| Field | Type, values and meaning |
| --- | --- |
| `task_id` | Required unique nonblank string. Duplicate or missing IDs reject. |
| `description` | Practitioner description of the intended work. Retained in the output when supplied; the helper does not infer or enforce investigation completeness from this text. |
| `owner` | Nonblank accountable person/team/role. Missing, null, blank or literal `unknown`/`n/a`/`na` creates an owner gap. |
| `state` | `open`, `in_progress`, `complete`, `waived` or `unknown`; omission becomes `unknown` and a data gap. Other values, including null, reject. |
| `due_date` | Supplied reviewed calendar date. Missing/null creates a deadline gap. Invalid non-null date rejects. |
| `deadline_basis` | `reviewed_rule_profile` or `service_target`. Missing/other values create a gap. The helper does not calculate statutory dates or business-day calendars. |
| `depends_on` | Array of predecessor task IDs. Omission means no supplied dependencies; use `[]` explicitly when there are none. IDs must exist in this task list. Cycles or unknown predecessor IDs reject. |
| `completion_evidence` | Nonblank completion/waiver evidence locator or description, required when state is `complete` or `waived`. Connect its supporting record through source_refs. |
| `source_refs` | Nonempty registered references for the task, state, deadline and any completion evidence. Missing, unresolved or future-dated sources create a gap. |

The top-level reviewed `rule_profile` supplies jurisdiction/line/effective-date
context. A service target does not become a legal deadline merely because it is in
a profile. Scope and rule applicability must be established by the practitioner.
Do not use a boolean completion flag in place of `state` or invent a completion
record to satisfy a dependency.

## Dependency, date and missingness semantics

A predecessor blocks its successor unless its supplied state is `complete` or
`waived` and its completion_evidence is nonblank. A task claimed complete/waived
without that evidence gets `effective_state: unknown`. A complete task whose own
predecessors remain unresolved creates a sequence-review finding; the input is not
silently rewritten. Completion-evidence text is not authenticated by the script.

A task is overdue when `as_of` is strictly later than its due_date and effective
state is neither complete nor waived. Due today is not overdue. A missing deadline
produces `overdue: null`, not false. Dependencies do not hide overdue work. Tasks
sort by due_date, with unknown dates last, then task_id.

## Native results

`task_queue` retains supplied task fields and adds `effective_state`, `blocked_by`
(an array of predecessor IDs), `overdue` and `ready_to_work`. The latter means only
that no supplied predecessor blocks an open/in-progress task; it does not override
an unresolved owner, missing evidence or overall needs-data status. `communications_sent`
is false, `claim_resolution` is `not_determined`, and `deadlines_are` identifies the
supplied-profile/service-target basis. The queue does not perform tasks or contact anyone.
