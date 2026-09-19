# Wealth management P2 validation record

> Historical P2 milestone. P3 is now implemented; see [current scope](P3-IMPLEMENTATION.md) and [current validation](P3-VALIDATION.md). Counts and planned priorities below describe the original P2 milestone.

Verified 2026-09-17 against the working tree. This record covers implementation and bounded synthetic scenarios; it is not institutional deployment certification or professional acceptance. See [P2 scope and handoffs](P2-IMPLEMENTATION.md). Earlier results remain in [P0 validation](P0-VALIDATION.md) and [P1 validation](P1-VALIDATION.md).

## Repository and package checks

| Check | Observed result |
| --- | --- |
| Package/spec validation | **237 packages; 0 errors, 0 warnings** |
| Catalog/directory correspondence | Exact match for 237 unique packages; 25 wealth packages; manager diligence in Asset Management |
| Handoff-name validation | **0 dangling references** across 237 packages |
| Shared helpers | 24 evidence-contract copies, 3 P1 analysis-helper copies and 4 P2 workflow-helper copies match byte for byte |
| Whole-library executable evaluations | **1,064 passed, 0 failed** |
| P2 practitioner evaluation commands | **32 passed**, including **144 domain regression methods** nested inside these commands |
| Updated router | 2 evaluation commands, including 10 routing regression methods; included in whole-library total |
| Repository unittest discovery | **90 passed**: 40 core methods, 17 book forward methods and 33 private-market forward methods |
| Core repository tests | **40 passed**: 11 P0, 15 P1 and 14 P2 integration/prospect methods |
| Independent book replay | **17 passed** using fresh scenario and actual package CLI calls |
| Independent lending replay | **42 passed** using fresh financial expectations and adverse variants |
| Independent private-market replay | **33 passed**, including the three original evidence-label failures and related source-gap cases |
| Catalog regeneration | Approved-current JSON and CSV rebuild byte-identically; both earlier renames remain applied |
| Scoped lint and working diff | Ruff selected errors and `git diff --check` passed |

Executable evaluations count commands, not every nested assertion. The P2 packages have 68 evaluation specifications, of which 32 contain executed commands; natural-language-only entries remain specifications, not completed model evaluations. The book and private-market methods are included in the 90 repository unittest methods, not additional to that count. The lending harness contains 42 separate checks. The repository and forward harnesses are not counted in the 1,064 command total.

| P2 package | Executable commands | Author regression methods |
| --- | ---: | ---: |
| advisor-book-of-business-reviewer | 9 | 56 |
| wealth-prospect-referral-preparer | 8 | 28 |
| wealth-lending-liquidity-reviewer | 6 | 18 |
| private-market-client-reviewer | 9 | 42 |
| **P2 total** | **32** | **144** |

## Independent scenarios and repairs

Reviewers were different agents from package authors. They read the published schemas and constructed fresh synthetic cases without relying on author-provided expected answers. The four scenario fixtures are retained in [tools/fixtures/wealth-p2-forward](../../tools/fixtures/wealth-p2-forward). Actual input/calculation/output entry points or isolated package functions were exercised, with independent numerical expectations and adverse variants. This is a bounded agent-led review, not a blind wealth-professional acceptance study or a statistical assessment of real-model reliability.

| Area | Evidence and result |
| --- | --- |
| Book service, retention and capacity | Fresh four-household case reconciled 150 minutes of work per owner, an initial review due September 18, a review overdue by two days, and 2/3 opening-cohort retention. The supplied asset bridge tied $1.6m opening to $1.732m closing, with $115,000 net external flow, $12,000 recognized revenue and $2,500 direct contribution. Tests covered missing history/capacity/population/economics, growth priority, source gaps, lineage and tampering. The reviewer found no defect in the original 17 cases. A related author check subsequently found that uncited relationship dates could support full-book economics; the package now withholds full totals because those dates define period membership, preserving observed subtotals. The unchanged 17-case independent replay passed after this correction. |
| Prospect permissions and suppression | Fresh nonreferral manual-phone case produced a sourced internal discussion draft. Global opt-out withheld it despite a clear channel check and permission grant. Public/referral contact bases, internal-research-only use, competing/expired permission records, missing global screening, unknown observation dates and extra conflicting reviews all withheld outreach. Edited content or removed blocking findings failed output reconstruction. No actionable defect found. |
| Lending liquidity and stress | Independent cash availability $90,000 and funding gap $35,000; supplied liquidation net $132,000. New loan proceeds $124,375 remained separate from total facility principal $175,000. Eligible collateral capacity fell from $230,000 to $133,000 under combined stress, retaining a $42,000 maintenance paydown illustration. Floating rate cap produced 10.5% and $19,120 horizon cost. Independent amortization yielded $7,977.71 monthly payment and $92,692.48 balance after twelve months. Unknown/stale amounts, contractual limits, purpose, balloons, lineage and tampering were exercised. Review found reserved `scenario_id: base` passed input validation but failed calculation; validation now rejects it consistently, with 42/42 replay checks passing. |
| Private-market commitments and account funding | Partial mixed calls and recallable receipts independently reconciled remaining commitment $78,000, reserved unpaid commitment $16,000, uncalled $62,000 and outstanding calls $22,000. Account cash after reserves began at $15,000 and ended at -$10,000 for known obligations and -$17,000 with incremental forecasts. Positive household cash of $60,000 did not erase that account shortfall. Superseded forecasts, unsettled distributions and historical settled movements were not counted again as available cash. |
| Private-market evidence qualification | Review found uncited coverage could retain complete-ledger/cash-schedule labels, uncited NAV could appear current under policy, and an uncited eligibility requirement could appear documented. Global needs-data findings were already present. Repairs now require cited context and contributing records for supported balances and local qualification; raw observations remain labeled separately. The original 30 independent tests plus three added account/notice/settlement source-gap cases pass: **33/33**. |
| Cross-workflow concerns | All four P2 packages retain an injected unresolved scope concern with originating artifact ID, code, literal message and sources. Each keeps needs-data and reconstructs correctly. Attributed dated resolution is retained; it never authorizes action. Missing inventories, mismatched capacity, expired policy and resolution without attribution reject. Router-to-prospect mapping preserves the actual evidence origin; unmapped issue aliases reject. |
| Routing and catalog continuity | All 25 distinct destinations exist; book collection and household scopes remain distinct. P0 routes and the goal-progress alias survive. P0/P1 renamed packages remain retired through catalog regeneration. Current exact totals, metadata, resources and shared copies are tested separately from earlier milestone assertions. |

Author-side malformed-input sweeps also exercised 812 book and 1,776 prospect field mutations; the independent lending reviewer exercised 870. These were temporary diagnostic sweeps reported by the agents, not additional retained evaluation commands or certification evidence. The durable fixtures, domain regressions and independent replay scripts are the reproducible checks.

## Reproduction

Use Python 3.10+ with PyYAML and Ruff for repository checks; domain packages use the standard library. This run used Python 3.14.7, PyYAML 6.0.3 and Ruff 0.16.8. Workbook import additionally needs openpyxl and the external workbook; the approved-current-catalog path does not.

```bash
python tools/build_catalog_from_xlsx.py --from-current
python tools/validate_skills.py
python tools/check_handoffs.py
python tools/sync_wealth_contract.py --check
python tools/run_selftests.py
python -m unittest discover -s tools -p 'test_wealth*.py' -v
python tools/test_wealth_p2_lending_forward.py
ruff check --select E4,E7,E9,F --ignore E401,E702,E731,E741 tools shared skills
git diff --check
```

The independent [book](../../tools/test_wealth_p2_book_forward.py) and [private-market](../../tools/test_wealth_p2_private_forward.py) tests are discoverable unittest modules. The [lending harness](../../tools/test_wealth_p2_lending_forward.py) is a separate guarded 42-check replay. [P2 integration/prospect tests](../../tools/test_wealth_p2.py) include exact catalog/shared-resource checks and all-four-workflow issue propagation. Imports do not execute financial cases or contaminate package-local module identities.

## Acceptance still required

Human review must verify source truth, inventory completeness, actual permissions, contractual/legal interpretations and source-specific freshness policy. Hashes and output reconstruction establish internal consistency, not authenticity. Narrative semantics, input extraction quality and real-model end-to-end behavior need separate evaluated runs. Institution-specific professional/control-owner acceptance, access/retention controls, approved live integrations and production release gates remain outstanding. No account action, order, payment, CRM update or client communication was executed during implementation.
