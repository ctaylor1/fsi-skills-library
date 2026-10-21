"""Bounded supplied-input review. No source authentication or business action."""
from decimal import Decimal
from foundation_contract import (D,ratio,date_value,exact,validate_common,validate_actual_date,validate_referenced_sources,require_sources,finish,cli_compute)
from native_integrity import canonical_hash

@exact
def analyze(d):
    require_sources(d,[x.get('source_ref') for x in d['selected_lots']+d['related_purchases']])
    if not d['selected_lots']:raise ValueError('selected tax lots required')
    if d['jurisdiction']!='US' or d['account_type']!='taxable-equity':raise ValueError('unsupported tax profile; approved tax engine/professional required')
    sale=date_value(d['sale_date']);cutoff=date_value(d['knowledge_cutoff']);rows=[];issues=[];gross=tax=Decimal(0);seen=set()
    if d.get('related_accounts_coverage')!='complete':issues.append('related-account trading coverage incomplete')
    for row in d['selected_lots']:
        if row['lot_id'] in seen:raise ValueError('duplicate selected lot')
        seen.add(row['lot_id']);q=D(row['sale_quantity']);available=D(row['available_quantity']);basis=D(row['basis_per_unit']);price=D(row['sale_price']);rate=D(row['supplied_tax_rate'])
        if not 0<q<=available or basis<0 or price<0 or not 0<=rate<=1:raise ValueError('invalid lot amounts/rate')
        validate_actual_date(d,row['acquired'],row['source_ref'])
        if date_value(row['acquired'])>sale:raise ValueError('lot acquired after sale')
        gain=q*(price-basis);gross+=gain;estimated=max(gain,Decimal(0))*rate;tax+=estimated
        matches=[]
        for p in d['related_purchases']:
            observed=validate_actual_date(d,p['trade_date'],p['source_ref'])
            if observed>cutoff:raise ValueError('related purchase not known at cutoff')
            if p['tax_identity']==row['tax_identity'] and abs((observed-sale).days)<=30:
                if D(p['quantity'])<=0:raise ValueError('purchase quantity must be positive')
                matches.append({'purchase_id':p['purchase_id'],'quantity':p['quantity'],'day_offset':(observed-sale).days})
        window_complete=(cutoff-sale).days>=30 and d.get('related_accounts_coverage')=='complete'
        loss_status='not-a-loss' if gain>=0 else 'potential-wash-sale' if matches else 'window-incomplete' if not window_complete else 'requires-tax-review'
        if gain<0:issues.append('loss deductibility unresolved for selected lot '+row['lot_id'])
        rows.append({'lot_id':row['lot_id'],'gain_loss':str(gain),'estimated_positive_gain_tax':str(estimated),'recognized_loss_deduction':None,'loss_status':loss_status,'matching_purchases':matches,'window_complete':window_complete})
    return {'lots':rows,'net_economic_gain_loss':str(gross),'estimated_positive_gain_tax':str(tax),'loss_benefit_recognized':False},issues

SKILL='tax-aware-portfolio-implementation-reviewer'
METHOD='selected-us-tax-lot-impact'
LIMITS=['No wash-sale basis allocation or deduction determination; mappings/rates are supplied assertions.', 'No state, cross-border, derivative, IRA or retirement tax engine. All loss benefits withheld for review.']
HANDOFFS=['portfolio-rebalancing-planner', 'investment-recommendation-evidence-reviewer']

def validate(doc):
    errors=validate_common(doc)
    if errors:return errors
    errors+=validate_referenced_sources(doc)
    if doc.get('requested_action','review') not in ('review','draft'):errors.append('business execution unsupported')
    if errors:return errors
    try:analyze(doc)
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError) as exc:errors.append(str(exc))
    return errors

def compute(doc):
    errors=validate(doc)
    if errors:raise ValueError('; '.join(errors))
    results,issues=analyze(doc)
    return finish(doc,SKILL,METHOD,results,issues=issues,limitations=LIMITS,handoffs=HANDOFFS)

if __name__=='__main__':cli_compute(compute)
