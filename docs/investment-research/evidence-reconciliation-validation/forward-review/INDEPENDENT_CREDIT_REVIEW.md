# Independent synthetic credit review and draft

**Bounded outcome:** PASS for the two fresh supplied-evidence baselines, 18 independently designed adverse or boundary intake cases, and four output-reconstruction mutations. This is synthetic internal research, with no source authentication or professional acceptance.

## Draft for analyst review

As of 2026-10-20, using a knowledge cutoff of 22:00 UTC, Orion Industrial Holdings has reported nine-month EBITDA of USD 84 million and carrying gross debt of USD 438 million. The supplied complete debt inventory identifies one USD note with contractual principal of USD 450 million and a source-bound carrying-value bridge of −12 million. The bridge reconciles exactly to carrying debt; principal has not been substituted for accounting debt.

Reported gross leverage is 5.2143x, net leverage is 4.7619x and interest coverage is 7.00x. The supplied adjustment ledger selects both distinct components of restructuring event R (+7 and +5 million) once and the separate signed event B (−4 million), giving a net +8 million adjustment and EBITDA of 92 million. On that adjusted denominator, gross leverage is 4.7609x, net leverage is 4.3478x and interest coverage is 7.6667x. This adjustment remains an analyst supplied-evidence treatment whose economic justification and recurrence require review. Operating cash flow less capex is 42 million, and FFO/debt is 9.5890%.

On reported comparable nine-month periods, net leverage increased from 3.7000x to 4.7619x (+1.0619x) and interest coverage declined from 10.00x to 7.00x (−3.00x). Both exceed the supplied 0.25x change thresholds. Gross leverage increased from 4.20x to 5.2143x (+1.0143x); the native alert configuration specifically emits net leverage, interest coverage and spread alerts. The EBITDA-minus-mandatory-capex over interest proxy fell from 8.50x to 5.4167x. It is not DSCR or covenant compliance.

Supplied cash plus committed facilities over known near-term maturities declined from 0.8750x to 0.7556x, using inventories explicitly supplied as complete. The current numerator is 68 million versus 90 million of known maturities. That comparison does not establish funding access, full liquidity sufficiency or a maturity-by-maturity funding plan.

The identified note’s supplied OAS increased from 125.25 bps at 2026-10-19 18:00 UTC to 167.75 bps at 2026-10-20 19:00 UTC, a 42.50 bps widening above the supplied 40 bps threshold. Current age at cutoff is three hours, inside the eight-hour desk policy. Distinct quote source versions were known at 18:30 UTC on October 19 and 19:30 UTC on October 20. The supplied filing mapping covers the same USD note and issuing entity from 2019-01-01 through 2030-12-31, covering both quote instants. The selected quote evidence and exact mapping are retained in the output.

The supported draft therefore records deterioration in reported leverage, interest coverage, the fixed-charge proxy, the supplied liquidity proxy and OAS. It assigns no rating, changes no thesis, recommends no position, and grants no publication, credit-approval, trade or system-of-record authority. No covenant headroom, recovery value or legal-priority conclusion is established.

## Independent execution and evidence review

- Inputs were freshly authored from the supplied raw facts; the raw facts and independent rational calculations were saved before native execution. Fixture input envelopes were used solely to learn field structure. No expected-output or golden answer was interpreted.
- Native packages were copied and hash-frozen only after the parent confirmed the published contracts were ready. The packages are issuer-credit-researcher 0.2.0 and issuer-credit-surveillance-reviewer 0.4.0; their common output method_version remains the analytical-contract version 2.0.0.
- Each public input validator and compute command ran against the frozen package. Every computable output was checked by the public output validator with a separately retained, byte-identical detached original. Detached originals were set read-only.
- Twenty intake runs comprise two baselines plus 18 adverse or boundary cases. Eighteen computations returned JSON and all 18 reconstructed. Duplicate native adjustment ID and a timezone-naive quote were controlled input/compute rejections. No source or package runtime was imported into the independent expectation calculations.
- The initial independent audit harness assumed errors were written to stdout. Surveillance writes its compute error to stderr; the harness was corrected to inspect both streams. The native rejection was already controlled. This harness correction changed no native package or case.
- All 138 independent arithmetic/control/hash assertions passed. Four altered outputs failed public reconstruction: a changed leverage ratio, dropped reconciliation event, extra approval field and changed selected quote source version.

## Case outcomes

| Case | Adverse or boundary change | Actual outcome |
|---|---|---|
| I01 | Same component counted twice under distinct adjustment IDs | Partial; adjusted EBITDA and ratios withheld; reported metrics retained |
| I02 | Same economic event recited by a second source/version and renamed event | Partial; adjusted EBITDA and ratios withheld; reported metrics retained |
| I03 | Event total selected alongside its component rows | Partial; adjusted EBITDA and ratios withheld; reported metrics retained |
| I04 | Only one of two additive event components selected | Partial; adjusted EBITDA and ratios withheld; reported metrics retained |
| I05 | Ledger source version differs from registered source version | Partial; adjusted EBITDA and ratios withheld; reported metrics retained |
| I06 | Duplicate adjustment_id in native intake | Controlled input/compute rejection; no analytical JSON |
| I07 | Carrying-value bridge sign reversed to +12 | Partial; debt-dependent ratios withheld; EBITDA/interest/FCF retained |
| I08 | Debt inventory coverage explicitly partial | Partial; debt-dependent ratios withheld; EBITDA/interest/FCF retained |
| I09 | Identified instrument has no explicit inclusion treatment | Partial; debt-dependent ratios withheld; EBITDA/interest/FCF retained |
| I10 | Debt bridge event repeated under a distinct bridge row ID | Partial; debt-dependent ratios withheld; EBITDA/interest/FCF retained |
| S01 | Current quote exactly 8 elapsed hours old | Complete for supplied scope; +42.5 bps retained at exactly 8 hours |
| S02 | Current quote 8 hours plus one second old | Partial; spread/evidence context/alert withheld; financial metrics retained |
| S03 | Current quote assertion disagrees with selected evidence value | Partial; spread/evidence context/alert withheld; financial metrics retained |
| S04 | Supplied mapping starts after prior observation | Partial; spread/evidence context/alert withheld; financial metrics retained |
| S05 | Prior quote source known one second before its observation | Partial; spread/evidence context/alert withheld; financial metrics retained |
| S06 | Current observed_at omits timezone | Controlled input/compute rejection; no analytical JSON |
| S07 | Two selected-instant records have different IDs but identical value | Partial; spread/evidence context/alert withheld; financial metrics retained |
| S08 | A used source is known one second after research cutoff | Partial; entire result/lineage/citation/source projection suppressed |

## Semantic limits and review gates

The retained source blocks are synthetic supplied evidence authored for this test. Quote ledgers, source registers, event keys, debt inclusion and inventory-completeness declarations are assertions whose internal consistency was exercised; the software did not open or authenticate a filing, check a licensed market feed, establish rights, or inspect the truth of the source text. A copied or fabricated assertion can remain internally consistent if a caller also fabricates the source register and canonical identities. Event alias detection only works on the supplied stable economic key and target issuer; it does not discover undeclared real-world aliases.

The input envelope and raw source blocks were manually reconciled for the material financial amounts, signed event components, identified principal/bridge, source versions and known times, quote instants and values, and mapping period. That supplies a synthetic transcription review, not real source-content authentication. The two native drafts were executed independently; no governed inter-skill adapter or automatic handoff was claimed.

Completeness remains supplied-scope completeness. Corporate EBITDA formulas do not establish sector-wide suitability, rating methodology, a complete capital structure, legal enforceability, covenant interpretation, refinancing access, a credit decision or professional/institutional acceptance. All outputs retain supplied-not-authenticated, source_truth=unverified, professional_acceptance=not-established, authority_granted=false and action_taken=false.

These purposive cases are bounded engineering evidence, not a statistical evaluation or practitioner-acceptance study. No failure was observed within this suite; untested combinations remain open. Responsible analyst and institutional reviewers remain responsible for source authentication and entitlements, economic event identity, adjustment rationale, accounting perimeter/carrying-value bridge, credit-document interpretation and professional acceptance.

## Artifact and package binding

- Raw facts: `raw_facts.json`; independent source blocks: `raw_source_blocks.json`; pre-execution expectations: `independent_expectations.json`; pre-execution case plan: `case_design.json`.
- Per-case input, read-only detached original, output, raw compute stream and command transcripts: `cases/<case-id>/`.
- Package snapshot and full-file hashes: `snapshot/`, `snapshot_manifest.json`, `package_tree_digests.json`.
- Execution summary: `execution_records.json`; independent assertions: `assertion_results.json`; reconstruction probes and transcripts: `mutations/`.
- Readback and whole-experiment file hashes: `readback_verification.json`, `artifact_index.json`.

| Package | Version | Frozen package tree digest |
|---|---|---|
| issuer-credit-researcher | 0.2.0 | `f24bb55111b1466ba57e4aa1eada67eca182cfa2e0b9312b3d389cfed2e318fd` |
| issuer-credit-surveillance-reviewer | 0.4.0 | `46b3f74217df458d07f946c32a7cba8e5a88a2e7b5c326c88f1ab3c2b5545440` |

Live repository package contents matched these frozen packages after all execution. All experiment writes stayed under `/private/tmp/ir-reconciliation-forward-independent`. No repository file, external API, web source or external message was changed or used.
