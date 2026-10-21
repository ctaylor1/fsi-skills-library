# Control repair validation evidence

Completed 2026-10-20 for the four original P1/P2 software findings. The changes are
described in the [implementation record](../control-repairs-implementation.md).
This checkpoint preserves the Phase 1–4 records and does not reinterpret their
historical results as tests of the repaired versions.

| Check | Observed result | Evidence |
|---|---|---|
| Full repository suite, Python 3.12.14 | 1,324 tests passed | [Log](whole-library-tests.log), [exact command](whole-commands.json) |
| Focused Investment Research suite | 414 tests passed | [Log](focused-tests.log), [commands](focused-commands.json) |
| New regression methods | 39 passed: issuer 10, surveillance 21, routing 8 | [Issuer tests](../../../tools/test_ir_issuer_control_repairs.py), [surveillance tests](../../../tools/test_ir_surveillance_control_repairs.py), [routing tests](../../../tools/test_ir_route_contract_parity.py) |
| Isolated standalone packages | 44 packages, 293 declared command checks passed, zero errors | [Report](portable.json) |
| Metadata/specification/references | 395 skills, zero errors and warnings | [Log](skills.log) |
| Native routing parity | 42 public dispatchers, 588 subject probes, 38 profile probes, zero parity errors | [Audit](native-route-audit.json), [structural check](structure.log) |
| Bundled resources and current indexes | Both checks passed | [Resources](resources.log), [index](index.log) |
| Saved catalog regeneration | JSON and CSV byte identical after isolated `--from-current` rebuild | [Proof](catalog-rebuild.json), [log](catalog-rebuild.log) |
| Original failure classes through public commands | Seven replay cases met expectations; accepted outputs reconstructed against retained originals | [Report](after-repair/report.json), [replay source](replay_findings.py) |
| Preservation | All 956 earlier phase evidence files unchanged; no changes outside declared repair ownership | [Audit](preservation.json), [pre-edit baseline](source-baseline.json) |

Counts overlap. The 39 new test methods are included in the focused and full
suites; native probe counts and portable checks are different inventories. Commands
ran offline with supplied synthetic data. Portable copies remove inherited Python
paths and use their bundled resources. The external source workbook was not
reconciled; catalog regeneration proves local reproducibility only.

The [run record](run.json) retains exact interpreter, command outcomes, source and
package manifest hashes and saved-artifact hashes. The pre-edit baseline captured
19,397 files in the initially dirty checkout. Preservation compares those original
bytes, without attributing earlier Git changes to this repair.

## Regressions and actual failure replays

Future reported financial periods reject in issuer credit and surveillance at
intake, calculation and output reconstruction. The tests also cover a cutoff
earlier than economic as-of, UTC date boundaries and labels that attempt to treat a
future forecast/scenario as reported history. Source future/rights gating remains
separate and continues to withhold otherwise computable projections.

Repeated adjustment IDs reject before summation, including exact copies and
conflicting amounts/citations. Independently specified arithmetic checks retain
reported EBITDA and apply legitimate distinct positive/negative adjustments once.
The output test binds a legacy-like candidate to the exact invalid original, so
rejection cannot pass merely through a mismatched original hash.

Routing tests compare actual native validators with advertised subjects for all
42 methods. They exercise supported/missing/unsupported profile values and wrong
selector fields, preserve the two comps schema modes and legacy model-reviewer
mode, and prove that altered subject/profile declarations fail the new structural
guard. The active specialist integration test supplies the explicit structured
model profile. A route remains a plan with no execution or approval.

Spread checks cover missing dates/policy, stale/future/reversed/equal instants,
quote-key mismatches, date-only precision, source publication ordering, timezones,
the exact age boundary and zero-age policy. Invalid comparisons expose neither a
numerical spread change nor its widening alert. Useful financial metrics can
remain partial; an ineligible top-level source still withholds the entire
projection. The historical prior observation is not tested against current-quote
freshness. Original Phase 1 surveillance fixtures remain unchanged.

The [before-repair reproduction summary](before-repair/ir-review-root-public-cli-repros.json)
retains the formerly accepted future periods and duplicated adjustment arithmetic.
New transcripts and outputs live in `after-repair/`; no historical report or golden
was overwritten to suggest the earlier versions had passed these controls.

## Independent fresh skill-use review

A separate agent read the two credit skill contracts and authored new inputs from
raw facts, without receiving intended financial answers or prior conclusions.
It froze both packages and independently calculated expected values using rational
arithmetic. The [review](forward-review/review-report.md) retains 34 fresh cases,
57 numerical/boundary checks, eight integrity probes and 105 actual public command
invocations, including expected failures. All declared checks met their stated
expectations. The [summary](forward-review/summary.json), [synthetic research draft](forward-review/credit-research-draft.md)
and [evidence manifest](forward-review/evidence-manifest.json) preserve original
inputs, outputs, transcripts, source snapshots and readback. The archive includes
454 manifest-listed files plus the manifest itself, copied byte equal from the
isolated review directory. Original scratch paths in the transcripts are retained
as provenance; the complete directory is saved here.

The base issuer result is reported gross/net leverage 6.5x/6x, adjusted EBITDA 96,
adjusted gross/net leverage 6.09375x/5.625x, FCF 44 and FFO/debt 4/39. Surveillance
shows net leverage increasing 1.5x, coverage declining 13/7x and OAS widening
55 bps, with the supplied current quote four hours old under an eight-hour policy.
These are nine-month EBITDA ratios, not automatically LTM/annualized measures.

The research draft remains **PARTIAL**. Fresh cases also demonstrate remaining
supplied-evidence limits: different IDs can describe the same economic adjustment;
instruments are not reconciled automatically to financial debt/currency; mutually
matching quote IDs do not authenticate their issuer mapping; source labels do not
prove source content. Those variants were accepted by native software and rejected
by the authored analyst draft. They are retained as observed limitations, not
misreported as automated detections or additional closed findings. Source/economic
reconciliation and professional acceptance remain separate next steps.

## Auxiliary validator limitation

The installed skill-creator `quick_validate.py` rejects the existing `compatibility`
frontmatter key in all three changed packages. Its [raw results](skill-creator-quick-validation.json)
are retained. The repository's validator explicitly supports that metadata and
passes all 395 skills. No supported metadata was removed and no external validator
was altered to create a passing result.

No authenticated source access, legal/model/practitioner acceptance, institutional
deployment, publication, live model write, credit approval or trade is established.
