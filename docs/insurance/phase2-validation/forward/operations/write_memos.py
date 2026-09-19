import pathlib,json,hashlib
R=pathlib.Path('/tmp/insurance-p2-forward-operations')
memos={
'policy':'''Draft policy-operations packet — FWD-OPS-POLICY, 2026-09-18

Cedar Oven CO-1 / policy P-CO-77, current version 8. Result: needs-review. The requested endorsement would change the location effective 2026-09-25, with a supplied USD 125.50 increase in written premium. The current policy shows 12 Main St; the request incorrectly identifies 10 Main St as the before address. Proposed destination is 40 Mill Rd. Preserve all three values until the request owner reconciles them. [POL, REQ, PREM]

The matching versioned endorsement form is supplied. A separate pending endorsement E-23 may invalidate the version-8 snapshot; policy operations must establish sequence and obtain a refreshed snapshot/request before relying on the draft. [DOC, QUEUE]

Native-output defect: proposed_changes.before repeats 10 Main St, although the current policy remains 12 Main St and the discrepancy is flagged. A reviewer should use the current/source/request distinction above, not copy that native row as an authoritative before/after instruction.

No policy state changed, notice was sent, or premium was posted. A later insurance-premium-billing-reconciler handoff needs an actual billed entry, account, posting period and balance evidence; the supplied written-premium effect is not a posted invoice.
''',
'billing':'''Draft billing reconciliation — FWD-OPS-BILLING, 2026-09-18

Synthetic account AC-72 / policy P-72; August 2026, USD gross premium receivable. Result: needs-review. Opening 1000.00 plus invoice 600.00, less receipts 700.00 and 650.00 and credit 100.00, with receipt R-2 and its full 200.00 reversal netting to zero, produces 150.00. The reported close is 420.00, a calculated-minus-reported difference of -270.00. [CTL, LEDGER]

OLD-1 has 200.00 outstanding and was 47 days overdue at the August 31 period end. NEW-1 is fully allocated and has zero outstanding. Receipt R-3 has 50.00 unapplied; do not assign it to OLD-1 without allocation evidence. Invoice receivable 200.00 less the separate unapplied 50.00 equals the calculated account balance of 150.00. [OPEN, ALLOC, LEDGER]

Billing finance should investigate the 270.00 control discrepancy and obtain an authorized allocation instruction for the 50.00 remainder. The package establishes no coverage lapse, collection decision, posting authority or cancellation right. A gl-reconciler handoff would need the actual GL account/control extract, period and native ledger mapping; none was supplied.
''',
'producer':'''Draft onboarding evidence memo — FWD-OPS-PRODUCER, 2026-09-18

Harbor Agency LLC AGENCY-4 and individual IND-4; carrier C-9, US-TEST property scope. Result: needs-data under synthetic reviewed profile PR-4 v3 and its 30-day freshness interval. The agency license and individual carrier appointment match supplied scope and dates. [SCOPE, LICAG, APPT]

The individual license is unresolved: the September 17 feed says active, while the September 18 compliance extract says suspended effective September 16. Both records are retained. This is an adverse-status conflict requiring the licensing owner to reconcile authoritative status; it is not merely a clerical duplicate. No agency appointment record was supplied. [LICA, LICB, APPT]

Request reconciliation of the individual suspension/active conflict and the business entity appointment evidence. Human review must also determine whether the supplied two requirements cover the full intended activity. No onboarding decision, carrier representation authority or system-access activation is recorded. Any later placement or delegation packet must establish its own contractual authority independently.
''',
'placement':'''Draft broker placement packet — FWD-OPS-PLACEMENT, 2026-09-18

Placement PL-77 / insured CO-1; term October 1, 2026–October 1, 2027. Result: needs-data. The broker's instruction identifies North N-2 as current; N-1 remains in response history. Current North premium 11800 plus fees 300 cannot be totaled because taxes are pending. North's roof-inspection subjectivity is unresolved because the claimed satisfied status has no supporting evidence. [MANDATE, SELECT, N1, N2]

South S-1 has premium 10900, fees 200 and taxes 545, for USD 11645. Its signed-application subjectivity remains open. South's 10000 retention differs from North's 5000; neither the current incomplete costs nor the different terms justify a like-for-like price ranking. Both state a 1000000 primary occurrence building limit with flood excluded. [S1, N2]

The broker should obtain North's tax amount and subjectivity support, and the South signed application, while checking the quoted terms and expiry dates with the market owner. No market has been selected and no risk is bound. Detailed wording comparison can pass the current full forms and versions to policy-wording-comparator; coverage adequacy requires the separate needs-versus-coverage workflow.
''',
'delegation':'''Draft delegated-authority oversight memo — FWD-OPS-DELEGATION, 2026-09-18

Agreement DA-12 v4, insurer INS-1 and delegate MGA-2; proposed transaction T-88. Native result: needs-data; substantive authority result: aggregate exception. The USD 180000 insured-limit request is within the 250000 per-risk limit, leaving 70000 per-risk headroom. The complete same-day ledger shows 1880000 used against 2000000 aggregate capacity: 120000 remains, and adding this request produces 2060000, exceeding aggregate by 60000. [AGR, REQUEST, LEDGER]

The August bordereau was received September 16 against a September 10 due date, six calendar days late. On its own supplied USD written-premium basis, reported 94750.50 less expected 95000.00 is -249.50. The native method flags lateness but suppresses this difference because the agreement authority basis is insured limit. That restriction conflates authority-limit units with report units; the above difference is independently calculated from comparable report amounts and must remain separate from insured-limit capacity. [REPORT]

The exception email is a request, not an executed amendment. The insurer's authority owner must resolve the 60000 aggregate overrun and the report timing/value discrepancy; no authority is granted by this packet. Native aggregate wording also says a complete ledger is needed although one was supplied; the problem is insufficient capacity, not an absent ledger. [EMAIL, LEDGER]
''',
'life':'''Draft annuity sales-supervision memo — FWD-OPS-LIFE, 2026-09-18

Synthetic customer L-17, fixed annuity via insurance-agent channel; replacement evidence review. Result: needs-data. The application says near-term liquidity needs of 10000; the interview records 60000 for home repairs within 12 months. Preserve and reconcile that conflict before the supervisor assesses funding and liquidity. Income 48000, liquid assets 160000, age 66 and a stated seven-year horizon are supplied summaries, not an independent capacity determination. It is unclear whether the liquid-assets amount includes the existing annuity. [APP, INTERVIEW]

The existing annuity has value 103000 and a stated 3000 surrender charge, leaving 100000 before any unprovided tax or other adjustments, equal to the proposed premium. Replacement relinquishes the existing 3.5% guarantee for two more years; the proposal states 4.2% for three years and starts a seven-year surrender schedule. Higher initial rate alone does not establish the transaction's net benefit. The stated commission is 5% of premium, or 5000. [INTERVIEW, PROD, RATIONALE]

Native gaps include conflicting liquidity, non-guaranteed elements, disclosure/training support, annuitization options and replacement disclosures. A disclosure acknowledgment was supplied, but training evidence was absent; the combined native topic is withheld rather than treating acknowledgment as complete training. Other lost benefits remain unresolved even though the native lost-guarantees row labels its supplied partial summary evidence-present. Review the actual existing/proposed forms and all lost benefits. Retaining the existing contract and deferring until the repair liquidity is resolved are documented alternatives. [PROD, INTERVIEW, RATIONALE]

The supplied rule determinations are institution-policy checklist assertions only; no enacted-law applicability determination was provided. The native applicability matrix says applies but does not itself establish jurisdictional legal compliance. The responsible compliance owner must establish applicable requirements. No suitability/best-interest decision, tax conclusion, principal approval or sale/replacement execution is made. [PROFILE, RULE]
'''
}
for k,memo in memos.items():
 out=json.loads((R/k/'native-output.json').read_text());meta='\nEvidence record: native-output.json. Source passages: raw-source.json. Source-to-native mapping: normalization.md. Input SHA-256: '+hashlib.sha256((R/k/'native-input.json').read_bytes()).hexdigest()+'.\n\nSynthetic offline review only; not professional or deployment acceptance.\n'
 (R/k/'practitioner-response.md').write_text(memo+meta)
report='''# Independent forward review: six insurance operations workflows

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
'''
(R/'REVIEW.md').write_text(report)
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in R.rglob('*') if p.is_file() and p.name!='evidence-manifest.json'}
(R/'evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Six practitioner memos and REVIEW.md written; '+str(len(manifest))+' evidence files hashed.')
