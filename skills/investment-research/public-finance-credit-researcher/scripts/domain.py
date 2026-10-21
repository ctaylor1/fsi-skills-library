"""GO and single-system revenue-credit bridges; no legal interpretation (MIT)."""
from __future__ import annotations
import copy
from analysis_contract import validate_base, number, references, finish, rows, unique
from research_runtime import require, text, only, calendar_date, temporal, eligible_time

SKILL = 'public-finance-credit-researcher'
TOPICS = {'pledge-documents', 'economic-tax-or-rate-base', 'operating-finances', 'maturity-liquidity',
          'pension-other-liabilities', 'capital-maintenance', 'governance-data-quality'}
GO = 'general_revenue operating_costs_excluding_debt_service_and_pension pension_required_contribution pension_paid_contribution unfunded_pension_liability unrestricted_available_fund_balance restricted_cash assessed_tax_base top_ten_taxpayers_share capital_needs committed_capital_funding'.split()
REV = 'gross_pledged_revenue operating_costs required_other_prior_payments available_debt_service_reserve capital_needs committed_capital_funding supplied_coverage_threshold'.split()


def cite(doc, row, label):
    refs = references(doc, row.get('evidence_refs'), label)
    require(bool(refs), label + ' requires precise evidence')
    require(eligible_time(row.get('known_at'), doc['knowledge_cutoff']) is True,
            label + ' row knowledge must not postdate cutoff or have ambiguous precision')
    kind, at = temporal(row['known_at']); day = at if kind == 'date' else at.date()
    require(day <= calendar_date(doc['as_of']), label + ' postdates as_of')
    src = {s['source_id']: s for s in doc['sources']}
    for ref in refs:
        require(eligible_time(src[ref['source_id']]['known_at'], row['known_at']) is True,
                label + ' source must not postdate row knowledge or have ambiguous precision')
    return day


def coverage(doc):
    records = unique(rows(doc.get('coverage'), 'coverage'), 'topic', 'coverage')
    for r in records:
        only(r, 'topic status note known_at evidence_refs', 'coverage')
        require(r['topic'] in TOPICS, 'unsupported public-finance coverage topic')
        require(r.get('status') in {'reviewed-supplied', 'missing', 'not-reviewed'}, 'explicit coverage status required')
        require(text(r.get('note')), 'coverage note required')
        if r['status'] == 'reviewed-supplied': cite(doc, r, 'coverage')
        else: references(doc, r.get('evidence_refs'), 'coverage')
    return records


def validate_document(doc):
    validate_base(doc)
    require(doc.get('schema_version') == 'ir-phase4-public-finance/1.0', 'schema_version ir-phase4-public-finance/1.0 required')
    s = doc.get('financial_scope'); require(isinstance(s, dict), 'financial_scope required')
    only(s, 'entity_id jurisdiction accounting_basis currency units fiscal_year obligation_type pledged_system_id pledge_basis legal_pledge_description', 'financial_scope')
    for k in ('entity_id', 'jurisdiction', 'accounting_basis', 'legal_pledge_description'):
        require(text(s.get(k)) and s[k].strip().lower() not in {'unknown', 'unavailable'}, 'known financial_scope.' + k + ' required')
    subject = doc['subject']; target = subject.get('issuer_id') if subject['type'] == 'security' else subject['id']
    require(s['entity_id'] == target, 'entity_id must match requested public issuer identity')
    require(isinstance(s.get('currency'), str) and len(s['currency']) == 3 and s['currency'].isalpha() and s['currency'].isupper(), 'uppercase three-letter currency required')
    require(s.get('units') in {'ones', 'thousands', 'millions', 'billions'}, 'explicit monetary units required')
    require(type(s.get('fiscal_year')) is int and 1900 <= s['fiscal_year'] <= 2200, 'fiscal_year required')
    require(s.get('obligation_type') in {'general-obligation', 'revenue'}, 'GO or revenue mode required')
    if s['obligation_type'] == 'general-obligation':
        require(s.get('pledged_system_id') is None and s.get('pledge_basis') == 'general-resources', 'GO requires general resources and no revenue-system substitution')
    else:
        require(text(s.get('pledged_system_id')), 'revenue mode requires single pledged_system_id')
        require(s.get('pledge_basis') in {'net-revenues', 'gross-revenues'}, 'explicit gross or net revenue pledge required')
    f = doc.get('financials'); require(isinstance(f, dict), 'financials required')
    expected = GO if s['obligation_type'] == 'general-obligation' else REV
    require(set(f) == set(expected + ['period_start', 'period_end', 'known_at', 'evidence_refs']), 'financials must use exactly documented fields for chosen mode')
    start, end = calendar_date(f['period_start']), calendar_date(f['period_end'])
    require(start < end and 330 <= (end - start).days <= 370 and end.year == s['fiscal_year'], 'annual fiscal period must match fiscal_year with explicit start/end')
    require(end <= cite(doc, f, 'financials'), 'reported financials cannot be known before fiscal period end')
    for k in expected:
        number(f[k], k, nullable=k in {'pension_required_contribution', 'pension_paid_contribution', 'unfunded_pension_liability', 'assessed_tax_base', 'top_ten_taxpayers_share', 'supplied_coverage_threshold'}, minimum=None if k == 'unrestricted_available_fund_balance' else 0)
    if s['obligation_type'] == 'general-obligation' and f['top_ten_taxpayers_share'] is not None:
        require(f['top_ten_taxpayers_share'] <= 1, 'taxpayer concentration must be fraction 0..1')
    require(type(doc.get('obligation_inventory_complete')) is bool, 'explicit obligation inventory completeness required')
    records = unique(rows(doc.get('obligations'), 'obligations', nonempty=True), 'obligation_id', 'obligations')
    security_ids = set()
    for r in records:
        require(text(r.get('security_id')) and r['security_id'] not in security_ids, 'each obligation requires a unique security_id; duplicate security debt cannot be summed')
        security_ids.add(r['security_id'])
        require(r.get('period_start') == f['period_start'] and r.get('period_end') == f['period_end'], 'obligation due period must exactly match analytical fiscal period')
        only(r, 'obligation_id security_id period_start period_end obligor_id pledged_system_id scope outstanding principal_due interest_due allocable_share included_in_direct_debt known_at evidence_refs', 'obligation')
        require(text(r.get('obligor_id')), 'obligor_id required')
        require(r.get('scope') in {'direct', 'overlapping', 'contingent'}, 'explicit direct, overlapping or contingent scope required')
        for k in ('outstanding', 'principal_due', 'interest_due', 'allocable_share'): number(r.get(k), k, minimum=0)
        require(r['allocable_share'] <= 1, 'allocable_share must be fraction 0..1')
        require(r['principal_due'] <= r['outstanding'], 'principal due exceeds outstanding; no automatic rollover')
        require(type(r.get('included_in_direct_debt')) is bool, 'included_in_direct_debt boolean required')
        if r['scope'] == 'direct':
            require(r['obligor_id'] == s['entity_id'] and r['allocable_share'] == 1 and r['included_in_direct_debt'] is False, 'direct debt needs same obligor, full share and no duplicate inclusion flag')
            require(r.get('pledged_system_id') == s['pledged_system_id'], 'direct obligation pledge system differs from analytical scope')
        else:
            require(r['obligor_id'] != s['entity_id'], 'overlapping or contingent third-party exposure needs distinct obligor identity')
        cite(doc, r, 'obligation')
    if subject['type'] == 'security':
        require(any(r['scope'] == 'direct' and r['security_id'] == subject['id'] for r in records), 'requested security must appear in direct analytical pledge inventory')
    scenarios = unique(rows(doc.get('scenarios'), 'scenarios'), 'scenario_id', 'scenarios')
    for r in scenarios:
        only(r, 'scenario_id label revenue_change operating_cost_change interest_cost_change capital_cost_change known_at evidence_refs', 'scenario')
        require(text(r.get('label')), 'scenario label required')
        for k in ('revenue_change', 'operating_cost_change', 'interest_cost_change', 'capital_cost_change'):
            require(number(r.get(k), k) >= -1, k + ' must not be below -1')
        cite(doc, r, 'scenario')
    coverage(doc)
    return []


def measures(doc, shocks):
    s, f = doc['financial_scope'], doc['financials']
    direct = [r for r in doc['obligations'] if r['scope'] == 'direct']
    principal = sum(r['principal_due'] for r in direct)
    interest = sum(r['interest_due'] for r in direct) * (1 + shocks['interest_cost_change'])
    ds = principal + interest
    capital = f['capital_needs'] * (1 + shocks['capital_cost_change'])
    result = {'supplied_direct_debt_outstanding': sum(r['outstanding'] for r in direct),
              'supplied_direct_principal_due': principal, 'supplied_direct_interest_due': interest,
              'supplied_direct_debt_service': ds,
              'direct_inventory_complete': doc['obligation_inventory_complete'],
              'capital_needs': capital, 'unfunded_capital_needs': max(0, capital - f['committed_capital_funding']),
              'covenant_compliance_established': False, 'legal_pledge_enforceability_established': False}
    if s['obligation_type'] == 'general-obligation':
        revenue = f['general_revenue'] * (1 + shocks['revenue_change'])
        cost = f['operating_costs_excluding_debt_service_and_pension'] * (1 + shocks['operating_cost_change'])
        paid, required = f['pension_paid_contribution'], f['pension_required_contribution']
        available = None if paid is None else revenue - cost - paid
        total_operating = None if paid is None else cost + paid
        result.update(general_revenue=revenue, operating_costs_excluding_debt_service_and_pension=cost,
                      supplied_pension_paid_contribution=paid,
                      pension_contribution_shortfall=max(0, required - paid) if required is not None and paid is not None else None,
                      unfunded_pension_liability=f['unfunded_pension_liability'],
                      available_before_direct_debt_service=available,
                      recurrent_balance_after_direct_debt_service=available - ds if available is not None and doc['obligation_inventory_complete'] else None,
                      illustrative_general_resource_coverage=available / ds if available is not None and ds > 0 and doc['obligation_inventory_complete'] else None,
                      unrestricted_fund_balance_to_operating_costs=f['unrestricted_available_fund_balance'] / total_operating if total_operating not in (None, 0) else None,
                      direct_debt_to_assessed_tax_base=result['supplied_direct_debt_outstanding'] / f['assessed_tax_base'] if f['assessed_tax_base'] not in (None, 0) and doc['obligation_inventory_complete'] else None,
                      top_ten_taxpayers_share=f['top_ten_taxpayers_share'],
                      restricted_cash_excluded_from_available_funds=f['restricted_cash'])
    else:
        revenue = f['gross_pledged_revenue'] * (1 + shocks['revenue_change'])
        operating = f['operating_costs'] * (1 + shocks['operating_cost_change'])
        pledge_before_prior = revenue - operating if s['pledge_basis'] == 'net-revenues' else revenue
        available = pledge_before_prior - f['required_other_prior_payments']
        recurring_coverage = available / ds if ds > 0 and doc['obligation_inventory_complete'] else None
        result.update(gross_pledged_revenue=revenue, operating_costs=operating,
                      pledged_cash_before_other_prior_payments=pledge_before_prior,
                      recurring_available_for_direct_debt_service=available,
                      illustrative_pledged_revenue_coverage=recurring_coverage,
                      supplied_coverage_threshold=f['supplied_coverage_threshold'],
                      numerical_margin_to_supplied_threshold=recurring_coverage - f['supplied_coverage_threshold'] if recurring_coverage is not None and f['supplied_coverage_threshold'] is not None else None,
                      recurring_cash_shortfall=max(0, ds - available) if doc['obligation_inventory_complete'] else None,
                      available_debt_service_reserve=f['available_debt_service_reserve'],
                      cash_shortfall_after_one_time_reserve=max(0, ds - available - f['available_debt_service_reserve']) if doc['obligation_inventory_complete'] else None,
                      system_operating_cash_after_operating_costs_and_debt_service=revenue - operating - f['required_other_prior_payments'] - ds if doc['obligation_inventory_complete'] else None)
    return result


def compute(doc):
    validate_document(doc)
    base = {k: 0 for k in ('revenue_change', 'operating_cost_change', 'interest_cost_change', 'capital_cost_change')}
    metrics = measures(doc, base); issues = []
    if metrics['unfunded_capital_needs'] > 0:
        issues.append('Supplied capital needs lack committed funding; capital funding gap remains unresolved')
    if not doc['obligation_inventory_complete']:
        issues.append('Direct obligation inventory incomplete; total debt-service coverage and residual financial balance withheld')
    if not any(r['scope'] == 'direct' for r in doc['obligations']):
        issues.append('No direct obligations supplied; direct coverage undefined')
    if metrics['supplied_direct_debt_service'] == 0:
        issues.append('Zero direct debt-service denominator; coverage undefined')
    scenarios = []
    for r in doc['scenarios']:
        scenarios.append({'scenario_id': r['scenario_id'], 'label': r['label'], 'metrics': measures(doc, r)})
    cov = coverage(doc); seen = {r['topic'] for r in cov if r['status'] == 'reviewed-supplied'}
    issues += ['Required public-finance topic missing or not reviewed: ' + k for k in sorted(TOPICS - seen)]
    f = doc['financials']
    if doc['financial_scope']['obligation_type'] == 'general-obligation':
        for k in ('pension_required_contribution', 'pension_paid_contribution', 'unfunded_pension_liability', 'assessed_tax_base', 'top_ten_taxpayers_share'):
            if f[k] is None: issues.append('Missing GO measure retained as null: ' + k)
        if metrics['pension_contribution_shortfall'] not in (None, 0): issues.append('Supplied pension payment is below required contribution')
        if f['assessed_tax_base'] == 0: issues.append('Zero assessed tax base; debt burden ratio undefined')
        if f['unrestricted_available_fund_balance'] < 0: issues.append('Supplied unrestricted available fund balance is negative')
        if metrics['recurrent_balance_after_direct_debt_service'] is not None and metrics['recurrent_balance_after_direct_debt_service'] < 0:
            issues.append('Reported general resources do not cover modeled recurrent costs and direct debt service')
    else:
        if f['supplied_coverage_threshold'] is None: issues.append('Document coverage threshold unavailable; numerical margin withheld')
        if metrics['recurring_cash_shortfall'] not in (None, 0): issues.append('Recurring pledged resources are below modeled direct debt service')
        if metrics['system_operating_cash_after_operating_costs_and_debt_service'] is not None and metrics['system_operating_cash_after_operating_costs_and_debt_service'] < 0:
            issues.append('System operating costs and direct debt service exceed supplied recurring revenue even if gross pledge coverage is positive')
    for scenario in scenarios:
        m = scenario['metrics']
        if m.get('recurring_cash_shortfall', 0) not in (None, 0) or (m.get('recurrent_balance_after_direct_debt_service') is not None and m['recurrent_balance_after_direct_debt_service'] < 0):
            issues.append(scenario['scenario_id'] + ': stressed recurring resources insufficient for modeled direct debt service')
        if m.get('system_operating_cash_after_operating_costs_and_debt_service') is not None and m['system_operating_cash_after_operating_costs_and_debt_service'] < 0:
            issues.append(scenario['scenario_id'] + ': stressed system operating cash balance is negative')
    exposures = []
    for r in doc['obligations']:
        if r['scope'] != 'direct':
            exposures.append({'obligation_id': r['obligation_id'], 'obligor_id': r['obligor_id'], 'scope': r['scope'],
                              'allocable_share': r['allocable_share'], 'allocable_outstanding': r['outstanding'] * r['allocable_share'],
                              'included_in_direct_debt': r['included_in_direct_debt'], 'aggregated_with_direct_debt': False})
    result = {'financial_scope': copy.deepcopy(doc['financial_scope']),
              'reported_fiscal_period': {'start': f['period_start'], 'end': f['period_end']},
              'reported_metrics': metrics, 'conditional_scenarios': scenarios,
              'separate_overlapping_contingent_exposures': exposures, 'research_coverage': copy.deepcopy(cov),
              'ratio_basis': 'illustrative supplied annual cash-flow definition; document covenant definition requires separate interpretation',
              'tax_treatment_determined': False, 'rating_assigned': False, 'credit_approved': False,
              'research_acceptance': 'institutional-qualitative-document-and-source-review-required'}
    lineage = [{'formula': 'GO available = general_revenue - operating_costs_excluding_debt_service_and_pension - pension_paid; illustrative coverage = available / direct_debt_service'},
               {'formula': 'net pledge available = gross_pledged_revenue - operating_costs - prior_payments; gross pledge available = gross_pledged_revenue - prior_payments; reserve excluded from recurring coverage'},
               {'formula': 'direct debt service = supplied direct principal + supplied direct interest; overlapping and contingent exposures shown separately; no automatic legal allocation'},
               {'formula': 'unfunded capital = max(0, capital_needs - committed_capital_funding); pension shortfall = max(0, required_contribution-paid_contribution)'}]
    return finish(doc, SKILL, result, issues, lineage)
