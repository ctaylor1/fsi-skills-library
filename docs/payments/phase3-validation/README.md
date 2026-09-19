# Payments Phase 3 validation record

Validated 2026-09-18 in the shared working checkout. This record separates executed
checks, independent synthetic forward evaluation and outstanding acceptance gates.
See [implementation](../PHASE3-IMPLEMENTATION.md) and [roadmap](../ROADMAP.md).
No payment, financial posting, external submission, rule deployment or cutover occurred.

## Executed checks

| Check | Result | Evidence |
| --- | --- | --- |
| Payments plus PCI package commands | 234 passed, 0 failed | [Final log](payment-package-evaluations.log) |
| Payments contract/foundation/integration methods | 49 passed | [Final log](payment-integration-tests.log) |
| Whole-library package commands | 1,329 passed, 0 failed | [Recorded sweep](repository-package-evaluations.log) |
| Whole-library repository methods | 336 passed | [Recorded sweep](repository-tests.log) |
| Payments plus PCI structure/handoffs | 35 packages; 0 errors, warnings or dangling references | [Checks](checks.json) |
| Whole-library structure/handoffs | 271 packages; 0 errors, warnings or dangling references | [Checks](checks.json) |
| Payment routes/migrations | 0 errors | [Checks](checks.json) |
| Shared bundles | Contract matches 35 packages; foundation matches 19 core and two dispute extensions | [Checks](checks.json) |
| Defect lint | Explicit E9/F scope passes | [Log](defect-lint.log) |
| Whitespace | `git diff --check` passes | [Checks](checks.json) |
| Prior work | 555 wealth files, 111 Phase 1 and 1,143 Phase 2 payments files match pre-turn hashes | [Preservation](preservation-check.json) |

The eleven Phase 3 domain suites contain **281 regression methods**, including
legacy-compatibility coverage. Their executable commands are included within the
234 package commands; these counts must not be added as independent evaluations.
[Method inventory](domain-method-inventory.json) records the distribution. Nine new
integration methods cover all eleven native contexts, including independently copied
packages, source-bound output validation, upstream-issue propagation, unsupported
jurisdictions, authority/source tampering, target-native handoff requirements,
catalog regeneration, migrations and retained Phase 4 routing gaps.

Whole-library results are the recorded shared-checkout sweep and include concurrent
insurance changes. Insurance work was not edited by this phase. After that sweep,
the final source audit corrected only the bank message-registry source URL/version
and documentation/handoff references; the final payments package/integration checks
and structural/bundle checks were rerun. The catalog has 271 entries, of which this
phase adds six Payments entries. Previous phase evidence was preserved unchanged.

Reproduce with Python 3, PyYAML and Ruff installed:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B tools/run_selftests.py skills/payments skills/cybersecurity-operational-resilience/pci-dss-evidence-assistant
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tools -p 'test_payment*.py'
PYTHONDONTWRITEBYTECODE=1 python -B tools/run_selftests.py
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tools
PYTHONDONTWRITEBYTECODE=1 python -B tools/validate_skills.py
PYTHONDONTWRITEBYTECODE=1 python -B tools/check_handoffs.py
PYTHONDONTWRITEBYTECODE=1 python -B tools/check_payment_handoffs.py
PYTHONDONTWRITEBYTECODE=1 python -B tools/sync_payment_contract.py --check
PYTHONDONTWRITEBYTECODE=1 python -B tools/sync_payment_foundation.py --check
ruff check --config ruff.toml --select E9,F --no-cache skills/payments skills/cybersecurity-operational-resilience/pci-dss-evidence-assistant shared/payments tools/sync_payment_contract.py tools/sync_payment_foundation.py tools/check_payment_handoffs.py tools/test_payment_contract.py tools/test_payment_foundation.py tools/test_payments_phase1.py tools/test_payments_phase2.py tools/test_payments_phase3.py
git diff --check
```

The environment used `/tmp/fsi-p0-venv/bin/python` and Ruff, with that environment
first on PATH for eval commands. No unrestricted Ruff pass is claimed. The repository
validator understands the library's existing `compatibility` metadata; the generic
skill-creator validator is not the structural acceptance gate for this library.

## Independent forward evaluation

Implementation agents evaluated other agents' packages using instructions and native
contracts. They authored fresh synthetic inputs and practical expectations without
reading target regression tests, fixtures or goldens. Reports retain inputs, outputs,
argv, assertions, limitations and source hashes. This is bounded agent evaluation,
not human practitioner acceptance or broad model benchmarking.

| Group | Executed coverage | Evidence |
| --- | --- | --- |
| Platform, commercial, liquidity | 21 scenarios, 61 native calls, 115 assertions pass | [Report](forward-flows/REPORT.md) |
| Operations, incident, architecture/readiness resilience | 23 scenarios, 69 calls, 69 assertions pass | [Report](forward-operations/report.md) |
| Acceptance, fraud, credentials, bank collection | Initial 47 calls and 90 assertions pass; one additional identity defect found. Final fix verification adds 14 calls and 39 passing assertions | [Report](forward-trust-analytics/REPORT.md), [fix assertions](forward-trust-analytics/final-fix-verification/assertions.json) |
| Routing | Original 18 requests plus 19 supplementary cases; 74 calls and 198 assertions pass | [Report](forward-router/REPORT.md) |

The original 18 routing requests produced 13 preliminary destinations, one participant
clarification and four declared capability gaps. An agent selected explicit intents;
the native router does not classify natural language. Missing jurisdictions remain
visible, and a routed destination is not a complete downstream input. No blinded
natural-language benchmark or end-to-end deployment was performed.

Examples of independently checked results:

- Two sellers retain separate payout capacities of USD250 and USD255 after their
  own refunds, reserves and pending payouts. Different ownership cannot be pooled.
- Invoice balances and partial remittance remain separate: supplier A retains 250
  and supplier B 150. Missing amounts or duplicate ERP identities suppress affected totals.
- Weekend FedNow deficit is 300 under the baseline and 540 under stress; RTP is
  300 and 520. EUR4,000 remains separate from USD balances.
- Operations capacity value of 48 produces only 12 of realizable cash savings and
  negative 15 net benefit after costs. Overlapping opportunities are not additive.
- Incident analysis counts three payments versus five attempts. Missing, failed,
  old-version or unbound fault artifacts prevent evidence-complete readiness.
- Token state, updater consent, authentication and payment intent stay distinct;
  an accepted collection message neither submits nor settles a payment.

## Findings corrected

| Finding | Correction and verification |
| --- | --- |
| Different collection requests reused one immutable payer-response ID and both advanced to initiation review | Supplied response identities must be nonempty strings unique across requests. The unchanged independent adversarial input now fails both input validation and calculation; malformed response and identity shapes fail cleanly. Original defect artifacts remain retained. |
| Fraud strategy route named a mode absent from the target schema and implied historical replay | Route now selects native `strategy`. The unchanged original strategy request and independent compatibility assertion pass. This was a source-inspection finding, not a fabricated failed CLI run. |
| Active operations instructions named a nonexistent single-payment destination | Both references now name `payment-lifecycle-diagnoser`; independent readback proves exactly those documentation substitutions. |
| Superseded FedNow February reference remained in current rail/message profiles | Current profiles use April 2026 v3.6. Rail profile version is 2026-09-18.2; message registry is 1.0.1. Parser behavior is unchanged. Historical Phase 2 records retain their original checkpoint references. |
| Existing card instructions omitted an inbound credential handoff | Card program/lifecycle references now route token, updater and authentication evidence to the installed reviewer, preserving native inputs and authority limits. |

The [source readback](forward-source-readback.json) exposes all differences from the
independent snapshots. The original trust snapshot predates the collection fix;
the separate final fix snapshot covers the corrected runtime/schema. The later
message-registry edit changes only a version and source URL, verified by exact
reverse-hash reconstruction in [reference readback](post-review-reference-readback.json).
Operations documentation corrections are separately proven in
[its readback](forward-operations/post-review-documentation-correction.json).
No runtime differs from the final independently evaluated runtime snapshots.
The [final scope audit](scope-audit.md) verifies the roadmap coverage and closes
the documentation/source findings above.

## Evidence and outstanding gates

The [source manifest](source-manifest.json) hashes the final Payments implementation,
shared resources, integration tools and relevant catalog/docs. The
[artifact manifest](artifact-manifest.json) hashes retained evidence excluding itself.
Copied runners retain original absolute temporary paths for provenance; reproduction
requires restoring those paths or explicitly recording path adaptations. Manifests
are consistency snapshots, not signed source-authenticity attestations.

All results use synthetic supplied evidence. Helpers do not authenticate source
records, reviewer identity, deployed configurations or actual system behavior.
Public rail/scheme summaries are bounded; licensed current rules and institution
contracts remain necessary. Exact target-native inputs must still be assembled and
validated at each handoff. Human specialist review, trusted-source integration,
broader model evaluation and operational acceptance remain open. Phase 4 was not
implemented, and the external source workbook remains unchanged.
