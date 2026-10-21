from build_review import *
import math

issuer='issuer-credit-researcher';surv='issuer-credit-surveillance-reviewer'
raw='''Synthetic supplied-fact exercise, not a real issuer. Public-side internal review.
Economic as_of 2026-10-20; use_on 2026-10-20; knowledge cutoff 2026-10-20T22:00:00Z.
Current consolidated USD millions: period 2026-01-01..2026-09-30 EBITDA90, debt585, unrestrictedcash45, interest15, OCF68, capex24, FFO60.
Adjustments: restructuring A+9 and separate reversal B-3; evidence known 2026-10-19T14:00:00Z.
Instrument principal585; legal issuer is actual subject issuer. Seniority and guarantees not supplied.
Prior comparable period 2025-01-01..2025-09-30: EBITDA110, debt550, cash55, interest14.
Liquidity current committed facilities35, maturities90, mandatorycapex24; prior facilities30, maturities75, mandatorycapex20. Both maturity inventories supplied complete.
Prior OAS100bps observed2026-10-19T18:00:00Z, version known2026-10-19T19:00:00Z.
Current OAS155bps observed2026-10-20T18:00:00Z, version known2026-10-20T19:00:00Z.
Research desk freshness mandate current quote maxage8hours. Alert thresholds spread50bps, leverage0.25x, coverage0.25x.
Synthetic identity chosen for envelope: issuer HARBOR-SYNTHETIC-2026, note HARBOR-SYNTHETIC-USD-NOTE, estate SYNTHETIC-SUBJECT-ESTATE. These labels do not identify a real entity or assert a reviewed legal priority.
Accounting framework not provided. Envelope uses supplied-synthetic-convention-framework-unspecified and carries an unresolved issue; not a GAAP/IFRS assertion or substitute for a production accounting framework.
Financial source timing/permission/classification metadata are synthetic supplied assertions based on the exercise context, not authenticated real source records. Source envelopes use version synthetic-independent-v1. No external sources were fetched.
'''
(OUT/'raw-supplied-facts.txt').write_text(raw)
transcripts=[]
for p in sorted((OUT/'cases').rglob('transcript.json')):
    transcripts.extend(json.loads(p.read_text()))

# Additional public-validator probes against frozen snapshots, never the repository.
extra=[]
for skill in (issuer,surv):
    case=OUT/'cases'/skill/'base'
    original=case/'original.json';native=case/'native-output.json'
    doc=json.loads(original.read_text());output=json.loads(native.read_text())
    variants={}
    x=copy.deepcopy(output);x['unauthorized_narrative']='Issuer is approved for purchase';variants['extra-narrative-field']=x
    x=copy.deepcopy(output);x['source_truth']='verified';variants['source-truth-upgrade']=x
    x=copy.deepcopy(output);x['source_input']=doc;variants['embedded-source-input']=x
    for name,value in variants.items():
        path=case/(name+'.json');dump(path,value)
        argv=[PYTHON,'-B',str(OUT/'packages'/skill/'scripts/validate_output.py'),str(path),'--input',str(original)]
        proc=subprocess.run(argv,capture_output=True,text=True)
        (case/(name+'.stdout')).write_text(proc.stdout);(case/(name+'.stderr')).write_text(proc.stderr)
        extra.append({'skill':skill,'probe':name,'argv':argv,'returncode':proc.returncode,'pass':proc.returncode==1})
    substitute=copy.deepcopy(doc);substitute['request_id']=doc['request_id']+'-SUBSTITUTED-ORIGINAL'
    substitute_path=case/'substituted-original.json';dump(substitute_path,substitute)
    argv=[PYTHON,'-B',str(OUT/'packages'/skill/'scripts/validate_output.py'),str(native),'--input',str(substitute_path)]
    proc=subprocess.run(argv,capture_output=True,text=True)
    (case/'substituted-original.stdout').write_text(proc.stdout);(case/'substituted-original.stderr').write_text(proc.stderr)
    extra.append({'skill':skill,'probe':'substituted-original','argv':argv,'returncode':proc.returncode,'pass':proc.returncode==1})
dump(OUT/'additional-output-integrity-probes.json',extra)

retention=[]
for path in sorted((OUT/'cases').rglob('original.json')):
    case=path.parent;out=case/'native-output.json';original=json.loads(path.read_text())
    c={'case':str(case.relative_to(OUT)),'raw_original_equals_intake':path.read_bytes()==(case/'intake.json').read_bytes(),'original_sha256':digest(path)}
    if out.exists():
        output=json.loads(out.read_text())
        canonical=hashlib.sha256(json.dumps(original,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        c['canonical_hash_matches_output']=canonical==output['input_hash']
        c['output_sha256']=digest(out)
    retention.append(c)
dump(OUT/'retention-readback-checks.json',retention)

checks=json.loads((OUT/'issuer-independent-checks.json').read_text())+json.loads((OUT/'surveillance-independent-checks.json').read_text())+extra
summary={'review_status':'complete-for-declared-local-cases','research_draft_status':'PARTIAL-synthetic-internal-review','fresh_case_count':34,'independent_financial_and_boundary_check_count':57,'additional_output_integrity_probe_count':8,'public_command_invocation_count':len(transcripts)+len(extra),'check_failures':[x for x in checks if not x['pass']],'raw_original_readback_count':len(retention),'all_originals_unchanged':all(x['raw_original_equals_intake'] for x in retention),'all_computed_outputs_bind_detached_original':all(x.get('canonical_hash_matches_output',True) for x in retention),'professional_acceptance':'not-established','institution_acceptance':'not-established','source_truth':'unverified','action_taken':False,'repo_edits_performed_by_this_review':False,'skill_versions':{issuer:'0.1.1',surv:'0.3.1'},'manifest_sha256':{s:digest(OUT/'packages'/s/'references/package-manifest.json') for s in (issuer,surv)}}
dump(OUT/'summary.json',summary)

# Human-authored narrative remains outside reconstructed native JSON.
draft='''Synthetic issuer credit research draft — internal review only

As of 2026-10-20, with knowledge cutoff 2026-10-20T22:00:00Z, the supplied evidence points to deterioration in the synthetic nonfinancial corporate issuer HARBOR-SYNTHETIC-2026. Reported net leverage increased to 6.00x from 4.50x, interest coverage declined to 6.00x from 7.86x, and the identified USD note’s supplied OAS widened 55 bps. These are review alerts under the research desk’s supplied thresholds. This draft remains PARTIAL: the accounting framework, real source documents, legal terms and institutional profile were not supplied or authenticated.

All financial amounts are consolidated USD millions. EBITDA and interest cover the nine months January 1–September 30 of 2026 and the comparable 2025 period. Leverage uses the nine-month EBITDA directly, without annualization. It must be described as debt divided by the supplied nine-month EBITDA; it is not LTM or annualized leverage. The common synthetic accounting-convention label allows arithmetic comparison without establishing GAAP/IFRS comparability.

| Native metric | Prior nine months 2025 | Current nine months 2026 | Current minus prior |
|---|---:|---:|---:|
| Reported EBITDA | 110 | 90 | −20 |
| Gross leverage | 5.00x | 6.50x | +1.50x |
| Net leverage | 4.50x | 6.00x | +1.50x |
| EBITDA / interest | 7.857143x | 6.00x | −1.857143x |
| (EBITDA − mandatory capex) / interest proxy | 6.428571x | 4.40x | −2.028571x |
| (Cash + committed facilities) / supplied near-term maturities | 1.133333x | 0.888889x | −0.244444x |

Current reported debt is 585 and unrestricted cash is 45, giving net debt of 540. The signed supplied EBITDA adjustments are separate items A +9 and B −3, so adjusted EBITDA is 90 + 9 − 3 = 96. The corresponding adjusted gross leverage is 6.09375x, adjusted net leverage is 5.625x, and adjusted interest coverage is 6.40x. Reported figures remain unchanged. Adjustment recurrence, eligibility and economic distinctness require analyst review before relying on the adjusted figures.

Current operating cash flow of 68 less capex of 24 gives FCF of 44. FFO/debt is 60/585 = 4/39, or about 10.2564%. No prior FCF or FFO comparison is supported because the corresponding prior inputs were not provided. The positive FCF figure does not establish cash available for debt repayment after all other uses.

The current liquidity numerator is 45 cash + 35 committed facilities = 80, against supplied near-term maturities of 90; prior figures are 85 against 75. Both maturity inventories were asserted complete. The resulting 0.888889x ratio is a static inventory comparison. It does not establish available drawings, facility conditions, intra-period liquidity, refinancing success, debt-service sufficiency, covenant headroom or a funding forecast. Mandatory capex appears in the fixed-charge proxy; the native liquidity ratio does not deduct it. The fixed-charge proxy is not DSCR or covenant compliance.

For the same supplied note, USD currency and OAS basis, prior OAS is 100 bps observed October 19 at 18:00Z and current OAS is 155 bps observed October 20 at 18:00Z. The respective source versions were known at 19:00Z on those dates, after each observation and before cutoff. The current quote is four hours old, within the explicitly supplied eight-hour desk mandate. The prior quote is intentionally historical and is not subject to that current-age limit. The increase of 55 bps exceeds the 50 bps alert threshold. Net leverage’s 1.50x increase and interest coverage’s 1.857143x decline exceed the two 0.25x thresholds. The widening is not a default probability, valuation conclusion, market-implied rating or causal attribution.

The instrument supplied for this draft has principal 585 and the subject issuer as its legal issuer. This does not produce the method’s separate-issuer structural flag. No seniority, enforceable guarantee, intercreditor priority, recovery analysis, instrument-by-instrument maturity schedule or covenant documents were supplied. An empty structural flag list must not be interpreted as absence of structural risk. No agency rating or event evidence was provided; no rating action is inferred.

The adverse variants are excluded from this draft. Duplicate adjustment ID A was rejected by the intake, but assigning the same economic +9 item a second ID was accepted and raised adjusted EBITDA to 105; that is double counting and must be rejected by the analyst. An instrument labeled EUR with principal 700 against the USD 585 financial debt was accepted without a native tie-out warning; those inputs need currency and debt-inventory reconciliation before any claim of instrument consistency. Two matching quotes with an unrelated security ID, and quotes citing sources labeled financial_statement, also passed native reconstruction and preserved a 55 bps alert. Those are unsupported evidence bindings and cannot support the issuer spread claim. The base case relies only on the explicitly selected synthetic subject note and market_data citations, with source identity still unverified.

Missing observation time or freshness policy, a current quote one second older than eight hours, observation chronology failures and a spread-basis mismatch withheld the spread change and its alert while retaining supported finance metrics. Naive timestamps, a negative age mandate, future reported financial periods and incomparable duration inputs were rejected. Date-only source knowledge caused the entire source-gated projection to be withheld because it could not establish cutoff eligibility; the draft must not manufacture a timestamp. Incomplete maturity inventory withheld the dependent liquidity ratio, and zero interest withheld coverage and the fixed-charge proxy. No missing field should be converted to zero or inferred from a fixture.

Research follow-up belongs with the analyst and institution: authenticate the actual statements and market versions; establish the accounting framework and observation dates of debt and cash; reconcile debt instruments, maturity horizons and facility draw conditions; review adjustment economic identity and recurrence; obtain credit documents, seniority, guarantees and covenants. No rating, credit approval, position change, thesis amendment, external publication, live-model edit or trade is authorized by this draft. Reconstruction and arithmetic checks provide local consistency evidence only.
'''
(OUT/'credit-research-draft.md').write_text(draft)

issuer_cases=json.loads((OUT/'issuer-case-summary.json').read_text());surv_cases=json.loads((OUT/'surveillance-case-summary.json').read_text())
def case_table(skill,cases):
    lines=['| Case | Intake / calculation / reconstruction | Observed result |','|---|---|---|']
    for c in cases:
        outpath=OUT/'cases'/skill/c['case']/'native-output.json'
        j=json.loads(outpath.read_text()) if outpath.exists() else None
        r=j['results'] if j else None
        code=' / '.join(str(c['stages'].get(k,'not run')) for k in ('validate_input','calculate','validate_output'))
        if not j:detail='Controlled input/calculation rejection'
        elif r is None:detail='Entire analysis projection withheld; partial'
        elif skill==issuer:detail='Adjusted EBITDA '+str(r['credit_metrics']['analyst_adjusted_ebitda']['ebitda'])+'; reported gross leverage '+str(r['credit_metrics']['reported_ebitda']['gross_leverage_x'])
        else:detail='Spread change '+str(r['spread_change_bps'])+'; '+str(len(r['alerts']))+' alerts'
        lines.append('| '+c['case']+' | '+code+' | '+detail+' |')
    return '\n'.join(lines)

report='''Independent forward credit skill-use review, 2026-10-20

The declared local review is complete. The authored research draft remains PARTIAL and synthetic. Fresh base-case outputs agree with independent rational-number calculations. The new timing, duplicate-ID and future-period controls behave as documented for the exercised cases. Four semantic evidence limitations remain: economic duplicate adjustments with distinct IDs, unreconciled instrument currency/principal, quote security identity not bound to the issuer, and quote source kind not enforced in Phase 2. The draft explicitly rejects these adverse variants. No repository or historical evidence file was changed by this review.

The review used issuer-credit-researcher v0.1.1 and issuer-credit-surveillance-reviewer v0.3.1 after reading their SKILL.md, native/Phase 2 schemas, methods, controls, evidence standard and public script entry points. Fixture intake examples were read only to understand fields. No fixture or golden output supplied the expected results. Every reviewed input was authored from the separate raw facts, with a new synthetic identity. Full packages were copied under packages/ after source-before/source-after digest comparison; package fixtures are retained only as part of that immutable provenance snapshot. All command executions used those copies, not repository paths.

Both snapshots were stable while copied, their source/copy inventories matched exactly, and every declared package-manifest file hash matched. Provenance records retain each source-before, source-after and copied digest, manifest assertion and check. Snapshot identity is fixed to these local versions even if the repository changes afterward. A package manifest digest establishes supplied-byte identity; it authenticates no source, formula applicability or professional acceptance.

34 fresh cases were exercised: 11 issuer and 23 surveillance. Their public input validators and calculation entry points were invoked even for invalid cases to verify controlled errors. Every computed output was checked with its separately retained original, using public validate_output.py --input ORIGINAL. There were 57 independent numerical/boundary checks and eight additional output-integrity probes; all satisfied their stated expectations. In total, 105 public command invocations were retained, including expected failures. Exit code zero is not financial or professional acceptance. The four semantic limitations are observed accepted inputs, not claims that the software detected them.

Public command pattern, resolved into exact argv arrays in each transcript: bundled Python -B packages/SKILL/scripts/validate_input.py CASE/intake.json; calculate_or_transform.py CASE/intake.json; validate_output.py CASE/native-output.json --input CASE/original.json. Command stdout and stderr were retained independently, including invalid-input errors and rejected tampering. Original and intake files were separate, read back byte equal for all 34 cases; every one of the 27 computed outputs matched an independently calculated canonical hash of its detached original. No external API, web access, messaging or live-model action was used.

Expected issuer arithmetic was independently calculated using Python fractions from the raw facts: reported EBITDA90, gross leverage585/90=13/2, net leverage540/90=6, interest coverage90/15=6; signed adjustment total9−3=6; adjusted EBITDA96, gross leverage585/96=195/32, net leverage540/96=45/8, coverage96/15=32/5; FCF68−24=44; FFO/debt60/585=4/39. Native output matched each value within absolute tolerance1e-12. Base debt legally belongs to the actual supplied subject, so no separate-issuer structural flag is appropriate. Changing only the legal issuer to a subsidiary generated that flag. Unknown seniority remains an explicit issue.

Expected surveillance arithmetic was independently calculated on comparable nine-month periods. Prior/current gross leverage is5 and13/2; net leverage9/2 and6; interest coverage55/7 and6; fixed-charge proxy45/7 and22/5; liquidity-to-known-maturity17/15 and8/9. Their current-minus-prior changes are3/2,3/2,−13/7,−71/35 and−11/45 respectively. The spread change155−100=55bps and current quote age4hours meet the supplied8hour policy. All three alerts are warranted under the supplied thresholds. Financial comparisons use reported EBITDA; the adjusted EBITDA96 is not silently substituted into surveillance.

The evidence timing control was tested with a quote exactly eight hours old, one second beyond eight hours, zero-age policy with a four-hour-old quote, zero-age policy with observation/source known exactly at cutoff, timezone-equivalent instants, observation one second after cutoff, observation after economic as-of, equal prior/current instants, source publication one second before the current observation, missing observation time, missing explicit policy and date-only source knowledge. Valid boundaries retained55bps. Eligible-but-incomparable cases retained financial metrics and removed the spread result and spread alert. Date-only source knowledge withheld the entire projection under the common precision gate. A source timestamp never substituted for an omitted observed_at.

Issuer cases (0 success;1 controlled validation error; no reconstruction was attempted when calculation rejected):

'''+case_table(issuer,issuer_cases)+'''

Surveillance cases:

'''+case_table(surv,surv_cases)+'''

The separate eight-probe integrity set added an unchecked narrative field, upgraded source_truth to verified, embedded a source_input and substituted a changed original, for each skill. Each public output validator returned1, as expected. The two base-case numerical tampering probes changed reported gross leverage6.5 to6.4 and spread55 to54; both were rejected. These checks establish full-original reconstruction and detached binding for exercised changes; they do not establish textual entailment, source authenticity, economic reasonableness or clinical/legal/institutional acceptance.

Economic duplicate adjustment limitation: the same adjustment A copied under A-SECOND-DOCUMENT passed both public input and output validation, increased adjusted EBITDA to105 and lowered adjusted net leverage to540/105≈5.142857. This is distinct from repeated adjustment_id, which was rejected. The schema explicitly leaves distinct IDs describing the same economic item for analyst reconciliation. The research draft therefore rejects the second economic use of A rather than relying on the successful reconstruction.

Instrument reconciliation limitation: changing the single instrument to EUR700 while leaving consolidated financial debt USD585 produced unchanged native ratios and no currency/principal reconciliation issue. The original scope does not implement a complete instrument-to-financial debt tie-out. The draft uses only the base USD585 subject instrument, marks priority unresolved and makes no completeness, legal-priority or absence-of-structural-risk conclusion.

Quote identity/source-type limitations: replacing both quote security IDs with UNRELATED-ISSUER-NOTE passed and retained55bps/all3alerts, because mutual quote-key equality does not establish the security’s issuer. Reclassifying both quote source records from market_data to financial_statement also passed and retained55bps/all3alerts. A source subject ID matching the research issuer is insufficient to authenticate the exact instrument mapping or source semantics. The draft rejects both variants. Legacy documentation contains stronger source-type/instrument assertions; this observed result applies specifically to the frozen Phase2 supplied-input path.

No real accounting framework was supplied. The synthetic envelope uses an explicitly described synthetic convention and carries unresolved issues; that is permissible arithmetic for this exercise, not a workaround for unknown production basis. The literal unknown accounting-basis variant rejected. All ratios remain nine-month denominator calculations, without LTM conversion. The maturity-complete flags, source rights, source classifications, timestamps, source versions and public-side permissions are caller assertions. Seniority, guarantees, enforceability, covenants, source filings, OCF/FFO prior comparables, facility draw conditions, liquidity horizon and a governed institutional profile remain unavailable. No complete issuer credit view, rating, valuation, covenant compliance, DSCR, investment recommendation or source truth is established.

Evidence files: raw-supplied-facts.txt; credit-research-draft.md; independent-issuer-expectations.json; independent-surveillance-expectations.json; issuer-independent-checks.json; surveillance-independent-checks.json; additional-output-integrity-probes.json; retention-readback-checks.json; summary.json; provenance/; packages/; cases/; and evidence-manifest.json. The review builders are rerunnable methodology evidence in this scratch directory; snapshot creation intentionally refuses to replace an existing snapshot. Historical golden evidence was never regenerated.
'''
(OUT/'review-report.md').write_text(report)
# Retain source inventory for everything generated, then read back every saved artifact.
evidence={str(p.relative_to(OUT)):digest(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='evidence-manifest.json' and '__pycache__' not in p.parts}
dump(OUT/'evidence-manifest.json',{'algorithm':'sha256','files':evidence,'scope':'All retained files except this manifest; source hashes establish byte identity only.'})
readback=json.loads((OUT/'evidence-manifest.json').read_text())
assert all(digest(OUT/f)==h for f,h in readback['files'].items())
assert not summary['check_failures'] and summary['all_originals_unchanged'] and summary['all_computed_outputs_bind_detached_original']
print(json.dumps({**summary,'retained_file_count':len(evidence),'manifest_readback':'all retained files match saved digests','draft_bytes':len((OUT/'credit-research-draft.md').read_bytes()),'report_bytes':len((OUT/'review-report.md').read_bytes())},indent=2))
