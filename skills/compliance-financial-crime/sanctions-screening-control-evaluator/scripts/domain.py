"""Offline sanctions screening control review of supplied evidence (MIT).

No screening engine, current-list retrieval, label generation or legal disposition.
"""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import re
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, strings, records, unique_ids, day)

SKILL = 'sanctions-screening-control-evaluator'
METHOD = 'supplied-screening-control-reconciliation/1.0'
OBJECT_TYPES = {'sanctions_screening_control_review'}
DIMENSIONS = {'population','feed','list','field','transliteration','matching',
              'configuration','vendor','resilience','latency'}
TOP = {'request_id','object_id','object_type','as_of','knowledge_cutoff','workflow','sources','data'}
T = text
B = lambda v: isinstance(v, bool)
L = strings
E = lambda *items: lambda v: isinstance(v, str) and v in items


def instant(value):
    """Require explicit RFC3339 offset; naive instants cannot prove ordering."""
    if not isinstance(value, str) or not re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', value):
        return None
    if value[-1:]!='Z' and (int(value[-5:-3])>23 or int(value[-2:])>59):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z','+00:00'))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, OverflowError):
        return None


def decimal_string(value, rate=False):
    if not isinstance(value, str) or not re.fullmatch(r'(?:0|[1-9]\d*)(?:\.\d+)?', value):
        return False
    try:
        parsed = Decimal(value)
        return parsed.is_finite() and (not rate or parsed <= 1)
    except InvalidOperation:
        return False


def seconds(a, b):
    delta = b-a
    micros = (delta.days*86400+delta.seconds)*1000000+delta.microseconds
    sign = '-' if micros < 0 else ''
    whole, remainder = divmod(abs(micros),1000000)
    return sign+str(whole)+(('.'+str(remainder).zfill(6).rstrip('0')) if remainder else '')


D = lambda v: instant(v) is not None
Q = decimal_string
R = lambda v: decimal_string(v, True)
OBJECTS = {
 'review': {'window_from':D, 'window_to':D, 'regimes':L, 'population_ids':L,
    'feed_ids':L, 'list_ids':L, 'testset_ids':L, 'control_ids':L,
    'required_fields':L, 'required_scripts':L, 'required_test_dimensions':L,
    'maximum_list_update_lag_seconds':Q, 'maximum_latency_seconds':Q,
    'maximum_false_positive_rate':R, 'maximum_false_negative_rate':R,
    'mandate_owner':T, 'mandate_type':E('operational-qa','second-line-monitoring','independent-testing'),
    'population_grain':E('screening-input-record-id')},
 'configuration': {'engine_id':T, 'engine_version':T, 'configuration_version':T,
    'vendor_reference':T, 'vendor_version':T, 'effective_from':D, 'effective_to':D,
    'fields':L, 'scripts':L, 'normalization_rules':T, 'transliteration_rules':T,
    'matching_method':T, 'threshold_description':T},
}
COLLECTIONS = {
 'feeds':('feed_id', {'population_ids':L,'received_ids':L,'screened_ids':L,
    'fields':L,'scripts':L,'window_from':D,'window_to':D}),
 'lists':('list_id', {'regime':T,'expected_version':T,'loaded_version':T,
    'published_at':D,'effective_at':D,'loaded_at':D,
    'expected_entry_ids':L,'loaded_entry_ids':L}),
 'testsets':('testset_id', {'version':T,'case_ids':L,'label_reference':T,
    'label_version':T,'label_scope':T,'labels_as_of':D,
    'accepted_for_measurement':B,'selection_method':T,'represented_dimensions':L}),
 'tests':('test_id', {'case_id':T,'testset_id':T,'testset_version':T,
    'feed_id':T,'list_id':T,'list_version':T,'engine_id':T,'engine_version':T,'configuration_version':T,
    'dimension':T,'input_fields':L,'input_script':T,
    'expected_detection':E('expected-alert','expected-no-alert'),
    'observed_detection':E('alert','no-alert','error'),
    'observed_at':D,'latency_seconds':Q,'evidence_complete':B}),
 'controls':('control_id', {'dimension':E(*sorted(DIMENSIONS)),'requirement':T,
    'procedure':T,'population_ids':L,'observed_at':D,
    'outcome':E('pass','fail','unknown'),'evidence_complete':B,'finding':T}),
}


def validate(doc):
    errors = validate_common(doc, OBJECT_TYPES)
    if not isinstance(doc, dict) or not isinstance(doc.get('data'), dict):
        return errors, []
    if set(doc) != TOP:
        errors.append('undeclared or missing native top-level fields')
    data = doc['data']
    if set(data) != set(OBJECTS)|set(COLLECTIONS):
        errors.append('data must contain exactly the declared domain objects and collections')
    def check(row, schema, label, identifier=None):
        if not isinstance(row,dict):
            errors.append(label+': object required')
            return
        if set(row) != set(schema)|({identifier} if identifier else set()):
            errors.append(label+': missing or undeclared fields')
        for field,predicate in schema.items():
            claim=row.get(field)
            if not isinstance(claim,dict) or set(claim) != {'value','source_refs','fact_ids'}:
                errors.append(label+'.'+field+': exact claim object required')
                continue
            if not strings(claim['source_refs']) or not strings(claim['fact_ids']):
                errors.append(label+'.'+field+': string reference arrays required')
            elif len(set(claim['source_refs'])) != len(claim['source_refs']) or len(set(claim['fact_ids'])) != len(claim['fact_ids']):
                errors.append(label+'.'+field+': duplicate references forbidden')
            value=claim['value']
            if value is not None:
                if not predicate(value):
                    errors.append(label+'.'+field+': unsupported value type, decimal precision, timestamp or enum')
                elif isinstance(value,list) and len(set(value)) != len(value):
                    errors.append(label+'.'+field+': duplicate identities forbidden')
    for name,schema in OBJECTS.items():
        check(data.get(name),schema,name)
    for name,(identifier,schema) in COLLECTIONS.items():
        rows=data.get(name)
        if not records(rows) or not unique_ids(rows,identifier):
            errors.append(name+': distinct nonempty record IDs required')
            continue
        for row in rows:
            check(row,schema,name+'.'+row[identifier],identifier)
    if errors:
        return errors, []
    raw=lambda row,key:row[key]['value']
    review=data['review']
    for name,(identifier,_) in COLLECTIONS.items():
        scope={'feeds':'feed_ids','lists':'list_ids','testsets':'testset_ids','controls':'control_ids'}.get(name)
        if scope and raw(review,scope) is not None:
            if set(raw(review,scope)) != {row[identifier] for row in data[name]}:
                errors.append(name+': collection IDs differ from declared review scope')
    scopes={name:{row[identifier]:row for row in data[name]} for name,(identifier,_) in COLLECTIONS.items()}
    populations=[]
    for feed in data['feeds']:
        ids=raw(feed,'population_ids')
        if ids is not None:
            populations.extend(ids)
            declared=raw(review,'population_ids')
            if declared is not None and not set(ids).issubset(declared):
                errors.append(feed['feed_id']+': feed population outside declared review')
            for field in ('received_ids','screened_ids'):
                observed=raw(feed,field)
                if observed is not None and not set(observed).issubset(ids):
                    errors.append(feed['feed_id']+': '+field+' outside exact feed population')
        a,b=instant(raw(feed,'window_from')),instant(raw(feed,'window_to'))
        if a and b and a>b:
            errors.append(feed['feed_id']+': reversed feed window')
    if len(populations)!=len(set(populations)):
        errors.append('feed population record identities overlap; mixed/repeated grain forbidden')
    a,b=instant(raw(review,'window_from')),instant(raw(review,'window_to'))
    if a and b and a>b:
        errors.append('review window is reversed')
    a,b=instant(raw(data['configuration'],'effective_from')),instant(raw(data['configuration'],'effective_to'))
    if a and b and a>b:
        errors.append('configuration effective interval is reversed')
    case_keys=set()
    for test in data['tests']:
        for field,collection in [('feed_id','feeds'),('list_id','lists'),('testset_id','testsets')]:
            identity=raw(test,field)
            if identity is not None and identity not in scopes[collection]:
                errors.append(test['test_id']+': '+field+' outside supplied review scope')
        testset=scopes['testsets'].get(raw(test,'testset_id'))
        if testset:
            ids=raw(testset,'case_ids')
            if ids is not None and raw(test,'case_id') is not None and raw(test,'case_id') not in ids:
                errors.append(test['test_id']+': case identity outside testset')
        identity=(raw(test,'testset_id'),raw(test,'case_id'))
        if all(identity):
            if identity in case_keys:
                errors.append('duplicate testset/case observation; separate runs need separate scoped case identities')
            case_keys.add(identity)
    pop=raw(review,'population_ids')
    for control in data['controls']:
        ids=raw(control,'population_ids')
        if ids is not None and pop is not None and not set(ids).issubset(pop):
            errors.append(control['control_id']+': control population outside review scope')
    return errors, []


def values(doc,row,schema,label,issues):
    output={}
    for key in schema:
        output[key],gaps=claim_value(doc,row[key],label+'.'+key)
        issues.extend(gaps)
    return output


def eligible_time(doc,value,start,end):
    at=instant(value)
    if at is None or start is None or end is None:
        return False
    return start<=at<=end and at.date()<=day(doc['knowledge_cutoff']) and at.date()<=day(doc['as_of'])


def observed_before_receipt(doc,claim,value):
    at=instant(value)
    if at is None:
        return False
    sources={source['source_ref']:source for source in doc['sources']}
    return all(at.date()<=day(sources[ref]['received_at']) for ref in claim['source_refs'] if ref in sources)


def compare_rate(count,denominator,limit):
    if not denominator or limit is None:
        return None
    return Fraction(count,denominator)<=Fraction(Decimal(limit))


def fraction_rate(count,denominator):
    return {'numerator':count,'denominator':denominator,
            'exact_fraction':str(count)+'/'+str(denominator) if denominator else None}


def compute(doc):
    require_valid(doc,validate)
    issues=[]
    data=doc['data']
    r=values(doc,data['review'],OBJECTS['review'],'review',issues)
    c=values(doc,data['configuration'],OBJECTS['configuration'],'configuration',issues)
    start,end=instant(r['window_from']),instant(r['window_to'])
    window_ok=start is not None and end is not None and end.date()<=min(day(doc['as_of']),day(doc['knowledge_cutoff']))
    if not window_ok:
        issues.append('Review window is unknown or exceeds assessment/knowledge cutoff')
    required=('regimes','population_ids','feed_ids','list_ids','testset_ids','control_ids',
              'required_fields','required_scripts','required_test_dimensions')
    for key in required:
        if not r[key]:
            issues.append('Review '+key+' is unknown or empty; coverage cannot be assumed')
    review_scope_known=all(r[key] for key in required) and all(r[key] is not None for key in ('mandate_owner','mandate_type','population_grain'))
    config_ok=all(v is not None for v in c.values())
    if config_ok:
        config_ok=window_ok and instant(c['effective_from'])<=start and end<=instant(c['effective_to'])
    fields_ok=None if r['required_fields'] is None or c['fields'] is None else set(r['required_fields']).issubset(c['fields'])
    scripts_ok=None if r['required_scripts'] is None or c['scripts'] is None else set(r['required_scripts']).issubset(c['scripts'])
    config_ok=config_ok and fields_ok is True and scripts_ok is True
    if not config_ok:
        issues.append('Configuration/vendor/matching/normalization/transliteration or effective coverage incomplete')
    feeds={}
    feed_rows=[]
    all_population=[]
    for row in data['feeds']:
        v=values(doc,row,COLLECTIONS['feeds'][1],row['feed_id'],issues)
        feeds[row['feed_id']]=v
        population,received,screened=v['population_ids'],v['received_ids'],v['screened_ids']
        missing_received=None if population is None or received is None else sorted(set(population)-set(received))
        missing_screened=None if received is None or screened is None else sorted(set(received)-set(screened))
        bypass=None if received is None or screened is None else sorted(set(screened)-set(received))
        f_ok=None if v['fields'] is None or r['required_fields'] is None else set(r['required_fields']).issubset(v['fields'])
        s_ok=None if v['scripts'] is None or r['required_scripts'] is None else set(r['required_scripts']).issubset(v['scripts'])
        scope_ok=instant(v['window_from'])==start and instant(v['window_to'])==end and window_ok
        complete=(scope_ok and all(x is not None for x in (population,received,screened))
                  and not missing_received and not missing_screened and not bypass and f_ok is True and s_ok is True)
        feeds[row['feed_id']]['review_evidence_consistent']=complete
        if population is not None:
            all_population+=population
        if not complete:
            issues.append(row['feed_id']+': feed/population/fields/scripts/window reconciliation incomplete')
        feed_rows.append({'feed_id':row['feed_id'],'evidence':v,'unreceived_population_ids':missing_received,
            'received_not_screened_ids':missing_screened,'screened_without_receipt_ids':bypass,
            'required_fields_covered':f_ok,'required_scripts_covered':s_ok,
            'supplied_feed_coverage_consistent':complete})
    population_ok=(r['population_grain']=='screening-input-record-id' and r['population_ids'] is not None and bool(r['population_ids']) and
                   len(all_population)==len(set(all_population)) and set(all_population)==set(r['population_ids']) and
                   bool(feeds) and all(v['review_evidence_consistent'] for v in feeds.values()))
    if not population_ok:
        issues.append('Declared population does not reconcile to complete supplied feed coverage')
    lists={}
    list_rows=[]
    list_requirement_evidence_complete=bool(data['lists'])
    all_list_lag_requirements_met=True
    for row in data['lists']:
        v=values(doc,row,COLLECTIONS['lists'][1],row['list_id'],issues)
        lists[row['list_id']]=v
        pub,eff,load=(instant(v[k]) for k in ('published_at','effective_at','loaded_at'))
        chronology=(pub is not None and eff is not None and load is not None and
                    pub<=load and eff<=load and load.date()<=min(day(doc['knowledge_cutoff']),day(doc['as_of'])) and
                    observed_before_receipt(doc,row['loaded_at'],v['loaded_at']))
        version=None if v['expected_version'] is None or v['loaded_version'] is None else v['expected_version']==v['loaded_version']
        expected,loaded=v['expected_entry_ids'],v['loaded_entry_ids']
        missing=None if expected is None or loaded is None else sorted(set(expected)-set(loaded))
        extras=None if expected is None or loaded is None else sorted(set(loaded)-set(expected))
        lag=seconds(eff,load) if chronology else None
        lag_ok=None if lag is None or r['maximum_list_update_lag_seconds'] is None else Fraction(Decimal(lag))<=Fraction(Decimal(r['maximum_list_update_lag_seconds']))
        regime_ok=None if v['regime'] is None or r['regimes'] is None else v['regime'] in r['regimes']
        complete=chronology and window_ok and load<=start and eff<=start and version is True and missing==[] and extras==[] and regime_ok is True
        lists[row['list_id']]['review_evidence_consistent']=complete
        if lag_ok is None:
            list_requirement_evidence_complete=False
            issues.append(row['list_id']+': list-update lag requirement evidence is unknown')
        if lag_ok is not True:
            all_list_lag_requirements_met=False
        if lag_ok is False:
            issues.append(row['list_id']+': known list-update lag exceeds the supplied requirement; eligible detection observations are retained')
        if not complete:
            issues.append(row['list_id']+': list version/entries/effective-load timing/regime reconciliation incomplete')
        list_rows.append({'list_id':row['list_id'],'evidence':v,'chronology_consistent':chronology,
            'version_consistent':version,'missing_loaded_entry_ids':missing,'extra_loaded_entry_ids':extras,
            'update_lag_seconds_exact':lag,'within_supplied_update_lag_limit':lag_ok,
            'supplied_list_coverage_consistent':complete})
    represented_regimes={v['regime'] for v in lists.values() if v['regime'] is not None}
    list_coverage_ok=bool(lists) and all(v['review_evidence_consistent'] for v in lists.values()) and bool(r['regimes']) and represented_regimes==set(r['regimes'] or [])
    if not list_coverage_ok:
        issues.append('Required regimes lack reconciled supplied lists; no current-list completeness inference')
    testsets={}
    for row in data['testsets']:
        testsets[row['testset_id']]=values(doc,row,COLLECTIONS['testsets'][1],row['testset_id'],issues)
    testset_raw={row['testset_id']:row for row in data['testsets']}
    counts={'true_positive':0,'false_positive':0,'true_negative':0,'false_negative':0}
    observations={'alert':0,'no-alert':0,'error':0,'unknown':0}
    unlabeled=0
    ineligible=0
    tests=[]
    measured_case_keys=set()
    covered_dimensions=set()
    all_latency_ok=True
    latency_coverage_complete=bool(data['tests'])
    for row in data['tests']:
        v=values(doc,row,COLLECTIONS['tests'][1],row['test_id'],issues)
        observed=v['observed_detection']
        observations[observed if observed in observations else 'unknown']+=1
        reasons=[]
        ts=testsets.get(v['testset_id'])
        feed=feeds.get(v['feed_id'])
        lst=lists.get(v['list_id'])
        tsraw=testset_raw.get(v['testset_id'])
        label_known=v['expected_detection'] in {'expected-alert','expected-no-alert'}
        if not label_known:
            unlabeled+=1
            reasons.append('Expected detection label unknown; observation cannot define its own label')
        if ts is None or not all(ts[k] is not None for k in COLLECTIONS['testsets'][1]):
            reasons.append('Testset/version/reference/scope/selection evidence incomplete')
        elif (ts['accepted_for_measurement'] is not True or ts['version']!=v['testset_version'] or
              v['case_id'] not in ts['case_ids'] or v['dimension'] not in ts['represented_dimensions']):
            reasons.append('Test label is outside supplied accepted testset/version/dimension scope')
        if ts and tsraw:
            label_sources=set(tsraw['label_reference']['source_refs'])|set(row['expected_detection']['source_refs'])
            engine_sources=set().union(*(set(row[key]['source_refs']) for key in ('observed_detection','observed_at','latency_seconds','evidence_complete','engine_id','engine_version','configuration_version','list_version')))
            if label_sources & engine_sources:
                reasons.append('Test label reference and engine observation must use distinct source records')
            if label_known and not set(row['expected_detection']['source_refs']).issubset(tsraw['label_reference']['source_refs']):
                reasons.append('Expected detection source is outside exact testset label reference')
            label_at=instant(ts['labels_as_of'])
            observed_at=instant(v['observed_at'])
            if label_at is None or observed_at is None or label_at>observed_at or label_at.date()>day(doc['knowledge_cutoff']):
                reasons.append('Label reference timing is unknown, future or post-observation')
        if not config_ok or any(v[key]!=c[key] for key in ('configuration_version','engine_id','engine_version')):
            reasons.append('Observed configuration differs or supplied configuration evidence is incomplete')
        if feed is None or not feed['review_evidence_consistent']:
            reasons.append('Feed context lacks reconciled supplied evidence')
        if lst is None or not lst['review_evidence_consistent'] or v['list_version']!=lst['loaded_version']:
            reasons.append('Observed list differs or lacks reconciled supplied evidence')
        elif instant(v['observed_at']) is None or instant(lst['loaded_at'])>instant(v['observed_at']) or instant(lst['effective_at'])>instant(v['observed_at']):
            reasons.append('List load/effective time follows observation')
        if (v['input_fields'] is None or c['fields'] is None or r['required_fields'] is None or
            not set(r['required_fields']).issubset(v['input_fields']) or not set(v['input_fields']).issubset(c['fields']) or
            feed is None or feed['fields'] is None or not set(v['input_fields']).issubset(feed['fields'])):
            reasons.append('Test input fields are missing or outside exact configured field coverage')
        if (v['input_script'] is None or c['scripts'] is None or v['input_script'] not in c['scripts'] or
            feed is None or feed['scripts'] is None or v['input_script'] not in feed['scripts']):
            reasons.append('Test script lacks supplied configuration/transliteration coverage')
        if not window_ok or not eligible_time(doc,v['observed_at'],start,end) or not observed_before_receipt(doc,row['observed_at'],v['observed_at']):
            reasons.append('Observation timing is unknown/outside review window/cutoff/source receipt')
        if v['evidence_complete'] is not True or observed not in {'alert','no-alert'}:
            reasons.append('Engine observation is incomplete, errored or unknown')
        latency_ok=None if v['latency_seconds'] is None or r['maximum_latency_seconds'] is None else Fraction(Decimal(v['latency_seconds']))<=Fraction(Decimal(r['maximum_latency_seconds']))
        if latency_ok is None:
            latency_coverage_complete=False
        if latency_ok is not True:
            all_latency_ok=False
            issues.append(row['test_id']+': observed latency is unknown or exceeds supplied requirement')
        classification=None
        if not reasons:
            classification={('expected-alert','alert'):'true_positive',('expected-alert','no-alert'):'false_negative',
                ('expected-no-alert','alert'):'false_positive',('expected-no-alert','no-alert'):'true_negative'}[(v['expected_detection'],observed)]
            counts[classification]+=1
            measured_case_keys.add((v['testset_id'],v['case_id']))
            covered_dimensions.add(v['dimension'])
        else:
            ineligible+=1
            issues.extend(row['test_id']+': '+reason for reason in reasons)
        tests.append({'test_id':row['test_id'],'evidence':v,'measured_sample_classification':classification,
            'within_supplied_latency_limit':latency_ok,'measurement_issues':reasons})
    unmeasured=[]
    for identity,ts in testsets.items():
        if ts['case_ids'] is None:
            unmeasured.append({'testset_id':identity,'case_id':None})
        else:
            unmeasured.extend({'testset_id':identity,'case_id':case} for case in ts['case_ids'] if (identity,case) not in measured_case_keys)
    missing_dimensions=None if r['required_test_dimensions'] is None else sorted(set(r['required_test_dimensions'])-covered_dimensions)
    test_coverage_ok=bool(testsets) and bool(tests) and not unmeasured and not ineligible and missing_dimensions==[]
    if not test_coverage_ok:
        issues.append('Known-test sample/dimension coverage incomplete; unmeasured cases do not become negatives or passes')
    positive=counts['true_positive']+counts['false_negative']
    negative=counts['true_negative']+counts['false_positive']
    fp_compare=compare_rate(counts['false_positive'],negative,r['maximum_false_positive_rate'])
    fn_compare=compare_rate(counts['false_negative'],positive,r['maximum_false_negative_rate'])
    if fp_compare is None or fn_compare is None:
        issues.append('Sample rate comparison withheld where supplied label denominator or criterion is unavailable')
    elif not fp_compare or not fn_compare:
        issues.append('Measured sample outcomes exceed supplied false-positive/false-negative criterion')
    control_counts={'pass':0,'fail':0,'unknown':0}
    controls=[]
    control_dimensions=set()
    for row in data['controls']:
        v=values(doc,row,COLLECTIONS['controls'][1],row['control_id'],issues)
        complete=(all(v[k] is not None for k in COLLECTIONS['controls'][1]) and v['evidence_complete'] is True and
            r['population_ids'] is not None and set(v['population_ids'])==set(r['population_ids']) and window_ok and eligible_time(doc,v['observed_at'],start,end) and
            observed_before_receipt(doc,row['observed_at'],v['observed_at']))
        state=v['outcome'] if complete and v['outcome'] in {'pass','fail'} else 'unknown'
        control_counts[state]+=1
        if state in {'pass','fail'}:
            control_dimensions.add(v['dimension'])
        if state!='pass':
            issues.append(row['control_id']+': supplied control observation '+state+'; owner follow-up required')
        controls.append({'control_id':row['control_id'],'evidence':v,'eligible_supplied_control_outcome':state})
    uncovered_controls=sorted(DIMENSIONS-control_dimensions)
    control_coverage_ok=bool(controls) and not uncovered_controls and not control_counts['unknown']
    if not control_coverage_ok:
        issues.append('Required control dimensions lack supported complete observations: '+', '.join(uncovered_controls))
    coverage=(review_scope_known and window_ok and population_ok and list_coverage_ok and config_ok and test_coverage_ok and control_coverage_ok and latency_coverage_complete and list_requirement_evidence_complete)
    within_criteria=(fp_compare and fn_compare and all_latency_ok and all_list_lag_requirements_met and control_counts['fail']==0) if coverage and fp_compare is not None and fn_compare is not None else None
    results={'review':r,'configuration':c,'population_feed_coverage_consistent':population_ok,
        'list_regime_coverage_consistent':list_coverage_ok,'configuration_coverage_consistent':config_ok,
        'feeds':feed_rows,'lists':list_rows,'tests':tests,'controls':controls,
        'supplied_engine_outcome_counts':observations,'measured_sample_counts':counts,
        'unlabeled_observation_count':unlabeled,'ineligible_measurement_count':ineligible,
        'unmeasured_testset_cases':unmeasured,'missing_test_dimensions':missing_dimensions,
        'known_test_coverage_complete':test_coverage_ok,'latency_evidence_complete':latency_coverage_complete,
        'false_positive_rate':fraction_rate(counts['false_positive'],negative),
        'false_negative_rate':fraction_rate(counts['false_negative'],positive),
        'within_supplied_false_positive_criterion':fp_compare,'within_supplied_false_negative_criterion':fn_compare,
        'supplied_control_outcomes':control_counts,'uncovered_control_dimensions':uncovered_controls,
        'supplied_control_coverage_complete':control_coverage_ok,'supplied_review_coverage_complete':coverage,
        'within_supplied_review_criteria':within_criteria,'operational_effectiveness':'not-established',
        'legal_exposure':'not-determined','match_identity_disposition':'not-determined',
        'independent_assurance':'not-issued','screening_engine_execution':'not-performed',
        'current_list_verification':'not-performed','statistical_population_inference':'not-performed'}
    return result(doc,SKILL,METHOD,results,issues,[
        'False-positive/false-negative counts concern only source-bound eligible test labels and observed outcomes; labels are supplied, scoped and unverified.',
        'Exact integer fractions and decimal-string criteria preserve precision; sample comparisons do not estimate population error rates.',
        'Coverage completeness, sample outcomes and supplied control findings do not establish operational effectiveness, legal exposure or independent assurance.',
        'No current sanctions list, default threshold, engine configuration, resilience requirement, label or sanctioned-person determination is inferred.',
        'Configuration, vendor, resilience and latency evidence is supplied review material; no engine execution or system mutation is implemented.'
    ],['sanctions-match-investigator','sanctions-exposure-reviewer','compliance-control-testing-assistant',
       'compliance-remediation-evidence-reviewer'])
