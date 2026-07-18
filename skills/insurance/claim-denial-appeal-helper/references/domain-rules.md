# Domain Rules — claim-denial-appeal-helper

How denial reasons map to **supporting evidence**, how the **appeal deadline** is computed,
and how **readiness** is derived. The reason→evidence checklist and the appeal window are
configuration (versioned, owned by the plan/benefit team), not fixed judgments, and are
overridable per plan/jurisdiction via `doc["config"]`. The denial notice's stated appeal
rights and the governing plan document take precedence over these defaults.

## Denial reason → supporting-evidence checklist (default config)

| Reason code | Typical supporting evidence a well-formed appeal attaches |
| ----------- | --------------------------------------------------------- |
| `not_medically_necessary` | clinical_notes, physician_letter, clinical_guidelines |
| `experimental_investigational` | physician_letter, peer_reviewed_literature, specialist_attestation |
| `out_of_network` | network_adequacy_proof, referral_or_authorization, emergency_documentation |
| `prior_authorization_missing` | retro_auth_request, urgency_attestation, provider_attestation |
| `coding_error` | corrected_claim, coding_documentation, medical_records |
| `benefit_exclusion` | plan_document_excerpt, physician_letter |
| `not_covered_service` | plan_document_excerpt, physician_letter |
| `timely_filing` | proof_of_timely_submission, clearinghouse_report |
| `duplicate_claim` | proof_of_distinct_service, medical_records |
| `coordination_of_benefits` | primary_eob, other_insurance_details |
| `eligibility` | proof_of_coverage, enrollment_confirmation |

Unknown reason codes fall back to a generic checklist (`denial_notice`, `medical_records`,
`physician_letter`) and are flagged by `validate_input`. The checklist describes what a
complete appeal record *contains*; it is **not** a statement that the service should be
covered.

## Evidence gaps and argument scaffolding

- For each reason, evidence present in the bundle is matched against the checklist; the
  remainder are **gaps**.
- An **argument point is drafted only when cited evidence backs it.** A reason with no
  matching evidence yields an empty `argument_points` and appears in the gap list only — the
  package never argues around missing evidence.

## Appeal deadline (deterministic, administrative)

- `appeal_deadline = denial_date + appeal_window_days` (window from the denial notice / plan
  config; a common internal-appeal window for ERISA group health plans is 180 days, but
  always use the value stated on the notice).
- `days_remaining = appeal_deadline - as_of`.
- `deadline_status`: `past_due` if `days_remaining < 0`; `due_soon` if
  `0 ≤ days_remaining ≤ due_soon_days` (default 30); otherwise `open`.

This is arithmetic on stated dates, not a legal opinion on whether a late appeal can still be
accepted. When the window appears closed, flag it prominently and route the timeliness
question to the plan's process or a licensed attorney.

## Readiness mapping (deterministic)

| Readiness | Rule |
| --------- | ---- |
| `ready_to_draft` | No evidence gaps across any reason |
| `gaps_present` | Any reason has ≥1 evidence gap |

Readiness describes the **completeness of the evidence package**, never the likely outcome.

## Appeal levels (informational)

Internal level-1 → internal level-2 (where offered) → independent external review (IRO).
The package notes the requested `appeal_level`; it does not decide which level applies or
escalate on its own.

## Hard boundaries (fail closed)

- Never assert the claim/service **is** covered, that coverage applies, that the member is
  eligible, or that the denial is invalid — that is the insurer's or external reviewer's
  determination.
- Never give **legal advice** or assess litigation/bad-faith exposure — refer to a licensed
  attorney.
- Never **guarantee** an outcome or state the appeal will be overturned.
- Never **file or submit** the appeal, and never state that it has been filed.
