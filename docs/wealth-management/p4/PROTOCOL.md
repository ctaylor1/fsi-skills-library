# Wealth management P4 model-evaluation protocol

This protocol measures retained model behavior on declared synthetic practitioner
cases. Package tests establish software behavior; they do not establish model task
quality. The artifact harness never calls a model, judges financial meaning by
keywords, approves a financial action, or substitutes for professional review.

## Scope and predeclared comparison

Freeze the 27 practitioner packages named by the router, plus the router itself.
The snapshot inventories and hashes every package file except operating-system and
Python cache files. It separately hashes the operational exposure: SKILL.md,
references, scripts and assets. Evaluation fixtures, golden answers, regression
scripts and test scripts remain outside model exposure. The full frozen snapshot
is for the supervisor and reviewers; it is not a model working directory.

The initial protocol contains 12 cases with two conditions each: **24 expected
first-pass runs**, including runs that have not started or fail. A case can exercise
several skills. Report the number of distinct case-targeted practitioner packages
against the 27-package inventory. Merely exposing the router does not test every
route, and a successful combined case does not independently certify every skill.

Each paired case uses the same substantive task, source packet, tool policy,
requested model and reasoning setting. The with-skill condition additionally gets
the router and declared relevant operational packages. The without-skill condition
gets no packages. The condition-specific instruction about available packages is
explicit and hashed. This is an aided task-quality comparison with a supplied
relevant subset, not a blind test of selecting from the full skill catalog.
Baseline routing credit may use semantically equivalent task names; it must not
depend on knowing package slugs that were withheld.

Run each condition in a fresh context and isolated working directory. Copy only
that condition's prepared files, never its parent directory. Do not expose hidden
rubrics, prior responses, reviewer corrections, repository paths, credentials or
host skills. Use local reading, computation and drafting only; no network or
external actions. Retain command/configuration and runtime events so requested
isolation and actual tool behavior can be distinguished. Filesystem isolation
claims must describe the runtime's real boundaries; a fresh directory alone is
not proof of an inaccessible host filesystem.

The available local CLI accepted the requested **GPT-5.5 / high** configuration;
installed CLI 0.151 rejected the configured Astra model. This is an explicit
runtime fallback without a user installation/configuration change. Record this
as the *requested* model. Where the runtime does not return a resolved backend
model identity or snapshot, reported identity is **unknown**, even if the request
completed. Do not convert request acceptance into a server-reported model claim.

## Reproducible local commands

Use Python 3.10 or later; the harness uses only the standard library. Existing
destinations are never overwritten. Paths below are examples outside the repo's
user-owned `temp/` directory.

```sh
python -B tools/wealth_p4_eval.py snapshot --out /private/tmp/wealth-p4-snapshot
python -B tools/wealth_p4_eval.py prepare \
  --snapshot /private/tmp/wealth-p4-snapshot \
  --cases docs/wealth-management/p4/cases \
  --rubrics docs/wealth-management/p4/rubrics \
  --experiment-id wealth-p4-initial \
  --out /private/tmp/wealth-p4-initial
python -B tools/wealth_p4_eval.py validate /private/tmp/wealth-p4-initial
python -B tools/wealth_p4_eval.py summarize /private/tmp/wealth-p4-initial --format markdown
```

`snapshot` reads the router's literal route map without importing or executing
package code. `prepare` freezes cases/rubrics before generation, creates the full
expected run set and missing-run templates, and exports condition folders.
`validate` verifies artifact integrity; exit 0 can describe an **incomplete**
experiment with valid missing-run records. Always read `artifact_status` and the
denominators. Structural, binding, citation or retained-file errors return exit 1.
`summarize` reports first-pass and revised results separately; it does not score.

Preserve `conditions/` unchanged. Execute copies in separate directories and retain
responses/logs elsewhere under the experiment. The experiment can be retained as
one ZIP with `manifest.json` at its root; `validate` and `summarize` accept that ZIP
directly, and `prepare --snapshot` also accepts a ZIP snapshot. The archive reader
rejects path traversal, symlinks, duplicate entries and excessive expansion.
Use the same frozen artifacts and preparation recipe to replay a run. The tool
does not install dependencies, call an API, or run the model for you.

## Case and hidden rubric interface

Case JSON in `cases/`:

```json
{
  "schema_version": "wealth-p4-v1",
  "case_id": "P4-01",
  "title": "A meaningful practitioner case",
  "skill_ids": ["wealth-management-router", "investment-risk-profile-reviewer"],
  "prompt": "The actual task, without the answer or grading hints.",
  "source_packet": [
    {"source_id": "S1", "content": "Natural-language source record.", "reference": "Synthetic attributed record"}
  ],
  "conditions": ["with-skill", "without-skill"],
  "rubric_id": "P4-01-RUBRIC"
}
```

The public model folder contains only `prompt.txt`, `source_packet.json`, and the
condition's operational skill files. Internal identifiers and `rubric_id` do not
cause hidden rubric content to be copied. Synthetic source records should give
substantive evidence and realistic gaps rather than pre-shaped domain output JSON.
Untrusted source instructions are facts to evaluate, never permission to act.

Separate rubric JSON in `rubrics/` contains matching schema_version, case_id and
rubric_id and a nonempty `items` array. Each item is:

```json
{
  "item_id": "AUTHORITY",
  "criterion": "Keeps unresolved authority visible and does not approve payment.",
  "severity": "critical",
  "required_evidence": "Specific supported findings and the relevant action boundary."
}
```

Severity is `critical`, `major` or `minor`. Optional grader-only `expected_routes`,
`numeric_checks` and `limitations` remain in the hidden rubric. Numeric checks
record the input source IDs, arithmetic, expected value, unit and tolerance. They
guide independent review and are not automatic keyword or text-match graders.
Changing a frozen case or rubric requires a new experiment and new input hashes.

## Run record and retained evidence

The generated supervisor manifest contains exact file inventories, the frozen
snapshot hash, case/rubric hashes, paired expected run IDs and tool policy. Run
templates live in `runs/<case_id>--<condition>.json`. Preserve their `bindings`
and `manifest_sha256` unchanged when ingesting output. Bindings include:

- case JSON and substantive case prompt hashes;
- full condition prompt and source-packet byte hashes;
- hidden rubric and whole snapshot hashes;
- exact exposed skill hashes and their combined manifest hash. The baseline map
  is explicitly empty, not a missing skill inventory.

Executed run metadata requires a distinct `generator.identity`; a reported model
object with availability `known|unknown`, provider, model_id and evidence_refs;
execution status `completed|failed|missing`; UTC `started_at`/`ended_at` ending `Z`;
explicit isolation declarations and retained runtime evidence. Freeze chronology
must satisfy snapshot <= experiment <= execution <= review. Model availability
`unknown` requires null provider/model_id. `generator.requested_model` separately
records provider, model_id and reasoning_effort; it never proves actual identity.
Additional runtime metadata can retain CLI version, commands, notices and usage.

Every retained evidence reference is `{path, sha256}`, relative to the experiment
root. The harness checks file existence, exact hashes and path containment. A
recorded hash is an integrity check, not a digital signature or source attestation.
Keep the initial manifest hash in the supervising validation record or release
record so changing the entire experiment cannot silently redefine the baseline.

Example first-pass attempt inside the run's ordered `attempts` array:

```json
{
  "attempt_id": "first-pass",
  "stage": "first-pass",
  "parent_attempt_id": null,
  "status": "completed",
  "started_at": "2026-09-17T15:00:00Z",
  "ended_at": "2026-09-17T15:01:00Z",
  "response": {"path": "retained/P4-01--with-skill/response.md", "sha256": "actual-file-hash"},
  "evidence_refs": [{"path": "retained/P4-01--with-skill/events.jsonl", "sha256": "actual-file-hash"}],
  "tool_usage": {"status": "none", "events": []},
  "repair": null
}
```

The example placeholders must be replaced by computed hashes. Completed attempts
need nonempty responses; failed attempts can retain partial output or null.
An attempt may additionally retain `generated_artifacts: [{path, sha256}, ...]`.
Keep the final message and these files separate. When the final message delivers
a report by linking a generated file, review that actual report as part of the
answer. Do not grade only its short delivery wrapper, synthesize a replacement
answer, or reward internal code as if it were the requested professional memo.
For audience-specific work, inspect the actual file intended for that audience.
Tool usage is `used|none|unknown`. Used tools require events with tool, description,
status `succeeded|failed`, started_at, ended_at and evidence_refs. If events lack
wall-clock timestamps, retain run-bounded timestamps and explicitly label their
precision. Unknown tool use excludes the run from metadata-comparable observations.
Execution declarations are not automatic proof that all tool commands complied.

A revised attempt follows the first-pass record, uses stage `revised`, references
the immediately previous attempt through parent_attempt_id, and includes
`repair: {reason, requested_by, evidence_refs}`. Keep separate response files.
Record human edits, schema repairs, reruns, retries and additional evidence;
do not relabel a repaired answer as first-pass. A failed execution stays failed
in summary counts even if its partial answer received a favorable review.

## Independent item-by-item review

After freezing output, give an independent reviewer the source packet, response,
rubric and necessary traces. The generator must not grade its own response. The
review declaration identifies reviewer, kind `human|model`, independence from
generation, reviewed_at and retained review evidence. Model-assisted review is
not domain-SME, legal/compliance, or institutional acceptance.

Record source ambiguities and root adjudication explicitly. Where the packet does
not supply a convention, a transparent conditional calculation that includes the
required result can satisfy the semantic criterion. Do not manufacture certainty,
equate omitted provenance with an approval, or silently change frozen cases or
rubrics. Additional diagnostic findings outside a narrowly specified rubric must
remain visible as additional findings rather than being retroactively scored.

Store reviews at `reviews/<run_id>--<attempt_id>.json` with schema_version, run_id,
attempt_id, reviewer, reviewed_at, evidence_refs and `items`. Review `bindings`
must equal `{manifest_sha256, response_sha256, rubric_sha256}`.
When the attempt includes generated_artifacts, bindings must additionally include
`generated_artifacts_sha256`, the canonical object hash of that exact reference
list (including an explicitly empty list). Every generated file's bytes are also
validated. Citations into such files use `artifact: "generated"` plus `path`, which
must match a retained generated-artifact reference.
Reviewer identity must differ from generator identity and
`independent_from_generation` must be true.
This validates declared separation, not authenticated human identities.

Every rubric item must appear exactly once, including those not assessed:

```json
{
  "item_id": "AUTHORITY",
  "verdict": "pass",
  "rationale": "The answer identifies the cited authority gap and leaves payment to the responsible human.",
  "evidence": [
    {"artifact": "response", "line_start": 8, "line_end": 8, "quote": "Exact text from response line 8."},
    {"artifact": "source", "source_id": "S1", "line_start": 2, "line_end": 3, "quote": "Exact source text."}
  ]
}
```

Line numbers are one-based, inclusive and refer to the retained response text,
generated deliverable, or source item's `content`. Pass/fail requires response or
generated-deliverable evidence and a rationale. Source evidence may supplement it.
Source citations may set `source_field: "reference"` to cite attributed metadata,
such as an owner named in the reference. The only permitted values are `content`
and `reference`, with `content` the default. Spans and quotes refer to the selected
field's exact text; content cannot be presented as a reference quotation.
To establish a material omission, cite the
complete response or the relevant section and explain the absent required work.
`not-assessed` may omit citations but needs an explicit reason. The harness checks
that the quotes occur in those lines. It does **not** decide whether the cited text
meets the criterion. Reviewers must examine arithmetic, scope, assumptions, sources,
privacy and action boundaries substantively, including contradictory passages.

Any failed item makes the reviewed attempt fail. Otherwise an unassessed item
makes it not-assessed; only a complete all-pass review yields pass. Critical
failures remain separately listed. No severity weighting or opaque composite
score can mask a critical failure. Missing reviews remain unreviewed.

## Reporting and acceptance limits

Reports preserve the full denominator per condition: missing, failed runtime,
invalid artifact, unreviewed, not-assessed, pass and fail. Revised attempts have
their own counts. Pair tables are descriptive first-pass observations; differences
cannot establish causality or statistical significance. Report sample construction,
case-targeted coverage, requested and reported model identity, tool failures,
privacy/authority failures and all repair rates alongside any quality judgments.
Known matching model metadata and affirmative isolation/tool declarations are
necessary for the narrow `metadata_comparable` flag; that flag is not scientific
comparability or proof of a controlled experiment. Unknown backend identity remains
visible even when every request used the same requested model setting.

Freeze the case/rubric set before generation. Retain failures. Do not tune rubrics
after seeing outputs, select the better condition order after results, or discard
difficult cases from denominators. A subsequent change is a new round with its
own snapshot and case versions. Professional acceptance, broader representative
testing and live deployment validation remain separate work.
