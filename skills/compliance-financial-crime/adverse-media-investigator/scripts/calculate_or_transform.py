"""Review supplied media records; no live search, identity decision, clearance or filing."""
from policy_contract import day, require_valid, limitations
from validate_input import validate
from native_integrity import attach_source

STANDING_NOTE='Adverse-media investigation is decision support only. No identity, sanctions or PEP status, customer outcome, case closure or filing is determined. Supplied sources remain unverified.'

def _norm(value):
    return ' '.join(str(value or '').casefold().split())

def _identity(subject,hit):
    name_ok=False; positive=[]; conflicts=[]
    for row in hit.get('match_evidence',[]):
        field=row.get('field'); source=row.get('source_value'); claimed=row.get('subject_value')
        if row.get('source_ref')!=hit['source_ref'] or not row.get('source_excerpt') or not source or not claimed: continue
        if field=='name': known=[subject['name']]+subject.get('aliases',[])
        elif field=='identifier': known=subject.get('known_identifiers',[])
        elif field=='dob': known=[subject.get('dob')]
        else: continue
        if _norm(claimed) not in {_norm(x) for x in known if x}: continue
        matches=_norm(source)==_norm(claimed)
        if field=='name': name_ok=matches
        elif matches: positive.append(field)
        else: conflicts.append(field)
    if conflicts:
        if positive or hit['source_tier']==3: return 'unresolved','Conflicting or low-reliability identity evidence; human disambiguation required.'
        return 'namesake-discarded','Supplied reliable-source identifier comparison conflicts with the subject; human confirmation remains required.'
    if name_ok and positive: return 'strong','Supplied name and DOB/identifier values agree; source truth remains unverified.'
    return 'unresolved','Name similarity or subject identifiers without source-side corroboration do not establish attribution.'

def _coverage(subject,asof,cfg):
    c=subject.get('search_coverage',{}); observed=day(c.get('as_of'))
    complete=bool(c.get('status')=='complete' and observed and 0<=(asof-observed).days<=cfg['coverage_max_age_days']
                  and c.get('source_ref') and c.get('sources') and c.get('queries') and c.get('languages'))
    return {'status':'documented-supplied-scope' if complete else 'incomplete','details':c},complete

def _score(hit,asof,cfg):
    if hit['assertion_type']=='resolved-dismissed': return 0
    age=(asof-day(hit['published_date'])).days; rec=cfg['recency']
    recency=rec['within_2y'] if age<=rec['within_2y_days'] else rec['within_5y'] if age<=rec['within_5y_days'] else rec['older']
    return cfg['category_weight'][hit['category']]+cfg['assertion_addend'][hit['assertion_type']]+cfg['source_tier_addend'][str(hit['source_tier'])]+recency

def investigate_subject(subject,doc,cfg):
    asof=day(doc['as_of_date']); coverage,complete=_coverage(subject,asof,cfg)
    matched=[]; discarded=[]; unresolved=[]; chronology=[]; routes=[]; citations=set(); needs=[]
    hits=subject.get('hits',[]); byid={h['hit_id']:h for h in hits}; identities={h['hit_id']:_identity(subject,h) for h in hits}
    superseded={}
    for h in hits:
        pub=day(h.get('published_date')); event=day(h.get('event_date'))
        if h['assertion_type']!='resolved-dismissed' or h['source_tier'] not in (1,2) or identities[h['hit_id']][0]!='strong' or not pub or pub>asof or not event or event>pub: continue
        for hid in h.get('supersedes_hit_ids',[]):
            prior=byid[hid]; prior_event=day(prior.get('event_date'))
            if h.get('matter_id') and h.get('matter_id')==prior.get('matter_id') and prior_event and prior_event<=event:
                superseded[hid]=h['hit_id']
    for h in hits:
        tier,basis=identities[h['hit_id']]; pub=day(h.get('published_date')); event=day(h.get('event_date'))
        citation=h['source_ref']; citations.add(citation)
        item={'hit_id':h['hit_id'],'source':h['source'],'source_tier':h['source_tier'],'citation':citation,'headline':h['headline'],
              'category':h['category'],'assertion_type':h['assertion_type'],'list_type':h.get('list_type'),'match_tier':tier,'match_basis':basis,
              'published_date':h.get('published_date'),'event_date':h.get('event_date'),'matter_id':h.get('matter_id'),'source_excerpt':h['excerpt'],
              'evidence_status':'supplied-unverified','relevance':None,'superseded_by':superseded.get(h['hit_id'])}
        chronology.append({'hit_id':h['hit_id'],'event_date':h.get('event_date'),'publication_date':h.get('published_date'),
                           'event':h['headline'],'assertion_type':h['assertion_type'],'citation':citation,'superseded_by':superseded.get(h['hit_id'])})
        if h.get('list_type')=='sanctions' and tier!='namesake-discarded': routes.append('sanctions-match-investigator')
        if h.get('list_type')=='pep' and tier!='namesake-discarded': routes.append('customer-due-diligence-reviewer')
        if tier=='namesake-discarded': discarded.append(item); continue
        dated=bool(pub and event and event<=pub<=asof)
        if tier=='unresolved' or not dated or h['source_tier']==3:
            item['unresolved_reason']='; '.join(x for x in [basis if tier=='unresolved' else '', 'Missing/invalid/future publication or event date.' if not dated else '', 'Low-reliability source requires independent corroboration; not scored as material.' if h['source_tier']==3 else ''] if x)
            unresolved.append(item); continue
        item['relevance']=0 if h['hit_id'] in superseded else _score(h,asof,cfg)
        matched.append(item)
    score=max((h['relevance'] for h in matched),default=0)
    if unresolved: needs.append('Resolve source-side identity, chronology or independent corroboration gaps before attributing these records.')
    if not complete: needs.append('Supply current search scope, sources, queries, languages and coverage evidence.')
    positive='Material' if score>=cfg['material_min'] else 'Watch' if score>=cfg['watch_min'] else None
    band=positive or ('Unknown' if needs else 'Not material')
    if 'sanctions-match-investigator' in routes:
        disposition='recommend-route-sanctions'; route='sanctions-match-investigator'
    elif 'customer-due-diligence-reviewer' in routes:
        disposition='recommend-route-pep-cdd'; route='customer-due-diligence-reviewer'
    elif positive=='Material': disposition='recommend-escalate-edd'; route='enhanced-due-diligence-assessor'
    elif needs: disposition='needs-data'; route=None
    elif positive=='Watch': disposition='recommend-monitor'; route=None
    else: disposition='recommend-no-material-adverse-media'; route=None
    reason='Scoped recommendation from supplied records. Search incompleteness and unresolved hits remain open; no clearance or identity determination is made.'
    if coverage['details'].get('source_ref'): citations.add(coverage['details']['source_ref'])
    cid=subject.get('case_id') or 'AMI-'+subject['subject_id']
    bundle={'case_id':cid,'subject':{'subject_id':subject['subject_id'],'name':subject['name'],'type':subject['type']},
            'chronology':sorted(chronology,key=lambda r:str(r['event_date'] or '')),'matched_hits':matched,'discarded_namesakes':discarded,
            'unresolved_hits':unresolved,'citations':sorted(citations),'search_coverage':coverage}
    return {'subject_id':subject['subject_id'],'case_id':cid,'materiality_score':score if band!='Unknown' else None,'materiality_band':band,
            'disposition':disposition,'disposition_reason':reason,'needs':needs,'route_specialist':route,'routes':sorted(set(routes)),
            'matched_hits':matched,'discarded_namesakes':discarded,'unresolved_hits':unresolved,'search_coverage':coverage,'evidence_bundle':bundle}

def investigate(doc):
    require_valid(doc,validate)
    cases=[investigate_subject(s,doc,doc['scoring_config']) for s in doc['subjects']]
    dispositions={c['disposition'] for c in cases}
    return attach_source({'config_version':doc['config_version'],'as_of_date':doc['as_of_date'],'case_batch_id':doc.get('case_batch_id'),
        'cases':cases,'summary':{'total':len(cases),'by_disposition':{d:sum(c['disposition']==d for c in cases) for d in sorted(dispositions)}},
        'limitations':limitations()+['Supplied record review only; no live negative-news search, automated source authentication, alias/transliteration inference or legal culpability determination. Category labels describe reported allegations/findings, not proven crimes.'],
        'standing_note':STANDING_NOTE},doc)

compute=investigate

def main(argv):
    import json,sys
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'evals/files/screening_batch_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
    try:
        print(json.dumps(investigate(json.loads(p.read_text() if p else sys.stdin.read())),indent=2,allow_nan=False))
        return 0
    except (ValueError,TypeError,KeyError,AttributeError) as exc:
        print('ERROR',exc,file=sys.stderr); return 1

if __name__=='__main__':
    import sys
    raise SystemExit(main(sys.argv[1:]))
