"""Canonical portable investment foundations, v1.0 (MIT).

Validation binds supplied content; it does not authenticate it or approve a decision.
Domain calculators own their financial methods. Keep originals detached.
"""
from __future__ import annotations
import argparse
import copy
from datetime import date
from decimal import Context, Decimal, Inexact, InvalidOperation, Rounded, localcontext
from functools import wraps
import json
from pathlib import Path
import re
import sys
from native_integrity import attach_source, canonical_hash, validate_reconstruction

VERSION='investment-foundation/1.0'

def text(value):return isinstance(value,str) and bool(value.strip())

def date_value(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValueError('real YYYY-MM-DD date required')
    return date.fromisoformat(value)

def D(value):
    if isinstance(value,bool) or value is None or not isinstance(value,(str,int,float,Decimal)):
        raise ValueError('finite decimal value required; missing is not zero')
    literal=str(value)
    if len(literal)>256:raise ValueError('numeric literal exceeds256 characters')
    try: number=Decimal(literal)
    except InvalidOperation:raise ValueError('finite decimal value required') from None
    if not number.is_finite():raise ValueError('non-finite decimal')
    if len(number.as_tuple().digits)>38 or abs(number.as_tuple().exponent)>38 or abs(number.adjusted())>38:
        raise ValueError('decimal exceeds supported38-digit / exponent+/-38 domain')
    return number

def exact(function):
    @wraps(function)
    def run(*args,**kwargs):
        with localcontext(Context(prec=256)) as context:
            context.traps[Inexact]=True;context.traps[Rounded]=True
            return function(*args,**kwargs)
    return run

def ratio(numerator,denominator,places=12):
    """Explicit rounded analytical ratio; sums and cash arithmetic remain exact."""
    if denominator==0:return None
    with localcontext(Context(prec=256)):
        return format((numerator/denominator).quantize(Decimal(1).scaleb(-places)),'f')

def validate_common(doc):
    if not isinstance(doc,dict):return ['input must be an object']
    errors=[]
    nodes=0
    def bounded(value,depth=0):
        nonlocal nodes
        nodes+=1
        if depth>50 or nodes>1000000:raise ValueError('input exceeds supported nesting/aggregate size')
        if isinstance(value,list):
            if len(value)>100000:raise ValueError('collection exceeds100000 records')
            for child in value:bounded(child,depth+1)
        elif isinstance(value,dict):
            for child in value.values():bounded(child,depth+1)
    try:bounded(doc)
    except ValueError as exc:return [str(exc)]
    try:canonical_hash(doc)
    except (ValueError,TypeError) as exc:return [str(exc)]
    for key in ('request_id','object_id','currency'):
        if not text(doc.get(key)):errors.append(key+' required')
    if not re.fullmatch(r'[A-Z]{3}|not-applicable',str(doc.get('currency',''))):errors.append('currency must be ISO-style3-letter code or not-applicable')
    if doc.get('audience')!='internal-review':errors.append('native foundation output is internal-review only')
    for key in ('as_of','knowledge_cutoff'):
        try:date_value(doc.get(key))
        except (ValueError,TypeError):errors.append(key+' must be a real date')
    sources=doc.get('sources')
    if not isinstance(sources,list) or not sources or len(sources)>100000:return errors+['nonempty bounded sources list required']
    seen=set()
    for i,source in enumerate(sources):
        if not isinstance(source,dict):errors.append(f'sources[{i}] must be an object');continue
        for field in ('source_ref','version'):
            if not text(source.get(field)):errors.append(f'sources[{i}].{field} required')
        ref=source.get('source_ref')
        if isinstance(ref,str):
            if ref in seen:errors.append('duplicate source_ref: '+ref)
            seen.add(ref)
        for field in ('as_of','known_at'):
            try:date_value(source.get(field))
            except (ValueError,TypeError):errors.append(f'sources[{i}].{field} must be a date')
        try:
            if date_value(source.get('known_at'))>date_value(doc.get('knowledge_cutoff')):errors.append('source known after knowledge cutoff: '+str(ref))
        except (ValueError,TypeError):pass
        for field in ('valid_from','valid_to','expires_at'):
            if field in source:
                try:date_value(source[field])
                except (ValueError,TypeError):errors.append('invalid source '+field)
    for key in ('unresolved_issues',):
        if key in doc and (not isinstance(doc[key],list) or not all(text(v) for v in doc[key])):errors.append(key+' must be strings')
    return errors

def source_issues(doc,ref,require_approved=False):
    if not text(ref):return ['source reference missing']
    source=next((r for r in doc.get('sources',[]) if isinstance(r,dict) and r.get('source_ref')==ref),None)
    if source is None:return ['source not registered: '+ref]
    audiences=source.get('permitted_audiences')
    if audiences is not None and (not isinstance(audiences,list) or doc['audience'] not in audiences):
        return ['source withheld for audience restriction']
    errors=[]
    try:
        when=date_value(doc['as_of'])
        if date_value(source['known_at'])>date_value(doc['knowledge_cutoff']):errors.append('source not known at cutoff: '+ref)
        if 'valid_from' in source and date_value(source['valid_from'])>when:errors.append('source not yet effective: '+ref)
        for key in ('valid_to','expires_at'):
            if key in source and date_value(source[key])<when:errors.append('source stale/expired: '+ref)
    except (ValueError,KeyError,TypeError):errors.append('source date invalid: '+ref)
    if require_approved and source.get('approval_status')!='approved':errors.append('source approval not supplied: '+ref)
    return errors

def validate_referenced_sources(doc,allow_future=False):
    """Validate declared row provenance; no authentication or semantic inference."""
    errors=[]
    def visit(value,path=''):
        if isinstance(value,dict):
            for key,item in value.items():
                if not path and key=='sources':continue
                if key=='source_ref' or key.endswith('_source_ref'):
                    errors.extend(source_issues(doc,item))
                    source=next((s for s in doc.get('sources',[]) if isinstance(s,dict) and s.get('source_ref')==item),None)
                    if source and not allow_future:
                        try:
                            if date_value(source['as_of'])>date_value(doc['as_of']):errors.append('observation source as-of exceeds review date')
                        except (ValueError,KeyError,TypeError):errors.append('invalid observation date')
                else:visit(item,path+'/'+key)
        elif isinstance(value,list):
            for item in value:visit(item,path+'/*')
    visit(doc)
    return list(dict.fromkeys(errors))

def require_sources(doc, references, *, require_approved=False):
    """Require explicit links for domain-owned facts; a registry alone is not provenance."""
    for ref in references:
        if not text(ref):raise ValueError('required observation source reference missing')
        errors=source_issues(doc,ref,require_approved=require_approved)
        if errors:raise ValueError('; '.join(errors))
        source=next(s for s in doc['sources'] if s['source_ref']==ref)
        if date_value(source['as_of'])>date_value(doc['as_of']):
            raise ValueError('observation source as-of exceeds review date')


def validate_actual_date(doc, value, source_ref):
    """Validate an actual observed event, never a forecast/contractual future date.

    Call after domain eligibility checks when unsupported evidence is withheld.
    This validates chronology of supplied declarations, not historical source truth.
    """
    observed=date_value(value)
    require_sources(doc,[source_ref])
    source=next(s for s in doc['sources'] if s['source_ref']==source_ref)
    if observed>min(date_value(doc['as_of']),date_value(doc['knowledge_cutoff']),date_value(source['known_at'])):
        raise ValueError('actual observation date exceeds review, knowledge cutoff or source known-at date')
    return observed


def finish(doc,skill,method,results,issues=(),limitations=(),handoffs=()):
    errors=validate_common(doc)
    if errors:raise ValueError('; '.join(errors))
    retained=list(dict.fromkeys(list(doc.get('unresolved_issues',[]))+list(issues)))
    if not all(text(v) for v in retained):raise ValueError('unresolved issues must be nonempty strings')
    output={'contract_version':VERSION,'skill':skill,'request_id':doc['request_id'],'object_id':doc['object_id'],
            'as_of':doc['as_of'],'knowledge_cutoff':doc['knowledge_cutoff'],'currency':doc['currency'],
            'audience':'internal-review','status':'needs-review' if retained else 'draft','draft':True,
            'action_taken':False,'human_review_required':True,'delivery_status':'not-delivered',
            'method':{'id':method,'version':'1.0','origin':'local-analysis'},'results':results,
            'unresolved_issues':retained,'limitations':list(limitations),'handoffs':list(handoffs),
            'source_assurance':'supplied-unverified','source_refs':[s['source_ref'] for s in doc['sources']
                if s.get('permitted_audiences') is None or isinstance(s['permitted_audiences'],list) and doc['audience'] in s['permitted_audiences']]}
    return attach_source(output,doc)

def validate_result(output,original,compute):
    errors=[]
    if original is not None:errors.extend(validate_common(original))
    validate_reconstruction(output,compute,errors,original_input=original)
    return errors

def _read(path):return json.loads(Path(path).read_text() if path else sys.stdin.read())

def cli_compute(compute):
    parser=argparse.ArgumentParser();parser.add_argument('input',nargs='?');args=parser.parse_args()
    try:print(json.dumps(compute(_read(args.input)),indent=2,allow_nan=False))
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError,OSError) as exc:parser.exit(1,str(exc)+'\n')

def cli_input(validate):
    parser=argparse.ArgumentParser();parser.add_argument('input',nargs='?');args=parser.parse_args()
    try:
        result=validate(_read(args.input));errors=result[0] if isinstance(result,tuple) else result
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError,OSError) as exc:errors=[str(exc)]
    print(json.dumps({'errors':errors}));raise SystemExit(bool(errors))

def cli_output(validate):
    parser=argparse.ArgumentParser();parser.add_argument('output',nargs='?');parser.add_argument('--input',required=True);args=parser.parse_args()
    try:
        result=validate(_read(args.output),_read(args.input));errors=result[0] if isinstance(result,tuple) else result
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError,OSError) as exc:errors=[str(exc)]
    print(json.dumps({'errors':errors}));raise SystemExit(bool(errors))
