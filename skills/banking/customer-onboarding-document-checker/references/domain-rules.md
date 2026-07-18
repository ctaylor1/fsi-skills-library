# Domain Rules — customer-onboarding-document-checker

Deterministic **completeness checks** for an onboarding package and how the fired findings
map to a **package-readiness band**. The required-document checklist, key identity fields,
staleness/expiry thresholds, and severities are **configuration** (versioned, owned by
banking product & credit operations), not hard-coded judgements, and are never tuned to an
individual. Jurisdiction/product packs (e.g., US CIP document requirements) take precedence
as configured.

## Required-document checklist (default config: individual / consumer-deposit / US)

| Required type | Signature required | Expiry checked | Max age (days) |
| ------------- | ------------------ | -------------- | -------------- |
| `government_id` | no | yes | — |
| `proof_of_address` | no | no | 90 |
| `tax_certification` | yes | no | — |
| `signature_card` | yes | no | — |

Business customers, other products, and other jurisdictions load a different checklist from
config; the engine reads whatever `config.required_documents` supplies.

## Check taxonomy

| Check | Fires when | Severity | Evidence attached |
| ----- | ---------- | -------- | ----------------- |
| `missing_required_document` | A required type has no `provided` document | blocking | Required type + present statuses + config ref |
| `expired_document` | Expiry-checked doc has `expiration_date` < `as_of` | blocking | Doc + expiration date |
| `expiring_soon` | Expiry-checked doc expires within `expiring_soon_days` (default 30) | advisory | Doc + expiration date |
| `missing_signature` | Signature-required doc has `signature_present == false` | blocking | Doc |
| `illegible_document` | A required doc is `provided` but marked `illegible` | blocking | Doc |
| `stale_document` | Doc `issue_date` older than the type's `max_age_days` | blocking | Doc + issue date |
| `data_inconsistency_key` | A **key identity field** (name, DOB) differs across the applicant record and/or documents | blocking | Each differing value + source |
| `data_inconsistency_other` | A non-key field (e.g., address) differs across sources | advisory | Each differing value + source |
| `unresolved_exception` | Any onboarding exception has `status == open` | blocking | Each open exception |

Checks are **additive and independent**; the output reports each that fired with its own
evidence. There is no opaque composite "onboarding score".

## Readiness mapping (deterministic, documented)

| Readiness status | Rule |
| ---------------- | ---- |
| **Ready** | No check fired |
| **Ready-with-advisories** | Only advisory checks fired (e.g., expiring-soon, non-key mismatch) |
| **Not-ready** | ≥1 **blocking** check fired |

`readiness_status` is a **completeness state for a human reviewer**, not an onboarding
approval, an identity verification, or a KYC/CIP determination. "Ready" means the documents
are present, current, signed, and internally consistent — it does **not** mean the customer
is approved or verified.

## Hard boundaries (fail closed)

- Never state or imply the package is **approved**, the applicant is **verified / cleared /
  eligible to onboard**, or the account may be **opened**.
- Never make a **KYC / CIP / sanctions / PEP** determination ("KYC passed", "no sanctions
  match", "not a PEP") — describe the open exception factually and route it.
- Never **waive** a required document, signature, or exception — that is an approval action.
- Never take or recommend an **account action** (open, activate, fund).
- Never tune the checklist, thresholds, or severities to the individual; use the versioned
  config only.
- `data_inconsistency_*` describes a **field mismatch to reconcile**, not fraud or intent.

## Remediation prompts (always include for fired findings)

Each fired finding carries a plain remediation action (obtain the missing/legible document,
obtain the unexpired document, obtain the required signature, reconcile the mismatched field
with the customer, resolve or route the open exception). The report invites the onboarding
specialist to remediate and re-run, or to route substantive screening to the compliance
skills in `references/handoffs.md`.
