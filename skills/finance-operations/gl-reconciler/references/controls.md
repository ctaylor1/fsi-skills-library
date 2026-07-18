# Controls — gl-reconciler

- **Risk tier:** R2 — analytical / drafting. **Action mode:** Draft-only; no system-of-record
  change.
- **Human approval:** `external-delivery` — required before the reconciliation or any proposed
  correction is delivered externally or written to a system of record. Internal analytical use
  may be reviewer-sampled.

## Prohibited (fail closed)

- **No posting.** The skill never posts, books, or writes a journal entry to the general
  ledger or any subledger. Corrections are **proposals only** (`status: "PROPOSED"`).
- **No forced tie.** No plug, netting, or suppression of breaks to make a reconciliation
  appear to tie. If classified breaks do not explain the difference, surface the residual.
- **No adjudication.** The skill does not decide which side (GL or subledger) is correct, nor
  approve its own proposed corrections.
- **No per-reconciliation threshold tuning.** Tolerances, materiality, and the suspense
  account come only from the versioned `config`.
- **No account action** implied by a break (freeze, write-off, close) — those are human
  decisions.

## Required output screens (`scripts/validate_output.py`)

- **Tie-out:** `sum(break gl_impact) == gl_total − subledger_total`, `residual == 0`, corrected
  GL agrees to subledger after proposed corrections (documented timing items excepted).
- **Break taxonomy:** every break's `type` is in the fixed set
  {`timing_difference`, `amount_mismatch`, `unrecorded_in_gl`, `unsupported_in_gl`,
  `duplicate`} with an id, amount, and material flag.
- **Lineage:** every break cites its GL/subledger source rows (`gl:` / `subledger:` prefix).
- **Idempotency:** `reconciliation_id` is derived from `entity/account/as_of/input_fingerprint`
  with no timestamp/random component; `input_fingerprint` is a 64-hex content hash.
- **Proposed-only:** every correction has `status: "PROPOSED"`, is balanced (dr == cr), and its
  net offsets the break; no posting-completed language anywhere.
- **Disclaimer:** the standing no-posting disclaimer is present.

## Segregation of duties

- The skill **prepares** the reconciliation and **proposes** corrections. A different,
  authorized human (controller / senior accountant) **reviews, approves, and posts** in the
  ERP. Preparation and posting must not be the same actor.
- The reconciliation preparer is not the correction approver.

## Data classification, privacy, records

- **Confidential (financial records).** No customer NPI is required for GL reconciliation;
  minimize any counterparty detail to what evidences a break.
- Retain the reconciliation, breaks, lineage, proposed corrections, and `config_version` per
  records policy; log the read and any external-delivery approval.

## Reproducibility

`reconciliation_id` + `input_fingerprint` bind the output to the exact inputs and config
version; re-running the same inputs reproduces the same breaks, corrections, and tie-out.
