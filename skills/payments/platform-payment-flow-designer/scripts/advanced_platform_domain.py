"""Optional hierarchical allocation and batch review, preserving the core mode."""
from copy import deepcopy
from decimal import Decimal
import domain as core
from payment_foundation import finding

SKILL = core.SKILL


def validate(data):
    errors = core.validate(data)
    core.rows(data, 'connections', ['connected_id','owner_entity_id','account_id','agreement_ref','refund_owner_ref','chargeback_owner_ref'], errors)
    core.rows(data, 'batches', ['batch_id','owner_entity_id','currency','contract_ref'], errors)
    for row in data.get('allocations',[]):
        if isinstance(row,dict) and not core.text(row.get('connected_id')):
            errors.append('allocation connected_id required')
    seen = set()
    for row in data.get('adjustments',[])+data.get('payouts',[]):
        if not isinstance(row,dict):
            continue
        if not core.text(row.get('economic_id')):
            errors.append('adjustment/payout economic_id required')
        elif row['economic_id'] in seen:
            errors.append('duplicate economic_id across adjustments and payouts')
        seen.add(row.get('economic_id'))
    for row in data.get('batches',[]):
        if not isinstance(row,dict) or not isinstance(row.get('payout_ids'),list) or not row['payout_ids'] or any(not core.text(i) for i in row['payout_ids']):
            errors.append('batch payout_ids nonempty string list required')
    return errors


def analyze(request):
    d = request['data']
    findings = []
    def gap(code,message,row=None):
        findings.append(finding(code,message,(row or {}).get('source_ids',[])))
    entities = {r['entity_id']:r for r in d['entities']}
    accounts = {r['account_id']:r for r in d['accounts']}
    connections = {r['connected_id']:r for r in d['connections']}
    allocations = {r['allocation_id']:r for r in d['allocations']}
    children = {i:[] for i in allocations}
    bad = False
    used_accounts = set()
    for c in connections.values():
        account = accounts.get(c['account_id'])
        if not account or account['owner_entity_id']!=c['owner_entity_id'] or c['owner_entity_id'] not in entities:
            bad = True
            gap('connection-owner', c['connected_id']+': legal ownership is explicit, never inherited from parent.', c)
        if c['account_id'] in used_accounts:
            bad = True
            gap('duplicate-connected-account',c['account_id'],c)
        used_accounts.add(c['account_id'])
        seen = {c['connected_id']}
        parent = c.get('parent_connected_id')
        while parent:
            if parent in seen or parent not in connections:
                bad = True
                gap('connection-cycle-or-missing-parent', c['connected_id'], c)
                break
            seen.add(parent)
            parent = connections[parent].get('parent_connected_id')
    for aid,a in allocations.items():
        connection = connections.get(a['connected_id'])
        if not connection or connection['owner_entity_id']!=a['beneficiary_entity_id']:
            bad = True
            gap('allocation-connection-owner',aid,a)
        parent = a.get('parent_allocation_id')
        if parent:
            if parent not in allocations:
                bad = True
                gap('allocation-parent-missing',aid,a)
            else:
                children[parent].append(a)
                p = allocations[parent]
                if a['charge_id']!=p['charge_id'] or a['currency']!=p['currency'] or (a['beneficiary_entity_id']!=p['beneficiary_entity_id'] and not core.text(a.get('transfer_agreement_ref'))):
                    bad = True
                    gap('allocation-edge-binding',aid+': exact charge/currency and cross-entity contract required.',a)
                if connection and connection.get('parent_connected_id')!=p['connected_id']:
                    bad = True
                    gap('allocation-connection-hierarchy',aid,a)
        seen = {aid}
        while parent:
            if parent in seen or parent not in allocations:
                bad = True
                gap('allocation-cycle-or-missing-parent',aid,a)
                break
            seen.add(parent)
            parent = allocations[parent].get('parent_allocation_id')
    tree = []
    for aid,a in allocations.items():
        kids = children[aid]
        if not kids:
            continue
        total = sum((core.amount(k['amount']) for k in kids),Decimal(0)) if a.get('amount') is not None and all(k.get('amount') is not None and k['currency']==a['currency'] for k in kids) else None
        difference = core.amount(a['amount'])-total if total is not None else None
        if difference!=0:
            bad = True
            gap('hierarchy-conservation',aid+': children must exhaust parent exactly; retain residual as a separate leaf.',a)
        tree.append({'parent_allocation_id':aid,'currency':a['currency'],'children_total':str(total) if total is not None else None,'difference':str(difference) if difference is not None else None})
    charges = {r['charge_id']:r for r in d['charges']}
    for cid,ch in charges.items():
        roots = [a for a in allocations.values() if a['charge_id']==cid and not a.get('parent_allocation_id')]
        total = sum((core.amount(a['amount']) for a in roots),Decimal(0)) if roots and ch.get('amount') is not None and all(a.get('amount') is not None and a['currency']==ch['currency'] for a in roots) else None
        if total is None or total != core.amount(ch['amount']):
            bad = True
            gap('root-allocation-conservation',cid,ch)
    for row in d['adjustments']+d['payouts']:
        if row['allocation_id'] in children and children[row['allocation_id']]:
            bad = True
            gap('parent-economic-use',row['allocation_id']+': internal nodes cannot also be paid or adjusted; distribute the economic event to leaves.',row)
    for payout in d['payouts']:
        allocation = allocations.get(payout['allocation_id'])
        connection = connections.get(allocation['connected_id']) if allocation else None
        if not connection or payout['destination_account_id']!=connection['account_id']:
            bad = True
            gap('payout-connection-account',payout['payout_id'],payout)
    payouts = {r['payout_id']:r for r in d['payouts']}
    assigned = set()
    batch_results = []
    for batch in d['batches']:
        total = Decimal(0)
        known = True
        for pid in batch['payout_ids']:
            p = payouts.get(pid)
            if pid in assigned or p is None:
                bad = True
                known = False
                gap('batch-duplicate-or-missing-payout',pid,batch)
                continue
            assigned.add(pid)
            allocation = allocations.get(p['allocation_id'])
            if not allocation or allocation['beneficiary_entity_id']!=batch['owner_entity_id'] or p['currency']!=batch['currency']:
                bad = True
                known = False
                gap('batch-owner-or-currency',pid,batch)
            if p.get('amount') is None:
                known = False
            else:
                total += core.amount(p['amount'])
        batch_results.append({'batch_id':batch['batch_id'],'owner_entity_id':batch['owner_entity_id'],'currency':batch['currency'],'nominal_instruction_total':str(total) if known else None,'released':False})
    for pid in payouts.keys()-assigned:
        bad = True
        gap('unbatched-payout',pid,payouts[pid])
    flattened = deepcopy(request)
    flattened['data']['allocations'] = [a for aid,a in allocations.items() if not children[aid]]
    if bad:
        flattened['data']['ledger_complete'] = False
    analysis = core.analyze(flattened)
    analysis['findings'] = findings+analysis['findings']
    analysis['result'].update({'mode':'advanced-platform','connection_ownership':d['connections'],'allocation_tree_reconciliation':tree,'batch_reviews':batch_results,'batch_released':False,'inter_entity_netting':'not-performed'})
    return analysis
