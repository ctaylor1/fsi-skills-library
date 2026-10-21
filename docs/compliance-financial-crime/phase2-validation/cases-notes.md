# Phase 2 case, diligence, sanctions and reporting packages

Implemented 2026-10-03 within the root-authorized Phase 2 task. No commits, external
messages, filing, notifications, customer/account actions or system-of-record writes.

## Delivered jobs and native modes

| Package | Version | Native object type / mode |
|---|---|---|
| financial-crime-case-investigator | 0.1.0 | financial_crime_case |
| sanctions-exposure-reviewer | 0.1.0 | sanctions_exposure |
| financial-crime-information-sharing-reviewer | 0.1.0 | information_sharing_review |
| financial-crime-reporting-reviewer | 0.1.0 | financial_crime_reporting |
| compliance-regulatory-notification-reviewer | 0.1.0 | regulatory_notification |
| customer-due-diligence-reviewer | 0.2.0 | customer, explicit mode=lifecycle |
| enhanced-due-diligence-assessor | 0.2.0 | customer, explicit mode=substantive |

CDD/EDD original validators and producers were preserved as `legacy_validate_input.py`
and `legacy_calculate_or_transform.py`, with public `compute` / EDD `package` dispatch
and legacy fixture/selftest paths retained. Original packages were not reinitialized.
Phase 2 uses the source-bound root foundation contract; root owns canonical helpers,
portable resource pins, common adapter registration, catalogs and router integration.

All seven carry SKILL, source map + exact URL/status JSON, domain rules, controls,
handoffs, input/output schemas, template, native domain method/calculator/validators,
meaningful regression suite, executable evals, synthetic input/golden/tamper fixtures
and changelog. Bundled helper copies were refreshed from root canonical resources.

## Meaningful native behavior verified

- Case investigation is distinct from scenario replay. Exact sourced entity/account IDs,
  account→entity relationships, transaction IDs, endpoints, currencies and dates bind the
  graph. Unknown/mismatched identity withholds dependent amounts. Each unique transaction
  is counted once; internal transfers remain internal and proceeds remain unknown.
  Decimal precision is sized from supplied coefficient/exponent ranges; a 40-digit
  amount and currency totals remain exact. Hypotheses, counterevidence, chronology and
  unexecuted investigative questions remain separate from facts and human disposition.
- Sanctions supports an explicitly accepted OFAC direct blocking ownership method only.
  Source-bound owner IDs/stakes/completeness prevent duplicate attribution. Exactly50%
  is recognized, but no transaction clearance is given. Indirect, foreign, sectoral or
  incomplete unsupported exposure remains unknown. Authorization scope/date/conditions
  are source-bound observations for human review, not an authorization decision.
- Sharing binds actual content kinds, recipient, purpose, legal basis, eligibility,
  registration, security and exact permission content scope. Ordinary314b excludes SAR
  material/existence. Joint-SAR authority is distinct, requires actual participant and
  content-bound permission evidence, and uses restricted authorized-FIU native handling.
  Unnecessary or unsupported items are withheld; nothing is sent.
- NonSAR reporting binds event identity, membership, exact currency amounts, explicit
  applicable obligations, comparison method, period, deadline/channel, obligation-scoped
  exception facts and acknowledgment receipt/status/identity/date. Duplicate event
  membership cannot double count amounts. No FX, calendar default, filing or SAR substitute.
- Notifications bind regulated entity/activity/event, awareness chronology, source-bound
  all/any materiality method/criteria, timing and channel. Immediate becomes urgent human
  review without an invented deadline. Prudential, payments and exam-response methods
  retain their adjacent owners; no notification is made.
- CDD lifecycle computes due dates only from sourced explicit anchor/cadence, compares
  current/prior policy-material fields, reviews same-currency expected/observed activity,
  declared ownership/control coverage and review-control evidence, and proposes unexecuted
  remediation. Missing evidence never becomes a benign result.
- Substantive EDD reconciles SoF/SoW claims and unique corroboration, preserves chronology,
  compares sourced economic activity/capacity/basis, surfaces hypotheses/counterevidence,
  and evaluates design/operating sample evidence. Residual risk remains Unknown without
  a separate accepted sourced method, band labels, required control IDs and assessed
  operating evidence; unresolved issues, capacity gaps or mismatched controls prevent
  downgrade. Legacy EDD assembly remains Unknown.
- Applicable-method acceptance source-binds method ID/version, jurisdiction, institution,
  purpose, dates and approval status. A changed approval-status or role string does not
  establish accepted methodology. Exact detached reconstruction rejects added narrative,
  approval/action claims, rehashing and changed originals. Inherited issues/access remain.

## Fresh primary sources

Source maps record exact URLs, source type/status and retrieval date 2026-10-03. Key updates:

- [FinCEN FIN-2026-R001](https://www.fincen.gov/system/files/2026-02/FinCEN-Order-CCDExceptiveRelief.pdf)
  retains risk/reliability-triggered beneficial-owner updates while providing relief from
  every-account reacquisition; institutional applicability/adoption remains human-owned.
- [FinCEN June12 2026 314b fact sheet](https://www.fincen.gov/system/files/shared/314bfactsheet.pdf)
  supersedes the December2020 fact sheet. Ordinary314b and joint-SAR sharing are distinct;
  foreign safeharbor coverage and other privacy law need separate review.
- [OFAC FAQ401](https://ofac.treasury.gov/faqs/401),
  [FAQ398](https://ofac.treasury.gov/faqs/398) and
  [FAQ5 updated September9 2026](https://ofac.treasury.gov/faqs/5)
  support regime-specific scope boundaries rather than universal sanctions outcomes.
- FFIEC current CDD/private-banking/SAR/CTR manual pages, FinCEN filing resources and
  FCA SUP15.3/current form/operational incident pages anchor distinct workflow boundaries.
  Future FCA operational incident rules effective2027-03-18 are not current obligations.

No approved deployment jurisdiction law profile is fabricated or bundled.

## Executed verification

- Seven Phase 2 suites: **83 tests passed** (11 case;12 sanctions;11 sharing;13 reporting;
  11 notification;12 CDD;13 EDD).
- Preserved Phase 1 CDD/EDD suites: **48 tests passed** (24 each).
- Every declared executable eval command in the seven packages: **45/45 passed**, including
  original legacy commands, exact fixtures and expected tamper rejection. See
  `cases-native-evals.json` and `cases-native-evals.log` for command/result/latency evidence.
- Actual repository `tools/validate_skills.py` against all seven: **0 errors,0 warnings**.
- Skill-creator bundled `quick_validate.py` was attempted but rejects the repository's
  supported `compatibility` frontmatter key. Repository METADATA-SCHEMA explicitly requires
  preserving that field; this validator incompatibility is recorded, not hidden by editing
  valid package metadata. The actual repository validator passed.

Executable deterministic tests are distinct from unexecuted model activation/routing,
privacy/prompt-injection and real-model latency/cost scenarios. These bounded checks
establish source-value consistency, exact computation and control behavior, not source
truth, legal applicability/approval, practitioner acceptance, licensed access or deployment
readiness. Independent forward and repository integration verification are root-owned.
