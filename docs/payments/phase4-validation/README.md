# Payments Phase 4 validation record

Executed 2026-09-18 in the shared working checkout. See the
[implementation](../PHASE4-IMPLEMENTATION.md) and [roadmap](../ROADMAP.md).
The four agreed implementation phases are authored. Relevant human specialist
review and institutional/deployment acceptance remain open. No payment, financial
posting, credential release, external submission or deployment occurred.

## Executed checks

| Check | Result | Evidence |
| --- | --- | --- |
| Payments plus PCI package commands | 311 passed, 0 failed | [Log](payment-package-evaluations.log) |
| Payments contract/foundation/integration methods | 61 passed | [Log](payment-integration-tests.log) |
| Whole-library package commands | 1,517 passed, 0 failed | [Recorded sweep](repository-package-evaluations.log) |
| Whole-library repository methods | 362 run; 361 passed, one insurance metadata failure | [Recorded sweep](repository-tests.log) |
| Payments plus PCI structure/handoffs | 39 packages; zero errors, warnings or dangling references | [Checks](checks.json) |
| Whole-library structure/handoffs | 296 packages; zero errors, warnings or dangling references | [Checks](checks.json) |
| Payment routes/migrations | Zero errors | [Checks](checks.json) |
| Shared bundles | 39 contracts; 23 foundation packages plus two dispute extensions, zero drift | [Checks](checks.json) |
| Scoped defect lint and whitespace | E9/F and `git diff --check` pass | [Lint](defect-lint.log), [checks](checks.json) |
| Prior records | 555 wealth files and 111/1,143/743 Phase 1/2/3 Payments files match pre-turn hashes | [Preservation](preservation-check.json) |

The eleven new native contexts contain **359 regression methods**. These run inside
package commands and are not additive independent evaluations. The
[method inventory](domain-method-inventory.json) records their distribution.
The new integration suite covers all eleven contexts, standalone package copies,
source-bound outputs, unresolved upstream evidence, unsupported regions, action and
output tampering, catalog regeneration and exact router modes. Removing optional
modules leaves the original six package calculators' outputs unchanged. The shared
foundation test also proves that input data cannot expand jurisdiction support.

The full-repository failure is `test_spec_cards_reproduce_insurance_metadata`:
concurrent `insurance-router` SKILL metadata says Phase 3 while its catalog-derived
spec card says Phase 2. It remains outside this Payments change; no clean
whole-repository test result is claimed. The earlier integration failure was a
test assumption that all optional outputs use `module`; two documented native
contracts use `mode`. The test now reads the declared field and verifies its value
against the router. [Initial logs](initial-sweep/) retain both findings; subsequent
Payments integration passes all 61 methods. Concurrent insurance work accounts for
21 of the 25 catalog additions since the pre-turn baseline; Payments adds four.

[Exact argv and exits](executed-commands.json) accompany the logs. Reproduce with
Python 3, PyYAML and Ruff, putting that Python environment first on PATH for package
subprocesses:

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
git diff --check
```

The recorded environment used `/tmp/fsi-p0-venv/bin/python` and Ruff. Lint uses the
explicit E9/F paths in executed-commands.json; no unrestricted Ruff pass is claimed.
The generic skill-creator validator rejects all four new packages solely because
its allowlist omits the repository's existing `compatibility` field; its
[unmodified results](generic-skill-validator.json) are retained. The repository
validator supports that field and is the structural acceptance gate.

## Independent fresh forward evaluations

Implementation agents independently evaluated other agents' packages using public
instructions, native schemas and primary-source boundaries. They authored new
fictional case data and practical expectations without reading target tests,
fixtures or golden outputs. Retained artifacts include inputs, outputs, exact CLI
arguments, assertions, evaluator corrections and source snapshots. These are bounded
agent evaluations, not human professional acceptance or a broad model benchmark.

| Review | Result and retained evidence |
| --- | --- |
| Wallet, advanced platform, commercial cards | 31 cases, 95 calls and 109 assertions pass. One evaluator expectation was corrected: missing backing does not erase separately known liability. [Report](forward-programs/README.md). |
| Stablecoin, business models, regional bank, cross-border design/funding | 69 main cases, 182 calls and 240 assertions, plus an independently observed intermediary funding defect. The unchanged positive/adversarial replay adds six calls and 17 passing assertions after repair. Twenty earlier evolving-schema calls are retained separately. [Report](forward-specialist-regions/README.md). |
| Agent initiation, credential and platform evidence | 106 cases, 315 calls and 1,082 initial assertions: 1,079 passed and three exposed one shared AP2 subdelegation defect. All nine unchanged normal/institution-defined/AP2 cases passed after repair across 27 calls. [Report](forward-agents/README.md). |
| Router | Original 18 requests plus 23 supplemental cases; 85 calls and 303 assertions pass. Two guessed evaluator package names were corrected using public installed responsibilities; no routing implementation change was needed. [Report](forward-router/README.md). |

The original broad orchestration request retains participant clarification. Other
original requests now have preliminary destinations, with missing case context still
visible. An agent maps natural language to explicit intent; the native router does
not implement natural-language classification. A destination does not constitute
complete downstream native input or specialist approval.

Independently checked examples include KES11,000 wallet liability against KES10,500
backing (shortfall KES500); separate marketplace seller capacities of 800 and 550;
settled versus held commercial-card invoice amounts; USD1,005 payer debit versus
GBP795.4 beneficiary receipt with explicit intermediary funding; and an agent cart
of USD270 with USD800 remaining before the proposal after both settled and pending
spend. Unknowns, duplicate economic identities, ownership mismatches, replay and
unresolved outcomes retain explicit gaps.

## Findings and closeout

- **AP2 subdelegation:** all three generalized agent modules initially accepted
  positive delegation depth with institution consent even when labeled AP2 v0.2.
  Public-protocol subdelegation now remains `protocol-subdelegation-not-implemented`.
  Institution-defined designs retain their distinct scope. Original failed inputs
  and outputs and independent unchanged-input retests remain available.
- **Intermediary funding:** a declared GBP1 intermediary transfer could coexist
  with a GBP795.4 final payout and a ready comparison. The supported chain now
  requires funding reconciliation at that stage and reports the explicit amount
  difference. The unchanged negative case now needs evidence; the normal case and
  endpoint arithmetic remain correct.
- **Schema usability:** the independent reviewer exposed unclear Interac field
  nesting and evolving cross-border chain/scope requirements. Final references
  make these native fields explicit; initial schema attempts remain retained.
- **Compatibility verification:** the root integration test now recognizes the
  existing `mode` and `module` output contracts without changing those APIs.

[Final forward source readback](forward-source-readback.json) matches every file in
the final independent snapshots. Earlier agent snapshots precede the AP2 fix;
its separate retest captures the corrected runtime. The final specialist snapshot
captures the intermediary funding fix. The [scope audit](scope-audit/scope-audit.md) and [final link readback](local-link-check.json)
confirm coverage and documentation closure; source hashes are consistency checks,
not authenticity attestations.

## Evidence and remaining gates

[Source manifest](source-manifest.json) captures the final Payments code, shared
resources, tooling and catalog/docs. [Artifact manifest](artifact-manifest.json)
hashes retained evidence excluding itself. [Manifest readback](manifest-readback.json)
verifies those snapshots, excluding itself from the evidence manifest to avoid a
circular hash. The pre-turn baseline and historical evidence remain unchanged.
Copied evaluator runners retain their original temporary paths for provenance;
reruns require restoring those paths or explicitly recording adaptations.

Professional review of actual country, rail, product, legal, accounting and treasury
cases remains required, along with licensed/current institution rule packs, trusted
source integration, broader model evaluation and target-native handoff assembly.
The source workbook is unchanged. No target-host installation, release publication,
provider interoperability, production identity/permission enforcement, live
revocation, atomic reservation or operational recovery acceptance is supplied.
Offline implementation completion does not satisfy those gates.
