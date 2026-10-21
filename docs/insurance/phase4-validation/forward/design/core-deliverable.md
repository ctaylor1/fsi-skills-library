# Cedar Harbor modernization options and rehearsal review — draft, 20 September 2026

Sara Reed owns this synthetic policy-history/FNOL coexistence review. CORE-5 v5 (19 September), under REV-4, records two options and a failed rehearsal. No option is selected and cutover is not authorized.

## Options and history contract

FACADE/refactor retains the legacy issuance archive and exact policy key, adding a read facade and replay journal. REPLACE imports immutable edition history but its candidate lacks reverse journal replay. Both are recorded as meeting mandatory history preservation; REPLACE is explicitly recorded not-met for mandatory recovery of new writes. These are supplied workshop assessments, not independently verified product capabilities.

Map-3 must preserve the policy identity, form edition and effective interval; never replace an old issued form with the current edition. Billing and claims continue using legacy IDs through an explicit crosswalk. The same historical semantics must be mapped to the data-product contract, including unresolved form conflicts; an artifact ID alone is insufficient receiver input.

The supplied disjoint components are $180,000 implementation plus $60,000 one-year operations for FACADE; $300,000 plus $90,000 for REPLACE. The original native output totals $240,000 and $390,000 for the identical 1 October 2026–30 September 2027 horizon. These are undiscounted sums of supplied components, not validated full costs, NPV or a ranking.

## Rehearsal, rollback and gates

One supplied wave exists: POLICY-HISTORY in wave 1, with no dependencies. This modest scope establishes no full-enterprise sequencing. Snapshot legacy-20260918 maps to sandbox-20260919 under map-3 for 240 historical policy-form assertions. Target count is 239: target minus source = −1 row, outside explicit zero tolerance. CORE-5 identifies the missing edition for CH-19. The native `core-rehearsal.output.json` preserves that break and returns needs-review.

The supplied DR-2 description says two synthetic post-switch writes were recovered exactly once: stop writes, export the ordered journal, replay to legacy, reconcile write IDs. Sara is rollback owner; any missing form row or unrecovered new write triggers rollback review. The description is supplied evidence, not an executed test here. Reconciliation and business acceptance failed; rollback, parallel-run (20 paired draft comparisons) and sandbox security tests are supplied as passed. Passed statuses do not override the failed gates.

CORE-GAP v1 (20 September) reports that DR-2 evidence is absent from a second review copy despite the prior narrative. `core-delta-gap.output.json` retains the contrary CORE-5 source, reports missing delta recovery and nulls costs and reconciliation arithmetic. It must not infer zero writes or approve rollback.

## Source audit and next decisions

The initial mapper wrongly affirmed inventory and cost completeness from a list of records. CORE-5 does not establish exhaustive costs or requirements. `core-source-audited.input.json` corrects those flags to null and retains the issue; its native output is needs-data with dependent arithmetic withheld. Treat the component sums and −1 row above as transparent source comparisons, not a usable complete business case or accepted native result.

Sara must obtain complete requirement/cost inventories, restore the missing CH-19 form edition, rerun reconciliation against matched snapshots, inspect actual DR-2 write-level evidence, and obtain renewed business acceptance. Claims and billing owners must assess coexistence and identity mappings. Option choice requires the human sponsor's decision after those gates; vendor choice, deployment, migration and claim actions were not performed. No customer data or external system was used.
