# Insurance Phase 5 validation — 2026-10-04

The five specialist packages and bounded validation are complete. Insurance now has
**69 packages**. See the [implementation record](../PHASE5-IMPLEMENTATION.md).
This is supplied-source offline review capability, with no clinical, coverage,
actuarial, payment, network or deployment approval.

## Final checks

| Check | Verified result | Evidence |
| --- | --- | --- |
| Insurance structure/metadata | 69 packages; zero errors/warnings | [log](checks/insurance-structure.log) |
| Library structure snapshot | 364 packages; zero errors/warnings, including concurrent work | [log](checks/all-structure.log) |
| Insurance executable package checks | 352 passed, zero failed | [log](checks/insurance-selftests.log) |
| Insurance integration/contract tests | 64 methods passed, including 12 Phase 5 methods | [log](checks/insurance-integration.log) |
| New native methods | 259 passed: parametric 55, pricing 59, network 58, utilization 41, payment 46 | Individual `checks/*-native.log` files; these methods also run inside the package-command checks, not additive totals |
| Portable resource parity | 45 specialist bundles match; existing 44 workflow bundles and 69 Insurance helper/reference pairs match | [specialist](checks/specialist-resources.log), [workflow](checks/workflow-resources.log), [Insurance](checks/insurance-contract.log) |
| Routing/handoffs | Zero missing references and route/migration errors; participant/line/availability/action boundaries tested | [handoffs](checks/handoffs.log), [routes](checks/routes.log) |
| Focused runtime lint | F and E9 rules pass on new domain methods, tests, specialist support and new tools | [log](checks/lint.log) |
| Frozen independent case replay | 12/12 results match reviewed outputs; 36 native input/calculate/output calls pass | [report](final-replay/report.json), [log](checks/replay.log) |
| Prior Insurance preservation | 3,439 protected earlier files unchanged; none missing | [preservation](preservation.json) |

The integration suite copies all five packages into isolated temporary installations,
executes their native commands and checks source preservation, uncertain inputs,
explicit context mapping, real service-identity transfer, upstream issue propagation,
rehashed tampering, unsupported profiles and no execution authority. Raw JSON
regressions exercise fractional tokens that parsers could round into whole floats,
including superseded claim records that are not used in the current calculation.

Reproduce with a Python environment containing PyYAML and Ruff:

```sh
python tools/validate_skills.py skills/insurance
python tools/run_selftests.py skills/insurance
python -m unittest discover -s tools -p 'test_insurance*.py'
python tools/sync_insurance_specialist.py --check
python tools/check_insurance_handoffs.py
python tools/replay_insurance_phase5.py
```

Native installed packages use only the Python standard library. Repository-specific
metadata includes `compatibility`; the bundled generic skill quick-validator lacks
that key in its whitelist. Its rejection is not presented as a passing check; the
repository structure/spec-card checks above validate the actual repository contract.
No whole-library runtime or unrelated-domain acceptance claim is made.

## Independent source-to-output review

Three independent agents used the package instructions and schemas to map fresh
fictional requests/source packets. They did not read the relevant authors' fixtures,
tests, implementations or expected answers before their forward evaluations. Raw
packets, initial attempts, missing facts, explicit source supplements, mappings,
outputs and reviewer notes are retained. These are bounded agent exercises, not
human practitioner acceptance or a statistical model-quality benchmark.

- [Parametric review](forward/parametric/independent-forward-review.md) and
  [draft memorandum](forward/parametric/review-memorandum.md): revised final reading
  supports USD 30,000 provisional unpaid; old-final, preliminary-terminal and
  contrary-primary fallback attempts withhold dependent results. Missing reviewer
  facts and explicit later clarifications remain separate. Seventeen historical
  attempts are preserved; only final current-schema cases 14–17 enter the replay.
- [Pricing/network review](forward/pricing-network/review.md): independent 340 PMPM
  pricing case, missing-IBNR withholding, distinct-provider/site counting and missing
  travel-measurement withholding. Exact record-ID clarifications and native capacity
  normalization are recorded separately.
- [Utilization/payment review](forward/utilization-payment/review.md): explicit
  administrative clock, contrary/missing clinical observations, corrected claim
  replacement, independently supplied allocation, payment variance and unknown
  cost-sharing preserved without back-solving.

The frozen [case index](replay-cases.json) drives the current replay tool. Historical
agent scripts in the forward folders retain their original temporary paths as
execution evidence; use `tools/replay_insurance_phase5.py` for portable replay.
Planned natural-language eval-manifest entries remain labeled not-run. These actual
forward cases are recorded separately rather than relabeling all planned cases.

## Findings and disposition

| Finding | Disposition and evidence |
| --- | --- |
| Numeric revision identifiers had an undocumented text requirement | Schema now states exact text version labels; historical rejected mappings retained; clarified source-faithful text mappings replay successfully. |
| Parametric completeness booleans lacked source-bound inventory statements | Required locator, source references and reading/ledger attestations bound to exact contract, event and aggregate period; bare flags and unknown-empty-ledger tests withhold amounts. Final cases 14–17 map the existing explicit source statements. |
| Integer-valued floats could already have lost source precision | Reject every float throughout native data, including inactive/superseded evidence. Exact decimal strings and integer tokens remain supported; raw-token integration regressions pass for all five jobs. |
| Orphan claim events could affect coding pairs without withholding line amounts | Inventory and orphan findings now precede the shared chain-validity barrier; targeted orphan paired-code regression withholds line coding, allowance and payable. |
| Clinical criteria lacked explicit program scope; payment snapshots could predate the terminal event | Criteria now bind market/program/product; service/event/snapshot chronology enforced and tested. |
| Health pricing/network context and review dates needed stronger binding | Exact health capacities and cohort/plan objects required; review cannot predate valuation/observation. Pricing arithmetic now preserves exact intermediates. |
| Missing utilization request scope also suppresses otherwise met aggregate criterion states | Conservative behavior retained and explicitly documented. Original attributed observations remain visible. Independence applies to criterion-level evidence gaps once request scope is valid; it does not override missing request scope. |

The independent code-review findings were repaired before final verification. The
source-mapping reports retain their original observations; this disposition records
which findings were repaired and which conservative behavior was clarified.

## Preservation and acceptance limits

The initial [baseline](baseline.json) captured the already-dirty checkout before
Phase 5 authoring. The preservation report verifies earlier Insurance packages,
canonical Insurance/workflow resources and earlier validation archives. It also
lists integration changes and concurrent changes observed elsewhere; it does not
claim exclusive authorship or a clean working tree. Previous archives were not
regenerated. Global catalog counts are a validation-time snapshot, not an attribution
of other tasks' additions to Insurance.

The source and evidence manifests capture the final reviewed files and evidence
hashes. Hashes prove file identity, not source truth, permissions, professional
acceptance or production readiness. The [primary-source record](PRIMARY-SOURCES.md)
documents design boundaries without embedding adopted regional rules or licensed
clinical/coding content.

Actual source access/authenticity, field mappings, inventory attestations, applicable
methods, licensed content, privacy/access and qualified practitioner/control-owner
acceptance remain necessary. Deployment also needs operational recovery, monitoring
and institution testing. Full health-payer coverage, additional regional methods and
external source-workbook reconciliation remain open. No external communication,
filing, payment, network change, commit, merge, release or deployment occurred.
