# Insurance Phase 4 validation — 2026-09-20

Implementation and bounded verification are complete. This record covers three new
Insurance packages, four shared packages, routing, portable runtime resources and
actual native receiver adapters. The catalog contains **303 packages**, including
**64 Insurance packages**. See [the implementation record](../PHASE4-IMPLEMENTATION.md).
No production connector, operational workflow, regulated decision or business
transaction was activated.

## Final checks

| Check | Result | Evidence / command |
| --- | --- | --- |
| Package structure and metadata | 303 valid; zero errors/warnings | `python tools/validate_skills.py`; `checks/validate-final.log` |
| Whole-library executable package checks | 1,552 passed; zero failed | `python tools/run_selftests.py`; `checks/selftests-final.log` |
| Repository tooling tests | 377 passed | `python -B -m unittest discover -s tools -p 'test_*.py'`; `checks/tool-tests-final.log` |
| Phase 4 native methods | 130 passed inside 35 package commands | Seven package `scripts/test_domain.py` programs; `checks/phase4-selftests-final.log` |
| Phase 4 integration | 15 passed, included in repository test total | `python -B tools/test_insurance_phase4.py`; `checks/integration.log` |
| Portable bundles | 44 workflow resources, 64 Insurance references/helpers, 38 earlier foundation bundles match | `tools/sync_workflow_resources.py --check`, existing Insurance sync checks |
| Handoffs and routes | Zero dangling references or Insurance route/migration errors | `tools/check_handoffs.py`, `tools/check_insurance_handoffs.py` |
| Focused defect lint | F and E9 rules pass on new/modified runtime and integration files | `checks/structure-and-lint.log` |
| Final frozen forward replay | 18/18 reviewed results match; 54 native calls pass | `final-replay/report.json`, `checks/replay.log` |

Counts overlap. A valid needs-data artifact is an expected successful command, not
acceptance of its evidence or conclusions. The 130 native methods are invoked by
the package suite; the 15 integration methods are part of 377 repository methods.
Ruff coverage is explicitly F/E9. An initial unrestricted run also raised broader
import/style/exception-policy suggestions, including in inherited portable code;
this record does not claim unrestricted Ruff conformance.

## Independent forward work

Two independent evaluators originated fictional source records from realistic
requests, read the packages, prepared native inputs, ran the actual CLIs and wrote
practitioner deliverables. Their original failures remain in place.

- [Design review](forward/design/README.md): workflow paths, temporal data contracts
  and migration options/rehearsals; eight native cases plus four negative calls.
  Read the [workflow](forward/design/workflow-deliverable.md),
  [data](forward/design/data-deliverable.md) and
  [core](forward/design/core-deliverable.md) drafts with their disclosed source audit.
- [Measurement review](forward/measurement/README.md): architecture, automation,
  data value and queue performance; ten final cases, thirty exact-input repair
  calls and 74 independent arithmetic/source-retention/authority assertions.
  Current drafts are in [repairs](forward/measurement/repairs/architecture-draft.md):
  [automation](forward/measurement/repairs/automation-draft.md),
  [data value](forward/measurement/repairs/data-draft.md) and
  [operations](forward/measurement/repairs/operations-draft.md).

Parent review read the practitioner outputs and source-audit records, checked the
raw-arithmetic audit and compared the final native replay with the reviewed outputs.
The replay includes original diagnostic examples as well as corrected source-audit
cases; output identity does not retroactively accept an unsupported original input.

## Findings, repairs and residual limits

1. **Input documentation:** profile nesting and exact mode/control IDs were unclear.
   Schemas now specify `data.profile` and conditional enums/fields. Evaluator mapping
   corrections are disclosed separately from newly authored fictional supplemental
   source evidence; they are not represented as unchanged-input code repairs.
2. **License-result dependency:** unknown projection assumptions or an invalid
   benchmark could incorrectly change the supplied-license usability flag. Its
   evidence check now stands separately; invalid comparisons/projections remain
   null. Byte-identical original inputs verify the repair.
3. **Unfinished episode costs:** unknown open-work costs hid queue counts and
   completed-cohort results. Non-completed episodes no longer require cost/labor;
   original nulls remain unchanged. Only actual completed-cohort amounts enter means.
4. **Queue control discrepancy:** known closing-control breaks now explicitly emit
   `snapshot_reconciled=false`. Retained figures are extract-only, with needs-review;
   method text and practitioner drafts say so. Unknown completeness still blocks
   dependent metrics.
5. **Source-to-input fidelity:** the design evaluator initially inferred affirmative
   purpose/completeness flags from a purpose statement or list of records. Those
   original outputs remain. Corrected source-audited inputs use null and yield
   needs-data. Entry instructions now require explicit source statements/locators
   for affirmative review, permission and completeness flags. This instruction
   repair is not claimed as proof that another model will never repeat the error.
6. **Recomputation boundary:** deliberately changing a mapped cost to $1 while
   retaining a source ID passed native output validation. The raw-source mismatch
   is retained as a negative demonstration. Validators bind native input/output;
   they cannot authenticate the source or verify arbitrary source-locator semantics.

The author also corrected Decimal intermediate rounding in cash-value arithmetic,
required matching migration control scope/cost horizons, and blocked dependent
recommendations when upstream uncertainty or an unmapped scope change remains.
The initial integration harness incorrectly assumed the existing lineage validator
printed JSON; it actually prints a text report. The corrected harness accepts its
native protocol without changing that existing package. The failed initial
repository run remains at `checks/tool-tests-initial.log`.

The measurement evaluator disclosed a search that incidentally returned three test
implementation lines; no test fixtures or expected datasets were used to originate
facts. Its package snapshot was captured during editing and is not represented as a
pristine pre-repair archive. See [full findings](forward/measurement/FINDINGS.md).
No broader holdout, cross-model, real-institution or representative-benefit claim
is made from these tiny diagnostic samples.

## Reproduction and integrity

Use Python 3.10+ with repository validation dependencies. This run used
`/tmp/fsi-p0-venv/bin/python`. Package CLIs need only their bundled standard-library
resources. Commands and raw stdout/stderr are retained with each review. Paths in
historical command ledgers identify the actual original temporary workspaces.

Run `python tools/run_insurance_phase4_forward.py` to compare all 18 frozen inputs
with their reviewed native outputs in a fresh temporary directory. Supply
`--output /new/empty/path` to retain replay evidence; the runner refuses to overwrite
an existing nonempty destination. Do not rerun historical authoring scripts over
these archives. Preserve new attempts separately.

`baseline.json` records the starting content. `preservation.json` identifies the
few intentional existing-file edits and verifies other baseline files. The source
and evidence manifests retain SHA256 content identity for the final checkpoint.
Historical Phase 1–3, Payments and Wealth evidence was not regenerated.

## Acceptance still required

Named practitioners and institution/control owners must verify actual sources,
field mappings, profiles, privacy/licensing, review flags, methodology and authored
reports. Deployment needs real connector identity/access, least privilege, recovery,
monitoring, operational testing and measured benefit evidence. The external source
workbook needs reconciliation. Conditional Phase 5 and unrelated Wealth/Payments
acceptance items remain open. Passing software checks does not grant these approvals.
