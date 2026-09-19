"""Optional controlled commercial-card obligation and instruction review."""
from datetime import date, timezone
from decimal import Decimal
from domain import amount, rows, stamp, text, handoff
from payment_foundation import finding

SKILL = 'commercial-payment-workflow-designer'


def validate(data):
    errors = []
    if data.get('program_type') not in {'virtual','purchasing','fleet','corporate'}:
        errors.append('program_type must be virtual, purchasing, fleet or corporate')
    if type(data.get('history_complete')) is not bool:
        errors.append('history_complete boolean required')
    for key in ('buyer_entity_id','issuer_ref','program_contract_ref','provider_control_review_ref'):
        if not text(data.get(key)):
            errors.append(key+' required')
    credentials = rows(data,'credentials',['credential_id','owner_entity_id','supplier_ref','currency','valid_from','valid_until','usage_mode'],errors,['transaction_limit','total_limit'])
    for c in credentials:
        if not isinstance(c,dict):
            continue
        if c.get('usage_mode') not in {'one-time','limited'}:
            errors.append('usage_mode must be one-time or limited')
        if type(c.get('max_uses')) is not int or c['max_uses']<1 or (c.get('usage_mode')=='one-time' and c['max_uses']!=1):
            errors.append('positive max_uses required; one-time exactly one')
        if not isinstance(c.get('allowed_mccs'),list) or not c['allowed_mccs'] or any(not isinstance(m,str) or len(m)!=4 or not m.isdigit() for m in c['allowed_mccs']):
            errors.append('allowed_mccs explicit nonempty four-digit string list required')
        if stamp(c['valid_from'])>=stamp(c['valid_until']):
            errors.append('credential window must increase')
        for key in ('transaction_limit','total_limit'):
            if key not in c:
                errors.append(key+' required; null means unknown')
    rows(data,'invoices',['invoice_id','invoice_identity_ref','buyer_entity_id','supplier_ref','currency','remittance_ref'],errors,['open_amount'])
    identities = [r.get('invoice_identity_ref') for r in data.get('invoices',[]) if isinstance(r,dict)]
    if len(identities)!=len(set(identities)):
        errors.append('duplicate invoice_identity_ref')
    attempts = rows(data,'attempts',['payment_id','economic_id','credential_id','invoice_id','supplier_ref','currency','mcc','occurred_at','state','remittance_ref'],errors,['amount'])
    ids = set()
    for a in attempts:
        if not isinstance(a,dict):
            continue
        if a.get('economic_id') in ids:
            errors.append('duplicate economic_id; canonical current state per payment required')
        ids.add(a.get('economic_id'))
        if a.get('state') not in {'proposed','authorization-held','pending','settled','failed','unknown'}:
            errors.append('state must distinguish proposed, authorization-held, pending, settled, failed or unknown')
        stamp(a['occurred_at'])
        if 'amount' not in a:
            errors.append('attempt amount required; null means unknown')
    return errors


def analyze(request):
    d = request['data']
    findings = []
    def gap(code,msg,row=None):
        findings.append(finding(code,msg,(row or {}).get('source_ids',[])))
    credentials = {c['credential_id']:c for c in d['credentials']}
    invoices = {i['invoice_id']:i for i in d['invoices']}
    bad_creds = set()
    bad_invoices = set()
    if not credentials or not invoices:
        gap('missing-commercial-evidence','Credentials and exact supplier invoices are required.')
    for c in credentials.values():
        if c['owner_entity_id']!=d['buyer_entity_id']:
            bad_creds.add(c['credential_id'])
            gap('credential-owner',c['credential_id'],c)
        if not text(c.get('provider_enforcement_ref')):
            bad_creds.add(c['credential_id'])
            gap('unverified-control-enforcement',c['credential_id']+': local matching is not issuer enforcement.',c)
    reviews=[]
    for a in d['attempts']:
        c = credentials.get(a['credential_id'])
        i = invoices.get(a['invoice_id'])
        reasons=[]
        if a['credential_id'] in bad_creds:
            reasons.append('credential-review-unresolved')
        if not c or not i:
            reasons.append('unknown-credential-or-invoice')
        if i and (i['buyer_entity_id']!=d['buyer_entity_id'] or a['supplier_ref']!=i['supplier_ref'] or a['currency']!=i['currency'] or a['remittance_ref']!=i['remittance_ref']):
            reasons.append('invoice-supplier-remittance-binding')
        if c:
            if a['supplier_ref']!=c['supplier_ref'] or a['currency']!=c['currency'] or a['mcc'] not in c['allowed_mccs']:
                reasons.append('supplier-currency-or-mcc-control')
            at = stamp(a['occurred_at'])
            if not stamp(c['valid_from'])<=at<stamp(c['valid_until']):
                reasons.append('credential-time-window')
            if at.astimezone(timezone.utc).date()>date.fromisoformat(request['as_of']) and a['state']!='proposed':
                reasons.append('future-outcome')
            if a['amount'] is None or c['transaction_limit'] is None or amount(a['amount'])>amount(c['transaction_limit']):
                reasons.append('transaction-limit-or-unknown')
        if a['state']=='settled' and not text(a.get('settlement_ref')):
            reasons.append('missing-settlement-evidence')
        if d['program_type']=='fleet' and (not text(a.get('vehicle_ref')) or not text(a.get('driver_or_fleet_policy_ref'))):
            reasons.append('fleet-vehicle-policy-binding')
        if d['program_type']=='corporate' and not text(a.get('expense_policy_ref')):
            reasons.append('corporate-expense-policy')
        if d['program_type'] in {'purchasing','virtual'} and not text(a.get('purchase_order_ref')):
            reasons.append('purchase-order-evidence')
        for reason in reasons:
            gap(reason,a['payment_id'],a)
        if reasons:
            bad_creds.add(a['credential_id'])
            bad_invoices.add(a['invoice_id'])
        reviews.append({'payment_id':a['payment_id'],'state':a['state'],'local_binding':'needs-evidence' if reasons else 'matches-supplied-controls','payment_authorized':False,'counts_as_settled_payment':a['state']=='settled' and not reasons})
    budgets=[]
    for cid,c in credentials.items():
        linked=[a for a in d['attempts'] if a['credential_id']==cid and a['state']!='failed']
        unknown = not d['history_complete'] or cid in bad_creds or c['total_limit'] is None or any(a['amount'] is None or a['state']=='unknown' for a in linked)
        used=sum((amount(a['amount']) for a in linked if a['state']!='proposed'),Decimal(0)) if not unknown else None
        proposed=sum((amount(a['amount']) for a in linked if a['state']=='proposed'),Decimal(0)) if not unknown else None
        remaining=amount(c['total_limit'])-used if used is not None else None
        if unknown:
            gap('unknown-credential-capacity',cid,c)
        if len(linked)>c['max_uses'] or (remaining is not None and (remaining<0 or proposed>remaining)):
            gap('credential-reuse-or-budget-exceeded',cid,c)
        budgets.append({'credential_id':cid,'observed_and_proposed_uses':len(linked),'maximum_uses':c['max_uses'],'committed_or_held':str(used) if used is not None else None,'proposed':str(proposed) if proposed is not None else None,'remaining_before_proposed':str(remaining) if remaining is not None else None})
    balances=[]
    for iid,i in invoices.items():
        linked=[a for a in d['attempts'] if a['invoice_id']==iid and a['state']!='failed']
        known=d['history_complete'] and iid not in bad_invoices and i.get('open_amount') is not None and all(a['amount'] is not None and a['state']!='unknown' for a in linked)
        paid=sum((amount(a['amount']) for a in linked if a['state']=='settled'),Decimal(0)) if known else None
        reserved=sum((amount(a['amount']) for a in linked if a['state'] in {'authorization-held','pending'}),Decimal(0)) if known else None
        proposed=sum((amount(a['amount']) for a in linked if a['state']=='proposed'),Decimal(0)) if known else None
        available=amount(i['open_amount'])-paid-reserved if known else None
        if not known:
            gap('unknown-invoice-obligation',iid,i)
        if available is not None and (available<0 or proposed>available):
            gap('invoice-double-payment-risk',iid,i)
        balances.append({'invoice_id':iid,'supplier_ref':i['supplier_ref'],'currency':i['currency'],'settled_paid':str(paid) if paid is not None else None,'held_or_pending_not_paid':str(reserved) if reserved is not None else None,'uncommitted_before_proposed':str(available) if available is not None else None})
    return {'result':{'mode':'commercial-card','program_type':d['program_type'],'attempt_reviews':reviews,'credential_budgets':budgets,'invoice_positions':balances,'credential_issued':False,'payment_submitted':False,'credit_or_rewards_decision':'not-performed'},'findings':findings,'handoffs':[handoff('card-program-designer','Review issuer, sponsor, commercial product and liability arrangement.',['program contract','buyer and issuer roles','controls evidence']),handoff('payment-credential-authentication-reviewer','Review opaque credential lifecycle, authentication and payment intent.',['credential references','supplier and scope','intent']),handoff('payment-initiation-control-reviewer','Validate any exact eventual supplier instruction separately.',['invoice and remittance','amount and supplier','authority','held and unknown outcomes'])]}
