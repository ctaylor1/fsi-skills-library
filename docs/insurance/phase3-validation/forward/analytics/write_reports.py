from pathlib import Path
import json,hashlib,datetime
R=Path('/tmp/insurance-p3-forward-analytics');texts={
'insurance-market-strategy-researcher':'''The supplied 2025 market reconciles to $125 million of gross direct written premium: Alder has 40%, Bay 30% and Cedar 30%. The complete three-carrier inventory yields HHI 3,400. This describes the defined product, geography, year and premium basis; it establishes neither like-for-like prices nor legal market power (filing §1–2).

The broker’s “25% cheaper” assertion is unusable as a matched-price comparison. The supplied brochures describe Bay at $1 million liability limits and Alder at $2 million, without matched deductibles or risks. Same-day versus two-day indications are vendor statements, not independently observed service performance (research §1–2). The native artifact correctly retains counterevidence and requires review despite complete market arithmetic.

A reasonable next research option is to test whether faster indications matter to brokers and can be delivered at acceptable underwriting cost. An alternative is differentiated limits/service at the current turnaround. Obtain observed turnaround logs and broker win/loss interviews first, then matched quote and wording files; a nonexistent service gap or weak demand would reject the speed hypothesis. Distribution capacity and operating feasibility remain unmeasured (research §3). Market strategy owns that research; any subsequent economics case needs its own native inputs. No strategy was selected or handoff executed.''',
'insurance-product-economics-modeler':'''The complete BASE carrier scenario produces $378,000 underwriting profit and $423,000 pretax period result. The bridge is $2.4 million earned premium less $1.38 million incurred loss including LAE, $552,000 total acquisition/admin/fixed expense and $360,000 ceded premium, plus $180,000 recoveries and $90,000 ceding commission; investment income adds $45,000 (finance §1).

Gross loss ratio is 57.5%. The expense ratio is $552,000 / $2.6 million written premium = 21.230769%, so the stated combined-ratio convention is 78.730769%. Period return on supplied $600,000 allocated capital is 70.5%; it is not an IRR, annualized transformation or capital-adequacy opinion. The carrier bears underwriting risk.

The non-risk-bearing MGA receives $390,000 commission plus $35,000 service fees and $40,000 profit commission, totaling $465,000 revenue. Producer, operating and fixed costs total $310,000, leaving $155,000 operating result and 33.333333% margin. The $2.6 million written premium is a commission base, not agency revenue (finance §2). These business models have different responsibilities and cannot be ranked solely by dollar profit.

The REINSURANCE-UNCERTAIN scenario remains unvalued because its ceded recoveries are unknown; the artifact preserves null and remains partial (finance §3). Product finance and the treaty owner should confirm wording, recoverability and assumption consistency before selecting a scenario. No price, capital or business-model decision is made.''',
'insurance-portfolio-performance-analyzer':'''Q1 calendar loss ratio increased from 56% to 74%, an 18 percentage-point change. Both periods have $1 million earned premium and $1.1 million written premium. Incurred loss including LAE rose from $560,000 to $740,000; underwriting expense rose from $200,000 to $220,000 (ledger §1–2).

The exact bridge allocates 8 points to the change in earned-premium mix at prior segment loss ratios and 10 points to within-segment changes at current weights. Rural’s mix contribution is +16 points, offset by Urban’s −8; within contributions are Rural +6 and Urban +4. Components reconcile with zero residual. Rural’s premium weight rose from 40% to 60%; Urban/Rural loss ratios moved from 40%/80% to 50%/90%.

Expense ratios use written premium: 18.181818% then 20%. Combined ratios under that stated convention are 74.181818% and 94%. Claims increased from 20 to 22 while earned exposure fell from 800 to 700 location-years; frequency rose from 0.025 to 0.031428571 claims per location-year. Calendar incurred severity rose from $28,000 to approximately $33,636.36 per claim. These aggregate ratios use summed components, not averages of segment ratios.

The manager’s repair-cost inflation explanation is unproven (ledger §3). The bridge is arithmetic and may reflect development, mix, rate level, claim severity or other factors. Portfolio performance should obtain claim-development, repair-cost and rate-level evidence before attribution or action. No reserve, rate or management action is selected.''',
'insurance-fraud-pattern-analyzer':'''The exact-token screen identifies bank token B-7 shared by C1, C2 and C4, and email token E-2 shared by C2 and C4. Bank-linked claimed amount is $5,000; email-linked amount is $4,200. Because the signals overlap, the union is three claims and $5,000 of claimed amount—not $9,200 and not an estimate of fraud loss (claims §2–3).

R-COMMON is excluded on the supplied vendor-master rationale that it represents a regional repair network used by unrelated customers. This exclusion does not remove the bank or email links and does not clear any claim (outcomes §2). Shared tokens may reflect a household, authorized representative, shared service, data quality issue or misconduct; token linkage does not resolve identity or intent.

May has three claims across 1,000 location-months: 0.003 per exposure and 3/31 = 0.096774 claims per day. June also has three, across 1,200: 0.0025 per exposure and 3/30 = 0.1 per day. The flagged fractions are 2/3 and 1/3; independently, flagged rates per exposure are 0.002 and 0.000833333. The unequal calendar lengths explain why per-day and exposure-based comparisons differ (claims §1).

Among the three flagged claims, one supplied disposition is confirmed, one cleared and one pending. Confirmed share is 1/2 = 50% among mature outcomes, excluding pending C4 (outcomes §1). Links were discovered across both windows at review time; this is not historical alert precision or predictive validation. SIU should verify underlying links and legitimate alternatives before case selection. No fraud determination, referral or adverse action occurred.''',
'insurance-market-conduct-reviewer':'''Under the supplied internal ACK5 rule, excluding the receipt day, R1’s five days are within target and R2’s seven days are an observed exception. R3 is explicitly pending and ages to eight days at the review date, also an exception. R4 has no completion date and no pending evidence; its result must remain unknown, rather than treating six elapsed days since receipt as proof of an overdue action (profile §3; sample §1–2).

There are two known exceptions among three evaluable sampled cases, plus one unevaluable case. This four-file purposive sample cannot establish population prevalence or legal noncompliance. The target is a supplied internal control, not an asserted statutory deadline.

The separate complete population KPI reconciles disjoint North and South partitions: (8 + 2) late acknowledgements / (100 + 50) eligible claims = 10/150 = 6.666667%. The shared definition ACK-D1, version 2026.1, period 2026-H1, unit claims and scope HALF-YEAR are retained. This population metric does not derive from the purposive sample (metrics §1).

Claims operations should review the known delays and record cause, owner, remediation and closure evidence; the source-event owner should recover R4’s acknowledgement/status record. The incomplete chronology keeps overall readiness partial. A missing extraction and an uncompleted action remain competing explanations for R4. No compliance opinion, sample extrapolation or filing has been issued.''',
'insurance-premium-audit-reviewer':'''Using the supplied reviewed classes and full-period manual, warehouse premium is $625,000.25 / 100 × $1.37 × 0.92 = $7,877.503151. Office premium is $123,456.78 / 100 × $0.19 × 0.92 = $215.80245144. The distinct PAY-W and PAY-O payroll records sum to unrounded manual premium $8,093.30560244 (manual §1; payroll §1).

Adding the supplied $37.50 fixed charge yields $8,130.80560244, above the $8,000 minimum. Rounding only then, half-up to cents, produces audited premium $8,130.81. Less the $7,900 deposit, the audit adjustment is $230.81. Calculated premium exceeds the reported $8,130.80 by $0.01 (manual §2; control §1).

The cent difference is a known reconciliation exception. Row rounding could be one explanation, but the evidence does not prove the report’s rounding method; finance should inspect its computation before accepting or correcting the result. Classification specialist review and audited inclusions/exclusions were supplied assertions, not newly adjudicated here. This draft does not authorize billing or change coverage.

Evaluation chronology: the initial native mapping omitted a newly explicit source-record identity field and safely withheld aggregate money. A separately retained mapping supplement adds basis_record_id PAY-W/PAY-O from the unchanged raw payroll record identifiers. Replay then produced the complete arithmetic above and needs-review status. The original input/output remain available for audit.''',
'insurance-producer-compensation-reconciler':'''AG7’s evidenced earning trigger and 13.75% rate generate E1 gross commission $13,750.48125 and E2 $5,500. Clause 7’s evidenced 25% reversal of E1 produces a negative $3,437.6203125 chargeback, using E1’s original 65%/35% splits (agreement §1–2; events §1–2).

Period net earned is $15,812.8609375. P65 receives $10,278.359609375 and P35 $5,534.501328125. Relative to reported controls, calculated-minus-reported differences are −$0.000390625 and +$4.501328125 respectively. All figures retain unrounded arithmetic; this is earned activity, not a payable or cash balance roll-forward (reported §1).

P65’s reported $10,278.36 is consistent with ordinary cent rounding, but no approved payout rounding policy was supplied, so the exact difference remains visible. P35’s $5,530 control needs substantive source/control reconciliation. Distribution finance should identify the difference and document the rounding/settlement policy before disposition. No payment, fiduciary withdrawal, licensing decision or producer communication occurred.

Evaluation chronology: the initial native mapping linked the agreement and clause evidence but omitted the newly explicit chargeback_basis field, so the helper withheld the reversal and period totals. A separate mapping supplement places the already supplied clause 7 entitlement in that field without changing raw evidence or expectations. Replay returns the values above and needs-review status. Original and supplemented inputs and outputs are retained.'''
}
for name,body in texts.items():
 p=R/name;inp=json.loads((p/'native-input.json').read_text());rd='mapping-replay' if (p/'mapping-replay/result.json').exists() else 'initial';o=json.loads((p/rd/'result.json').read_text());c=inp['context']
 s=f'# Practitioner response — {name}\n\nSynthetic evaluation case; not a live insurance engagement.\n\nCase `{inp["case_id"]}` | {c["represented_party"]} | {c["capacity"]} | object `{c["object_id"]}` | {c["jurisdiction"]} / {c["line_of_business"]} | as of {inp["as_of"]}.\n\n'+body+f'\n\nNative disposition: **{o["status"]}**, completeness **{o["completeness"]}**, evaluability **{o["evaluability"]}**. Retained native artifact: [{rd}/result.json]({rd}/result.json). Raw source register and exact section mapping: [mapping.json](mapping.json). All evidence is supplied synthetic v1, unauthenticated. Human review remains required; approval not requested and execution not performed.\n'
 (p/'practitioner-response.md').write_text(s)
# Retain an additive correction instead of editing a frozen pre-run expectation.
(R/'reviewer-corrections.md').write_text('''# Evaluator corrections and run notes

- The fraud pre-run expectation correctly froze the unique flagged amount at5000 but incorrectly described the sum of overlapping signal amounts as8000. The raw amounts imply5000+4200=9200. This was an evaluator mental-arithmetic typo, not a native-code defect; original expectations remain unchanged. Exact rational checks independently confirmed every signal amount and union.
- Independent checker attempt1 exited1 because its own text parser captured terminal sentence punctuation in a decimal. Attempt2 exited1 because its own regex assumed a space before a source amount. Both stderr/stdout logs are retained. The corrected checker (attempt3) exited0 with248/248 assertions. No package code, inputs, raw values or expected financial conclusions changed to repair the checker.
- Calculation-source inspection was limited to targeted searches for basis_record_id and chargeback_basis after all seven raw/native cases were frozen and the initial runs completed. No packaged tests/evals/fixtures/goldens/prior audits were opened or run. Directory discovery output listed some filenames but their contents were not consulted.
''')
checker_cmd='/tmp/fsi-p0-venv/bin/python /tmp/insurance-p3-forward-analytics/independent_checks.py'
(R/'independent-executions.json').write_text(json.dumps([{'attempt':i,'command':checker_cmd,'exit':code,'stdout':str(R/(f'independent-checks-attempt{i}.stdout' if i<3 else 'independent-checks.stdout')),'stderr':str(R/(f'independent-checks-attempt{i}.stderr' if i<3 else 'independent-checks.stderr'))} for i,code in [(1,1),(2,1),(3,0)]],indent=2)+'\n')
rows=[]
for name in texts:
 p=R/name;run='mapping-replay' if (p/'mapping-replay/result.json').exists() else 'initial';d=json.loads((p/run/'result.json').read_text());rows.append(f'| {name} | {d["status"]} / {d["completeness"]} | [Practitioner response]({name}/practitioner-response.md) |')
report='''# Independent Phase 3 forward evaluation: analytics group

Seven new practitioner requests and raw synthetic evidence packets were designed from SKILL.md, method/schema/source-map documents, controls, handoffs and output templates. All requests, source packets, evidence mappings, native inputs and expected outcomes were frozen before native computation or implementation inspection. The work was read-only in the repository; outputs are confined to this temporary evaluation directory. No packaged tests, evals, fixtures, golden outputs or prior audits were read or run. No external action or repository edit occurred.

## Outcome

No new calculation, evidence-preservation or professional-meaning defect was demonstrated by these seven cases. Each native input/calculate/output command exited0:21 initial commands plus6 mapping-supplement replay commands. Exit0 includes expected partial draft artifacts; it is not a blanket completion verdict.

The five initial analytics cases matched independent arithmetic and scope expectations. The audit and compensation initial artifacts correctly withheld totals for runtime fields that became explicit during concurrent repository updates. The schema versions first read omitted those field names; current schemas include them. Original raw evidence already supported the facts, so the two cases received separately frozen mapping-only supplements and replayed unchanged financial facts/expectations. This is disclosed as concurrent schema/interface drift, not counted as a new skill defect and not represented as an unchanged-native-input replay. Both original and supplemented artifacts remain inspectable.

An independent exact-rational checker passed248 assertions across frozen-file integrity, retained context/source documents, execution boundaries, arithmetic, unknowns, dates and supported interpretations. It imports no package calculation code. Two checker-parser failures and their repairs are preserved separately; they were evaluator defects, not skill failures. One nonmaterial pre-run handwritten sum typo is disclosed without modifying the frozen expectations.

| Skill | Final native draft state | Authored deliverable |
|---|---|---|
'''+ '\n'.join(rows)+'''

## Material findings and interpretation

- Market:40%/30%/30%, HHI3400 from complete125m inventory. Competing brochure/price evidence survives; no normalized price advantage or strategy selection.
- Product economics: carrier underwriting378000, pretax423000; MGA revenue465000 and result155000. Unknown treaty recovery remains null and the overall artifact partial.
- Portfolio: loss ratio56% to74%; exact18-point bridge comprises8 points mix and10 within. Written-premium expense denominators, exposure frequency and calendar incurred severity remain explicit; inflation causality unproven.
- Fraud: overlapping signals produce three distinct flagged claims and5000 claimed amount; common repairer exclusion is sourced. Mature confirmed share is1/2, not1/3; retrospective discovery is not historical precision or fraud loss.
- Market conduct:5-day observed pass,7-day exception,8-day explicitly pending exception, fourth case unknown. Complete disjoint population metric10/150 is independent of purposive sample; overall partial.
- Premium audit:8130.81 final audited premium,230.81 deposit adjustment and.01 report break, after exact row accumulation and final half-up cents.
- Producer compensation: exact nets10278.359609375 and5534.501328125. P65 sub-cent report difference retained; P35 substantive4.501328125 break retained. Clause-based reversal uses original splits.

## Evidence and reproduction

- `frozen-manifest.json`: pre-execution chronology and SHA256 of all original requests/raw packets/maps/native inputs/expectations.
- Each skill directory: `request.md`, `raw/*.md`, `mapping.json`, `native-input.json`, `expected-before-execution.md`, `initial/result.json` and all initial stdout/stderr, plus `practitioner-response.md`.
- Two affected directories additionally contain `mapping-supplement.json`, `native-input-mapping-supplement.json`, `mapping-replay/result.json` with stdout/stderr and code hashes.
- `initial-executions.json`, `initial-exact-commands.txt`, `mapping-replay-executions.json`: exact interpreter/script/input commands and exit codes.
- `initial-source-hashes.json`: hashes of skill instructions/references/templates and non-test runtime source used at execution; no full package snapshots retained.
- `independent_checks.py`, `independent-checks.json`, `independent-executions.json` and all checker stdout/stderr: transparent independent rational recomputation and source locators.
- `reviewer-corrections.md`: evaluator parsing failures, preserved expectation typo and implementation-inspection chronology.

These results establish bounded behavior on seven synthetic forward cases. They do not establish source authenticity, regulatory applicability, professional signoff, operational deployment acceptance, broad adversarial coverage or production readiness. The practitioner memos are authored evaluation outputs, not evidence of independent insurance-professional acceptance.
'''
(R/'report.md').write_text(report)
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(R.rglob('*')) if p.is_file() and p.name!='delivery-manifest.json'}
(R/'delivery-manifest.json').write_text(json.dumps({'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':manifest},indent=2)+'\n')
print('Authored7 practitioner responses and report; delivery manifest files',len(manifest))
