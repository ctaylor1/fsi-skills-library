# Independent forward review: six insurance operations workflows

Scope: fresh synthetic requests and minimal raw evidence were saved before reading evaluator implementations. SKILL, source maps, native schemas, controls, handoffs, output templates and implementation interfaces were read. No packaged tests, eval fixtures, golden outputs or prior audits were read or used. No repository files were edited. All source evidence is invented and all jurisdiction profiles are US-TEST institution configuration; no external action or professional acceptance is claimed.

## Results

| Workflow | Input / calculation / output exit codes | Native status | Practitioner outcome |
|---|---|---|---|
| Policy transaction | 0 / 0 / 0 | needs-review | Stale requested before value and concurrent change detected; generated before value still misleading |
| Premium billing | 0 / 0 / 0 | needs-review | 150 calculated close, -270 control difference, 200 aged invoice and 50 unapplied cash correctly separated |
| Producer onboarding | 0 / 0 / 0 | needs-data | Conflicting active/suspended individual records and absent agency appointment retained as unresolved |
| Placement | 0 / 0 / 0 | needs-data | Current version honored; incomplete North total withheld; South total 11645; unsupported subjectivity unresolved |
| Delegated authority | 0 / 0 / 0 | needs-data | 60000 aggregate overrun and late report detected; valid report difference improperly withheld |
| Life/annuity sales | 0 / 0 / 0 | needs-data | Liquidity conflict and missing product/replacement evidence surfaced; no suitability decision |

32 independent assertions: 30 passed, 2 failed. Numeric comparisons use Decimal equality, so formatting differences do not count as failures. All six preserve approval=not_requested and execution=not_performed. Validator success establishes reproducibility only; the two failing domain expectations both have output-validation exit 0.

## Actionable findings

1. P2 — policy change table uses a disputed request value as `before`. Source POL shows current 12 Main St; REQ states stale 10 Main St. `insurance-policy-transaction-packager/scripts/domain.py:114-118` detects the conflict but writes request.before into proposed_changes.before. Output retains the true snapshot elsewhere and status needs-review, so this is a misleading artifact field rather than false clearance. Add separate policy_before and requested_before fields (or source the primary before from policy), preserve both sources and conflict status. Repro: policy/native-input.json and native-output.json.

2. P2 — delegated-authority bordereau reconciliation depends on authority-limit amount basis. In `insurance-delegated-authority-reviewer/scripts/domain.py:161-170`, a report with expected 95000 and reported 94750.50 on written-premium basis is rejected because the agreement's insured-limit basis differs. Authority capacity and reporting totals are distinct dimensions; the two report amounts are directly comparable. The independently correct within-report delta is -249.50. Keep authority comparisons tied to authority basis and reporting comparisons tied to explicit report/control basis. The aggregate-limit finding at lines 138-143 also asks for a complete ledger in the over-limit case even when one exists; output should say exceeds aggregate by 60000. Repro: delegation/native-input.json and native-output.json.

3. P2 usability — the life sales schema does not publish required topic vocabulary; references/schema.md:11 says it is in the normal fixture. An operator cannot populate the native interface from its advertised schema without reading fixtures or implementation. Publish the consumer, product, annuity/life and replacement topic lists in schema.md. Policy source-map similarly omits the pc/life/annuity supported line enum, while natural commercial-property values produce an unsupported-line gap unless normalized to pc. This review read the domain constants to complete normalization, with that step disclosed in normalization.md.

## Method boundaries and narrative responsibilities

- Producer duplicate license output identifies records and sources but summarizes the problem only as multiple matches. The practitioner memo explicitly surfaces the suspended record rather than treating this as a clerical duplicate.
- Life scalar summaries require authored interpretation. The lost-guarantees summary explicitly mentions an unresolved extent, yet its row is evidence-present. This is not proof of complete benefits discovery. Likewise institution-policy applicability rows cannot establish enacted-law review. The memo preserves both limits; no automated semantic inference is claimed.
- No fixture-derived intended answer was used. Independent checks reconstruct values from raw evidence and test domain behavior, not package implementation details.

## Artifact index

Each case directory contains request.txt, raw-source.json, design.json, normalization.md, native-input.json, native-output.json, input-validation.json, output-validation.json, commands-status.json, package-source-hashes.json and practitioner-response.md. Root files include design_cases.py, map_inputs.py, run_review.py, independent_checks.py, independent-checks.json, independent-arithmetic.md, run-summary.json and evidence-manifest.json. These files permit replay against the captured package hashes. Hashes identify content; they do not authenticate sources or signify acceptance.
