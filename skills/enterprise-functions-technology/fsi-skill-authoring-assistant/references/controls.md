# Controls — fsi-skill-authoring-assistant

- **Risk tier:** R2 — analytical / drafting support. No binding decision. **Action mode:**
  Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — a human must review and authorize before a drafted
  skill package is published, registered, or released into the catalog, or any system of
  record changes. Internal drafting may be reviewer-sampled.

## Prohibited (fail closed)

- **Publishing, registering, releasing, or promoting** a skill into the catalog, or any
  catalog / system-of-record write. This skill drafts only; a human/release pipeline ships it.
- **Self-approval** — marking the drafted package validated, approved, signed off, certified,
  or released. Those are human decisions recorded outside this skill.
- **Unsupported / unapproved claims** — any readiness assertion (validated, reviewed,
  approved) not backed by a recorded approval.
- **Fabricated metadata, sources, evaluations, or approval records**, or an allowed value /
  archetype not in the current build standards.
- **Personalized advice** and **binding regulated decisions** — out of scope; this skill
  authors packages, it does not exercise the authored skill's domain judgment.

## Package statuses (this skill may set only these)

`draft-package` (packageable, ready for owner review) | `metadata-incomplete` |
`missing-components` | `unsupported-claim` | `needs-data`. It may **not** set `released`,
`published`, `registered`, `approved`, `signed-off`, or `certified`.

## Required output screens (`scripts/validate_output.py`)

- Every record uses an allowed drafting status; no release/publish/sign-off state.
- A `packageable` record renders all required template sections, has no missing required
  components, a non-empty frontmatter block, and a passing `metadata_check`.
- Every readiness claim is backed by a recorded approval; the tier's required approvals are
  all enumerated (as owed/pending — never asserted complete here).
- No release / publish / self-approval language (regex): `published to the catalog`,
  `registered the skill`, `released to production`, `signed off by`, `owner-approved`,
  `approved for release`, `ready to ship`, `no further review required`,
  `validated and approved`, `self-approved`, etc.
- Standing note present: the owner-review / no-publish / no-self-approval / approvals-owed
  disclaimer.

## Segregation of duties

Authoring is distinct from **review**, **approval**, and **release**. The same person/skill
must not both draft a package and approve or publish it. This skill produces the artifact and
the checklist of approvals owed; different humans review, approve, and release.

## Data classification, privacy, records

- **Confidential.** Skill specs, domain artifacts, and approval records may reference
  proprietary controls and thresholds; treat as internal. Do not embed customer NPI/PII in a
  drafted package or fixture — use de-identified fixtures under `evals/files/`.
- Retain the drafted plan, the `build_standard_version`, source citations, and the approval
  checklist with the skill; log every read and every plan produced with the author identity.
- Recertify the drafted skill's sources, rules, and tools on the recorded recertification
  date; support rollback via the CHANGELOG and version history.
