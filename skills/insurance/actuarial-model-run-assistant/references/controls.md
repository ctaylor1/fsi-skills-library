# Controls — actuarial-model-run-assistant

- **Risk tier:** R2 — analytical/model support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — external delivery of the run requires human sign-off;
  no reserve is ever set or booked by this skill.

## Prohibited (fail closed)
- No **booking or setting of a reserve**; no reserving decision.
- No **certification of reserve adequacy**.
- No **improvised method or invented assumption** (tail factor, selection) outside the config.

## Required output screen (`scripts/validate_output.py`)
- Per-origin `ultimate == latest_diagonal + ibnr` (within tolerance).
- `total_ultimate == Σ ultimate` and `total_ibnr == Σ ibnr` (within tolerance).
- LDFs and CDFs present; a not-computable factor is flagged, not silently zero.
- No reserve-setting/booking/adequacy language (regex: set/book the reserve/reserve is
  adequate/carried reserve/reserve decision).
- Standing disclaimer present.

## Segregation of duties
The run assistant is not the reserving actuary; the run supports, never replaces, the qualified
actuary's selection and booking.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Retain run + triangle reference + assumptions.
- Log read + external-delivery approval.

## Reproducibility
`run_id` binds output to the exact triangle cells and assumption version; the computation is
deterministic and stdlib-only.
