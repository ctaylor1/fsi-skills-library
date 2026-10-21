# Insurance Phase 6 verification — 2026-10-04

Offline acceptance evidence tooling is implemented and verified. Insurance remains
at **69 skills**; the scoped portable inventory also includes **four existing shared
Phase 4 owners**. The authoritative current output is the
[reviewed dossier](reviewed-dossier/report.md), backed by
[its snapshot](reviewed-dossier/snapshot.json) and
[the reviewed portable run](portable-reviewed.json).

Actual institution scope, source/method review records, authenticated reviewers and
deployment acceptance were not supplied. All **657 package/gate records remain
not-supplied** in the current 73-package dossier. Software checks are successful;
institutional acceptance and deployment authority remain unestablished.

## Verified checks

| Check | Result | Evidence |
| --- | --- | --- |
| Isolated package execution | 73 packages; 372/372 declared commands passed; no source/install mutation | [Portable report](portable-reviewed.json), [log](checks/portable-reviewed.log) |
| Planned evaluations | 391 explicitly unexecuted entries, excluded from pass counts | `planned_unexecuted` in each package's portable report |
| Insurance repository tests | 156 methods passed, including 70 new evidence/readiness methods and 22 new runner methods | [Log](checks/insurance-tests-final.log) |
| Insurance structure | 69 packages; zero errors/warnings | [Log](checks/insurance-structure.log) |
| Insurance routes/resources | Zero route/migration errors; all 45 specialist copies match | [Routes](checks/routes.log), [resources](checks/specialist-resources.log) |
| Focused code lint | F and E9 rules pass for all five new tooling/test files | [Log](checks/lint.log) |
| Prior work preservation | 4,452 protected prior files unchanged; all 73 package digests unchanged between initial and reviewed runs | [Preservation](preservation.json), [baseline](baseline.json) |
| Independent forward use | Seven preserved attempts, including overwrite refusal and two corrected-report replays | [Review](forward/review-notes.md), [final readback](forward/reviewed-readback-verification.json) |

A whole-library structural snapshot observed 370 packages with zero errors and six
warnings for concurrent Asset Management packages not yet in the catalog. See
[the observed snapshot](checks/structure.log). This is not an Insurance failure or
a claim that unrelated implementation is complete; those files were not altered.
No whole-library runtime, human acceptance or production-readiness claim is made.

The 156-method run includes unchanged earlier Insurance tests. The 372 isolated
commands also invoke package-native tests, so these counts are different layers of
verification and must not be added together as independent cases. No planned
natural-language evaluation was relabeled as an executed case.

## Evidence and independent review

The initial and intermediate `portable-initial.json`, `portable-final.json` and
`current-dossier/` remain historical checkpoints. Formatting and the human-report
usability repair changed the pinned tooling digest. The forward exercise observed
and retained the resulting stale-report failures. The latest authoritative pair is
`portable-reviewed.json` and `reviewed-dossier/`; hashes agree with current scoped
source files. Earlier records were not rewritten to look current.

A fresh agent used only the review guide, schema/templates, public package snapshot
and documented command interfaces. It did not read implementations, tests or intended
answers before constructing its fictional source packet. The exercises verified:

- Empty scope and records preserve all required gates as not-supplied.
- A fictional accepted source-review record labeled synthetic remains unresolved;
  neither a named fictional reviewer nor an accepted assertion becomes approval.
- A different program and subsequently altered evidence file surface scope mismatch
  and changed evidence, while the original packet and pinned digest remain visible.
- Repeating a command against an existing dossier fails without changing saved bytes.
- The repaired human report exposes record ID, gate, reviewer assertion, dates,
  rationale, evidence references and actual unresolved checks.

The original report omitted per-record reasons and the guide used an unavailable
`python` command on this host. Both were corrected; final readback verifies the
expanded human report and `python3` instructions. The guide now expressly states
that synthetic/unknown evidence cannot supply an institutional review record.
Original observations and artifacts remain in [forward/](forward/review-notes.md).

Independent regression authoring also identified malformed decision/package-name
values and malformed evaluation-manifest shapes that produced unhelpful exceptions.
Those inputs now reject explicitly or produce unresolved findings. Tests additionally
cover omitted gates, duplicate/conflicting receipts, future/expired reviews, missing
or modified proof, traversal/symlink/nonregular paths, forged success flags, omitted
command observations, wrong exits, timeout, mutation and changed source snapshots.

## Reproduction

Run from the repository root in the normal project Python environment, using fresh
output names rather than overwriting any checked-in evidence:

```sh
python3 -B -m unittest discover -s tools -p 'test_insurance*.py'
python3 tools/run_insurance_portable.py --output /tmp/insurance-portable-new.json
python3 tools/check_insurance_readiness.py --as-of 2026-10-04 \
  --portable-report /tmp/insurance-portable-new.json \
  --output-directory /tmp/insurance-dossier-new
```

Use the actual date for a new institutional review. The current repository test suite
needs its normal dependencies (including PyYAML); the new readiness tools and isolated
skill programs use the standard library. A zero dossier exit only confirms artifact
creation/readback. Inspect its explicit evidence states and authority fields.

The new [source manifest](source-manifest.json) and
[evidence manifest](evidence-manifest.json) identify this checkpoint's bytes. They do
not authenticate sources, reviewers or permissions. Historical phase archives and
skill runtimes are unchanged. Scope includes neither actual institution acceptance,
external-workbook reconciliation, additional regional methods nor comprehensive
health-payer expansion. No commit, release, external communication, connection,
regulated decision or deployment was performed.
