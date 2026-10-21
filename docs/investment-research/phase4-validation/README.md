# Phase 4 validation evidence

Completed 2026-10-20 for the bounded specialist supplied-evidence library scope.
Professional, institutional and production acceptance remain not established.
Inventories overlap; test and case counts are not additive.

| Check | Final observed result | Evidence |
|---|---|---|
| Whole repository regression suite, Python 3.12.14 | 1,285 tests passed | [Log](whole-library-tests.log) |
| Focused IR regressions | 375 tests passed | [Log](focused-tests.log) |
| Standalone affected packages | 44 packages, 284 command checks passed | [Report](portable.json) |
| Specification, metadata and references | 395 packages, zero errors/warnings | [Log](skill-validation.log) |
| Structure, aliases, indexes, handoffs, AM boundaries and resource pins | Passed | [Gates](gates.json) |
| Saved catalog regeneration | Byte-identical | [Record](catalog-repeat.json) |
| Source-byte preservation | No unexpected changes; Phase 1–3 records untouched | [Audit](preservation.json) |
| Independent fresh-case review | All final financial cases passed; exact originals/results retained | [Artifacts](forward-review), [copy readback](forward-review/copy-readback.json) |

All 42 target IR packages are installed, with no planned packages left in the
agreed roadmap. Global installed/catalog inventory is 395. Five new specialist
methods and one new macro-to-theme mapping bring reviewed pairings to nine. This
is package-roadmap completion within explicit native bounds, not unrestricted
geographic, instrument or model coverage. The 44 portable packages include the
42 IR methods plus two shared owners, copied outside the repository with inherited
Python paths removed. No external source, enterprise approval or live action is
established by these checks.

## Independent forward review

Separate agents read the SKILL/schema instructions and built fresh synthetic inputs
without receiving intended financial answers. Every accepted result was validated
against its retained original. Reports preserve actual evaluated source/package
hashes, raw cases, results and command transcripts.

| Review | Fresh observed coverage | Evidence |
|---|---|---|
| Sovereign and public finance | 19 checks: debt/GDP, cash/noncash recognition, cash draw, financing gap, reserve scope, net/gross pledge stress, coverage and adverse periods/identities | [Report](forward-review/structured-agent-credit/report.md) |
| Structured credit | 10 cases: pool180 collateral/loss/cash math, trigger order, reserve/interest shortfalls, missing research/numerics, source rights and unsupported profiles | [Report](forward-review/credit-agent-structured/report.md) |
| Macro and theme | 21 checks: two cutoff vintages, future exclusion, revisions, nulls, units, rate/FX/equity responses, falsifiers and original binding | [Report](forward-review/structured-agent-macro-theme/report.md) |
| Actual macro-to-theme handoff | 16 cases: exact subset/basis, no inferred shocks, producer/receiver originals, conflicts, rights/cutoff/source collisions, issues and isolated router tool | [Proof](forward-review/macro-agent-handoff/proof.json) |
| Final structured threshold replay | 3 fresh cases: exact equality and neighboring decimal thresholds, cash recipients, conservation and detached-original validation | [Report](forward-review/credit-agent-structured/final-boundary/report.md) |

Method unit tests independently specify financial identities rather than accepting
supplied pass flags: vintage-selected transformations and annualization; local
linear/duration responses; sovereign debt-ratio components, cash/noncash GFN and
cash draws; separate GO/net/gross pledge metrics; collateral default/recovery/prepay,
loss support, reserves, fees, interest and principal allocations. Public commands
reject duplicate/nonfinite JSON, and complete reconstruction rejects missing,
extra or tampered fields, source substitution and wrong originals.

## Findings and verified repairs

| Finding | Final correction and proof |
|---|---|
| Strict structured trigger could breach at mathematical equality because float subtraction gave 0.7999999999999999 versus 0.8 | Reconstruct declared decimal inputs as exact rationals and compare cross-products without an epsilon. Exact numerator/denominator and comparison basis are disclosed; the float ratio is display-only. Root reproduction/replay and a separate fresh Decimal replay verify equality and neighboring thresholds plus cash recipients. |
| A positive gross-pledge ratio could obscure an economic operating-cash deficit | Preserve the pledge ratio and separate system operating balance; baseline/stress deficits remain explicit unresolved issues. Fresh gross-pledge stress with positive coverage and negative operating cash was replayed. |
| Sovereign stock changes and financing could conflate cash/noncash adjustments or cash capacity/draw | Separate cash/noncash flows: both affect debt, only cash enters GFN; only an explicit feasible cash draw reduces debt and covers needs. Independent debt1099.44/GDP2080, GFN151.24 and gap36.24 demonstrate distinct effects. |
| Annual public-finance debt service lacked explicit period/security binding | Require exact financial period and unique security identity, including the requested direct security in its pledge scope. Wrong periods, duplicates and mismatched securities reject. |
| Single-period structured intake allowed a multi-year horizon with a small supplied accrual fraction | Bound the future period to 1..366 days and retain supplied year fraction; no automatic day-count inference. Multi-year case rejects. |

The [original trigger output and repaired replay](forward-review/root-trigger-boundary)
are retained alongside final code hashes and the independent boundary report.
The earlier 373-test focused run is preserved in integration-focused-tests.log;
focused-tests.log records the final 375-test state. A safe limitation
found in fresh theme review remains documented: mismatched scenario/sensitivity
units can pass structural intake validation, then reject with a controlled error
during calculation. No numerical projection, conversion or reviewed handoff is
released for that request. It is not treated as a successful financial calculation.

## Source and model boundaries

Macro selection is latest eligible supplied release, not authenticated publication
coverage. Future/imprecise rows have metadata-only exclusion records; a future or
otherwise ineligible top-level cited source conservatively withholds the entire
projection. Old missing values are not replaced by convenient earlier releases.
Real/nominal, frequency, annualization, seasonal adjustment, geography and price base
remain explicit. Driver evidence does not establish a forecast shock or causal model.

Sovereign paths are conditional on supplied financing assumptions and explicit
government/GDP/debt scope. Whole-economy reserves are not fiscal cash. Public finance
preserves GO versus dedicated revenues, gross/net pledges, fiscal periods and
separate direct/overlapping/contingent exposure. Supplied legal definitions,
qualitative coverage and source metadata remain unverified.

Structured credit supports only its supplied-reviewed simplified sequential-pay
profile: one future period, immediate cash recovery, explicit equity/junior loss
priority, fee/interest/reserve order and declared trigger timing. It does not model
arbitrary CLO/RMBS/ABS deals, reinvestment, lagged recoveries, PIK, prior arrears or
floating-rate resets; no rating, legal opinion, tranche price or complex-engine
validation is inferred. Exact trigger comparison uses rational interpretation of
the parsed finite JSON numbers' round-trip decimal values; it does not recover
precision absent from the supplied JSON representation.

Research topics, counter-evidence, falsifiers and gap narratives support a human
research workflow; arithmetic and supplied reviewed status do not establish textual
entailment, completeness, economic truth or publication clearance. Primary method
references and applicability limits are retained in each package's source-map and
[the source register](../research-sources.md). No proprietary or live third-party
data is redistributed as test evidence.

## Reproduction and preservation

Use Python 3.10+; final tests used 3.12.14. Repository frontmatter checks also need
PyYAML, provisioned through the existing temporary isolated validation environment,
without repository/global installation. The generic skill-creator validator's
stale allowlist rejects supported compatibility metadata; [exact results](skill-creator-compatibility.json)
are retained. The repository validator explicitly checks it and passes all395
packages. No metadata was removed and no checker weakened.

```sh
python3 -B tools/validate_skills.py
python3 -B tools/check_handoffs.py
python3 -B tools/check_investment_research.py
python3 -B tools/build_investment_research_index.py --check
python3 -B tools/sync_investment_resources.py --check
python3 -B tools/check_asset_management.py
python3 -B -m unittest discover -s tools -p 'test_ir*.py'
python3 -B -m unittest discover -s tools -p 'test*.py'
python3 -B tools/run_investment_research_portable.py --report /tmp/ir-phase4-portable.json
python3 -B tools/check_ir_phase4_preservation.py docs/investment-research/phase4-validation/source-baseline.json
```

The pre-edit baseline records 19,032 file digests and the initial dirty Git state.
Existing analytical engines and fixtures, unrelated packages and prior Phase1–3
implementation/validation evidence are unchanged. Existing IR/shared packages
receive only the reviewed canonical evidence standard and its manifest pin.
The audit attributes Phase4 through source bytes and explicit ownership, not the
aggregate Git diff. Repeat local catalog generation is byte-identical; the external
authoritative workbook was not reloaded.

The [run manifest](run.json) pins actual package manifests, changed sources,
registries and retained evidence hashes. Saved files and copied forward artifacts
were read back and verified. Practitioner, model/legal/control, institutional and
production acceptance, authenticated/licensed services and live authorization remain
separate work. No publication, financing, live model or trading action occurred.
