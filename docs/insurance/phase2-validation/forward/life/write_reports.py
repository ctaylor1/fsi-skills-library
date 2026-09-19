from pathlib import Path
import json,hashlib
P=Path('/tmp/insurance-p2-forward-life');R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance')
reports={
'life-underwriting-reviewer':'''# Draft life underwriting review: APP-71

As of September 18, 2026, this NY term-life application needs additional evidence and specialist review. Prepared for the carrier life underwriting case manager, representing Synthetic Carrier; applicant SYN-A71. The authorized underwriting function owns the decision.

The supplied amounts produce a coverage-to-income multiple of **20**: ($1,450,000 requested + $350,000 existing) / $90,000 disclosed annual income. That exceeds the supplied profile's referral threshold of 15. The amount is a comparison using disclosed income, not proof of income, financial need, insurability, or a recommended benefit. See [application](raw-source.md#application), [criteria](raw-source.md#criteria) and `actual-output.json:results.financial_review`.

The attending physician statement EV-M1 matches APP-71 / SYN-A71 and is within the supplied 180-day window. Income verification EV-F1 remains pending and does not satisfy F1; obtain the employer verification and preserve its date and identity. See [APS](raw-source.md#aps), [pending income](raw-source.md#income-pending) and `results.evidence_checks`.

The application's 'no' and physician statement's 'yes' for specialist follow-up conflict. Ask the underwriting specialist to reconcile the dated follow-up and its relevance; this review makes no diagnosis or automatic declination inference. Retain both values. Refer the 20-times disclosed-coverage multiple and missing income confirmation to financial underwriting. See `results.disclosure_reconciliation` and findings `disclosure_conflict` / `financial_referral`.

The native artifact is **needs-data**; input validation, calculation and output validation passed. Independent arithmetic agrees. No risk class, medical diagnosis, issue decision or business action was produced. Reviewer disposition remains open outside this artifact. Evidence: [native input](input.json), [validated output](actual-output.json), [independent check](independent-arithmetic.json).
''',
'life-annuity-contract-service-reviewer':'''# Draft annuity service review: AN-22 / W-22

As of September 18, 2026, owner SYN-O22's $50,000 withdrawal request needs assignee consent and a current valuation under the package's supported method. Prepared for the carrier annuity service specialist representing Synthetic Carrier, NY fixed annuity. The authorized service team owns rights verification and processing.

The contract identifies SYN-O22 as owner, SYN-B22 as beneficiary and SYN-L22 as collateral assignee. Owner consent matches this request; assignee consent is missing. Beneficiary designation does not establish authority to transact. The supplied owner/actor evidence is supported, while legal authority remains undetermined. See [contract](raw-source.md#contract), [owner consent](raw-source.md#consent-owner), [consent inventory](raw-source.md#consent-inventory) and `actual-output.json:results.rights_evidence`.

**Original packet:** the account snapshot is September 17, while review is September 18. The engine requires those dates to match exactly and returns `value_scenario: null`. It reports a generic 'current value' gap rather than naming the one-day date mismatch. Obtain a valuation dated September 18 or use a separately approved historical-snapshot method; do not relabel the original date. This is a package documentation/usability limitation recorded in [freshness finding](freshness-finding.md).

**Separately sourced same-day evaluation variant:** the synthetic [valuation supplement](same-day-source.md#valuation-confirmation) supplies the unchanged $180,000 account value dated September 18. Its supported bridge is $50,000 - $3,500 surrender charge + $1,250 signed MVA - $2,000 loan offset - $4,500 withholding = **$41,250 illustrative proceeds**. Account value after the gross withdrawal alone is **$130,000**. The package and independent arithmetic agree. This scenario preserves the missing assignee consent and remains **needs-data**. See `same-day-actual-output.json:results.value_scenario`.

The supplied guaranteed benefit base is **$230,000 before and $166,111.11 after**. That illustration is separate from cash proceeds and account value; its $63,888.89 reduction is not inferred from the cash bridge. Confirm actual contract debit mechanics and illustration applicability with the service specialist. See [terms](raw-source.md#terms).

Obtain request-specific assignee consent, reconcile any competing rights evidence, and have the authorized specialist review deductions and benefit consequences before considering processing. Both variants passed input/output validation. No withdrawal, tax calculation, replacement recommendation or business action occurred. Reviewer disposition remains open. Evidence: [original output](actual-output.json), [same-day output](same-day-actual-output.json), [independent arithmetic](independent-arithmetic.json).
''',
'life-benefit-claim-reviewer':'''# Draft life claim review: LC-91 / LP-91

As of September 18, 2026, this NY whole-life death-benefit claim needs corrected identity evidence and beneficiary/contestability review. Prepared for the carrier life claims reviewer representing Synthetic Carrier. The authorized claims and legal specialists own entitlement and any payment decision.

The supplied ledger reconciles to **$739,895.50 before entitlement**: $750,000 base + $12,500 additional benefits + $910.25 interest credit - $18,300 loan principal - $214.75 loan interest - $5,000 prior payments. The native output and independent arithmetic agree. This is not an amount approved for payment. See [ledger](raw-source.md#ledger) and `actual-output.json:results.benefit_bridge`.

Death is reported September 3, 2026, after January 10, 2025 issue/effective date but before the supplied January 10, 2027 contestability end. Refer the chronology for investigation under the supplied terms; it does not establish misrepresentation or automatic denial. See [policy](raw-source.md#policy), [death](raw-source.md#death), [terms](raw-source.md#terms), and `results.chronology`.

The certificate DC-91 lists SYN-I19, while the policy/death record identifies SYN-I91. It cannot satisfy the identity-matched certificate requirement as supplied. Preserve that rejected certificate and obtain corrected or reconciled evidence. Claimant statement CS-91 matches the policy and insured and is within the supplied window. See [certificate](raw-source.md#certificate), [claimant](raw-source.md#claimant) and `results.document_checks`.

Record BEN-91-A is active at 65% SYN-B1 / 35% SYN-B2; later BEN-91-B is disputed at 70% SYN-B1 / 30% SYN-B3. Both predate death. The signature challenge prevents allocation; a later date is not a validity decision. The output preserves both and returns **no illustrative allocation**. Have the beneficiary/legal specialist resolve the status and retain supporting and contrary evidence. See [active designation](raw-source.md#designation-active), [disputed designation](raw-source.md#designation-disputed) and `results.beneficiary_record_checks`.

The native artifact is **needs-data** and passed input, calculation and output checks. Entitlement was not determined, and no pay/deny decision or business action was produced. Reviewer disposition remains open. Evidence: [native input](input.json), [validated output](actual-output.json), [independent check](independent-arithmetic.json).
''',
'reinsurance-program-analyzer':'''# Draft deterministic program comparison: RP-26

Prepared for Cedar Mutual's ceded reinsurance analyst, as of September 18, 2026, US property catastrophe, USD and 2026 treaty period. The supplied stress favors Program B on retained loss plus supplied premiums; the no-loss scenario has lower cost under A. These two deterministic scenarios do not establish which program to buy.

| Scenario | Program | Gross loss | Illustrative recovery | Retained loss | Supplied premium | Retained plus premium |
|---|---:|---:|---:|---:|---:|---:|
| STRESS | A | $15,000,000 | $5,500,000 | $9,500,000 | $1,200,000 | $10,700,000 |
| STRESS | B | $15,000,000 | $8,250,000 | $6,750,000 | $1,950,000 | $8,700,000 |
| ZERO | A | $0 | $0 | $0 | $1,000,000 | $1,000,000 |
| ZERO | B | $0 | $0 | $0 | $1,600,000 | $1,600,000 |

Sources: [reviewed profile](raw-source.md#profile), [A](raw-source.md#program-a), [B](raw-source.md#program-b), [stress events](raw-source.md#stress), [zero-loss alternative](raw-source.md#zero). Exact native values are in `actual-output.json:results.comparisons`; independent arithmetic checks every layer and these totals.

Under A, event 1 recovers $1,000,000 from Q then $1,500,000 from X, retaining $2,500,000. Event 2 recovers $1,500,000 from each layer because both reach remaining aggregate capacity; it retains $7,000,000. Both A layers are exhausted after the two events.

Under B, event 1 recovers $1,250,000 from Q then $750,000 from X, retaining $3,000,000. Event 2 recovers $2,000,000 from Q then $4,250,000 from X, retaining $3,750,000. X is exhausted and Q has $250,000 aggregate capacity left. The second event is applied to capacity remaining after event 1; each alternative scenario resets to the supplied prior erosion.

B's retained-plus-premium figure is $2,000,000 lower under the supplied stress; its no-loss premium is $600,000 higher. No frequency, probability, PML, treaty legal recoverability, variable-premium formula or optimization was inferred. The explicit shared eligibility and sequential remaining-loss convention control this comparison. Ask the program owner to assess contract applicability, broader scenario evidence and purchase objectives before selection or placement.

The artifact is **ready-for-review** with no native findings, and all native and independent checks passed. This is an evidence-workflow status, not professional acceptance or a program recommendation; `recommended_program` is null. No placement or business action occurred. Reviewer disposition remains open. Evidence: [native input](input.json), [validated output](actual-output.json), [independent checks](independent-arithmetic.json).
''',
'reinsurance-contract-administration-reviewer':'''# Draft reinsurance administration review: TR-26 / RE-SYN

Prepared for Cedar Mutual's ceded reinsurance accountant as of September 18, 2026. Scope is August 1–31, 2026, USD, ceded paid recoverables for TR-26 / RE-SYN. The total roll-forward ties, but claim-level breaks, collateral shortfall and notice exceptions require review.

The closing recoverable reconciles to **$268,750**: $240,000 opening + $130,000 statement charges - $100,000 cash receipts - $1,250 signed adjustment. It equals the supplied closing balance with a $0 difference. This does not resolve the offsetting claim breaks: **CL-1 statement exceeds bordereau by $5,000; CL-2 is $5,000 below**. Both sources total $130,000, so a total-only reconciliation would miss them. Review the claim assignments and underlying entries before any correction. See [balances](raw-source.md#balances), [statement](raw-source.md#statement), [bordereau](raw-source.md#bordereau), [cash](raw-source.md#cash), [adjustment](raw-source.md#adjustment), and `actual-output.json:results.claim_tieouts` / `recoverable_rollforward`.

Supplied required collateral of $300,000 exceeds supplied eligible held collateral of $275,000 by **$25,000**. Refer the shortfall to the collateral owner and confirm the supplied requirement and eligibility basis; this review creates no regulatory percentage or credit-for-reinsurance opinion. See [collateral](raw-source.md#collateral) and `results.collateral_comparison`.

N1 was due September 5; the dispatch log says September 8, so it is **sent late by three days**. N2 was due September 15 with no dispatch evidence at review, so it is **overdue with no dispatch evidence**. The supplied notice inventory is expressly complete. Have the administration owner reconcile dispatch evidence and consequences under the contract. No notice was sent by this review. See [notice terms](raw-source.md#notice-terms), [dispatch evidence](raw-source.md#dispatch), [scope](raw-source.md#scope), and `results.notice_checks`.

The artifact is **needs-review**, with native input/output checks and independent arithmetic passing. Financial agreement does not establish collection, legal recoverability or statutory credit. No journal, bill, collection instruction or business action was produced. Reviewer disposition remains open. Evidence: [native input](input.json), [validated output](actual-output.json), [independent checks](independent-arithmetic.json).
'''}
for s,body in reports.items():
 p=P/s;(p/'response.md').write_text(body)
 d=json.loads((p/'input.json').read_text());o=json.loads((p/'actual-output.json').read_text());cmd=json.loads((p/'commands.json').read_text());checks=json.loads((p/'independent-arithmetic.json').read_text())
 mapping={'method':'manual transcription from frozen raw-source sections; no golden fixture copied','units':'money in stated currency units; percentage shares converted from percent to decimal','source_anchor_resolution':{x['source_ref']:str(p/'raw-source.md')+'#'+x['source_ref'].split('#',1)[1] for x in d['sources']},'unknowns':'pending/mismatched/disputed evidence preserved; no absent amount defaulted to zero','context_provenance':'request.md and raw-source.md scope/application/contract/policy/profile sections','native_package_reads':'SKILL.md, references/source-map.md, references/domain-rules.md, references/controls.md, references/handoffs.md, assets/output-template.md; underwriting wrappers/foundation/domain_support and service domain.py for interface/observed null diagnosis','package_tests_or_evals_read':False}
 (p/'mapping-notes.json').write_text(json.dumps(mapping,indent=2)+'\n')
 status={'case_design_frozen_before_implementation_read':True,'all_synthetic':True,'native_validation_passed':all(x['returncode']==0 for x in cmd),'observed_native_status':o['status'],'independent_numeric_checks':len(checks),'independent_numeric_checks_passed':all(x['passed'] for x in checks),'native_output_retains_original_input':o['source_document']==d,'external_actions':False,'professional_acceptance_claimed':False,'repo_modified':False,'review_result':'PASS_WITH_DOCUMENTATION_LIMITATION' if s=='life-annuity-contract-service-reviewer' else 'PASS','limitations':['exact same-day valuation required but undocumented; original snapshot correctly left unchanged; separate sourced variant used for arithmetic'] if s=='life-annuity-contract-service-reviewer' else []}
 (p/'status.json').write_text(json.dumps(status,indent=2)+'\n')
 manifest=[]
 for f in sorted((R/s).rglob('*')):
  if f.is_file() and (f.name=='SKILL.md' or f.parent.name in ('references','assets') or (f.parent.name=='scripts' and f.suffix=='.py' and not f.name.startswith('test'))):
   manifest.append({'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 for f in sorted(p.iterdir()):
  if f.is_file() and f.name not in ('source-hashes.json',):manifest.append({'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 (p/'source-hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Wrote 5 practitioner responses, mappings, case status files, and source/runtime/artifact hashes.')
