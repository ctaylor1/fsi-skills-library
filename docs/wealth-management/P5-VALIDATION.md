# Wealth management P5 validation

Date: 2026-10-04 (America/New_York).

**P5 implementation and its evaluation are complete; behavioral acceptance is not
achieved.** Eleven existing skills now have portable source-field review,
recipient projection and combined draft-review controls. No skills or practitioner
coverage were removed. Fourteen real-model writer sessions and all 140 rubric
decisions are retained. The initial skill-assisted outputs passed 48/60 criteria
and 0/6 complete cases; the baseline passed 52/60 criteria and 3/6 cases.

These observations do not demonstrate improvement from skills. The cases are
purposive, there is one writer per condition and case, and the exact backend model
identity is unavailable. The results identify concrete work still needed.

## Implemented controls

P5 addresses the two Q0 findings in [P4](P4-VALIDATION.md): unsupported facts in
structured inputs and insufficient isolation of restricted working artifacts.
The [implementation record](P5-IMPLEMENTATION.md) identifies all eleven packages.

- The evidence gate inventories every candidate leaf and empty container, binds
  separate field judgments to the source packet and candidate, checks exact
  source spans or values, and supports bounded derivations and explicit unknowns.
  An unsupported or unreviewed field withholds the complete projected input.
- The audience gate projects one exact recipient set using supplied permission
  dates and transitive source/content dependencies. Restricted content and its
  diagnostic metadata remain outside the recipient rendering.
- The combined gate requires claim links to reviewed candidate fields and a
  separate review of actual prose, dependencies and recipient scope. It validates
  final UTF-8 bytes. Missing or failed review emits no reviewed recipient file.

Canonical controls and guidance are copied into each package for standalone use.
Legacy calculators remain available; their successful validation is insufficient
for P5 clearance. The repository does not enforce deployment access or compel
every caller to use the combined gate.

## Frozen experiment and results

Six new synthetic advisor cases contain 32 source records, 60 rubric items and
33 numeric expectations per condition. The [case freeze](p5/case-freeze.json)
binds all 18 case, rubric and typed-resource files before execution. Both
conditions received identical source records and explicit permission evidence;
only the with-skill condition received operational skill resources. Hidden
rubrics were outside writer directories.

| Case | Advisor task | With skills | Without skills | Material observations |
| --- | --- | ---: | ---: | --- |
| P5-01 | Household goals and first investment mandate | 7/10 | 10/10 | With skills invented IPS requirements, omitted the 398,000 net-assets result and used unresolved artifact aliases. |
| P5-02 | Tax lots and missing estate classifications | 9/10 | 10/10 | With skills populated unsupplied estate policy requirements and document links, creating an unsupported mismatch. |
| P5-03 | Applicability sign-off versus completed recommendation review | 9/10 | 9/10 | Both conditions added an unsupported currency. Quoted fee arithmetic was correct. |
| P5-04 | Unknown protection observations and routing signature | 8/10 | 10/10 | With skills dropped the original observation artifact, issue code and assignee in the handoff. |
| P5-05 | Advisor, service and joint-client work products | 8/10 | 7/10 | With skills asserted unknown approval/working fields and left raw working files without exact recipients. Baseline omitted original fee/private issue IDs and codes; fee amounts and variance were correct. |
| P5-06 | Family facilitation and trust work across four audiences | 7/10 | 6/10 | With skills invented reviewer/date and policy facts, left a mixed working manifest without an exact audience, and omitted agenda totals. Baseline also omitted handoff, request and authority details. |
| **Initial total** | **Six paired cases** | **48/60; 0/6 whole cases** | **52/60; 3/6 whole cases** | All twelve writers completed; all 120 initial item decisions are reviewed. |

The audience failures concern access assignments on working artifacts. The
designated client/service/family reports were clean in those cases; this is not a
claim that restricted prose was actually delivered to an unauthorized person.
P5-01's handoff failure concerns unmapped local aliases, not fabricated historical
approval. P5-04's composite transaction labels were treated as local bookkeeping
with a caveat, not automatically as invented historical identifiers. The retained
review history records these adjudications.

Ten practitioner jobs receive fresh model coverage. Protection-needs is the
eleventh updated package and receives software checks, with original P4 evidence
preserved rather than a new P5 holdout. Router exposure does not establish
full-catalog routing or task quality.

### Estate correction and separate follow-up

The first estate failure exposed schema pressure to invent facts. Version 0.2.1
adds explicit null handling for unknown policy ownership, required review
inventories, recorded ownership and document links. Unknowns produce open
questions and skip unsupported completeness or comparison claims. Known-input
fixtures remain compatible.

Two new cold writer sessions repeated the unchanged P5-02 case and rubric with
this correction. The with-skill output retained the targeted unknown fields but
still inferred account ownership from the person who purchased securities. It
scored **9/10**, versus **10/10** for baseline. These 20 follow-up decisions are
separate from the initial 120; this is a reused diagnostic case, not a new holdout.

A subsequent deterministic review found that an unknown designation with no
record could still be compared as an empty beneficiary list. Final version
**0.2.2** only compares established records or an explicit no-record assertion.
Its 22 regression methods and six executable evaluations pass. Replaying the
unchanged follow-up candidate produces exactly the frozen output: `needs-data`,
one supported title mismatch and 15 open items. That candidate does not exercise
the newly repaired branch; dedicated regressions do. **No model was prompted
with 0.2.2.** See [final replay evidence](p5/results/estate-final-replay.json).

## Actual-writer end-to-end control audit

A separate model reviewer assessed all **93 candidate fields** from the unchanged
P5-03 with-skill output against the detached source packet. The gate qualified
82 fields and blocked 11. Two fields asserted unsupported USD units; one
conservative judgment withheld numeric zero for “no exit fee recorded.” That
third interpretation is explicitly debatable and is not an established
arithmetic error. Eight withheld fields were legitimate metadata or representation
incompatibilities with the narrow evidence schema, exposing a usability limit.

The audit also found seven content-plan pointers missing from the candidate leaf
inventory: three calculations in another file and four container references.
The combined gate stopped at the blocked field review, before reaching these
plan errors. The audience-only replay matched exact bytes, but combined assembly
and verification failed and **no reviewed recipient draft was created**. A
different human-readable memo received no transferred clearance.

The initial archive retains the field decisions, original-copy hashes, frozen
controls, six CLI operations and replay under
`control-audit/P5-03--with-skill/`. This demonstrates one useful blocked handoff
on actual model output, not a successful general workflow. Its reviewer was
separate from generation but authored supporting controls; review was not blind.

## Runtime and review limits

Requested model: `gpt-5.5`, reasoning `high`, through installed Codex CLI
`0.151.0`. The runtime accepted the request but did not return a resolved backend
snapshot. All fourteen runs therefore have unknown actual model identity and
zero metadata-qualified comparisons. Scores are descriptive review judgments.

Writers ran in fresh directories without resume, configured to disable host skill
discovery, external tools and network access inside their sandbox. Runtime
warnings and host-service startup failures mean configuration is not proof of
complete host-discovery isolation; no agent host-skill reads were observed in
audited traces. This was not a private read filesystem enforced by the operating
system. Reviewers audited retained traces.
P5-06 baseline attempted two writes outside its working directory containing mixed
source data; the sandbox denied them. Its tool-policy match is false. No
successful disclosure is asserted, and its semantic results remain reported
with this limitation rather than discarded.

Reviewers did not generate the evaluated writer outputs. Conditions were visible
and reviewers also authored cases or supporting controls. There was no blinded
qualified-professional acceptance. The harness checks review coverage and
artifact binding, not the truth of reviewers' semantic judgments.

Execution reused the P4 runner. The harness extension freezes and exposes the
same optional public JSON resources in both conditions while retaining old P4
compatibility. The runtime approach follows the official
[Codex command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
and [skill evaluation guidance](https://developers.openai.com/blog/eval-skills).

## Software verification and evidence preservation

Final scoped checks pass; logs and commands are in
[software-checks](p5/results/software-checks/checks.json):

- **370 wealth test methods**, including **106 new P5 tests**: 40 evidence,
  35 audience, 20 handoff/portability, seven public-resource and four case tests.
- **173 executable package checks**, including adjacent manager due diligence.
  Estate's 22 native regression methods are exercised within these commands;
  these counts are not additive independent model evaluations.
- All **27 wealth packages** pass structure validation with zero errors/warnings.
  All 66 helper/reference copies match across eleven portable bundles. All eleven
  versions agree across SKILL metadata, catalog JSON/CSV and approved overrides.
- Focused Python correctness lint passes. The broader inherited style profile is
  not claimed clean. Handoff checking reports zero dangling references in the
  observed 370-package checkout, which includes concurrent work in other domains.

An earlier whole-repository sweep passed 804 test methods and structure validation
of 364 packages. A later intermediate wealth run had two global-inventory failures
while four concurrent asset-management packages were not yet cataloged; the final
370-method wealth rerun passes. Those intermediate logs are retained. The initial
native-check attempt lacked the `python` alias; using the temporary Python
environment resolved that runtime issue. These historical snapshots are not a
claim that all current unrelated domain tests were rerun.

Independent control review found and repaired Boolean/integer receipt
substitution and extreme Decimal underflow/cancellation. Combined controls also
gained iterative dependency traversal, private exclusive file creation and
malformed-input rejection. See [control review](p5/results/control-review.md).

All **39 original P4 files**, including frozen archives, retain their original
hashes under the [preservation check](p5/results/preservation.json). Both P5
archives were extracted, validated and compared with their saved summaries.
`complete-reviewed` means complete valid evidence coverage, not behavioral pass.
See the [evidence index](p5/results/README.md) and
[archive hashes](p5/results/artifact-index.json).

## Remaining acceptance work, in priority order

1. **Source fidelity:** support unknown values across remaining native schemas;
   distinguish local workflow metadata from asserted source facts without forcing
   invented citations. Preserve role, ownership, review date and currency unknowns.
2. **Artifact access:** assign exact authorized people to every working artifact
   and diagnostic receipt. “Operator-only” is insufficient without authenticated
   storage permissions and a concrete authorized set.
3. **Handoff completeness:** carry actual origin IDs, issue codes, assignees and
   unresolved questions; bind calculations from other artifacts and expand
   container claims into reviewable leaves.
4. **Advisor usefulness:** retain requested totals and decision-relevant
   calculations while withholding unsupported conclusions. Test friction from
   metadata restrictions rather than treating every blocked packet as success.
5. **Independent acceptance:** obtain qualified professional review, authenticated
   source/reviewer/permission integration and new holdouts. Repeat broader routing
   and task evaluations after corrections. Q1 specialist-depth and maturity-horizon
   work remains separately prioritized.

Hashes, exact quotations and declarations do not establish source truth, reviewer
identity, entitlement authenticity or professional authority. A retained negative
test demonstrates that a dishonest semantic judgment can pass span checks.
Production use requires authenticated review, enforced storage/delivery controls
and mandatory gate use. This phase makes failure evidence inspectable and adds
bounded controls; it does not certify production readiness or close the Q0
behavioral blockers.
