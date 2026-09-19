# Payments Phase 2 validation record

Validated 2026-09-18 in the shared working checkout. This record separates
deterministic checks, independent synthetic forward evaluation, routing behavior
and acceptance still required. See [implementation](../PHASE2-IMPLEMENTATION.md)
and [roadmap](../ROADMAP.md). No live payment, external submission or deployment
occurred. The source and artifact manifests bind the retained files to SHA-256.

## Repository checks

| Check | Result | Evidence |
| --- | --- | --- |
| Whole repository package commands | 1,179 passed, 0 failed at closeout | [Closeout log](closeout-repository-package-evaluations.log) |
| Payments plus PCI package commands | 163 passed, 0 failed | [Package log](payment-package-evaluations.log) |
| Payments contract/foundation/integration methods | 40 passed | [Integration log](payment-integration-tests.log) |
| Whole repository test methods | 319 passed | [Repository log](repository-tests.log) |
| Payments plus PCI structure | 29 packages; 0 errors, 0 warnings | [Checks](checks.json) |
| Whole repository structure | 248 packages; 0 errors, 0 warnings | [Checks](checks.json) |
| Whole repository handoffs | 248 packages; 0 dangling references | [Checks](checks.json) |
| Payments routes/migrations | 0 errors | [Checks](checks.json) |
| Shared bundles | Phase 1 contract matches in 29 packages; additive resources match ten new and two existing dispute packages | [Checks](checks.json) |
| Defect lint | Explicit E9/F scope passes | [Lint log](defect-lint.log) |
| Whitespace | `git diff --check` passes | [Whitespace log](whitespace.log) |
| Prior work preservation | Wealth content/shared/records and historical payments Phase 1 records match the pre-turn baseline | [Preservation check](preservation-check.json) |

Counts refer to different units: package evaluations are executed commands, some
of which invoke regression suites; repository integration methods are counted
separately. They must not be added as if all were independent behavioral cases.
The ten new packages contain 200 domain regression methods. Router regressions
cover all installed/planned intents, participant ownership, scope disclosure and
current natural-language expectation metadata. Integration checks copy each new
package outside the checkout and run its source-bound output validation.

Concurrent insurance implementation changed this checkout during validation.
The initial broad package sweep returned 1,175 passes and four insurance failures;
the later sweep returned **1,178 passes and one failure**, in
`claims-triage-assistant`'s `det-output-valid`. These earlier failures are retained
in the [initial log](initial-repository-package-evaluations.log) and
[later log](repository-package-evaluations.log). A targeted read-only recheck
then passed all seven claims-triage commands, followed by a fresh full-library
closeout sweep: **1,179 passed, zero failed**. Insurance content was not edited
by the payments implementation; its concurrent owner supplied those fixes.
The catalog is now 248 after the concurrent insurance consolidation; Phase 2
itself adds ten payments packages.

The existing global catalog assertions in `tools/test_wealth_p3.py` now check
declared count, actual unique rows, catalog-to-disk equality and unchanged wealth
coverage instead of a frozen whole-library package count. Wealth package content
and retained milestone records were preserved. The external workbook remains
unchanged; approved additions/overrides pass regeneration consistency checks.

Reproduce from repository root with Python 3, PyYAML and Ruff installed:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B tools/run_selftests.py skills/payments skills/cybersecurity-operational-resilience/pci-dss-evidence-assistant
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tools -p 'test_payment*.py'
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tools
PYTHONDONTWRITEBYTECODE=1 python -B tools/validate_skills.py
PYTHONDONTWRITEBYTECODE=1 python -B tools/check_handoffs.py
PYTHONDONTWRITEBYTECODE=1 python -B tools/check_payment_handoffs.py
PYTHONDONTWRITEBYTECODE=1 python -B tools/sync_payment_contract.py --check
PYTHONDONTWRITEBYTECODE=1 python -B tools/sync_payment_foundation.py --check
ruff check --config ruff.toml --select E9,F --no-cache skills/payments skills/cybersecurity-operational-resilience/pci-dss-evidence-assistant shared/payments tools/sync_payment_contract.py tools/sync_payment_foundation.py tools/check_payment_handoffs.py tools/test_payment_contract.py tools/test_payment_foundation.py tools/test_payments_phase1.py tools/test_payments_phase2.py tools/test_wealth_p3.py
git diff --check
```

The environment used `/tmp/fsi-p0-venv/bin/python` and Ruff. No unrestricted Ruff
pass is claimed. The generic skill-creator quick validator rejects this library's
existing `compatibility` field; compatibility metadata was preserved and the
repository's metadata-aware validator supplies the recorded structural result.

## Independent forward evaluation

Agents independent of implementation read actual instructions and native contracts,
authored fresh synthetic requests, executed native tools and interpreted outputs.
They did not use golden outputs or regression expectations to construct the cases.

| Group | Coverage and outcome | Evidence |
| --- | --- | --- |
| Commercial | Three fresh requests plus five variants; 21 native calls plus an identical replay. Recurring coverage gaps, mandatory provider gates, incompatible fee units, stale evidence, complete economic contribution and unknown/overlap/tamper behavior | [Report](forward-commercial/REPORT.md), [commands](forward-commercial/command-results.json), [replay](forward-commercial/refresh-verification.json) |
| Bank/card/servicing | 29 scenarios, 87 final native calls; source-bound outputs validated, including intentional gap-bearing artifacts. Urgent rail design, exact individual/batch intent, mandates, future delegation, duplicate instructions, independently sourced outcomes, refund/return/recovery capacity and card stage distinctions | [Report](forward-lifecycle/REPORT.md), [final commands](forward-lifecycle/final-command-results.json), [funding retest](forward-lifecycle/funding-review-retest-summary.json) |
| Governance | 23 native calls, 17 independent assertions. UK EMI funds ownership, EA national overlay, unsupported Canada, safe/unsafe hub design and case-specific Reg E preparation/reuse | [Report](forward-governance/report.md), [commands](forward-governance/execution-log.json), [assertions](forward-governance/independent-assertions.json) |
| Natural-language routing | 18 original requests plus three explicit-role variants; 21 routes and 21 output validations. Original requests end with eight routed, nine declared gaps and one clarification | [Final report](routing-forward/final-report.md), [adjudication](routing-forward/final-adjudication.json), [findings](routing-forward/final-findings.json) |

Examples of independently checked practical results:

- Adding pay-by-bank reduced modeled costs by GBP1,636.60 but lost GBP1,800 in
  merchandise contribution; net contribution fell **GBP163.40 per month** under
  the supplied assumptions. Lower transaction costs alone did not imply a gain.
- GBP240 less GBP70 completed and GBP50 pending refunds leaves **GBP120** capacity
  before a new proposal. Missing or incomplete prior history leaves every total
  unknown, not zero.
- Card clearing, network settlement and issuer posting did not establish merchant
  funding. Unknown or overlapping hold-release evidence left the balance unknown.
- A partner bank holding an EMI's funds did not establish deposit insurance for
  the EMI customer. A reviewed issuer profile for case001 did not transfer to case002.

## Findings corrected during this phase

| Finding | Correction and independent verification |
| --- | --- |
| Initiation wrapper omitted required handoff inputs and failed calculation | Required inputs added; original individual and batch cases build and validate. |
| Delegation/policy could expire before scheduled execution | Exact validity must cover execution; unchanged delegation case and separate policy-expiry case preserve gaps. |
| Omitted service history produced numeric zero/capacity despite an uncertainty finding | Missing, incomplete or ambiguous history makes completed/pending/remaining amounts null; unchanged original case retested. |
| Arbitrary funding text appeared compatible with a native rail | Free-text arrangement remains declared-only with a specialist-review gap. All 29 lifecycle scenarios rerun; only the two bank design outputs changed. Native FedNow/RTP distinctions remain explicit. |
| Rail comparison silently omitted requested cards | Route discloses bank-only scope and separate provider/card/economics evidence; no combined ranking is claimed. |
| Ambiguous orchestration assumed a merchant | Missing role requests clarification; merchant/acquirer and bank/issuer/processor lead to the appropriate distinct workflows. |

The routing review also prompted visible participant/jurisdiction gaps in the new
routes. Legacy merchant-cost still requires practitioner clarification of audience
and incurred versus prospective scope; its empty context list is not readiness.
Initial failures, initial routing judgments and pre-funding-review outputs are
retained and explicitly superseded by the final reports. The governance report
records exact later documentation-only hash changes; no runtime changed after its
validated run. The lifecycle readback also records two identical schema wording
corrections (review date to review-due date); reversing those exact edits reproduces
the evaluated hashes. No runtime file differs from the final independent snapshots.
Freshness and source hashes do not establish source authenticity.

## Evidence handling and acceptance limits

The copied runners retain original absolute `/tmp/` working paths and source
references for provenance. Reproduction requires restoring those paths or recording
an explicit path adaptation. Read report-relative artifacts in this archive; do not
interpret an absent historical temporary path as missing retained evidence.
`source-manifest.json` hashes implementation files; `artifact-manifest.json` hashes
retained validation artifacts. [Forward source readback](forward-source-readback.json)
compares each final independent source manifest with this checkout. Manifests are
snapshots, not signed attestations.

These evaluations do not establish broad model reliability, professional acceptance
or production readiness. Regional profiles are initial summaries, native parsers
inspect documented subsets, scheme deadlines need current authorized rules, and
reviewer/source claims remain unauthenticated. Native target inputs still require
assembly and validation at every handoff. No execution, financial posting, customer
credit, dispute submission, cutover or release approval is implemented.
