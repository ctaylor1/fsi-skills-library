"""Exact legal-register/token/custody snapshot reconciliation; no network or keys."""
from foundation_contract import D, date_value, exact, finish, require_sources, text, validate_actual_date, validate_common
from specialist_contract import validate_specialist_common as validate_common

SKILL = 'tokenized-fund-operations-reviewer'


def fields(row, *keys):
    if not isinstance(row, dict) or any(not text(row.get(k)) for k in keys):
        raise ValueError('nonempty text required: ' + ', '.join(keys))


def rows(doc, key, identity, *, empty=False):
    values = doc.get(key)
    if not isinstance(values, list) or len(values) > 10000 or not empty and not values:
        raise ValueError(key + ' requires bounded explicit inventory')
    seen = set()
    for row in values:
        fields(row, identity, 'source_ref')
        if row[identity] in seen: raise ValueError('duplicate ' + identity)
        seen.add(row[identity]); require_sources(doc, [row['source_ref']])
    return values


def amount(value, *, integer=False):
    number = D(value)
    if number < 0 or integer and number != number.to_integral_value():
        raise ValueError('nonnegative integral atoms/counts or nonnegative units required')
    return number


@exact
def compute(doc):
    errors = validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    if doc.get('requested_action', 'review') not in {'review', 'draft'}: raise ValueError('mint, burn, transfer and key operations unsupported')
    fund = doc.get('fund'); ledger = doc.get('ledger')
    fields(fund, 'fund_id', 'share_class_id', 'owner', 'legal_register_basis', 'registry_snapshot_id', 'source_ref')
    fields(ledger, 'snapshot_id', 'network_id', 'contract_id', 'block_id', 'finality_status', 'source_ref')
    require_sources(doc, [fund['source_ref'], ledger['source_ref']])
    if fund['fund_id'] != doc['object_id']: raise ValueError('fund identity differs from request object')
    for key in ('legal_unit_decimals', 'token_decimals'):
        value = fund.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 18:
            raise ValueError(key + ' must be an integer in [0,18]')
    unit_scale = D(10) ** fund['legal_unit_decimals']; atom_scale = D(10) ** fund['token_decimals']
    tokens_per_unit = amount(fund.get('tokens_per_legal_unit'))
    if tokens_per_unit == 0: raise ValueError('tokens_per_legal_unit must be positive')

    def units(value):
        number = amount(value)
        if number * unit_scale != (number * unit_scale).to_integral_value():
            raise ValueError('legal units exceed declared native precision; rounding is not permitted')
        return number

    def to_atoms(number):
        converted = number * tokens_per_unit * atom_scale
        if converted != converted.to_integral_value():
            raise ValueError('legal units cannot map to integral token atoms; no rounding is inferred')
        return converted

    register_day = validate_actual_date(doc, fund.get('observed_on'), fund['source_ref'])
    ledger_day = validate_actual_date(doc, ledger.get('observed_on'), ledger['source_ref'])
    if register_day != ledger_day or register_day != date_value(doc['as_of']):
        raise ValueError('register/ledger snapshots must share review observation date')
    issued_units = units(fund.get('official_issued_units')); supply = amount(ledger.get('total_token_atoms'), integer=True)
    if ledger['finality_status'] not in {'final', 'pending', 'reorged', 'unknown'}: raise ValueError('unsupported finality status')
    policy = ledger.get('finality_policy'); fields(policy, 'version', 'reviewer', 'source_ref')
    require_sources(doc, [policy['source_ref']])
    confirmations = amount(ledger.get('confirmations'), integer=True)
    minimum = amount(policy.get('minimum_confirmations'), integer=True)
    if not isinstance(ledger.get('reorg_detected'), bool): raise ValueError('reorg_detected requires boolean')
    final = ledger['finality_status'] == 'final' and confirmations >= minimum and not ledger['reorg_detected']
    issues = []
    if not final: issues.append('ledger finality evidence unresolved or adverse')
    register = rows(doc, 'register', 'legal_account_id')
    wallets = rows(doc, 'wallets', 'wallet_id')
    beneficial = rows(doc, 'beneficial_register', 'record_id', empty=True)
    permissions = rows(doc, 'transfer_permissions', 'permission_id')
    transfers = rows(doc, 'transfers', 'transfer_id', empty=True)
    by_account = {r['legal_account_id']: r for r in register}; by_wallet = {r['wallet_id']: r for r in wallets}
    account_units = {}; wallet_atoms = {x: D(0) for x in by_account}
    for row in register:
        fields(row, 'account_type', 'snapshot_id', 'holder_identity')
        if row['account_type'] not in {'direct', 'omnibus'} or row['snapshot_id'] != fund['registry_snapshot_id']:
            raise ValueError('register account type/snapshot differs')
        if row.get('fund_id') != fund['fund_id'] or row.get('share_class_id') != fund['share_class_id']:
            raise ValueError('register fund/share class differs')
        account_units[row['legal_account_id']] = units(row.get('legal_units'))
    for row in wallets:
        fields(row, 'legal_account_id', 'snapshot_id', 'network_id', 'contract_id', 'custody_owner')
        if row['legal_account_id'] not in by_account or any(row.get(k) != ledger[k] for k in ('snapshot_id', 'network_id', 'contract_id')):
            raise ValueError('wallet identity/snapshot/network/contract differs')
        wallet_atoms[row['legal_account_id']] += amount(row.get('token_atoms'), integer=True)
    legal_total = sum(account_units.values(), D(0)); wallet_total = sum(wallet_atoms.values(), D(0))
    if legal_total != issued_units: issues.append('legal register sum differs from official issued units')
    if wallet_total != supply: issues.append('wallet inventory differs from declared token supply')
    if to_atoms(issued_units) != supply: issues.append('official issued units differ from token supply')
    accounts = []
    for account_id, number in account_units.items():
        delta = wallet_atoms[account_id] - to_atoms(number)
        if delta != 0: issues.append('legal-account/token balance break: ' + account_id)
        accounts.append({'legal_account_id': account_id, 'legal_units': str(number), 'expected_token_atoms': str(to_atoms(number)),
                         'observed_token_atoms': str(wallet_atoms[account_id]), 'difference_token_atoms': str(delta), 'balanced': delta == 0})
    beneficiaries = {}; beneficiary_keys = set()
    for row in beneficial:
        fields(row, 'omnibus_account_id', 'beneficial_holder_id', 'snapshot_id')
        account = by_account.get(row['omnibus_account_id'])
        if not account or account['account_type'] != 'omnibus' or row['snapshot_id'] != fund['registry_snapshot_id']:
            raise ValueError('beneficial register must bind an omnibus account and register snapshot')
        key = (row['omnibus_account_id'], row['beneficial_holder_id'])
        if key in beneficiary_keys: raise ValueError('duplicate beneficial holder within omnibus account')
        beneficiary_keys.add(key); beneficiaries.setdefault(row['omnibus_account_id'], []).append(units(row.get('legal_units')))
    custody = []
    for account_id, account in by_account.items():
        if account['account_type'] != 'omnibus': continue
        children = beneficiaries.get(account_id); child_total = sum(children, D(0)) if children is not None else None
        balanced = child_total is not None and child_total == account_units[account_id]
        if not balanced: issues.append('omnibus beneficial subregister missing or unreconciled: ' + account_id)
        custody.append({'omnibus_account_id': account_id, 'legal_units': str(account_units[account_id]),
                        'beneficial_units': str(child_total) if child_total is not None else None, 'balanced': balanced,
                        'added_to_issued_total': False})
    permitted = {}
    for row in permissions:
        fields(row, 'wallet_id', 'legal_account_id', 'policy_version')
        wallet = by_wallet.get(row['wallet_id'])
        if not wallet or row['wallet_id'] in permitted or row['legal_account_id'] != wallet['legal_account_id']:
            raise ValueError('permission requires unique matching wallet and legal account')
        if not isinstance(row.get('eligible'), bool) or not isinstance(row.get('frozen'), bool):
            raise ValueError('permission eligibility/frozen must be explicit booleans')
        checked = validate_actual_date(doc, row.get('observed_on'), row['source_ref'])
        if checked != ledger_day: issues.append('wallet permission evidence not current at snapshot: ' + row['wallet_id'])
        permitted[row['wallet_id']] = row['eligible'] and not row['frozen'] and checked == ledger_day
    if set(permitted) != set(by_wallet): issues.append('wallet transfer restriction evidence incomplete')
    transfer_results = []
    for row in transfers:
        fields(row, 'from_wallet', 'to_wallet', 'snapshot_id', 'status')
        if row['from_wallet'] not in by_wallet or row['to_wallet'] not in by_wallet or row['snapshot_id'] != ledger['snapshot_id']:
            raise ValueError('transfer wallet/snapshot binding differs')
        if row['from_wallet'] == row['to_wallet']: raise ValueError('self transfer unsupported')
        if row['status'] not in {'finalized', 'pending', 'reversed', 'reorged'}: raise ValueError('unsupported transfer status')
        if not isinstance(row.get('included_in_snapshot'), bool): raise ValueError('included_in_snapshot must be boolean')
        when = validate_actual_date(doc, row.get('observed_on'), row['source_ref'])
        if when != ledger_day: raise ValueError('transfer observation differs from snapshot date')
        count = amount(row.get('token_atoms'), integer=True)
        if count == 0: raise ValueError('transfer token atoms must be positive')
        allowed = permitted.get(row['from_wallet'], False) and permitted.get(row['to_wallet'], False)
        if row['status'] == 'finalized' and (not allowed or not row['included_in_snapshot']):
            issues.append('finalized transfer lacks eligibility or snapshot evidence: ' + row['transfer_id'])
        if row['status'] != 'finalized':
            issues.append('transfer finality/reversal requires review: ' + row['transfer_id'])
            if row['included_in_snapshot']: issues.append('nonfinal transfer included in supply snapshot: ' + row['transfer_id'])
        transfer_results.append({'transfer_id': row['transfer_id'], 'status': row['status'], 'token_atoms': str(count),
                                 'declared_restrictions_satisfied': allowed, 'included_in_snapshot': row['included_in_snapshot'],
                                 'applied_to_balances_by_reviewer': False, 'source_ref': row['source_ref']})
    return finish(doc, SKILL, 'tokenized-fund-register-custody-finality/1', {
        'fund_id': fund['fund_id'], 'share_class_id': fund['share_class_id'],
        'legal_register_units': str(legal_total), 'official_issued_units': str(issued_units),
        'wallet_token_atoms': str(wallet_total), 'declared_supply_token_atoms': str(supply),
        'beneficial_units_double_counted': False, 'account_reconciliation': accounts, 'omnibus_reconciliation': custody,
        'transfer_review': transfer_results, 'finality_criteria_met_under_supplied_policy': final,
        'confirmed_reconciled': final and not issues and not doc.get('unresolved_issues'),
        'legal_title_determined': False, 'permission_authenticated': False, 'network_contacted': False,
        'mint_burn_transfer_authorized': False,
    }, issues, limitations=[
        'One fund/share class and synchronized supplied snapshots. No blockchain query, keys, wallet control, mint, burn or transfer is performed.',
        'Atomic quantities and legal-unit precision are exact; fractional atoms or excess native decimals are rejected rather than rounded.',
        'Omnibus beneficial balances reconcile underneath their legal register account and are never added again to issued units.',
        'Policy finality, custody, identity, legal register authority and permission evidence remain supplied and unauthenticated.',
    ])
