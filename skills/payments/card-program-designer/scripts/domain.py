"""Source-declared card program design; no issuer, credit or licensing approval."""
from collections import Counter

SKILL = 'card-program-designer'
ROLES = ('issuer', 'sponsor', 'processor', 'program-manager')
BASE = ('issuing-accountability', 'authorization-processing', 'ledger-posting',
        'network-settlement', 'dispute-handling', 'card-and-token-servicing',
        'fraud-monitoring', 'customer-support')
TYPE_DUTIES = {'credit': ('credit-policy', 'receivables-funding', 'collections'),
               'debit': ('deposit-account-servicing', 'balance-availability'),
               'prepaid': ('customer-funds-protection', 'redemption', 'balance-availability')}


def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ['data must be an object']
    for key in ('program', 'funding', 'economics', 'rewards'):
        if key in data and not isinstance(data[key], dict):
            errors.append(f'{key} must be an object')
    for key in ('parties', 'responsibilities', 'controls', 'fund_flows'):
        if key in data and (not isinstance(data[key], list) or any(not isinstance(x, dict) for x in data[key])):
            errors.append(f'{key} must be a list of objects')
    program = data.get('program', {})
    if isinstance(program, dict):
        if 'territories' in program and (not isinstance(program['territories'], list) or
                                        any(not isinstance(x, str) for x in program['territories'])):
            errors.append('program.territories must be a list of strings')
    for party in data.get('parties', []) if isinstance(data.get('parties', []), list) else []:
        if isinstance(party, dict) and 'roles' in party and (not isinstance(party['roles'], list) or
                any(not isinstance(x, str) for x in party['roles'])):
            errors.append('party.roles must be a list of strings')
    if isinstance(data.get('rewards'), dict) and 'offered' in data['rewards'] and not isinstance(data['rewards']['offered'], bool):
        errors.append('rewards.offered must be boolean')
    string_fields = {'name', 'proposition', 'customer_segment', 'card_type', 'currency', 'party_id', 'owner_party_id',
                     'responsibility', 'model', 'source_of_funds', 'settlement_funding_party_id', 'customer_funds_model',
                     'credit_risk_party_id', 'receivables_owner_party_id', 'custodian_party_id', 'account_title',
                     'insolvency_treatment', 'flow_id', 'purpose', 'from_party_id', 'to_party_id', 'trigger', 'area', 'design'}
    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in string_fields and child is not None and not isinstance(child, str): errors.append(key + ' must be a string')
                if key in {'support_party_ids'} and (not isinstance(child, list) or any(not isinstance(x, str) for x in child)): errors.append(key + ' must be a list of strings')
                walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(data)
    return errors


def analyze(request):
    d = request['data']; p = d.get('program', {}); funding = d.get('funding', {})
    findings = []
    def gap(code, message, row=None):
        findings.append({'code': code, 'message': message, 'source_ids': (row or {}).get('source_ids', []), 'severity': 'gap'})
    for field in ('name', 'proposition', 'customer_segment', 'card_type', 'territories', 'currency'):
        if not p.get(field):
            gap('program-context-missing', f'Program {field} is unresolved.', p)
    if p.get('customer_segment') not in {'consumer', 'commercial'}:
        gap('segment-unsupported', 'Specify consumer or commercial; mixed programs need separate assessments.', p)
    card_type = p.get('card_type')
    if card_type not in TYPE_DUTIES:
        gap('card-type-unsupported', 'This blueprint supports credit, debit and prepaid separately; hybrid features require specialist decomposition.', p)
    if not p.get('source_ids'):
        gap('proposition-evidence-missing', 'The proposition has no cited business evidence.', p)
    for territory in p.get('territories', []):
        if territory not in {'US', 'EA', 'UK'}:
            gap('territory-unsupported', f'{territory} is outside the initial regional scope.', p)
        elif territory != request['jurisdiction']:
            gap('separate-jurisdiction-review', f'{territory} requires a separate jurisdiction-scoped assessment; this request covers {request["jurisdiction"]}.', p)
    parties = d.get('parties', [])
    counts = Counter(x.get('party_id') for x in parties)
    index = {x.get('party_id'): x for x in parties if x.get('party_id') and counts[x.get('party_id')] == 1}
    for key, count in counts.items():
        if not key or count > 1:
            gap('ambiguous-party', f'Party identity {key!r} is missing or duplicated; it cannot own a requirement.')
    role_map = []
    for role in ROLES:
        candidates = [x for x in parties if role in x.get('roles', []) and x.get('party_id') in index]
        role_map.append({'role': role, 'party_ids': [x['party_id'] for x in candidates],
                         'status': 'supplied' if candidates else 'unresolved',
                         'source_ids': sorted({s for x in candidates for s in x.get('source_ids', [])})})
        if not candidates:
            gap('role-unassigned', f'{role} responsibility is unresolved. A direct issuer may also occupy sponsor/program-manager roles, but declare this explicitly.')
        if any(not x.get('source_ids') for x in candidates):
            gap('role-evidence-missing', f'{role} assignment lacks agreement or operating-model evidence.')
    duties = list(BASE) + list(TYPE_DUTIES.get(card_type, ()))
    if d.get('rewards', {}).get('offered') is True:
        duties.append('rewards-funding-and-redemption')
    rows = d.get('responsibilities', [])
    matrix = []
    for duty in duties:
        matches = [x for x in rows if x.get('responsibility') == duty]
        row = matches[0] if len(matches) == 1 else {}
        owner = row.get('owner_party_id')
        reasons = []
        if len(matches) != 1:
            reasons.append('one explicit accountable assignment required')
        if owner not in index:
            reasons.append('accountable party unresolved')
        if not row.get('source_ids'):
            reasons.append('agreement or procedure evidence missing')
        if duty == 'issuing-accountability' and owner in index and 'issuer' not in index[owner].get('roles', []):
            reasons.append('issuing accountability must identify the issuer; outsourcing does not establish a substitute issuer')
        supporters = row.get('support_party_ids', [])
        if not isinstance(supporters, list) or any(x not in index for x in supporters):
            reasons.append('supporting party identity unresolved')
        matrix.append({'responsibility': duty, 'owner_party_id': owner, 'support_party_ids': supporters,
                       'status': 'unresolved' if reasons else 'supplied-assignment', 'issues': reasons,
                       'source_ids': row.get('source_ids', [])})
        for reason in reasons:
            gap('responsibility-gap', f'{duty}: {reason}.', row)
    required_funding = ['model', 'source_of_funds', 'settlement_funding_party_id', 'customer_funds_model']
    if card_type == 'credit':
        required_funding += ['credit_risk_party_id', 'receivables_owner_party_id']
    else:
        required_funding += ['custodian_party_id', 'account_title', 'insolvency_treatment']
    for key in required_funding:
        if not funding.get(key):
            gap('funding-unresolved', f'Funding field {key} is unresolved.', funding)
        elif key.endswith('_party_id') and funding[key] not in index:
            gap('funding-party-unresolved', f'Funding field {key} refers to an unknown or ambiguous party.', funding)
    if not funding.get('source_ids'):
        gap('funding-evidence-missing', 'Funding, credit exposure and customer-funds treatment require cited agreements.', funding)
    flows = []
    for flow in d.get('fund_flows', []):
        reasons = []
        for key in ('flow_id', 'purpose', 'currency', 'from_party_id', 'to_party_id', 'trigger', 'source_ids'):
            if not flow.get(key): reasons.append(f'{key} unresolved')
        if flow.get('from_party_id') not in index or flow.get('to_party_id') not in index:
            reasons.append('funds-flow endpoints unresolved')
        flows.append({**flow, 'assessment': 'unresolved' if reasons else 'supplied-proposal', 'issues': reasons})
        for reason in reasons: gap('funds-flow-gap', reason, flow)
    if not flows:
        gap('funds-flow-missing', 'Show account funding or lending draw, network settlement funding, and repayment/redemption flows applicable to the proposition.')
    controls = d.get('controls', [])
    for area in ('fraud', 'complaints-and-disputes', 'credential-security', 'financial-reconciliation'):
        matches = [x for x in controls if x.get('area') == area]
        if not any(x.get('design') and x.get('owner_party_id') in index and x.get('source_ids') for x in matches):
            gap('control-design-missing', f'{area}: a source-linked design and accountable party are required.')
    gap('regulatory-applicability-review', 'Local legal entity permissions, consumer/commercial scope, disclosures, customer funds and credit-feature applicability require the regulatory specialist; this blueprint is not an applicability determination.', p)
    if not d.get('economics', {}).get('source_ids'):
        gap('economics-unresolved', 'Funding, processing, network fees, loss, rewards and servicing economics are not supplied; no profitability conclusion is possible.')
    handoffs = [{'target_skill': 'payment-regulatory-applicability-reviewer', 'reason': 'Review the supplied proposition, legal entities, territories and funds/credit model.', 'required_inputs': ['program proposition', 'legal entities and territories', 'funding and credit features'], 'source_ids': p.get('source_ids', [])}]
    if card_type == 'credit':
        handoffs.append({'target_skill': 'credit-application-packager', 'reason': 'Prepare credit-policy/underwriting evidence with the banking owner; this design does not approve credit or prescribe limits.', 'required_inputs': ['credit product and customer segment', 'lending owner', 'approved underwriting policy'], 'source_ids': funding.get('source_ids', [])})
    return {'result': {'blueprint_status': 'draft-for-specialist-review', 'program': p,
                      'role_map': role_map, 'responsibility_matrix': matrix,
                      'funding_and_customer_funds': funding, 'funds_flow_blueprint': flows,
                      'control_designs': controls, 'rewards_proposal': d.get('rewards', {}),
                      'economic_assumptions': d.get('economics', {}),
                      'approval_or_licensing_determined': False}, 'findings': findings, 'handoffs': handoffs}
