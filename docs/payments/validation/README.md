# Payments Phase 1 validation record

Validated 2026-09-17 in the working checkout. This record separates repository
checks, bounded forward evaluation by independent agents, and acceptance still
needed from specialists and deployments. All scenario evidence is synthetic.
The [source manifest](source-manifest.json) binds payment packages, the moved PCI
package, shared contracts, catalog and affected tooling to their SHA-256 hashes.
The [preservation check](preservation-check.json) verifies existing wealth package,
shared and validation files against the pre-implementation baseline.

## Repository checks

| Check | Result | Retained evidence |
| --- | --- | --- |
| Full-library executable package evaluations | 1,101 passed, 0 failed; 100 are payments/PCI | [Package log](package-evaluations.log) |
| Skill structure and metadata | 239 packages, 0 errors, 0 warnings | [Structure log](structure-validation.log) |
| Payments shared-contract and integration methods | 13 passed | [Payments integration log](payment-integration-tests.log) |
| All repository integration/test methods | 277 passed, including the 13 payment methods | [Repository test log](repository-tests.log) |
| Whole-library handoffs | 239 packages, 0 dangling references | Final integration checks in `checks.json` |
| Payment routing and migrations | 0 errors | Final integration checks in `checks.json` |
| Shared payment bundles | Canonical helper/reference verified in 19 packages | Final integration checks in `checks.json` |
| Defect lint | Scoped E9/F checks passed | Final integration checks in `checks.json` |
| Whitespace | `git diff --check` passed | Final integration checks in `checks.json` |

Package evaluation counts are executed commands. Some commands invoke multiple
regression methods; those are not added to the 1,101 count. The 13 payments
integration methods include standalone package copying, catalog idempotence,
original-name migration, issuer/merchant alias handling and the requirement to
validate native target inputs after a valid handoff envelope.

The first broader repository run exposed one stale global catalog assertion in
`tools/test_wealth_p3.py`: provisional additions are now 67 rather than 66 because
of the payments router. That assertion was updated with the migration rationale;
the complete 277-method suite then passed. Wealth-management package content and
its retained validation records were unchanged.

Reproduce from repository root with Python 3, PyYAML and Ruff installed:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B tools/validate_skills.py
PYTHONDONTWRITEBYTECODE=1 python -B tools/run_selftests.py
PYTHONDONTWRITEBYTECODE=1 python -B tools/check_handoffs.py
PYTHONDONTWRITEBYTECODE=1 python -B tools/check_payment_handoffs.py
PYTHONDONTWRITEBYTECODE=1 python -B tools/sync_payment_contract.py --check
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tools -p 'test_*.py'
ruff check --config ruff.toml --select E9,F --no-cache skills/payments skills/cybersecurity-operational-resilience/pci-dss-evidence-assistant shared/payments tools/sync_payment_contract.py tools/check_payment_handoffs.py tools/test_payment_contract.py tools/test_payments_phase1.py tools/build_catalog_from_xlsx.py tools/check_handoffs.py tools/test_wealth_p3.py
git diff --check
```

The broader Ruff invocation in this environment enables additional rules and
reports 229 findings, mostly import ordering, executable-bit and style conventions.
It is **not** reported as passing. The three loop-binding warnings were inspected:
the comparison helper and replacement lambda are called synchronously within the
same iteration, with no deferred closures. The six implicit-string warnings are
intentional continuations. This milestone uses the explicit E9/F defect check
above and does not claim an unrestricted Ruff pass.

The generic skill-creator quick validator rejects the library's existing top-level
`compatibility` field. That result is not reported as a pass; the repository's
metadata-aware validator is the recorded structure check. Existing compatibility
metadata was retained.

## Independent forward evaluation

Two agents independent of implementation read actual skill instructions, authored
fresh synthetic inputs, ran native tools and interpreted the resulting evidence.
They covered nine bounded requests plus variants. This was not a blinded paired
model experiment, a human-SME review or the full proposed routing benchmark.

| Group | Requests and controls | Evidence |
| --- | --- | --- |
| Money and state, four requests | Authorization without clearing; exact-field bank repair and stale screening; payout discrepancy without bank evidence; transaction reconciliation with processor differences, currency separation and duplicates | [Report](forward-money/REPORT.md), [42 original commands](forward-money/command-results.json) |
| Cases and readiness, five requests | Rejected-only authorization logs; issuer claim without legal profile; authorized phone scam without email; observed merchant costs with unknown fixed fees; readiness links without inspections | [Report](forward-cases/report.md), [original commands](forward-cases/execution-log.json), [issuer variant](forward-cases/2b-execution-log.json) |

The evaluations found three defects that ordinary package tests had missed:

| Finding | Repair | Independent verification |
| --- | --- | --- |
| API diagnostic dropped `integration.window` and `log_entries[].ts` | Preserve documented fields and supported aliases; retain noncausal interpretation | Same original input, field-equality assertions and three native calls passed |
| Issuer discarded supplied scheme clock when optional scheme profile was absent | Retain supplied clock and source citation with unresolved profile/applicability | Same original input, clock/citation assertions and three native calls passed |
| Reconciliation counted one source record twice under different transaction references | Detect reused immutable source references before grouping arithmetic; quarantine every affected group in both reconcilers, across references, currencies and cycles | 35 native calls returned expected statuses: 34 accepted outputs and one intended rejection of the preserved old false-match output; original inputs unchanged, valid controls preserved |

Current fix evidence:

- [API and issuer verification commands](forward-cases/fix-verification-execution-log.json)
- [API output retaining chronology](forward-cases/1-rejected-logs-verified-output.json)
- [Issuer output retaining unresolved scheme clock](forward-cases/2b-issuer-deadline-only-verified-output.json)
- [Reconciliation retest commands](forward-money/retest-command-results.json)
- [Reconciliation assertions and conclusions](forward-money/retest-conclusions.json)
- [Unchanged original input hashes](forward-money/retest-original-input-hashes.json)
- [Source hashes before](forward-money/retest-source-hashes-before.json) and [after](forward-money/retest-source-hashes-after.json)

Original failing outputs and original reports are intentionally preserved as
historical evidence. Use `*-verified-output.json` for the two evidence-retention
fixes and `retest-*-output.json` for current reconciliation results. The residual
API causal wording noted in the cases report was subsequently corrected in
`payment-api-log-diagnostic-pack/SKILL.md` and checked during integration.

Historical runner scripts and command logs retain their original checkout and
temporary paths. They document execution rather than promise portable entrypoints.
To replay the exact duplicate reproduction portably from repository root:

```sh
python -B skills/payments/payment-transaction-reconciler/scripts/validate_input.py docs/payments/validation/forward-money/s4-reused-identity-all-equal-input.json
python -B skills/payments/payment-transaction-reconciler/scripts/calculate_or_transform.py docs/payments/validation/forward-money/s4-reused-identity-all-equal-input.json > /tmp/payments-phase1-identity-replay.json
python -B skills/payments/payment-transaction-reconciler/scripts/validate_output.py /tmp/payments-phase1-identity-replay.json --input docs/payments/validation/forward-money/s4-reused-identity-all-equal-input.json
```

Expected: both groups quarantined, usable totals null, matching conclusion false.
Source snapshots/hashes establish lineage; they do not authenticate source truth.

## Remaining acceptance boundaries

- The router has structured route tests and limited agent interpretation evidence.
  The broader natural-language evaluation cases remain unexecuted; their presence
  in `evals.json` is not a completed model evaluation.
- Institution-specific legal/rule profiles, licensed scheme content, professional
  review and regional coverage require separate acceptance. Public-source
  orientation is recorded in [source governance](../SOURCE-GOVERNANCE.md).
- Trusted source verification, identity/approval authentication, live connectors,
  operational recovery and permission enforcement belong to deployment acceptance.
  No payment-changing runtime is supplied by this phase.
- Workbook reconciliation remains pending with its owner. Approved catalog
  overrides/additions preserve this implementation through regeneration.
