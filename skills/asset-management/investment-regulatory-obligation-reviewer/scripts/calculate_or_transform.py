"""Bounded supplied-input review. No source authentication or business action."""
from decimal import Decimal
from foundation_contract import (D,ratio,date_value,exact,validate_common,validate_referenced_sources,finish,cli_compute)
from native_integrity import canonical_hash

@exact
def analyze(d):
    facts=d['entity_facts'];rules=d['rules'];rows=[];issues=[];today=date_value(d['as_of']);ids=set()
    if not rules:raise ValueError('explicit reviewed rule scope required')
    for r in rules:
        if r['rule_id'] in ids:raise ValueError('duplicate rule id')
        ids.add(r['rule_id']);effective=date_value(r['effective_from']);end=date_value(r['effective_to']) if r.get('effective_to') else None
        if end and end<effective:raise ValueError('inverted effective interval')
        if r['status'] not in {'final','proposed','withdrawn','superseded'}:raise ValueError('rule lifecycle status unsupported')
        if not r.get('version') or not r.get('reviewer') or r.get('review_status')!='reviewed':state='undetermined';reason='rule-pack review evidence missing'
        elif r['status']!='final':state='not-binding';reason='rule is '+r['status']
        elif today<effective or end and today>end:state='not-effective';reason='outside supplied effective interval'
        elif r['jurisdiction'] not in d['jurisdictions']:state='not-applicable';reason='jurisdiction differs'
        else:
            checks=[];missing=[]
            for pred in r['predicates']:
                key=pred['fact'];op=pred['operator']
                if op not in {'eq','in','gte','lt'}:raise ValueError('unsupported applicability operator')
                if key not in facts or facts[key] is None:missing.append(key);continue
                value=facts[key];expected=pred['value']
                if op=='eq':checks.append(type(value)==type(expected) and value==expected)
                elif op=='in':
                    if not isinstance(expected,list):raise ValueError('in operator requires list')
                    checks.append(any(type(value)==type(x) and value==x for x in expected))
                else:checks.append(D(value)>=D(expected) if op=='gte' else D(value)<D(expected))
            if not r['predicates']:state='undetermined';reason='no applicability predicate supplied'
            elif False in checks:state='not-applicable';reason='supplied predicate not met'
            elif missing:state='undetermined';reason='missing facts: '+', '.join(missing)
            else:state='applicable-under-supplied-rule';reason='all supplied predicates met'
        completed=r.get('completion_status')=='completed'
        applicable=state=='applicable-under-supplied-rule'
        # A caller's completed flag is not evidence that an obligation was discharged.
        due=r.get('due_date');overdue=bool(due and date_value(due)<today and applicable)
        if applicable and not r.get('owner'):issues.append(r['rule_id']+': accountable obligation owner missing')
        if applicable and completed:issues.append(r['rule_id']+': completion is supplied-unverified; confirm evidence and discharge with accountable reviewer')
        if state=='undetermined' or overdue:issues.append(r['rule_id']+': '+('overdue supplied obligation' if overdue else reason))
        rows.append({'rule_id':r['rule_id'],'version':r.get('version'),'state':state,'reason':reason,'due_date':due,'overdue':overdue,'owner':r.get('owner'),'source_ref':r['source_ref'],'completion_evidence_state':'supplied-unverified' if completed else 'not-confirmed'})
    return {'obligations':rows,'legal_conclusion':None,'rule_coverage':'only explicitly supplied reviewed rules'},issues

SKILL='investment-regulatory-obligation-reviewer'
METHOD='supplied-rule-applicability'
LIMITS=['Synthetic eval thresholds are not law; deploy only reviewed current primary rule packs.', 'No universal legal interpretation, regulatory filing or compliance certification.']
HANDOFFS=['regulatory-change-impact-analyzer', 'investment-disclosure-reviewer']

def validate(doc):
    if isinstance(doc, dict) and 'extension' in doc:
        from jurisdiction_profile import validate as validate_extension
        return validate_extension(doc)
    errors=validate_common(doc)
    if errors:return errors
    errors+=validate_referenced_sources(doc)
    if doc.get('requested_action','review') not in ('review','draft'):errors.append('business execution unsupported')
    if errors:return errors
    try:analyze(doc)
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError) as exc:errors.append(str(exc))
    return errors

def compute(doc):
    if isinstance(doc, dict) and 'extension' in doc:
        from jurisdiction_profile import compute as compute_extension
        return compute_extension(doc)
    errors=validate(doc)
    if errors:raise ValueError('; '.join(errors))
    results,issues=analyze(doc)
    return finish(doc,SKILL,METHOD,results,issues=issues,limitations=LIMITS,handoffs=HANDOFFS)

if __name__=='__main__':cli_compute(compute)
