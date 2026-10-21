"""Single-event, supplied-terms financial bridges; no approval or execution (MIT)."""
from __future__ import annotations

from analysis_contract import validate_base, number, require, references, finish
from research_runtime import calendar_date, temporal, eligible_time, text, only

SKILL = 'corporate-event-impact-reviewer'
SCALES = {'ones', 'thousands', 'millions', 'billions'}
TERMS = {
    'equity-raise': 'shares_issued issue_price fees',
    'share-repurchase': 'cash_spend repurchase_price fees cash_funding debt_funding',
    'acquisition': 'purchase_equity_value target_debt_assumed acquired_cash debt_funding equity_funding_shares issue_price cash_funding fees',
    'refinancing': 'principal_repaid new_debt_proceeds fees cash_funding cash_retained old_annual_rate new_annual_rate',
    'asset-disposal': 'sale_cash_proceeds debt_transferred cash_disposed fees taxes',
}


def cite(doc, row, label):
    refs = row.get('evidence_refs')
    require(isinstance(refs, list) and bool(refs), label + ' requires precise citations')
    references(doc, refs, label + ' evidence_refs')
    require(eligible_time(row.get('known_at'), doc['knowledge_cutoff']) is True,
            label + ' known_at must be no later than cutoff, with matching time precision')
    row_time = temporal(row['known_at'])
    row_day = row_time[1] if row_time[0] == 'date' else row_time[1].date()
    require(row_day <= calendar_date(doc['as_of']), label + ' known_at postdates as_of')
    sources = {s['source_id']: s for s in doc['sources']}
    for ref in refs:
        require(eligible_time(sources[ref['source_id']]['known_at'], row['known_at']) is True,
                label + ' citation cannot postdate asserted row knowledge or have ambiguous precision')
    return row_day


def positive(value, label):
    require(number(value, label, minimum=0) > 0, label + ' must exceed zero')


def reconciles(left, right, label):
    # Tolerance covers floating-point arithmetic only; no material unexplained plug.
    require(abs(left - right) <= 1e-9 * max(1, abs(left), abs(right)),
            label + ' sources must equal uses without an unexplained plug')


def validate_document(doc):
    validate_base(doc)
    require(doc.get('schema_version') == 'ir-phase3-event/1.0', 'schema_version ir-phase3-event/1.0 required')
    basis = doc.get('financial_basis')
    require(isinstance(basis, dict), 'financial_basis required')
    only(basis, 'currency units share_units accounting_basis consolidation_scope', 'financial_basis')
    require(isinstance(basis.get('currency'), str) and len(basis['currency']) == 3
            and basis['currency'].isalpha() and basis['currency'].isupper(), 'three-letter uppercase currency required')
    require(basis.get('units') in SCALES and basis.get('share_units') == basis['units'],
            'money and shares require the same explicit numeric scale; no implicit conversion')
    for key in ('accounting_basis', 'consolidation_scope'):
        require(text(basis.get(key)) and basis[key].strip().lower() not in {'unknown', 'unavailable', 'not-provided'},
                'known financial_basis.' + key + ' required')
    security = doc.get('valuation_subject')
    require(isinstance(security, dict), 'valuation_subject required')
    only(security, 'security_id share_class share_count_basis', 'valuation_subject')
    for key in ('security_id', 'share_class', 'share_count_basis'):
        require(text(security.get(key)), 'valuation_subject.' + key + ' required')
    require(doc['subject']['type'] != 'security' or security['security_id'] == doc['subject']['id'],
            'valuation_subject security identity differs from subject')
    baseline = doc.get('baseline')
    require(isinstance(baseline, dict), 'baseline required')
    only(baseline, 'balance_date known_at cash debt shares evidence_refs', 'baseline')
    baseline_date = calendar_date(baseline.get('balance_date'))
    require(baseline_date <= calendar_date(doc['as_of']), 'baseline balance_date postdates as_of')
    baseline_known = cite(doc, baseline, 'baseline')
    require(baseline_date <= baseline_known, 'baseline cannot be known before its balance_date')
    for key in ('cash', 'debt'):
        number(baseline.get(key), 'baseline.' + key, minimum=0)
    positive(baseline.get('shares'), 'baseline.shares')
    event = doc.get('event')
    require(isinstance(event, dict), 'one event object required; interactions require separate review')
    only(event, 'event_id type status announcement_date effective_date known_at scenario_label evidence_refs terms', 'event')
    require(text(event.get('event_id')), 'event_id required')
    require(event.get('type') in TERMS, 'unsupported event type')
    require(event.get('status') in {'proposed', 'announced', 'completed'}, 'explicit event status required')
    known_day = cite(doc, event, 'event')
    effective = calendar_date(event.get('effective_date'))
    require(baseline_date < effective, 'baseline must precede event effective_date to avoid applying the event twice')
    if event['status'] == 'proposed':
        require(event.get('announcement_date') is None, 'proposed scenario must not assert an actual announcement date')
    else:
        announced = calendar_date(event.get('announcement_date'))
        require(announced <= known_day and announced <= effective,
                'announcement must be known and cannot follow effective_date')
    if event['status'] == 'completed':
        require(effective <= known_day and effective <= calendar_date(doc['as_of']),
                'completed event requires effective_date known by as_of')
        require(event.get('scenario_label') is None, 'completed supplied terms must not carry a scenario_label')
    else:
        require(text(event.get('scenario_label')), 'pending/proposed event requires an explicit conditional scenario label')
    terms = event.get('terms')
    require(isinstance(terms, dict), 'event.terms required')
    expected = set(TERMS[event['type']].split())
    require(set(terms) == expected, 'event.terms must contain exactly the documented fields for its event type')
    for key in expected:
        number(terms[key], 'terms.' + key, minimum=0)
    kind = event['type']
    if kind == 'equity-raise':
        positive(terms['shares_issued'], 'shares_issued'); positive(terms['issue_price'], 'issue_price')
        require(terms['shares_issued'] * terms['issue_price'] >= terms['fees'], 'fees exceed gross equity proceeds')
    elif kind == 'share-repurchase':
        positive(terms['cash_spend'], 'cash_spend'); positive(terms['repurchase_price'], 'repurchase_price')
        require(terms['cash_spend'] / terms['repurchase_price'] < baseline['shares'],
                'repurchase must leave positive shares outstanding')
        reconciles(terms['cash_funding'] + terms['debt_funding'], terms['cash_spend'] + terms['fees'], 'repurchase funding')
    elif kind == 'acquisition':
        positive(terms['purchase_equity_value'], 'purchase_equity_value')
        if terms['equity_funding_shares']:
            positive(terms['issue_price'], 'issue_price')
        else:
            require(terms['issue_price'] == 0, 'zero new shares requires explicit zero issue_price; no unused hypothetical stock price')
        reconciles(terms['cash_funding'] + terms['debt_funding'] + terms['equity_funding_shares'] * terms['issue_price'],
                   terms['purchase_equity_value'] + terms['fees'], 'acquisition funding')
    elif kind == 'refinancing':
        positive(terms['principal_repaid'], 'principal_repaid')
        require(terms['principal_repaid'] <= baseline['debt'], 'refinanced principal exceeds baseline debt')
        require(terms['old_annual_rate'] <= 1 and terms['new_annual_rate'] <= 1, 'annual rates require fractions from zero to one')
        reconciles(terms['new_debt_proceeds'] + terms['cash_funding'],
                   terms['principal_repaid'] + terms['fees'] + terms['cash_retained'], 'refinancing funding')
    else:
        require(terms['debt_transferred'] <= baseline['debt'], 'disposal transfers more debt than baseline debt')
        require(terms['cash_disposed'] <= baseline['cash'], 'cash disposed exceeds baseline cash')
    return []


def compute(doc):
    validate_document(doc)
    b, event = doc['baseline'], doc['event']
    t, kind = event['terms'], event['type']
    delta = {'cash': 0, 'debt': 0, 'shares': 0}
    metrics, sources, uses, lineage = {}, None, None, []
    if kind == 'equity-raise':
        gross = t['shares_issued'] * t['issue_price']
        delta.update(cash=gross - t['fees'], shares=t['shares_issued'])
        metrics.update(gross_primary_equity_proceeds=gross, net_primary_equity_proceeds=delta['cash'])
        sources, uses = gross, t['fees'] + delta['cash']
        lineage.append({'formula': 'gross_primary_equity_proceeds = shares_issued * issue_price; cash change = gross proceeds - fees'})
    elif kind == 'share-repurchase':
        retired = t['cash_spend'] / t['repurchase_price']
        delta.update(cash=-t['cash_funding'], debt=t['debt_funding'], shares=-retired)
        metrics.update(shares_reduced=retired, fraction_of_opening_shares_reduced=retired / b['shares'])
        sources, uses = t['cash_funding'] + t['debt_funding'], t['cash_spend'] + t['fees']
        lineage.append({'formula': 'shares reduced = cash_spend / repurchase_price; cash_spend excludes fees; fees are part of funding uses'})
    elif kind == 'acquisition':
        delta.update(cash=-t['cash_funding'] + t['acquired_cash'],
                     debt=t['debt_funding'] + t['target_debt_assumed'], shares=t['equity_funding_shares'])
        equity_consideration = t['equity_funding_shares'] * t['issue_price']
        metrics.update(purchase_equity_value=t['purchase_equity_value'], equity_consideration=equity_consideration,
                       implied_acquired_enterprise_value=t['purchase_equity_value'] + t['target_debt_assumed'] - t['acquired_cash'])
        sources = t['cash_funding'] + t['debt_funding'] + equity_consideration
        uses = t['purchase_equity_value'] + t['fees']
        lineage.append({'formula': 'acquired EV = equity purchase value + debt assumed - acquired cash; cash change = acquired cash - buyer cash funding; debt change = new debt + assumed debt'})
    elif kind == 'refinancing':
        delta.update(cash=-t['cash_funding'] + t['cash_retained'], debt=t['new_debt_proceeds'] - t['principal_repaid'])
        old_interest = t['principal_repaid'] * t['old_annual_rate']
        new_interest = t['new_debt_proceeds'] * t['new_annual_rate']
        metrics.update(old_tranche_annual_interest=old_interest, new_tranche_annual_interest=new_interest,
                       annual_interest_change=new_interest - old_interest,
                       interest_scope='annualized supplied fixed rates for replaced/new tranches only; no fee amortization or tax effects')
        sources = t['new_debt_proceeds'] + t['cash_funding']
        uses = t['principal_repaid'] + t['fees'] + t['cash_retained']
        lineage.append({'formula': 'debt change = new debt - repaid principal; annual interest change = new debt * new annual rate - repaid principal * old annual rate'})
    else:
        delta.update(cash=t['sale_cash_proceeds'] - t['cash_disposed'] - t['fees'] - t['taxes'], debt=-t['debt_transferred'])
        metrics.update(net_sale_cash_after_fees_tax=t['sale_cash_proceeds'] - t['fees'] - t['taxes'],
                       cash_leaving_disposed_business=t['cash_disposed'])
        sources = t['sale_cash_proceeds']
        uses = t['fees'] + t['taxes'] + metrics['net_sale_cash_after_fees_tax']
        lineage.append({'formula': 'cash change = sale cash proceeds - cash disposed - fees - taxes; debt change = negative debt transferred'})
    before = {key: b[key] for key in ('cash', 'debt', 'shares')}
    before['net_debt'] = b['debt'] - b['cash']
    after = {key: b[key] + delta[key] for key in ('cash', 'debt', 'shares')}
    after['net_debt'] = after['debt'] - after['cash']
    delta['net_debt'] = delta['debt'] - delta['cash']
    metrics.update(new_shares_fraction_of_post_event_shares=max(delta['shares'], 0) / after['shares'],
                   share_count_change_fraction=delta['shares'] / b['shares'])
    ending_cash_shortfall = max(0, -after['cash'])
    # Supplied buyer cash funding must be available before acquired cash or
    # retained refinancing proceeds. A positive closing balance cannot prove
    # that an earlier cash-funded leg was financeable.
    upfront_cash_required = t['cash_funding'] if kind in {'acquisition', 'refinancing', 'share-repurchase'} else 0
    upfront_cash_shortfall = max(0, upfront_cash_required - b['cash'])
    gaps = max(ending_cash_shortfall, upfront_cash_shortfall)
    issues = []
    if ending_cash_shortfall:
        issues.append('Supplied post-event cash bridge has a shortfall of ' + str(ending_cash_shortfall) + '; additional financing or intervening cash flows are unestablished')
    if upfront_cash_shortfall:
        issues.append('Supplied upfront cash funding exceeds available baseline cash by ' + str(upfront_cash_shortfall) + '; acquired cash or retained refinancing proceeds do not establish earlier funding availability')
    if event['status'] != 'completed' and calendar_date(event['effective_date']) <= calendar_date(doc['as_of']):
        issues.append('Supplied expected effective date has elapsed; completion remains unestablished')
    lineage.append({'formula': 'after = baseline + change; net debt = debt - cash; no intervening operating cash flows or unmodeled transactions assumed'})
    results = {
        'event_summary': {k: event[k] for k in ('event_id', 'type', 'status', 'announcement_date', 'effective_date', 'known_at', 'scenario_label')},
        'effect_basis': 'supplied-completed-terms' if event['status'] == 'completed' else 'conditional-on-supplied-terms',
        'financial_bridge': dict(doc['financial_basis'], valuation_subject=doc['valuation_subject'], balance_date=b['balance_date'], before=before, change=delta, after=after),
        'event_metrics': metrics,
        'funding_reconciliation': {'sources': sources, 'uses': uses, 'difference': sources - uses,
                                   'cash_feasible_for_supplied_bridge': gaps == 0,
                                   'additional_cash_required': gaps,
                                   'ending_cash_shortfall': ending_cash_shortfall,
                                   'upfront_cash_required': upfront_cash_required,
                                   'upfront_cash_available_from_baseline': b['cash'],
                                   'upfront_cash_shortfall': upfront_cash_shortfall,
                                   'cash_feasibility_scope': 'Both supplied upfront cash-funded legs and post-event balances; no acquired-cash or retained-proceeds netting before the cash-funded leg.',
                                   'funding_availability': 'not-independently-established'},
        'review_limitations': ['Single supplied event and unchanged financial scope; no interaction or intervening cash-flow model.',
                               'Upfront cash funding precedes acquired cash and retained refinancing proceeds; alternative settlement sequencing or bridge facilities require separate evidenced review.',
                               'Share-count arithmetic preserves supplied class and basis; economic ownership, voting control and weighted-average EPS require separate review.',
                               'No purchase accounting, tax opinion, synergy forecast, market reaction, legal completion or execution determination.'],
        'legal_completion_verified': False, 'market_reaction_predicted': False,
    }
    return finish(doc, SKILL, results, issues=issues, lineage=lineage)
