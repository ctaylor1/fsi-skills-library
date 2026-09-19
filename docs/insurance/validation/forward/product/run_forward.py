from pathlib import Path
import json, subprocess, hashlib

ROOT=Path('/tmp/insurance-product-forward-20260918')
PYTHON='/tmp/fsi-p0-venv/bin/python'

def base(capacity,object_id,source_refs):
    return {'as_of':'2026-09-18','context':{'capacity':capacity,'represented_party':'Synthetic insurer or applicant; no live customer','object_id':object_id},'sources':[{'source_ref':r,'version':'synthetic-v1','as_of':'2026-09-18'} for r in source_refs]}
def save(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n')
def term(start,ref):
    return {'term_effective':start,'annual_premium':100000,'source_ref':ref,'coverages':[{'coverage':'Building','limit':1000000,'deductible':1000}],'exposures':[{'basis':'TIV','value':1000000}],'forms':[{'form_id':'SYNTH-PROP','edition':'2026-01'}]}
reserve=base('P&C reserving actuary','synthetic-paid-triangle',['triangle-v1'])
reserve.update({'dataset_version':'synthetic-reserve-v1','valuation_date':'2026-09-18','currency':'USD','unit':'USD thousands','large_loss_threshold':1000,'segments':[{'segment_id':'PROP-PAID','line_of_business':'P&C property','triangle_basis':'paid','development_ages':[12,24],'triangle':{'2024':[100,160],'2025':[250]},'factor_method':'volume-weighted','tail_factor':1,'source_ref':'triangle-v1'}]})
quote=base('Broker','synthetic-property-quotes',['quote-A-v1','quote-B-v1'])
quote.update({'config_version':'synthetic-normalization-v1','config':{'round_to':2},'risk_type':'property','quotes':[{'quote_id':qid,'carrier':'Synthetic carrier '+qid,'term_months':12,'premium':{'amount':amt,'frequency':'annual'},'fees':[],'currency':ccy,'as_of':'2026-09-18','source_ref':'quote-'+qid+'-v1','coverages':[{'code':'BUILDING','name':'Building','limit':100000,'deductible':1000}],'exclusions':[],'endorsements':[]} for qid,amt,ccy in [('A',1000,'USD'),('B',900,'CAD')]]})
renewal=base('Renewal analyst','SYNTHETIC-0001',['pas-expiring-v1','pas-proposed-v1','loss-history-v1'])
renewal.update({'policy_id':'SYNTHETIC-0001','config_version':'synthetic-renewal-v1','currency':'USD','line_of_business':'P&C property','review_window_days':1095,'claims_complete':True,'expiring':term('2025-10-01','pas-expiring-v1'),'proposed':term('2026-10-01','pas-proposed-v1'),'claims':[{'claim_id':'SYNTH-C'+str(i),'date_of_loss':str(year)+'-01-15','incurred':100000,'paid':100000,'status':'closed','cause':'synthetic property damage','source_ref':'loss-history-v1/row'+str(i)} for i,year in enumerate([2024,2025,2026],1)]})
reins=base('Ceded reinsurance analyst','SYNTH-TREATY-0001',['treaty-v1','loss-bordereau-v1','eligibility-review-v1'])
reins.update({'treaty_id':'SYNTH-TREATY-0001','cedent':'Synthetic insurer','treaty_type':'excess_of_loss','uw_year':'2026','currency':'USD','inception_date':'2026-01-01','expiry_date':'2026-12-31','illustration_basis':'losses_occurring','illustration_basis_source':'treaty-v1/article-1;reviewed-assumption','layer':{'attachment':5000000,'limit':10000000,'aggregate_limit':20000000,'reinstatements':1,'reinstatement_basis':'pro_rata_amount_on_erosion','reinstatement_terms':[{'premium_pct':100}],'layer_premium':2000000},'clauses':[{'clause_id':'A1','clause_type':'attachment','heading':'Layer and period','text':'For eligible losses occurring during 2026, this layer is USD 10,000,000 excess of USD 5,000,000 per occurrence.','source':{'system':'synthetic-treaty','ref':'treaty-v1/article-1'}},{'clause_id':'A2','clause_type':'limit','heading':'Aggregate','text':'The annual aggregate limit is USD 20,000,000.','source':{'system':'synthetic-treaty','ref':'treaty-v1/article-2'}},{'clause_id':'A3','clause_type':'reinstatement','heading':'Reinstatement','text':'One reinstatement restores erosion pro rata as to amount at 100 percent of the USD 2,000,000 layer premium, with no time adjustment.','source':{'system':'synthetic-treaty','ref':'treaty-v1/article-3'}}],'losses':[{'occurrence_id':'SYNTH-EVENT-1','date':'2026-07-01','gross_loss':12000000,'description':'Synthetic reviewed eligible loss','eligible_for_illustration':True,'eligibility_source_ref':'eligibility-review-v1/row1','source':{'system':'synthetic-bordereau','ref':'loss-bordereau-v1/row1'}}]})
cases=[('01-paid-reserving','reserving-analysis-assistant',reserve,"I am a P&C reserving actuary. Develop the paid triangle to ultimate: 2024 has 100 at 12 months and 160 at 24 months; 2025 has current paid 250 at 12 months. Use volume-weighted factors, tail 1, USD thousands, valuation 2026-09-18. For 2025 my separately supplied case outstanding is 80 and reviewer-selected ultimate is 400 (synthetic practitioner-context-v1). Explain the financial components this package supports and any limitations.",'The native documented schema has no separate case-outstanding/selected-ultimate field. Those figures remain in the raw request and practitioner context; the engine receives the stated paid triangle. No native schema field was invented.'),('02-mixed-currency-quotes','premium-quote-comparator',quote,"I am the broker for a synthetic property risk. Compare these same-date annual quotes: A costs USD 1,000; B costs CAD 900. Each lists a building limit of 100,000 and deductible 1,000 in its own currency. No extra fees, exclusions or endorsements are listed. No FX rate or separate equivalence assessment is supplied. Give a useful comparison without assuming the currencies or terms are equivalent.",'Quote dates and zero fees are supplied synthetic facts; currencies remain original. No FX or comparability evidence was invented.'),('03-earned-loss-ratio','policy-renewal-reviewer',renewal,"I am a renewal analyst. The complete supplied three-year USD claims history contains three closed claims with incurred losses 100,000 each, total 300,000, dated 2024-01-15, 2025-01-15 and 2026-01-15. The current annual premium is 100,000 and proposed annual premium is also 100,000. Terms, building exposure and form are otherwise unchanged. At 2026-09-18, calculate the earned loss ratio for the 1,095-day inclusive review window. I have no historical earned-premium ledger covering that same window.",'Confirmed synthetic history is marked claims_complete=true. No earned_premium object is supplied. Both terms are provided to satisfy renewal scope; identical coverage/exposure/form facts are declared synthetic.'),('04-ceded-illustration','reinsurance-treaty-interpreter',reins,"I am a ceded reinsurance analyst. Illustrate one reviewer-confirmed eligible USD 12m loss on 2026-07-01 in a USD 10m excess USD 5m losses-occurring layer for calendar 2026. Aggregate is explicitly USD 20m. One reinstatement restores erosion pro rata as to amount at 100% of a USD 2m layer premium, with no time adjustment. Supplied wording and eligibility references are synthetic review evidence. Explain ceded amount, remaining aggregate, restored amount and reinstatement premium; make no real-claim recoverability decision.",'All eligibility, chronology, attachment-basis and reinstatement assumptions required by the package are supplied explicitly with synthetic sources.')]
run_summary=[]
for name,package,inp,request,adaptation in cases:
    dest=ROOT/'cases'/name
    dest.mkdir(parents=True,exist_ok=True)
    (dest/'raw-request.md').write_text(request+'\n')
    (dest/'input-adaptation.md').write_text(adaptation+'\n')
    save(dest/'input.json',inp)
    if name.startswith('01'):
        save(dest/'practitioner-context.json',{'origin':'2025','case_outstanding':80,'reviewer_selected_ultimate':400,'currency':'USD','unit':'USD thousands','source_ref':'synthetic-practitioner-context-v1','assumption':'aligned origin, valuation, basis and units for explanatory reconciliation only'})
    logs=[]
    for label,script,arg in [('input-validation','validate_input.py','input.json'),('calculation','calculate_or_transform.py','input.json')]:
        args=[PYTHON,str(ROOT/package/'scripts'/script),str(dest/arg)]
        result=subprocess.run(args,text=True,capture_output=True)
        (dest/(label+'.stdout.txt')).write_text(result.stdout)
        (dest/(label+'.stderr.txt')).write_text(result.stderr)
        logs.append({'stage':label,'command':args,'exit_code':result.returncode})
        if label=='calculation' and result.returncode==0:
            output=json.JSONDecoder().raw_decode(result.stdout)[0]
            save(dest/'native-output.json',output)
    args=[PYTHON,str(ROOT/package/'scripts/validate_output.py'),str(dest/'native-output.json')]
    result=subprocess.run(args,text=True,capture_output=True)
    (dest/'native-output-validation.stdout.txt').write_text(result.stdout)
    (dest/'native-output-validation.stderr.txt').write_text(result.stderr)
    logs.append({'stage':'native-output-validation','command':args,'exit_code':result.returncode})
    save(dest/'run-log.json',logs)
    run_summary.append({'case':name,'package':package,'runs':logs})
save(ROOT/'run-summary.json',run_summary)
print(json.dumps([{k:r[k] for k in ['case','package']}|{'exits':[x['exit_code'] for x in r['runs']]} for r in run_summary],indent=2))
