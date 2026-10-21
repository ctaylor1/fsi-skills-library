#!/usr/bin/env python3
"""Decimal component control review; does not prepare or certify NAV."""
import json,sys
from decimal import Context,Decimal,Inexact,InvalidOperation,Rounded,localcontext
from datetime import date
from pathlib import Path
from native_integrity import attach_source,canonical_hash
COMPONENTS=('position','price','cash','accrual','income','expense','shares')
DEFAULT_SOURCES={'position':'custodian','price':'pricing','cash':'custodian','accrual':'administrator','income':'administrator','expense':'administrator','shares':'administrator'}
DEFAULT_TOLERANCES={'position':'0.0001','price':'0.000001','cash':'0.01','accrual':'0.01','income':'0.01','expense':'0.01','shares':'0.0001'}
COMPONENT_BREAK={'position':'quantity_break','price':'price_break','cash':'cash_break','accrual':'accrual_break','income':'income_break','expense':'expense_break','shares':'shares_break'}
PRICE_ROUTE='fund-valuation-oversight-reviewer'
DISCLAIMER=('Tie-out and break packet only; NAV has not been struck, no price has been selected, and no accounting entry has been posted. All resolutions are PROPOSED and require fund-accountant review and authorized action in the systems of record.')

def num(v):
    if v is None or isinstance(v,bool):raise ValueError('known numeric value required')
    literal=str(v).strip()
    if len(literal)>256:raise ValueError('numeric literal exceeds 256 characters')
    try:n=Decimal(literal)
    except InvalidOperation as exc:raise ValueError('invalid numeric value') from exc
    if not n.is_finite():raise ValueError('finite numeric value required')
    parts=n.as_tuple()
    if len(parts.digits)>38 or not -38<=parts.exponent<=38 or (n and not -38<=n.adjusted()<=38):
        raise ValueError('numeric value exceeds supported precision/magnitude: 38 coefficient digits, exponent and adjusted exponent -38..38')
    return n

def _compute(doc):
    cutoff=date.fromisoformat(doc['as_of'][:10]);cfg=doc.get('config') or {}
    sources={**DEFAULT_SOURCES,**cfg.get('component_sources',{})};tolerances={**DEFAULT_TOLERANCES,**cfg.get('tolerances',{})}
    buckets={};gaps=[];seen=set()
    expected=doc.get('expected_components')
    if not isinstance(expected,list) or not expected or not set(expected)<=set(COMPONENTS):
        raise ValueError('explicit expected_components subset required')
    for row in doc.get('lines',[]):
        if row['line_id'] in seen:raise ValueError('duplicate line_id')
        seen.add(row['line_id']);comp=row['component'];why=[]
        if comp not in expected:why.append('component outside declared review universe')
        if row['source'] not in {'book',sources.get(comp)}:why.append('unconfigured verifier source')
        try:
            if date.fromisoformat(str(row.get('as_of'))[:10])!=cutoff:why.append('observation does not match requested valuation date')
        except (ValueError,TypeError):why.append('missing or invalid observation date')
        if not row.get('currency'):why.append('currency unknown')
        unit=row.get('unit');basis=row.get('position_basis') or doc.get('position_basis');sclass=row.get('share_class') or doc.get('share_class')
        if not unit:why.append('measurement unit unknown')
        if comp=='position' and not basis:why.append('position basis unknown')
        if comp=='shares' and not sclass:why.append('share class unknown')
        num(row['value'])
        if why:gaps.append({'line_id':row['line_id'],'component':comp,'source_ref':row.get('source_ref'),'reasons':why});continue
        key=(comp,str(row['key']),row['currency'].upper(),unit,sclass if comp=='shares' else None,basis if comp=='position' else None)
        buckets.setdefault(key,{'book':[],'verifier':[]})['book' if row['source']=='book' else 'verifier'].append(row)
    for comp in expected:
        if not any(k[0]==comp for k in buckets):gaps.append({'component':comp,'reasons':['no comparable observations for expected component']})
    controls=[];breaks=[];matched=0;reviewed=set()
    for key,sides in sorted(buckets.items(),key=lambda kv:str(kv[0])):
        comp,identifier,currency,unit,sclass,basis=key;bl=sides['book'];vl=sides['verifier']
        if len(bl)>1 or len(vl)>1:
            gaps.append({'component':comp,'key':identifier,'reasons':['multiple rows at declared grain require upstream consolidation'],'line_ids':[r['line_id'] for r in bl+vl]});continue
        bv=num(bl[0]['value']) if bl else Decimal(0);vv=num(vl[0]['value']) if vl else Decimal(0);diff=bv-vv
        tol=num(tolerances[comp])
        if tol<0:raise ValueError('negative tolerance')
        within=bool(bl and vl) and abs(diff)<=tol
        impact=Decimal(0) if within else diff
        tolerated=diff if within else Decimal(0)
        lineage=[f"{r['source']}:{r.get('source_ref')}@{r.get('as_of')}" for r in bl+vl]
        controls.append({'component':comp,'key':identifier,'currency':currency,'unit':unit,'share_class':sclass,'position_basis':basis,
                         'book_total':str(bv),'verifier_total':str(vv),'difference':str(diff),'breaks_impact_sum':str(impact),
                         'within_tolerance_difference':str(tolerated),'residual':str(diff-impact-tolerated),'ties_out':True,'lineage':lineage})
        reviewed.add(comp)
        if within:matched+=1;continue
        bid=f'BRK-{len(breaks)+1:04d}';btype=COMPONENT_BREAK[comp] if bl and vl else 'missing_record'
        resolution={'resolution_id':f'PRS-{len(breaks)+1:04d}','break_id':bid,'status':'PROPOSED',
                    'disposition':'route_to_valuation_exception_packet' if comp=='price' else 'investigate_both_sources',
                    'route_to':PRICE_ROUTE if comp=='price' else None,'chooses_value':False,'strikes_nav':False,'posts_entry':False,
                    'recommended_action':'Review both source records and identify the supported cause before selecting any accounting correction.'}
        threshold=num(cfg.get('materiality',{}).get(comp,cfg.get('materiality',{}).get('default','100')))
        breaks.append({'break_id':bid,'type':btype,'component':comp,'key':identifier,'currency':currency,'unit':unit,
                       'share_class':sclass,'impact':str(diff),'material':abs(diff)>=threshold,'lineage':lineage,
                       'requires_resolution':True,'proposed_resolution':resolution})
    fp=canonical_hash(doc);out={'tie_out_id':f"npt-{doc['fund']}-{doc.get('share_class') or 'NA'}-{doc['as_of']}-{fp[:8]}",
        'fund':doc['fund'],'share_class':doc.get('share_class'),'as_of':doc['as_of'],'base_currency':doc['base_currency'],
        'config_version':doc['config_version'],'input_fingerprint':fp,'not_evaluable':gaps,
        'effective_config':{'component_sources':sources,'tolerances':tolerances},
        'tie_out':{'control_totals':controls,'residual':'0' if not gaps else None,'out_of_tolerance_count':len(breaks),'captured_break_count':len(breaks),
                   'components_reconciled':sorted(reviewed),'expected_components':expected,'all_control_totals_tie':True,'ties_out':not gaps,
                   'status':'needs_data' if gaps else 'reconciled_with_breaks' if breaks else 'clean_tie_out'},
        'matched_count':matched,'breaks':breaks,'proposed_resolutions':[b['proposed_resolution'] for b in breaks],
        'summary':{'total_breaks':len(breaks),'by_type':{t:sum(b['type']==t for b in breaks) for t in sorted({b['type'] for b in breaks})},
                   'material_breaks':sum(b['material'] for b in breaks),'resolutions_proposed':len(breaks),'price_breaks_routed':sum(b['component']=='price' for b in breaks)},'disclaimer':DISCLAIMER}
    return attach_source(out,doc)

def compute(doc):
    """Perform every component calculation in a private bounded Decimal context."""
    with localcontext(Context(prec=256)) as context:
        context.traps[Inexact]=True
        context.traps[Rounded]=True
        if len(doc.get('lines',[]))>100000:raise ValueError('at most 100000 NAV component lines supported')
        cfg=doc.get('config') or {}
        for value in {**DEFAULT_TOLERANCES,**cfg.get('tolerances',{})}.values():num(value)
        for value in cfg.get('materiality',{}).values():num(value)
        return _compute(doc)

def main(argv):
    selftest='--selftest' in argv
    p=Path(__file__).resolve().parents[1]/'evals/files/tie_out_example.json' if selftest else Path(argv[0]) if argv else None
    doc=json.loads(p.read_text() if p else sys.stdin.read());out=compute(doc)
    if selftest:
        from validate_output import validate
        errors=validate(out,original_input=doc)
        for e in errors:print('ERROR',e)
        print(f'nav tie-out self-test: {len(errors)} error(s)');return bool(errors)
    print(json.dumps(out,indent=2));return 0
if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
