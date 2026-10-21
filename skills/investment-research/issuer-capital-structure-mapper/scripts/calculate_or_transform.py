#!/usr/bin/env python3
"""Source-bound, currency-separated supplied debt inventory; no refinancing assessment."""
import importlib.util, json, sys
from collections import defaultdict
import calendar
from datetime import date
from pathlib import Path
from native_integrity import attach_source, canonical_hash
DISCLAIMER='Descriptive capital-structure map only; not financing advice, a recommendation, or a view on the optimal structure. No transaction is suggested.'

def _check(doc):
    spec=importlib.util.spec_from_file_location('_mapper_input',Path(__file__).with_name('validate_input.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    errors,_=m.validate(doc)
    if errors: raise ValueError('; '.join(errors))

def _group(rows,as_of):
    sums={k:defaultdict(float) for k in ('by_seniority','by_type','secured_unsecured','maturity_wall')}
    horizon=as_of.replace(year=as_of.year+2,day=min(as_of.day,calendar.monthrange(as_of.year+2,as_of.month)[1]))
    known=0.;wam_num=wac_num=dated=couponed=near=0.;gaps=[]
    for it in rows:
        ident=it['instrument_id'];p=it.get('principal')
        if p is None: gaps.append(ident+': principal unknown');continue
        known+=p
        sums['by_seniority'][it.get('seniority') or 'unknown']+=p
        sums['by_type'][it.get('type') or 'unknown']+=p
        sums['secured_unsecured']['unknown' if it.get('secured') is None else 'secured' if it['secured'] else 'unsecured']+=p
        c=it.get('coupon_pct')
        if c is None:gaps.append(ident+': coupon unknown')
        else:wac_num+=p*c;couponed+=p
        md=it.get('maturity_date')
        if md is None:sums['maturity_wall']['undated']+=p;gaps.append(ident+': maturity unknown');continue
        due=date.fromisoformat(md);sums['maturity_wall'][str(due.year)]+=p;dated+=p;wam_num+=p*(due-as_of).days/365.25
        if as_of<=due<=horizon:near+=p
    principal_complete=all(r.get('principal') is not None for r in rows)
    maturity_complete=principal_complete and all(r.get('maturity_date') is not None for r in rows)
    coupon_complete=principal_complete and all(r.get('coupon_pct') is not None for r in rows)
    return {'total_debt':round(known,2) if principal_complete else None,'known_principal':round(known,2),
            **{k:{x:round(v,2) for x,v in sorted(d.items())} for k,d in sums.items()},
            'wam_years':round(wam_num/known,2) if maturity_complete and known else None,
            'wac_pct':round(wac_num/known,4) if coupon_complete and known else None,
            'known_maturity_wam_years':round(wam_num/dated,2) if dated else None,
            'known_coupon_wac_pct':round(wac_num/couponed,4) if couponed else None,
            'near_term_24m':round(near,2) if maturity_complete else None,'known_near_term_24m':round(near,2),
            'coverage':{'principal_complete':principal_complete,'maturity_complete':maturity_complete,'coupon_complete':coupon_complete},'unresolved_issues':gaps}

def compute(doc):
    if isinstance(doc,dict) and doc.get('schema_version')=='ir-phase2/1.0':
        from phase2_domain import compute as phase2_compute
        return phase2_compute(doc)
    canonical_hash(doc);_check(doc);co=doc['company'];rows=doc['instruments'];groups={}
    for currency in sorted({r['currency'] for r in rows}):groups[currency]=_group([r for r in rows if r['currency']==currency],date.fromisoformat(co['as_of']))
    single=next(iter(groups.values())) if len(groups)==1 else None
    detail=[{key:r.get(key) for key in ('instrument_id','issuer_id','type','seniority','principal','currency','coupon_pct','maturity_date','secured','source_ref')} for r in rows]
    output={'map_id':'csmm-'+co['company_id']+'-'+canonical_hash(doc)[:12],'company_id':co['company_id'],'as_of':co['as_of'],
            'currency':next(iter(groups)) if single else None,'by_currency':groups,'instruments':detail,
            **(single if single else {'total_debt':None,'wam_years':None,'wac_pct':None,'near_term_24m':None,'by_seniority':{},'by_type':{},'secured_unsecured':{},'maturity_wall':{},'unresolved_issues':['mixed currencies: inspect by_currency; no cross-currency aggregate']}),
            'excluded_instruments':[{'instrument_id':r['instrument_id'],'reason':'principal unknown'} for r in rows if r.get('principal') is None],
            'disclaimer':DISCLAIMER,'authority':'supplied source and role assertions are unverified; no action authority'}
    canonical_hash(output)
    return attach_source(output,doc)

def main(argv):
    path=Path(__file__).resolve().parents[1]/'evals/files/debt_example.json' if '--selftest' in argv else (Path(argv[0]) if argv else None)
    try:print(json.dumps(compute(_read_json(path.read_text() if path else sys.stdin.read())),indent=2));return 0
    except (ValueError,TypeError,KeyError,ArithmeticError) as exc:print('ERROR',exc);return 1
def _read_json(raw, **options):
    """Reject duplicate object keys and nonfinite constants before binding."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON object key: '+key)
            result[key]=value
        return result
    def constant(value): raise ValueError('non-finite JSON constant: '+value)
    options.setdefault('object_pairs_hook',pairs)
    options.setdefault('parse_constant',constant)
    return json.loads(raw,**options)


_phase2_json_main = main

def main(*args, **kwargs):
    try: return _phase2_json_main(*args, **kwargs)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print('ERROR:', str(exc), file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
