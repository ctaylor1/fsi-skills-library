# Controls — third-party-ai-due-diligence-assistant

- **Risk tier:** R3 — regulated / control decision support. Evidence + a **recommended**
  disposition with mandatory human adjudication. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — a human must adjudicate the recommended disposition before
  any onboarding decision, risk acceptance, contract execution, or inventory/system-of-record
  change. This skill proposes and packages; it never decides.

## Prohibited (fail closed)

- **Any onboarding / approval / rejection decision.** The skill recommends; the third-party
  risk committee / accountable owner decides.
- **Risk acceptance** or issuing a risk waiver on the provider's behalf.
- **Signing, executing, or amending a contract**, or asserting a contract is signed/executed.
- **Recording the outcome** in the model inventory, risk register, or any system of record
  (route to `model-inventory-maintainer` after a human decision).
- **Unsupported/unapproved assertions** — any finding not backed by a bundled, identified
  evidence item, or any claim beyond what the evidence shows.
- **Fabricated or altered evidence**, or a domain/threshold/gate not in the current rubric.
- **Personalized legal advice** on contract terms (flag the clause; route to counsel).

## Package statuses (this skill may set only these)

`draft-assessment` (packageable) | `insufficient-evidence` | `stale-evidence` |
`unsupported-finding` | `needs-data`. It may **not** set `approved`, `onboarded`, `rejected`,
`risk-accepted`, or `closed`.

## Recommended dispositions (decision support only)

`proceed-with-conditions` | `remediate-before-onboarding` | `do-not-proceed`. Each is a
**recommendation for human adjudication** (`human_adjudication_required: true`), never a
decision. `do-not-proceed` is a recommendation against onboarding, not a rejection of the
provider.

## Required output screens (`scripts/validate_output.py`)

- Known provider criticality (or `needs-data`) and a `rubric_version`.
- Allowed status only; no approval/onboarding/closure states.
- Every package sets `human_adjudication_required: true`.
- A `packageable` record has a rubric-valid residual rating, a permitted recommended
  disposition, complete required-domain coverage, and a non-empty, fully **supported**
  findings index (every finding cites a bundled evidence item).
- No autonomous-decision / approval language (regex): `vendor/provider/model is approved|
  onboarded|rejected|cleared`, `approved for production/onboarding`, `risk (has been) accepted`,
  `we accept the residual risk`, `contract (is) signed/executed`, `go-live approved`,
  `no further review/due diligence required`, etc.
- Standing note present: the draft-only / no-decision / no-risk-acceptance disclaimer.

## Residual-risk discipline

- The residual rating is computed deterministically from the risk-flag rubric, finding
  severity, and hard gates (see [domain-rules.md](domain-rules.md)) — explainable inputs, not
  a black box. Any **hard-gate** flag (e.g., unapproved data residency, no incident-notification
  right, no production exit plan, unmanaged concentration) forces `Critical` / `do-not-proceed`.
- A blocked record (missing domain, stale evidence, unsupported finding, unclassified
  criticality) is surfaced with its reason and **never** force-packaged.

## Data classification, privacy, records

- **Confidential.** Provider evidence may include NPI/PII, security detail, and commercially
  sensitive material — apply data minimization; include only what evidences a domain.
- Retain the draft package, the `rubric_version`, evidence citations, the residual-risk basis,
  and the reviewer sign-off with the engagement; log every read and every package produced
  with the analyst identity. Segregation of duties: the assessor drafts; a separate authority
  adjudicates.
