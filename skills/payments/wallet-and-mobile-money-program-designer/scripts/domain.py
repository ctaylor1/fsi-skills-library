"""As-of program liability design; no issue, redemption or execution authority."""
from datetime import date
from decimal import Decimal
from program_utils import amount, rows, text, handoff
from payment_foundation import finding

SKILL = 'wallet-and-mobile-money-program-designer'
SUPPORTED_JURISDICTIONS = {'US','EA','UK','KE'}
MODELS = {'credential-pass-through', 'stored-value', 'e-money', 'mobile-money'}
ROLES = {'operator', 'issuer', 'holder', 'merchant', 'funding-provider', 'support-owner'}


def validate(data):
    errors = []
    if data.get('model') not in MODELS:
        errors.append('model must distinguish credential-pass-through, stored-value, e-money or mobile-money')
    if type(data.get('ledger_complete')) is not bool:
        errors.append('ledger_complete boolean required')
    rows(data, 'entities', ['entity_id', 'role', 'legal_name'], errors)
    rows(data, 'roles', ['role_id', 'role', 'entity_id', 'responsibility_ref'], errors)
    positions = rows(data, 'positions', ['position_id', 'issuer_entity_id', 'currency'], errors, ['opening_liability', 'reported_liability'])
    for row in positions:
        if isinstance(row, dict):
            for key in ('opening_liability', 'reported_liability'):
                if key not in row:
                    errors.append(key+' required; null means unknown')
    events = rows(data, 'events', ['event_id', 'economic_id', 'position_id', 'type', 'state', 'holder_ref', 'currency'], errors, ['amount'])
    economic = set()
    for row in events:
        if not isinstance(row, dict):
            continue
        if row.get('economic_id') in economic:
            errors.append('duplicate economic_id; provide one canonical outcome per economic event')
        economic.add(row.get('economic_id'))
        if row.get('type') not in {'issue', 'redeem', 'internal-payment'}:
            errors.append('event type must be issue, redeem or internal-payment')
        if row.get('state') not in {'settled', 'pending', 'failed', 'unknown'}:
            errors.append('event state must be settled, pending, failed or unknown')
        if 'amount' not in row:
            errors.append('event amount required; null means unknown')
    rows(data, 'backing', ['backing_id', 'account_ref', 'position_id', 'owner_entity_id', 'beneficiary_issuer_entity_id', 'ownership_review_ref', 'currency', 'eligibility_review_ref'], errors, ['amount'])
    seen = set()
    for row in data.get('backing', []):
        if isinstance(row, dict):
            if row.get('account_ref') in seen:
                errors.append('backing account_ref reused; split evidence requires a separately reconciled allocation model')
            seen.add(row.get('account_ref'))
            if 'amount' not in row:
                errors.append('backing amount required; null means unknown')
    receipts = set()
    for row in events:
        if isinstance(row,dict) and row.get('state')=='settled' and row.get('type') in {'issue','redeem'}:
            ref = row.get('funding_receipt_ref' if row['type']=='issue' else 'external_payout_ref')
            if ref and ref in receipts:
                errors.append('duplicate funding or redemption receipt; no repeated economic use')
            if ref:
                receipts.add(ref)
            if row.get('type')=='issue' and row.get('funding_amount') is not None:
                amount(row['funding_amount'])
    pack = data.get('program_pack')
    if not isinstance(pack, dict):
        errors.append('program_pack object required')
    else:
        for key in ('jurisdiction', 'owner', 'provider_ref', 'country', 'version', 'review_due', 'source_ids'):
            if key not in pack:
                errors.append('program_pack.'+key+' required')
        if pack.get('review_due'):
            date.fromisoformat(pack['review_due'])
    if not isinstance(data.get('channels'), list):
        errors.append('channels explicit list required')
    for channel in data.get('channels',[]):
        if not isinstance(channel,dict) or not isinstance(channel.get('source_ids'),list) or not channel['source_ids']:
            errors.append('channel source_ids required')
    return errors


def analyze(request):
    d = request['data']
    findings = []
    def gap(code, msg, row=None):
        findings.append(finding(code, msg, (row or {}).get('source_ids', [])))
    entities = {r['entity_id']: r for r in d['entities']}
    for role in d['roles']:
        if role['entity_id'] not in entities:
            gap('unknown-role-owner', role['role_id'], role)
    required = ROLES - ({'issuer'} if d['model'] == 'credential-pass-through' else set())
    if d['model'] == 'mobile-money':
        required |= {'cash-agent', 'agent-supervision'}
    for missing in sorted(required-{r['role'] for r in d['roles']}):
        gap('missing-role', missing)
    pack = d['program_pack']
    if request['jurisdiction']=='KE':
        if d['model']!='mobile-money' or pack.get('country')!='KE' or any(p['currency']!='KES' for p in d['positions']):
            gap('kenya-pack-scope','Kenya support is a domestic KES mobile-money program review only.',pack)
        for key in ['trust_arrangement_ref','cbk_authorization_ref','agent_supervision_ref','redemption_contract_ref','kenya_profile_review_ref']:
            if not text(pack.get(key)):
                gap('kenya-program-evidence',key,pack)
    checks = ['licensing_review_ref', 'access_review_ref', 'consumer_error_ref', 'aml_review_ref', 'support_ref', 'funding_ref', 'redemption_ref', 'reconciliation_ref']
    if d['model'] == 'mobile-money':
        checks += ['agent_liquidity_ref', 'agent_due_diligence_ref', 'cash_reconciliation_ref']
    for key in checks:
        if not text(pack.get(key)):
            gap('missing-program-review', key, pack)
    if pack.get('jurisdiction') != request['jurisdiction'] or not text(pack.get('country')) or not text(pack.get('owner')) or not text(pack.get('provider_ref')):
        gap('program-pack-scope', 'Country, provider, accountable owner and jurisdiction must bind to this program.', pack)
    if request['jurisdiction'] in {'US','UK'} and pack.get('country') != {'US':'US','UK':'GB'}[request['jurisdiction']]:
        gap('program-pack-country', 'Country does not match the supported jurisdiction.', pack)
    if request['jurisdiction']=='EA' and pack.get('country') not in {'AT','BE','BG','HR','CY','EE','FI','FR','DE','GR','IE','IT','LV','LT','LU','MT','NL','PT','SK','SI','ES'}:
        gap('program-pack-country', 'EA requires a named euro-area member country and its own applicability review.', pack)
    if not pack.get('source_ids') or pack['review_due'] < request['as_of']:
        gap('program-pack-stale-or-unsourced', 'Current country/provider evidence is required.', pack)
    if not d['channels']:
        gap('missing-channel','Identify at least one delivery channel and its support/access evidence.')
    for channel in d['channels']:
        if not isinstance(channel, dict) or channel.get('type') not in {'qr-merchant-presented','qr-consumer-presented','app','cash-agent'}:
            gap('unsupported-channel', 'Declare a supported channel with a scoped provider/network review.')
            continue
        for key in ['participant_access_ref','fraud_support_ref'] + (['qr_profile_ref','interoperability_test_ref','payee_binding_ref'] if channel['type'].startswith('qr-') else []):
            if not text(channel.get(key)):
                gap('channel-evidence-gap', channel['type']+': '+key, channel)
    positions = {r['position_id']: r for r in d['positions']}
    invalid_links = False
    for row in d['events']+d['backing']:
        if row['position_id'] not in positions:
            invalid_links = True
            gap('unknown-position', row['position_id'], row)
    groups = set()
    for p in positions.values():
        group = (p['issuer_entity_id'],p['currency'])
        if group in groups:
            invalid_links = True
            gap('duplicate-liability-group', 'Issuer/currency may appear only once; no duplicate claim or backing use.', p)
        groups.add(group)
    if d['model']=='credential-pass-through':
        if d['positions'] or d['events'] or d['backing']:
            gap('pass-through-value-conflict', 'A credential-only design cannot represent stored program balances; split the stored-value use case.')
        result = []
    else:
        if not positions:
            gap('missing-liability-ledger', 'Stored value requires issuer/currency liability and backing positions.')
        result = []
        for pid,p in positions.items():
            ev = [e for e in d['events'] if e['position_id']==pid]
            backing = [b for b in d['backing'] if b['position_id']==pid]
            bad = invalid_links or not d['ledger_complete'] or p['issuer_entity_id'] not in entities
            if p['issuer_entity_id'] not in {r['entity_id'] for r in d['roles'] if r['role']=='issuer'}:
                bad = True
                gap('liability-issuer-role', pid, p)
            for e in ev:
                if e['currency']!=p['currency']:
                    bad = True
                    gap('cross-currency-event', e['event_id'], e)
                if e['type']=='issue' and e['state']=='settled' and (e.get('funding_state')!='settled' or not text(e.get('funding_receipt_ref')) or e.get('funding_currency')!=e['currency'] or e.get('funding_amount') is None or e['amount'] is None or amount(e['funding_amount'])!=amount(e['amount'])):
                    bad = True
                    gap('unfunded-issuance', e['event_id'], e)
                if e['type']=='redeem' and e['state']=='settled' and not text(e.get('external_payout_ref')):
                    bad = True
                    gap('unproven-redemption', e['event_id'], e)
                if e['type']=='internal-payment' and not text(e.get('payee_claim_ref')):
                    gap('unmapped-internal-claim', e['event_id'], e)
            for b in backing:
                if b['currency']!=p['currency'] or b['owner_entity_id'] not in entities or b['beneficiary_issuer_entity_id']!=p['issuer_entity_id']:
                    bad = True
                    gap('backing-owner-or-currency', b['backing_id'], b)
            liability_known = not bad and p['opening_liability'] is not None and all(e['amount'] is not None and e['state']!='unknown' for e in ev)
            liability = amount(p['opening_liability']) + sum((amount(e['amount'])*(1 if e['type']=='issue' else -1 if e['type']=='redeem' else 0) for e in ev if e['state']=='settled'),Decimal(0)) if liability_known else None
            covered = sum((amount(b['amount']) for b in backing),Decimal(0)) if backing and not bad and all(b['amount'] is not None for b in backing) else None
            delta = liability-amount(p['reported_liability']) if liability is not None and p['reported_liability'] is not None else None
            surplus = covered-liability if covered is not None and liability is not None else None
            if liability is None or covered is None or delta is None:
                gap('unknown-liability-or-backing', pid+': absent evidence is unknown, never zero.', p)
            if delta is not None and delta!=0:
                gap('liability-reconciliation-break', pid, p)
            if (liability is not None and liability<0) or (surplus is not None and surplus<0):
                gap('negative-liability-or-backing-shortfall', pid, p)
            pending = sum((amount(e['amount']) for e in ev if e['type']=='redeem' and e['state']=='pending'),Decimal(0)) if all(e['amount'] is not None for e in ev) else None
            result.append({'position_id':pid,'issuer_entity_id':p['issuer_entity_id'],'currency':p['currency'],**{k:str(v) if v is not None else None for k,v in {'derived_outstanding_liability':liability,'reported_difference':delta,'reviewed_backing':covered,'backing_surplus_or_shortfall':surplus,'pending_redemptions_still_owed':pending}.items()}})
    return {'result':{'model':d['model'],'program_pack':pack,'role_map':d['roles'],'liability_reconciliation':result,'funds_issued':False,'redemption_executed':False,'legal_or_safeguarding_compliance':'not-determined','qr_or_network_certification':'not-performed'},'findings':findings,'handoffs':[handoff('payment-regulatory-applicability-reviewer','Review actual issuer, safeguarding and country/provider applicability.',['country and entity roles','program pack','liability and backing evidence']),handoff('payment-credential-authentication-reviewer','Review opaque pass-through credential lifecycle and exact payment intent.',['credential scope','consent','payment intent']),handoff('payment-initiation-control-reviewer','Any later external redemption needs separately validated initiation.',['exact payee and amount','funding evidence','authority and unresolved issues'])]}
