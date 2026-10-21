# P5 retained evidence

Recorded 2026-10-04, America/New_York. Both archives are `complete-reviewed`:
every expected writer run completed and has bound, complete independent-review
decisions. **This is artifact validity, not a behavioral pass.**

| Experiment | Sessions | Item passes with / without skills | Whole-case passes with / without skills |
| --- | ---: | --- | --- |
| [Initial six paired cases](initial-summary.json) | 12 | 48/60 / 52/60 | 0/6 / 3/6 |
| [Separate estate follow-up](estate-followup-summary.json) | 2 | 9/10 / 10/10 | 0/1 / 1/1 |

The follow-up reuses P5-02 after an estate correction; it is not a new holdout and
does not replace the initial result. Exact backend model identity is unknown in
every run. All 140 item decisions are model-reviewer judgments, not human
professional acceptance. See the [validation report](../../P5-VALIDATION.md).

## Archives

- [Initial experiment](wealth-p5-20261004.zip), SHA-256
  `b6475217fcd73debe19fd4ee9c0f5f609d45fe036af8e98c4c618f31aa2191f9`.
- [Estate follow-up](wealth-p5-estate-followup-20261004.zip), SHA-256
  `296c2dd54a8173af9ed75a57a4f3ea5628ab7a332332e6f4814b03554dd9aeaf`.

[artifact-index.json](artifact-index.json) records byte sizes and manifest hashes.
Each archive contains frozen prompts, skill exposure, cases, rubrics, source
resources, original writer outputs and generated files, runtime traces, final
review records and review history. Both archives were extracted and their reports
matched the saved summaries.

The initial archive also contains the unchanged P5-03 writer's source-field and
combined-gate audit under `control-audit/P5-03--with-skill/`: 93 reviewed fields,
82 qualified, 11 withheld, seven unresolved plan pointers, and no reviewed
recipient file. Its `REVIEW.md` distinguishes semantic failures from representation
limits and documents reviewer independence limits. These are separate findings
from initial rubric scoring.

From the repository root, reproduce artifact validation and summaries:

```sh
python3 tools/wealth_p4_eval.py validate docs/wealth-management/p5/results/wealth-p5-20261004.zip
python3 tools/wealth_p4_eval.py summarize docs/wealth-management/p5/results/wealth-p5-20261004.zip --format markdown
python3 tools/wealth_p4_eval.py validate docs/wealth-management/p5/results/wealth-p5-estate-followup-20261004.zip
```

## Software and preservation

- [Final commands and results](software-checks/checks.json): 370 wealth test
  methods, 173 executable package checks, 27 package structure checks, portable
  resource synchronization, focused correctness lint and handoff checks.
- [Independent control review](control-review.md): receipt type confusion,
  numeric edge cases and repaired control behavior.
- [Final estate replay](estate-final-replay.json): final 0.2.2 repair, 22 regression
  methods, six native evaluations, exact unchanged-candidate output preservation,
  and the explicit absence of a model run with the final comparison repair.
- [P4 preservation](preservation.json): all 39 original P4 files retain their
  hashes. No assertion is made that concurrent work in other domains was unchanged.
- `software-checks/historical-*` logs retain earlier successful snapshots and
  intermediate runtime/catalog failures. The final scoped checks supersede those
  failures; older whole-repository totals are not current whole-repository claims.

Use synthetic inputs only when reproducing this evidence. Artifact hashes bind
recorded content; they do not authenticate source truth, reviewers, permissions,
model identity or professional authority. No recipient delivery or account action
was performed.
