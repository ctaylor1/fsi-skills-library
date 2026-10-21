# Compliance & Financial Crime Phase2 verification — 2026-10-03

**Implementation and bounded automated verification are complete.** Nineteen new
professional workflow packages and substantive CDD/EDD modes are installed. The
catalog has 351 packages in 15 categories; CFC has 34 packages including its router,
with adjacent privacy retained in Data, AI & Model Governance. The router exposes 37
declared intents, including a primary route for each new or expanded Phase2 job.
See [implementation scope](../PHASE2-IMPLEMENTATION.md) and the
[support matrix](../SUPPORT-MATRIX.md).

These are offline supplied-evidence methods. All results remain human-review drafts,
with no source authentication, professional/legal/institutional acceptance or
production deployment established. The checks do not evaluate real-model skill
activation, document extraction, narrative quality or operational decision quality.

## Final automated checks

All checks ran after method, fixture, instruction and companion-schema repairs and
package-manifest synchronization. [final-checks.json](final-checks.json) records
commands, exit codes and logs.

| Check | Final result |
| --- | --- |
| Repository tests | 656 passed |
| Whole-library executable skill evaluations | 2,039 passed; zero failed |
| Isolated installation | 228 command checks passed across 36 packages |
| Focused package regressions included in isolated execution | 721 passed |
| Structure/metadata | 351 packages; zero errors and warnings |
| Adjacent skill references | Zero dangling references |
| CFC ownership, migrations, scope and routes | Zero errors |
| CFC, investment and workflow resources | Synchronized |
| Adjacent Asset Management ownership | Passed |
| Catalog regeneration from current approved records | 351 packages; byte-idempotent |
| Diff whitespace check | Passed |

The 36 isolated installations cover CFC, adjacent privacy and the retained Capital
Markets communications specialist. Each package is copied alone, without sibling
runtime imports or a repository PYTHONPATH. Native runtime remains standard-library
Python 3.10+; PyYAML 6.0.3 and jsonschema 4.26.0 are temporary verification dependencies.
The verification process prepended its Python environment to PATH for legacy commands.
No external build-plan workbook was reconciled.

[source-freeze.json](source-freeze.json) covers **6,874 files** in skills, shared
resources, catalog and tools. Every hash matched after the final suites. Root status
prose and validation archives are excluded from this runtime-source inventory.
[preservation-check.json](preservation-check.json), reproducible with
[verify-preservation.py](verify-preservation.py), compares the initial dirty-checkout
baseline: **12,991 protected existing files are unchanged**, including all 28 Phase1
validation files. No new file outside the declared Phase2 edit scope was found.
The baseline is retained in [checkout-baseline.json](checkout-baseline.json).

## Independent forward evidence

The three suites retain raw synthetic scenarios, expectations recorded before
execution, actual installed commands, detached inputs, results and source hashes.
Their counts describe different assertions and commands; they are not added together
as unique professional cases or independent acceptance votes.

| Suite | Final measured result | Evidence limits |
| --- | --- | --- |
| Primary CDD/EDD, investigation, promotion, testing and remediation | 60/60 current command checks; 14/14 reconstructions and 14/14 tamper rejections; seven output-schema checks | Original 44 assertions remain 40 exact passes and four withheld quantitative expectations. Two separate EDD amendments satisfy seven retained EDD assertions. |
| Governance, sanctions, information sharing, reporting and notification | 20 cases; 60/60 command checks; 150/150 expectation checks | Supplied profiles, sources and institutional authority remain unverified. Original notification failures are retained. |
| Information barriers, ABC, misconduct and customer outcomes | 28 cases; 89 installed CLI calls; 211/211 bounded assertions; five altered outputs rejected | Eight unchanged floating-threshold intakes remain incomplete for criterion comparison; they are not credited as successful prior positive/negative comparisons. |

Read the [primary final replay](forward/final-replay/assessment.md),
[governance replay](forward-governance/post-repair-replay/replay-assessment.md) and
[conduct final replay](forward-conduct/final-replay/REPORT.md) for exact outcomes.
The original primary CLI expectations remain literal: 50/54 match, two CDD stages now
reject copied receipt provenance, and two output stages are skipped after rejection.
This historical comparison is distinct from the passing current 60-command contract.

The original EDD intakes omit economic-event identity and additivity; totals and
differences now remain unknown. Separate amendments add explicitly sourced synthetic
workpaper assertions, grounded in retained amounts, dates and descriptions. Removing
those additions exactly reproduces each original intake. With the added evidence,
two distinct sale receipts total 375000.00, multiple documents for one receipt count
once, corroborated wealth is 900000.00 and the 300000.00 gap remains visible. Residual
risk remains Unknown. These are supplied assertions, not authenticated bank evidence.

The customer-outcomes amendment takes an exact decimal string from the retained raw
numeric lexeme and supplies a separate matching source fact. A threshold string
`"0.33333333333333333334"` is above exact one third; `"0.3333333333333333"` is below it.
Fractional JSON numeric thresholds remain valid partial intake with comparison
withheld. Compatible unique-customer numerator, denominator and population units
are required. Missing units or mixed event/customer units withhold proportions.

## Companion schemas and retained findings

[casework-schema-repair-audit.json](casework-schema-repair-audit.json) validates all
14 published Phase2 JSON companions using Draft 2020-12 with date format checking:
36 intakes and 34 native outputs pass; 78 authority/context/type negatives reject.
The CDD/EDD JSON companions explicitly cover their Phase2 modes. Their retained
legacy native validators and regression suites establish legacy compatibility.
JSON conformance supplements exact detached native reconstruction; it does not
replace native validation or establish source truth.

The [final independent governance schema audit](forward-governance/final-schema-replay/final-assessment.md)
passes eight intakes, eight outputs and eight native revalidations, plus 104 targeted
mutation expectations. Forty-eight malformed outputs fail both schema and native
validation; four well-typed changed legal-entity contexts pass structural validation
and fail native reconstruction against their original inputs. All 36 audited
schema/runtime hashes match the root source freeze. Earlier schema failures remain
unchanged.

[findings-and-repairs.json](findings-and-repairs.json) records ten semantic findings:
duplicate CDD receipt provenance; duplicate EDD economic events; approval after first
promotion use; unresolved later failed remediation retest; immediate notification
timing; notification row contamination; an information-barrier mismatch hidden by
unknown classification; missing mandate for an embedded list change; incompatible
customer metric units; and lost threshold decimal precision. Their repairs have
meaningful native regressions and independent replay evidence. Companion schemas
also now accept advertised typed source facts and valid withheld null branches while
retaining strict core context/action/authority constraints.

Earlier failures are preserved. The primary suite began at 40/44 domain assertions;
governance at 147/150; conduct at 91/94, then 139/140 when the decimal issue was found.
Original inputs, outputs, expectations, scripts and hashes remain intact. Changes to
intake representation are separately named, with fact-level lineage; earlier positive
expectations are not silently reclassified as passes. Initial implementation snapshots
and hash verification are under [initial-implementation](initial-implementation/).

[preflight-repairs.json](preflight-repairs.json) retains integration failures: missing
`python` on the inherited PATH and seven conduct manifests lacking executable `evals`
entries. The declared scenario expectations were kept and executable commands added.
[pre-repair-broad-checks](pre-repair-broad-checks/) retains earlier snapshots, including
a portable run made during an EDD repair. Those records are not final verification.

## Reproduction and remaining acceptance

Actual verification commands and working paths are in the final check and per-case
run records. From the repository, use a verification environment with PyYAML on PATH:

```sh
python -B -m unittest discover -s tools -p 'test_*.py' -v
python -B tools/run_selftests.py
python -B tools/run_compliance_portable.py
python -B tools/validate_skills.py
python -B tools/check_handoffs.py
python -B tools/check_compliance_financial_crime.py
python -B tools/sync_cfc_resources.py --check
```

The saved schema audit additionally requires jsonschema. Historical replay uses the
frozen script snapshots when live methods have changed. Test results, exact source-fact
matches and manifests prove bounded reconstruction/integrity; they do not authenticate
sources, prove complete legal coverage, privilege, lawful disclosure, independence,
causal harm, policy legitimacy or institution approval.

Professional acceptance still requires accountable practitioners, approved current
legal and method packs, lawful data access and classification/audience controls.
Deployment and any execution need separate operational acceptance and authority.
Four target jobs remain Phase3 gaps (S3, M1, M2, T2); advanced Phase4 scope remains
pending. No filing, notification, promotion dissemination, account/list action,
payment, investigation contact, actual finding closure, commit, push, merge or release
was performed.
