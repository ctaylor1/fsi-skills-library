# Independent insurance Phase 4 forward design evaluation

Date: 2026-09-20. Evaluator originated Cedar Harbor Mutual, a fictional commercial-property FNOL case, using fresh raw records rather than bundled examples, test cases or intended answers. Repository was read-only. No external systems, network, live customer information or business actions were used.

## Read and executed scope

Used repository packages `skills/insurance/insurance-workflow-designer`, `insurance-data-product-designer`, and `insurance-core-modernization-planner`. Read their SKILL.md, schema, domain rules, controls, source maps, handoffs and templates; read shared workflow contract/foundation and implementation to learn CLI behavior. No standalone installs were found in ~/.codex/skills, so results apply to the repository package snapshot. No eval fixture or test input was read.

`REQUESTS.md` is the fresh request set. `raw-sources.json` and `raw-gap-addendum.md` are the actual raw synthetic source records. Explicit version/date/owner metadata and REV-4 review-method scope are retained. Source locators are local JSON sections, not live connections. Raw records were not revised to justify native results.

## Practitioner deliverables

- `workflow-deliverable.md`: current and target routes, source contract, bounded retry/recovery, arithmetic, v3 access-review gap and pilot owner questions.
- `data-deliverable.md`: semantic/temporal contract, exact claim/policy link, early and late query result, conflict and source-audit correction.
- `core-deliverable.md`: options, declared cost horizon, historical-form preservation, one migration wave, −1 form-row break, failed acceptance, rollback after new writes and missing evidence.

## Results and failures retained

| Case | Native status | Findings / independent assessment |
|---|---|---|
| workflow-complete | ready-for-review | Current weighted 17.60 human / 49.00 elapsed, target 8.30 / 22.80 minutes. Independently correct serial weighted arithmetic. Scenario assumptions, not measured benefit. |
| workflow-access-gap | needs-data | Schema amendment lacks access review. All time results null. Correct withholding. |
| data-early | ready-for-review | CP-2026 from A2 at valid July 1 / known June 10. Conditional arithmetic/selection correct; first mapper over-asserted review/completeness. |
| data-conflict | needs-data | At known September 20, A2 and A3 overlap. Native keeps both record identities and withholds value. |
| data-source-audited | needs-data | Corrected unsupported purpose-review and inventory-completeness assertions to null, preserving failure. The current source-bound contract is not accepted. |
| core-rehearsal | needs-review | $240,000/$390,000 component sums and −1 row correct; replacement misses mandatory DELTA; two failed gates retained. First mapper over-asserted complete inventories. |
| core-delta-gap | needs-data | Contrary prior delta narrative retained; absent evidence blocks dependent metrics. |
| core-source-audited | needs-data | Corrected unsupported inventory/cost-completeness claims to null. Full business-case comparison is not accepted. |

All eight native runs return 0 on input/calculate/output stages, including needs-data artifacts. That is expected structural behavior, not a pass on practitioner acceptance. Complete originals remain alongside corrected copies.

Negative checks:

- `tampered-workflow-output.json` changed computed human time without updating retained input. Output validation rejected it, exit 1.
- `invalid-boolean-retries.json` supplied true as a numeric retry count. Input validation rejected it, exit 1.
- `unsupported-mapped-cost.json` deliberately changed FACADE implementation cost from raw $180,000 to $1 while keeping the source reference. Calculation and recomputation validation both returned 0. The resulting $60,001 is unsupported by raw evidence and must not enter the deliverable as a fact. The validator compares native retained evidence, not local source locator contents. This is a documented boundary exposed in a concrete probe, not an unexpected arithmetic defect.

## Acceptance judgment

Bounded calculations, explicit adverse findings, null handling and immutable-output validation worked in these cases. The three authored work products are useful drafts, and the source audit improved their fidelity. Source-to-native mapping is a real human/agent failure surface: the evaluator initially supplied unsupported affirmative flags even while following a source-bound workflow. The skill's prohibition on invented observations caught this in review, but CLIs cannot detect it from valid native fields. Do not report the initial ready-for-review outputs as source acceptance.

Global withholding is conservative: a delta-evidence gap also nulls independently supplied option sums and count differences. The deliverable can retain raw observations with explicit limits, but cannot imply the package accepted a full comparison. Temporal assertions detect overlap; actual correction/supersession semantics remain a data-owner design question. No professional, institutional, accessibility, privacy, deployment or production acceptance is established.

## Reproduction and record

Exact initial generation commands:

```
/tmp/fsi-p0-venv/bin/python /tmp/insurance-p4-forward-design/build_cases.py
/tmp/fsi-p0-venv/bin/python /tmp/insurance-p4-forward-design/run_cases.py
/tmp/fsi-p0-venv/bin/python /tmp/insurance-p4-forward-design/negative_checks.py > /tmp/insurance-p4-forward-design/negative-checks-console.txt
/tmp/fsi-p0-venv/bin/python /tmp/insurance-p4-forward-design/source_fidelity_corrections.py
```

`commands.json` retains every package command, stdout file, stderr file and exit code (28 invocations: 24 across eight cases and four negative-check calls). Each command is an absolute invocation of the repository package script. Native `*.output.json` files are immutable outputs; prose was authored separately. `negative-checks-console.txt` retains the full negative-check console. Each stderr file is kept even when empty. Reproduction scripts overwrite their deterministic files; preserve the current directory first if replaying. Do not rerun `run_cases.py` after adding corrected cases if you require the identical historical 28-invocation ledger, because its glob now includes corrected inputs.
