# Source Map — gl-reconciler

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **ERP / General Ledger** (position of record for the GL side) | GL account balance + detail entries being reconciled | Read-only |
| 2 | **Subledger / source system** (AP, AR, bank, fixed assets, payroll, etc.) | The supporting detail the GL control account must agree to | Read-only |
| 3 | **Consolidation / FP&A** | Elimination and mapping context for intercompany or consolidated accounts | Read-only |
| 4 | Reconciliation **config** (versioned) | Matching keys, tolerances, materiality threshold, suspense account | Read-only |
| 5 | Prior-period **reconciliation** (durable `reconciliation_id`) | Carry-forward of open reconciling items | Read-only |

The GL and the subledger are **two independent positions of record**; neither is subordinate
to the other. A break is a disagreement between them — the skill classifies and evidences it,
it does not decide which side is "right" or overwrite either. If a source assertion conflicts
with the recorded entry, cite both and flag for the reviewer.

## Input schema (validated by `scripts/validate_input.py`)

Top level: `entity`, `account`, `as_of` (YYYY-MM-DD), `config_version`, `currency`,
`gl_entries[]`, `subledger_entries[]`, `config{}`.

Each record (`gl_entries[]` / `subledger_entries[]`):
`entry_id` (unique across the job), `match_key`, `account`, `date` (YYYY-MM-DD),
`amount` (signed, in the account's natural sign), `currency`, `source_ref`, `description`.

`config`: `amount_tolerance`, `date_tolerance_days`, `materiality_threshold`,
`recon_suspense_account`.

## Citation format

`{system}:{source_ref}@{date}` — e.g. `gl:gl;je=JE-5002;ln=1@2026-06-29` and
`subledger:subledger;bank;stmt=JUN;ln=12@2026-06-29`. Every break carries lineage citations
to the GL and/or subledger rows it was derived from.

## Freshness / effective dates

- `config` (tolerances, materiality, matching keys, suspense account) is a **versioned
  contract**; the output records `config_version` so a reconciliation is reproducible.
- `as_of` fixes the cutoff. Timing differences are one-period reconciling items expected to
  clear next period; they are documented, not corrected.
- `input_fingerprint` (a content hash of the normalized inputs + config) makes the
  `reconciliation_id` a pure function of the inputs — re-running the same inputs is idempotent.

## Least-privilege operations (deployment)

- `gl.read(entity, account, from, to)` → bounded, paged GL detail rows.
- `subledger.read(entity, account, from, to)` → bounded, paged subledger detail rows.
- `config.get('gl-recon', version)` → tolerances, materiality, matching keys, suspense account.
- `recon.get(reconciliation_id)` → prior-period open items for carry-forward.

All read-only, deterministic, durable `reconciliation_id`, below the fixed timeout; page long
histories as resumable stages. **No write/post operation is bound to this skill** — proposed
corrections are handed to an authorized human/system to post.
