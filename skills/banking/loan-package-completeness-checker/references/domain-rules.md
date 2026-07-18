# Domain Rules — loan-package-completeness-checker

Completeness **checks**, their **severity**, and how severities map to a **readiness
disposition**. Required documents, validity windows, required signers, and the severity
mapping are **configuration** (versioned, owned by credit/closing operations per product and
jurisdiction), not hard-coded judgments, and never tuned to an individual file. The firm's
loan policy, product guide, and applicable federal/state closing requirements take precedence.

## Check taxonomy

| Check | Fires when | Default severity | Evidence attached |
| ----- | ---------- | ---------------- | ----------------- |
| `missing_document` | A **required** applicable checklist item has no matching document | Blocker | Checklist item id |
| `optional_document_absent` | A **non-required** checklist item has no matching document | Advisory | Checklist item id |
| `missing_signature` | A present document is missing a required signer party (not `signed`) | Blocker | Document id + party |
| `expired_document` | `as_of - effective_date > validity_days` for a present document | Blocker | Document id + effective date |
| `nearing_expiry` | Still valid but within `nearing_expiry_days` of the limit | Advisory | Document id + days remaining |
| `field_inconsistency` (money) | A `loan_amount` / `note_rate` / `term_months` field disagrees with `expected_terms` | Blocker | Offending document(s) |
| `field_inconsistency` (identity) | A `borrower_name` / `property_address` field disagrees with `expected_terms` | Exception | Offending document(s) |
| `exceeds_approved_amount` / `exceeds_approved_rate` | A document amount/rate exceeds the approval envelope | Blocker | Document + approval |
| `approval_missing` / `approval_expired` | No granted approval, or approval expired before `as_of` | Blocker | Approval record |
| `open_condition` (prior_to_close) | An outstanding `prior_to_close` condition | Blocker | Condition id |
| `open_condition` (other / waived) | Any other outstanding condition, or a condition marked `waived` | Exception | Condition id |

Checks are **independent and additive**; each firing check is reported with its own evidence.
There is no opaque composite "completeness score" — the readiness disposition is a
deterministic function of the finding severities.

## Severity meaning

- **Blocker** — the package cannot be certified until resolved (missing/expired required doc,
  missing required signature, money-term mismatch, approval breach, prior-to-close condition).
- **Exception** — must be reviewed and documented by the certifier, who may adjudicate it
  (identity/address mismatch, outstanding non-prior-to-close condition, marked waiver).
- **Advisory** — informational; does not affect readiness (optional doc absent, nearing expiry).

## Readiness mapping (deterministic, documented)

| Disposition | Rule |
| ----------- | ---- |
| **Not-ready (blockers present)** | >= 1 Blocker fired |
| **Conditional (exceptions to adjudicate)** | 0 Blockers and >= 1 Exception |
| **Complete (ready for human certification)** | 0 Blockers and 0 Exceptions |

Readiness is a **completeness recommendation for a human certifier**. It is never a lending
decision, a clear-to-close, or a certification.

## Hard boundaries (fail closed)

- Never state or imply a **credit decision** (approve/deny), a **clear-to-close**, an
  **adverse action**, or a **certification** — describe completeness factually and attribute
  every decision to the human certifier.
- Never **waive or clear** a condition, or **certify / close / fund / book** the loan.
- Never infer a required-document set when the checklist is absent; never tune validity
  windows or required signers to the individual file.
- Consistency findings describe **disagreements**, not the correct value — the certifier
  reconciles them against the source of record.

## Configuration notes

- `validity_days` per document type, `needs_signatures` per item, and the per-jurisdiction
  applicability list all live in the versioned checklist (`checklist_version`).
- `nearing_expiry_days` (default 30) controls the Advisory warning window.
- The money vs identity field split is fixed in the engine
  (`MATERIAL_FIELDS` / `IDENTITY_FIELDS` in `scripts/calculate_or_transform.py`).
