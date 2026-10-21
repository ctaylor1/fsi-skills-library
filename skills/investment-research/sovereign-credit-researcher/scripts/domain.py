"""Bounded nominal sovereign debt scenarios and supplied credit coverage (MIT)."""
from __future__ import annotations
import copy
from analysis_contract import validate_base, number, references, finish, unique, rows
from research_runtime import require, text, only, calendar_date, temporal, eligible_time

SKILL = 'sovereign-credit-researcher'
TOPICS = {'fiscal-debt-scope', 'maturity-financing-access', 'external-monetary',
          'institutions-political-risk', 'contingent-liabilities', 'data-quality'}
YEAR_FIELDS = 'year nominal_gdp_growth domestic_effective_rate foreign_effective_rate fx_depreciation primary_balance other_cash_debt_creating_flows other_noncash_debt_creating_flows new_debt_foreign_share domestic_principal_due foreign_principal_due_local committed_financing usable_fiscal_cash fiscal_cash_draw'.split()


def cite(doc, row, label):
    refs = references(doc, row.get('evidence_refs'), label)
    require(bool(refs), label + ' requires cited evidence')
    require(eligible_time(row.get('known_at'), doc['knowledge_cutoff']) is True,
            label + ' known_at must be no later than cutoff with matching precision')
    kind, at = temporal(row['known_at']); day = at if kind == 'date' else at.date()
    require(day <= calendar_date(doc['as_of']), label + ' postdates as_of')
    src = {s['source_id']: s for s in doc['sources']}
    for ref in refs:
        require(eligible_time(src[ref['source_id']]['known_at'], row['known_at']) is True,
                label + ' source cannot postdate row knowledge or have ambiguous precision')
    return day


def positive(value, label):
    require(number(value, label, minimum=0) > 0, label + ' must exceed zero')


def coverage(doc):
    records = unique(rows(doc.get('coverage'), 'coverage'), 'topic', 'coverage')
    for row in records:
        only(row, 'topic status note known_at evidence_refs', 'coverage')
        require(row['topic'] in TOPICS, 'unsupported sovereign coverage topic')
        require(row.get('status') in {'reviewed-supplied', 'missing', 'not-reviewed'}, 'explicit coverage status required')
        require(text(row.get('note')), 'coverage note required')
        if row['status'] == 'reviewed-supplied': cite(doc, row, 'coverage')
        else:
            references(doc, row.get('evidence_refs'), 'coverage')
    return records


def validate_document(doc):
    validate_base(doc, subject_types=('issuer', 'security', 'economy'))
    require(doc.get('schema_version') == 'ir-phase4-sovereign/1.0', 'schema_version ir-phase4-sovereign/1.0 required')
    scope = doc.get('sovereign_scope'); require(isinstance(scope, dict), 'sovereign_scope required')
    only(scope, 'country_id jurisdiction government_scope accounting_basis currency units debt_measure', 'sovereign_scope')
    for key in ('country_id', 'jurisdiction', 'government_scope', 'accounting_basis'):
        require(text(scope.get(key)) and scope[key].strip().lower() not in {'unknown', 'unavailable'}, 'known scope.' + key + ' required')
    subject = doc['subject']; target = subject.get('issuer_id') if subject['type'] == 'security' else subject['id']
    require(scope['country_id'] == target, 'country_id must match requested sovereign identity')
    require(scope.get('debt_measure') == 'gross', 'only gross debt stock is supported; no net-debt substitution')
    require(isinstance(scope.get('currency'), str) and len(scope['currency']) == 3 and scope['currency'].isupper() and scope['currency'].isalpha(), 'uppercase three-letter currency required')
    require(scope.get('units') in {'ones', 'thousands', 'millions', 'billions'}, 'explicit monetary units required')
    b = doc.get('baseline'); require(isinstance(b, dict), 'baseline required')
    only(b, 'balance_date gdp domestic_debt foreign_currency_debt_local known_at evidence_refs', 'baseline')
    day = calendar_date(b.get('balance_date')); known = cite(doc, b, 'baseline')
    require(day.month == 12 and day.day == 31, 'bounded annual model requires calendar year-end debt stock')
    require(day <= known, 'baseline cannot be known before balance_date')
    positive(b.get('gdp'), 'baseline GDP')
    for k in ('domestic_debt', 'foreign_currency_debt_local'): number(b.get(k), k, minimum=0)
    scenarios = unique(rows(doc.get('scenarios'), 'scenarios', nonempty=True), 'scenario_id', 'scenarios')
    for scenario in scenarios:
        only(scenario, 'scenario_id label known_at evidence_refs years', 'scenario')
        require(text(scenario.get('label')), 'scenario label required'); cite(doc, scenario, 'scenario')
        years = rows(scenario.get('years'), 'years', nonempty=True)
        require(len(years) <= 30, 'scenario horizon must not exceed 30 years')
        for i, year in enumerate(years):
            require(isinstance(year, dict) and set(year) == set(YEAR_FIELDS), 'year requires exactly documented annual assumptions')
            require(type(year['year']) is int and year['year'] == day.year + i + 1, 'scenario years must be contiguous after baseline')
            for k in YEAR_FIELDS[1:]: number(year[k], k)
            for k in ('nominal_gdp_growth', 'fx_depreciation'):
                require(year[k] > -1, k + ' must exceed -1')
            for k in ('domestic_effective_rate', 'foreign_effective_rate', 'domestic_principal_due', 'foreign_principal_due_local', 'committed_financing', 'usable_fiscal_cash', 'fiscal_cash_draw'):
                require(year[k] >= 0, k + ' must be nonnegative')
            require(0 <= year['new_debt_foreign_share'] <= 1, 'new_debt_foreign_share requires fraction 0..1')
        project(b, scenario)  # Check stock and amortization feasibility for every year.
    ext = doc.get('external_liquidity')
    if ext is not None:
        require(isinstance(ext, dict), 'external_liquidity must be object or null')
        only(ext, 'assessment_date scope currency units reserves_available short_term_external_debt_residual_maturity imports_next_12_months known_at evidence_refs', 'external_liquidity')
        require(calendar_date(ext.get('assessment_date')) <= cite(doc, ext, 'external_liquidity'), 'external observation cannot be known before assessment_date')
        require(ext.get('scope') == 'whole-economy', 'reserves coverage is whole-economy, not government fiscal cash')
        require(ext.get('currency') == scope['currency'] and ext.get('units') == scope['units'], 'external measures need same explicit conversion currency/units')
        for k in ('reserves_available', 'short_term_external_debt_residual_maturity', 'imports_next_12_months'):
            number(ext.get(k), k, nullable=True, minimum=0)
    coverage(doc)
    return []


def project(b, scenario):
    gdp, domestic, foreign = b['gdp'], b['domestic_debt'], b['foreign_currency_debt_local']
    output = []
    for y in scenario['years']:
        opening = domestic + foreign
        require(y['domestic_principal_due'] <= domestic + 1e-9 and y['foreign_principal_due_local'] <= foreign + 1e-9,
                'principal due exceeds opening currency-bucket debt; no implicit refinancing stock')
        gdp_next = gdp * (1 + y['nominal_gdp_growth'])
        fx = foreign * y['fx_depreciation']
        interest = domestic * y['domestic_effective_rate'] + foreign * (1 + y['fx_depreciation']) * y['foreign_effective_rate']
        cash_flows = interest - y['primary_balance'] + y['other_cash_debt_creating_flows']
        flows_before_cash = cash_flows + y['other_noncash_debt_creating_flows']
        due = y['domestic_principal_due'] + y['foreign_principal_due_local'] * (1 + y['fx_depreciation'])
        financing_requirement = due + cash_flows
        gfn = max(0, financing_requirement)
        require(y['fiscal_cash_draw'] <= y['usable_fiscal_cash'] and y['fiscal_cash_draw'] <= gfn,
                'fiscal cash draw exceeds supplied usable cash or gross financing need')
        net_issue = flows_before_cash - y['fiscal_cash_draw']
        share = y['new_debt_foreign_share']
        domestic_next = domestic + net_issue * (1 - share)
        foreign_next = foreign + fx + net_issue * share
        require(domestic_next >= 0 and foreign_next >= 0, 'net debt retirement allocation makes a currency stock negative')
        available = y['committed_financing'] + y['fiscal_cash_draw']
        closing = domestic_next + foreign_next
        components = {'interest': interest / gdp_next, 'exchange_rate_revaluation': fx / gdp_next,
                      'primary_balance': -y['primary_balance'] / gdp_next,
                      'other_cash_debt_creating_flows': y['other_cash_debt_creating_flows'] / gdp_next,
                      'other_noncash_debt_creating_flows': y['other_noncash_debt_creating_flows'] / gdp_next,
                      'fiscal_cash_draw': -y['fiscal_cash_draw'] / gdp_next,
                      'gdp_denominator_change': -opening * y['nominal_gdp_growth'] / gdp_next}
        stabilizing = interest + fx + y['other_cash_debt_creating_flows'] + y['other_noncash_debt_creating_flows'] - y['fiscal_cash_draw'] - opening * y['nominal_gdp_growth']
        output.append({'year': y['year'], 'gdp': gdp_next, 'opening_debt': opening,
                       'domestic_debt': domestic_next, 'foreign_currency_debt_local': foreign_next,
                       'gross_debt': closing, 'debt_to_gdp': closing / gdp_next,
                       'debt_to_gdp_change': closing / gdp_next - opening / gdp,
                       'debt_ratio_change_components': components,
                       'interest_expense': interest, 'fx_revaluation': fx, 'net_debt_creating_flows_excluding_fx': net_issue,
                       'primary_balance_surplus_positive': y['primary_balance'],
                       'debt_stabilizing_primary_balance': stabilizing,
                       'debt_stabilizing_primary_balance_to_gdp': stabilizing / gdp_next,
                       'principal_due_at_scenario_fx': due, 'gross_financing_needs': gfn,
                       'net_financing_requirement_before_floor': financing_requirement,
                       'committed_financing': y['committed_financing'], 'usable_fiscal_cash': y['usable_fiscal_cash'],
                       'fiscal_cash_draw': y['fiscal_cash_draw'],
                       'unused_fiscal_cash_capacity': y['usable_fiscal_cash'] - y['fiscal_cash_draw'],
                       'uncommitted_funding_gap': max(0, gfn - available),
                       'available_funding_surplus_over_modeled_gfn': max(0, available - gfn),
                       'funding_assurance': 'supplied-commitments-only; modeled debt does not establish financing access'})
        gdp, domestic, foreign = gdp_next, domestic_next, foreign_next
    return output


def compute(doc):
    validate_document(doc)
    scenarios, issues = [], []
    for scenario in doc['scenarios']:
        years = project(doc['baseline'], scenario)
        scenarios.append({'scenario_id': scenario['scenario_id'], 'label': scenario['label'], 'years': years})
        for y in years:
            if y['uncommitted_funding_gap'] > 0:
                issues.append(scenario['scenario_id'] + ' ' + str(y['year']) + ': financing access not established for modeled gross needs')
    cov = coverage(doc); seen = {r['topic'] for r in cov if r['status'] == 'reviewed-supplied'}
    issues += ['Required sovereign topic missing or not reviewed: ' + k for k in sorted(TOPICS - seen)]
    ext = doc.get('external_liquidity'); external = None
    if ext is None:
        issues.append('External liquidity inputs unavailable; reserve coverage not assessed')
    else:
        reserve, debt, imports = (ext[k] for k in ('reserves_available', 'short_term_external_debt_residual_maturity', 'imports_next_12_months'))
        external = {'assessment_date': ext['assessment_date'], 'scope': ext['scope'],
                    'reserves_to_short_term_external_debt': reserve / debt if reserve is not None and debt not in (None, 0) else None,
                    'reserve_import_months': 12 * reserve / imports if reserve is not None and imports not in (None, 0) else None,
                    'fiscal_availability_established': False}
        if any(x is None for x in (reserve, debt, imports)):
            issues.append('External liquidity measures incomplete; missing values retained as null')
        if debt == 0 or imports == 0:
            issues.append('Zero external liquidity denominator; corresponding coverage ratio undefined')
    result = {'sovereign_scope': copy.deepcopy(doc['sovereign_scope']), 'baseline': copy.deepcopy(doc['baseline']),
              'scenario_paths': scenarios, 'external_liquidity': external, 'research_coverage': copy.deepcopy(cov),
              'debt_path_basis': 'conditional-supplied-scenarios; no forecast probability or financing-access assurance',
              'fx_model': 'one foreign-currency composite; average and end-period exchange-rate change assumed equal',
              'primary_balance_convention': 'surplus-positive nominal current-year amount; subtract from debt creation',
              'rating_assigned': False, 'debt_sustainability_approved': False,
              'research_acceptance': 'institutional-qualitative-and-source-review-required'}
    lineage = [{'formula': 'D_next = D_open + FX_revaluation + interest - primary_surplus + other_cash_flows + other_noncash_flows - fiscal_cash_draw; GDP_next = GDP_open*(1+nominal_growth)'},
               {'formula': 'GFN = max(0, principal_due_at_scenario_FX + interest - primary_surplus + other_cash_flows); compare committed financing plus explicit fiscal cash draw, not unused cash capacity'},
               {'formula': 'debt-stabilizing primary balance = interest + FX_revaluation + other_flows - fiscal_cash_draw - opening_debt*nominal_GDP_growth'},
               {'formula': 'reserve_import_months=12*reserves/imports_next_12_months; reserves/short_term_external_debt uses residual maturity, same whole-economy scope'}]
    return finish(doc, SKILL, result, issues, lineage)
