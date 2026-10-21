"""Paired provider-augmentation outcome/cost benchmark with temporal leakage checks."""
from decimal import Decimal
from design_support import Review, total, ratio, validate_with
METHOD='paired-data-product-value-v1'


def evaluate(doc):
    r=Review(doc,METHOD);d=r.data
    rows=r.rows('cases','case_id');license=d.get('license')
    license_start = len(r.findings)
    if not isinstance(license,dict):raise ValueError('license must be an object')
    r.evidence(license);r.fields(license,('provider','version','purpose','reviewed_by','retention_rule'))
    allowed=r.flag(license,'use_permitted')
    expiry=r.date(license,'effective_to',future=True);start=r.date(license,'effective_from')
    allowed &= r.need(start is not None and expiry is not None and start<=r.date(doc,'as_of')<=expiry,'license-period','License dates must cover review and intended use',license)
    r.need(d.get('purpose')==license.get('purpose'),'purpose','Evaluation purpose differs from reviewed license purpose',license)
    license_valid = r.scope_valid and allowed and not any(f['severity'] == 'gap' for f in r.findings[license_start:])
    r.fields(d,('purpose','population','outcome_definition','currency','baseline_version','augmented_version','comparison_protocol'))
    r.flag(d,'paired_inventory_complete');r.flag(d,'ground_truth_reviewed')
    matrix={mode:{'tp':0,'tn':0,'fp':0,'fn':0} for mode in ('baseline','augmented')};gain=[];covered=0
    for row in rows:
        decision=r.date(row,'decision_on');outcome=r.date(row,'outcome_on');available=r.date(row,'provider_available_on') if row.get('provider_available_on') is not None else None
        r.need(decision is not None and outcome is not None and outcome>=decision,'outcome-date','Outcome must mature no earlier than the decision',row)
        r.need(row.get('population')==d.get('population') and row.get('currency')==d.get('currency'),'cohort','Case population/currency differs',row)
        r.need(row.get('baseline_version')==d.get('baseline_version') and row.get('augmented_version')==d.get('augmented_version'),'version','Compared algorithms must bind declared versions',row)
        r.need(isinstance(row.get('provider_match'),bool),'coverage','Provider match is explicit boolean',row)
        if row.get('provider_match'):
            covered+=1;r.need(available is not None and decision is not None and available<=decision,'temporal-leakage','Matched provider evidence was not available at decision time',row)
        r.need(all(isinstance(row.get(k),bool) for k in ('truth','baseline_prediction','augmented_prediction')),'label','Truth and both predictions must be known reviewed booleans',row)
        for mode in matrix:
            pred=row.get(mode+'_prediction');truth=row.get('truth')
            if isinstance(pred,bool) and isinstance(truth,bool):matrix[mode][('t' if pred==truth else 'f')+('p' if pred else 'n')]+=1
        a=r.num(row,'baseline_outcome_cost');b=r.num(row,'augmented_outcome_cost');gain.append(a-b if a is not None and b is not None else None)
    valid=r.clear
    for mode,counts in matrix.items():
        counts['precision']=ratio(Decimal(counts['tp']),Decimal(counts['tp']+counts['fp'])) if valid else None
        counts['recall']=ratio(Decimal(counts['tp']),Decimal(counts['tp']+counts['fn'])) if valid else None
    observed=total(gain) if valid else None
    projection=d.get('projection');annual=None
    if projection is not None:
        if not isinstance(projection,dict):raise ValueError('projection must be an object or null')
        r.evidence(projection);r.flag(projection,'representativeness_reviewed');r.fields(projection,('basis','reviewed_by'))
        volume=r.num(projection,'annual_volume');license_cost=r.num(projection,'annual_license_cost');run_cost=r.num(projection,'incremental_cost_per_case');fixed=r.num(projection,'annual_operating_cost')
        r.need(projection.get('currency')==d.get('currency'),'currency','Projection currency differs',projection)
        if r.clear and valid and rows and all(x is not None for x in (volume,license_cost,run_cost,fixed)):
            annual=volume*(observed/Decimal(len(rows))-run_cost)-license_cost-fixed
    if not valid:
        matrix=None;covered=None
    return r.finish({'sample_size':len(rows),'provider_matched_cases':covered,'provider_coverage':ratio(Decimal(covered),Decimal(len(rows))) if covered is not None else None,
                     'confusion_matrices':matrix,'observed_outcome_cost_reduction':observed,'projected_annual_net':annual,
                     'license_usable_for_stated_purpose':license_valid,'causal_uplift_established':False,'provider_selected':False})


def validate(doc):return validate_with(evaluate,doc)
