"""Source-bound recovery case and explicit loss-interest allocation; no demand."""
from domain_support import Review, total, validate_shape
from insurance_foundation import number

SKILL = 'claim-recovery-case-reviewer'
METHOD = 'supplied-rights-net-pro-rata-interest'


def validate(doc):
    return validate_shape(doc, arrays=('rights', 'interests', 'collections', 'tasks'),
                          numbers=('interest_amount', 'gross_amount', 'cost_amount', 'recoverable_limit'),
                          dates=('limitation_date', 'date', 'due_date', 'effective_from', 'effective_to'),
                          lists=('source_refs', 'jurisdictions', 'lines_of_business'),
                          booleans=('rights_inventory_complete', 'collection_ledger_complete', 'cost_deduction_reviewed'))


def evaluate(doc):
    d, r = doc['data'], Review(doc, METHOD)
    if d.get('claim_id') != doc['context']['object_id'] or not d.get('currency'):
        r.add('scope', 'Require context-bound claim and currency.')
    if d.get('rights_inventory_complete') is not True or d.get('collection_ledger_complete') is not True or 'collections' not in d:
        r.add('inventory', 'Rights and collection scope must be explicitly complete.')
    rights, interests, collections, tasks = (d.get(k, []) for k in ('rights', 'interests', 'collections', 'tasks'))
    for rows, key in ((rights, 'right_id'), (interests, 'interest_id'), (collections, 'collection_id'), (tasks, 'task_id')):
        r.unique(rows, key)
    indexed, rights_report = {}, []
    if not rights:
        r.add('rights-missing', 'Recovery rights need supplied policy/legal basis and a reviewed limitation date.')
    for row in rights:
        r.evidence(row, 'Recovery right and limitation basis')
        limit = r.required(number(row.get('recoverable_limit')), 'Source-established recovery limit', row)
        day = r.date(row.get('limitation_date'), 'Reviewed limitation date', row, future=True)
        if row.get('right_type') not in {'subrogation', 'salvage', 'contribution'} or not row.get('debtor_id') or not row.get('reviewed_by') or not row.get('rights_basis'):
            r.add('rights-basis', 'Each right needs supported type, debtor, substantive rights basis and human reviewer.', row)
        days = (day - r.date(doc['as_of'], 'As of')).days if day else None
        if days is not None and days <= 0:
            r.add('limitation-review', 'Supplied limitation date has arrived or passed; legal owner must review tolling and preservation. No right is declared extinguished.', row, 'review')
        indexed[row.get('right_id')] = {'row': row, 'limit': limit, 'day': day}
        rights_report.append({'right_id': row.get('right_id'), 'right_type': row.get('right_type'), 'debtor_id': row.get('debtor_id'),
                                  'rights_basis': row.get('rights_basis'), 'limitation_date': row.get('limitation_date'), 'days_to_supplied_limitation': days, 'recoverable_limit': limit, 'source_refs': row.get('source_refs', [])})
    interests_by_right = {}
    seen_parties = set()
    for row in interests:
        r.evidence(row, 'Loss-interest allocation basis')
        amount = r.required(number(row.get('interest_amount')), 'Loss interest', row)
        binding = (row.get('right_id'), row.get('party_id'))
        if binding in seen_parties or row.get('right_id') not in indexed or not row.get('party_id') or row.get('capacity') not in {'insurer', 'claimant', 'other'} or row.get('currency') != d.get('currency'):
            r.add('interest-binding', 'Each party interest must uniquely bind right, capacity and currency.', row)
        seen_parties.add(binding)
        interests_by_right.setdefault(row.get('right_id'), []).append((row, amount))
    for rid in indexed:
        values = interests_by_right.get(rid, [])
        if not values or any(v is None for _, v in values) or total(v for _, v in values) <= 0:
            r.add('interest-basis', 'Each right needs positive total known interests; no pro-rata denominator is inferred.')
    gross_by_right, net_by_right, collection_report = {}, {}, []
    for row in collections:
        r.evidence(row, 'Collection evidence')
        rid = row.get('right_id')
        r.date(row.get('date'), 'Collection date', row)
        gross = r.required(number(row.get('gross_amount')), 'Gross collection', row)
        cost = r.required(number(row.get('cost_amount')), 'Explicit collection costs', row)
        if rid not in indexed or row.get('currency') != d.get('currency') or row.get('cost_deduction_reviewed') is not True:
            r.add('collection-binding', 'Collection must bind a known right/currency and a reviewed cost-deduction basis, including explicit zero cost.', row)
        if gross is not None and cost is not None:
            if cost > gross:
                r.add('cost-overrun', 'Costs exceed this collection; this method does not allocate negative recovery.', row)
            else:
                gross_by_right[rid] = gross_by_right.get(rid, 0) + gross
                net_by_right[rid] = net_by_right.get(rid, 0) + gross - cost
        collection_report.append({'collection_id': row.get('collection_id'), 'right_id': rid, 'gross_amount': gross, 'cost_amount': cost,
                                      'net_amount': gross - cost if gross is not None and cost is not None and gross >= cost else None, 'source_refs': row.get('source_refs', [])})
    for rid, info in indexed.items():
        interest_values = interests_by_right.get(rid, [])
        if info['limit'] is not None and gross_by_right.get(rid, 0) > info['limit']:
            r.add('right-overcollection', 'Gross collections exceed the supplied recovery limit; reconcile before allocating.', info['row'])
        if interest_values and all(v is not None for _, v in interest_values) and net_by_right.get(rid, 0) > total(v for _, v in interest_values):
            r.add('interest-overcollection', 'Net collection exceeds total supplied loss interest; excess needs a separate allocation rule.')
    task_report = []
    for row in tasks:
        r.evidence(row, 'Recovery preservation task')
        due = r.date(row.get('due_date'), 'Task due date', row, future=True)
        right = indexed.get(row.get('right_id'))
        if not right or not row.get('owner') or not row.get('task'):
            r.add('task-binding', 'Recovery task requires a known right, named owner and precise action to review.', row)
        if right and due and right['day'] and due > right['day']:
            r.add('task-after-limitation', 'Task due date follows the supplied limitation date; preservation owner must resolve.', row, 'review')
        task_report.append(dict(row, execution='not_performed'))
    if not tasks:
        r.add('task-plan', 'A recovery case requires a source-bound preservation/task plan.')
    allocations = [] if r.clear else None
    if allocations is not None:
        for rid, values in interests_by_right.items():
            denominator = total(v for _, v in values)
            for row, interest in values:
                allocations.append({'right_id': rid, 'party_id': row['party_id'], 'capacity': row['capacity'],
                                        'loss_interest': interest, 'net_collection_share': net_by_right.get(rid, 0) * interest / denominator,
                                        'source_refs': row['source_refs']})
    return r.finish({'rights_register': rights_report, 'collections': collection_report, 'allocation_schedule': allocations,
                         'currency': d.get('currency'), 'task_plan': task_report, 'legal_rights_determined': False,
                         'demand_or_disbursement_authorized': False, 'rounding': 'unrounded-decimal; payment rounding requires reviewer'})
