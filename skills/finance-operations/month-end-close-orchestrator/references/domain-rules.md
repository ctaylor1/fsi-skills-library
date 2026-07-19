# Domain Rules — month-end-close-orchestrator

The firm's close policy and its **permissible close-action catalog** (versioned) govern.
Nothing outside the catalog may be planned or executed by this skill.

## Permissible close-action catalog (default)

| Action | Kind | What it does | Evidence required | Reversible? | Authority limit | Approver role |
| ------ | ---- | ------------ | ----------------- | ----------- | --------------- | ------------- |
| `post_accrual_journal` | journal | Post an accrual JE to the GL | `support_schedule` | Yes (reverse JE) | ≤ 250,000 | controller |
| `post_reclass_journal` | journal | Post a reclassification JE | `support_schedule` | Yes (reverse JE) | ≤ 250,000 | controller |
| `post_allocation_journal` | journal | Post an allocation JE | `allocation_basis` | Yes (reverse JE) | ≤ 1,000,000 | controller |
| `certify_reconciliation` | certify | Sign off a completed reconciliation | `reconciliation_ref` + `unresolved_breaks == 0` | Yes (rescind sign-off) | n/a | close-manager |
| `certify_close_task` | certify | Certify a close task complete | `task_evidence` | Yes (rescind sign-off) | n/a | close-manager |
| `lock_subledger` | lock | Lock a sub-ledger for the period | `subledger_ref` | Yes (unlock) | n/a | controller |
| `close_period` | lock | Lock the accounting period | `period_checklist` | Yes (re-open) | n/a | controller |

Actions not listed, journals over the authority limit, irreversible actions, or anything
requiring a policy exception are **out of scope** — fail closed and escalate to a human
authority (controller / CFO delegation).

## Plan-level required approver role

The plan's `required_role` is the **strictest** approver role across its steps
(`controller` > `close-manager`). A plan that contains any journal, `lock_subledger`, or
`close_period` step therefore requires a controller-level approval token, even if it also
contains close-manager-level certifications.

## Dependency and ordering rules

- **`depends_on` forms a DAG.** A dependency cycle or a `depends_on` that references an
  unknown task is rejected; no plan is built.
- Tasks are **topologically ordered** into steps (ties broken by task id for determinism);
  each step records the prerequisite step ids in `depends_on_steps`.
- A **reconciliation may be certified only with zero unresolved breaks**; open breaks route
  to `gl-reconciler` first.
- A **sub-ledger lock / period close may be sequenced and executed only after** all its
  prerequisite steps are verified. `validate_output` rejects a step sequenced or executed
  before its prerequisites.

## Plan requirements (every step)

- **Idempotency key** deterministic from `{plan_id, step_id, action, amount|kind, target}`;
  re-running a step with the same key must be a no-op.
- **Precondition** read from the system of record (period open, account postable,
  reconciliation clean, prerequisites verified) — checked at execute time, not assumed.
- **Expected effect** with a journal amount that ties to the posted delta.
- **Verification** that reads the system of record after the step and compares to expected.
- **Rollback** method that returns the close to the last verified checkpoint.

## Approval binding

- Approval yields a **token** bound to the **plan hash** and the approver's **role**.
- Any change to the plan after approval changes the hash and **voids** the token.
- Execution is permitted **only** with a valid token whose role matches the plan's required
  approver role and whose journal amounts are within the authority limit.

## Post-state verification & rollback

- Verify the **actual** post-state (read the GL / close-task / period-control system) equals
  the expected post-state. On mismatch, **roll back** the step and halt; never continue.
- On partial completion, roll back to the last verified checkpoint so the period is never
  left half-closed.
