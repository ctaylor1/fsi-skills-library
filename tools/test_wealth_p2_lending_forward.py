"""Independent P2 lending forward tests: fresh fixture, known arithmetic and adverse conditions."""
import copy,json,sys
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path


def _run_checks():
    ROOT=Path(__file__).resolve().parents[1]
    FIXTURE=ROOT/'tools/fixtures/wealth-p2-forward/wealth-lending-liquidity-reviewer.json'
    sys.path.insert(0,str(ROOT/'skills/wealth-management/wealth-lending-liquidity-reviewer/scripts'))
    from domain import build,validate,validate_output

    def cited(**kwargs):return dict(kwargs,source_ids=['case'])
    def request():
     return json.loads(FIXTURE.read_text())

    def money(x):return str(Decimal(str(x)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
    def sc(o,loan='SBLOC',i=0):return next(r for r in o['result']['loan_alternatives'] if r['loan_id']==loan)['scenarios'][i]
    def lo(o,loan='SBLOC'):return next(r for r in o['result']['loan_alternatives'] if r['loan_id']==loan)
    def codes(o):return {f['code'] for f in o['findings']}
    checks=[]
    def check(name,fn):
     try:
      fn();checks.append(dict(name=name,passed=True))
     except Exception as e:
      checks.append(dict(name=name,passed=False,error=repr(e)))
    def eq(a,b):
     assert a==b,(a,b)
    def needs(mut,code=None):
     d=request();mut(d);o=build(d);eq(o['status'],'needs-data');eq(validate_output(o),[])
     if code:
      assert code in codes(o),(code,codes(o))
     return o
    base=request();out=build(base)
    check('fresh input and full reconstruction',lambda:(eq(validate(base),[]),eq(validate_output(out),[])))
    check('cash reserve and cash funding gap',lambda:(eq(out['result']['liquidity_alternatives'][0]['net_proceeds'],'90000.00'),eq(out['result']['liquidity_alternatives'][0]['funding_gap'],'35000.00')))
    check('supplied liquidation net and no inferred tax',lambda:(eq(out['result']['liquidity_alternatives'][1]['net_proceeds'],'132000.00'),eq(out['result']['liquidity_alternatives'][1]['funding_gap'],'0.00')))
    check('draw proceeds separate from existing facility principal',lambda:(eq(lo(out)['new_net_proceeds'],'124375.00'),eq(lo(out)['opening_total_principal'],'175000.00'),eq(lo(out)['funding_gap'],'625.00')))
    check('base encumbered collateral excluded',lambda:(eq(sc(out)['borrowing_base'],'230000.00'),eq(sc(out)['effective_capacity'],'230000.00'),eq(sc(out)['debt_over_capacity'],'0.00')))
    check('combined collateral shock and advance-rate reduction',lambda:(eq(sc(out,i=1)['borrowing_base'],'133000.00'),eq(sc(out,i=1)['maintenance_paydown_illustration'],'42000.00'),eq(sc(out,i=1)['debt_over_capacity'],'42000.00')))
    check('floating cap and floor',lambda:(eq(Decimal(sc(out,i=1)['annual_rate_pct']),Decimal('10.5')),eq(Decimal(sc(out,i=2)['annual_rate_pct']),Decimal('4'))))
    check('base interest-only costs',lambda:(eq(sc(out)['loan_projection']['total_interest'],'12600.00'),eq(sc(out)['loan_projection']['horizon_financing_cost'],'13345.00'),eq(sc(out)['loan_projection']['ending_principal'],'175000.00'),eq(sc(out)['loan_projection']['maximum_budgeted_service'],'1060.00')))
    check('cap scenario interest-only costs',lambda:(eq(sc(out,i=1)['loan_projection']['total_interest'],'18375.00'),eq(sc(out,i=1)['loan_projection']['horizon_financing_cost'],'19120.00'),eq(sc(out,i=1)['loan_projection']['maximum_budgeted_service'],'1541.25')))
    # Independent amortization: calculate level payment using float annuity, then round actual cents with Decimal.
    payment=Decimal(money(180000*(0.06/12)/(1-(1+0.06/12)**-24)))
    balance=Decimal('180000');interest_total=Decimal(0)
    for month in range(12):
     interest=Decimal(money(balance*Decimal('.005')));interest_total+=interest;balance-=payment-interest
    expected=dict(payment=str(payment),balance=money(balance),interest=money(interest_total),cost=money(interest_total+Decimal(1800)))
    check('independent amortization recurrence and fees',lambda:(eq(sc(out,'AMORT')['loan_projection']['months'][0]['interest'],'900.00'),eq(sc(out,'AMORT')['loan_projection']['months'][0]['scheduled_principal'],'7077.71'),eq(sc(out,'AMORT')['loan_projection']['ending_principal'],expected['balance']),eq(sc(out,'AMORT')['loan_projection']['total_interest'],expected['interest']),eq(sc(out,'AMORT')['loan_projection']['horizon_financing_cost'],expected['cost'])))
    check('fixed loan unaffected by rate shock',lambda:eq(sc(out,'AMORT',0)['loan_projection'],sc(out,'AMORT',1)['loan_projection']))
    check('draft boundaries demand risk and no selected option',lambda:(eq(out['result']['selected_option'],None),eq(out['action_taken'],False),eq(out['delivery_status'],'not-delivered'),eq(bool(lo(out)['risk_notes']),True)))
    def complete_without_stress():
     d=request();d['scenarios']=[];o=build(d);eq(o['status'],'review-ready');eq(o['result']['selected_option'],None)
    check('known alternative cash gap is retained without automatic recommendation',complete_without_stress)
    check('unknown liquidation tax does not become zero',lambda:eq(needs(lambda d:d['liquidation_options'][0].update(tax_reserve=None),'liquidation-data-gap')['result']['liquidity_alternatives'][1]['net_proceeds'],None))
    check('late liquidation date',lambda:needs(lambda d:d['liquidation_options'][0].update(available_date='2026-10-02'),'late-funding'))
    check('loan quote must cover future funding date',lambda:needs(lambda d:d['loan_options'][0].update(quote_valid_until='2026-09-20'),'quote-expired'))
    check('late loan funding',lambda:needs(lambda d:d['loan_options'][0].update(funding_date='2026-10-03'),'late-funding'))
    check('stale quote within registry freshness',lambda:needs(lambda d:d['loan_options'][0].update(quote_date='2026-09-01'),'stale-quote'))
    check('unknown reserve does not become available cash',lambda:eq(needs(lambda d:d['liquid_resources'].update(protected_reserve=None),'unknown-amount')['result']['liquidity_alternatives'][0]['net_proceeds'],None))
    check('reserve shortfall',lambda:needs(lambda d:d['liquid_resources'].update(available_cash='50000.00'),'reserve-shortfall'))
    check('SBLOC cannot fund securities purchase',lambda:needs(lambda d:d['funding_need'].update(purpose_category='securities-purchase'),'use-of-proceeds-review'))
    check('unknown use review cannot be permitted',lambda:needs(lambda d:d['loan_options'][1].update(use_review='unknown'),'use-of-proceeds-review'))
    check('stale collateral suppresses borrowing base',lambda:eq(sc(needs(lambda d:d['loan_options'][1]['collateral'][0].update(valuation_date='2026-09-01'),'collateral-data-gap'))['borrowing_base'],None))
    check('unknown encumbrance suppresses borrowing base',lambda:eq(sc(needs(lambda d:d['loan_options'][1]['collateral'][0].update(value_reserved_elsewhere=None),'collateral-data-gap'))['borrowing_base'],None))
    check('encumbrance over market value suppresses borrowing base',lambda:eq(sc(needs(lambda d:d['loan_options'][1]['collateral'][0].update(value_reserved_elsewhere='400001.00'),'encumbrance-conflict'))['borrowing_base'],None))
    check('unknown limit does not become unlimited',lambda:eq(sc(needs(lambda d:d['loan_options'][1].update(credit_limit=None),'loan-data-gap'))['effective_capacity'],None))
    check('ineligible collateral excluded',lambda:eq(sc(needs(lambda d:d['loan_options'][1]['collateral'][0].update(eligible=False),'borrowing-capacity-gap'))['borrowing_base'],'50000.00'))
    check('monthly budget includes existing facility debt service',lambda:needs(lambda d:d['debt_budget'].update(monthly_available='1000.00'),'debt-service-gap'))
    def balloon():
     o=needs(lambda d:(d.update(horizon_months=18),d['loan_options'][1].update(maturity_funding='100000.00')),'maturity-funding-gap');p=sc(o)['loan_projection'];eq(p['balloon_within_horizon'],'175000.00');eq(p['maturity_funding_gap'],'75000.00');eq(p['ending_principal'],'0.00');eq(p['maximum_budgeted_service'],'1060.00')
    check('balloon separate from monthly affordability',balloon)
    def property_mode():
     d=request();d['loan_options'][1].update(type='property-secured',collateral_test='origination-only');o=build(d);eq(sc(o,i=1)['debt_over_capacity'],'42000.00');eq(sc(o,i=1)['maintenance_paydown_illustration'],None)
    check('origination-only property does not invent maintenance call',property_mode)
    def full_amort():
     d=request();d['horizon_months']=30;o=build(d);p=sc(o,'AMORT')['loan_projection'];eq(len(p['months']),24);eq(p['ending_principal'],'0.00');eq(p['principal_repaid'],'180000.00')
    check('amortizing final installment reconciles and stops at maturity',full_amort)
    def zero_rate():
     d=request();d['loan_options'][0].update(annual_rate_pct=0,term_months=24);o=build(d);p=sc(o,'AMORT')['loan_projection'];eq(p['months'][0]['scheduled_principal'],'7500.00');eq(p['months'][0]['budgeted_service'],'7525.00');eq(p['total_interest'],'0.00')
    check('zero-rate amortization',zero_rate)
    def no_floor():
     d=request();d['loan_options'][1].update(rate_floor_pct=None);o=build(d);eq(Decimal(sc(o,i=2)['annual_rate_pct']),Decimal('2.2'));d['scenarios'][1]['rate_shock_bps']=-900;o=build(d);eq(sc(o,i=2)['loan_projection'],None);assert 'unsupported-rate' in codes(o)
    check('no uncontracted zero floor',no_floor)
    check('upstream issues propagate',lambda:needs(lambda d:d.update(upstream_issues=[cited(artifact_id='prior-artifact',code='ownership-dispute',message='Pledge ownership remains disputed',status='unresolved')]),'upstream-unresolved'))
    check('missing item citation retained as finding',lambda:needs(lambda d:d['loan_options'][1]['collateral'][0].update(source_ids=[]),'evidence-gap'))
    def reject(mut):
     d=request();mut(d);assert validate(d),'input accepted'
    check('malformed capacity rejected without crash',lambda:reject(lambda d:d['engagement'].update(capacity=[])))
    check('booleans rejected as monetary input',lambda:reject(lambda d:d['loan_options'][0].update(draw_amount=True)))
    check('duplicate collateral rejected',lambda:reject(lambda d:d['loan_options'][1]['collateral'].append(copy.deepcopy(d['loan_options'][1]['collateral'][0]))))
    check('future quote rejected',lambda:reject(lambda d:d['loan_options'][0].update(quote_date='2026-09-18')))
    check('reserved base scenario rejected by input validator',lambda:reject(lambda d:d['scenarios'][0].update(scenario_id='base')))
    check('three-decimal monetary input rejected',lambda:reject(lambda d:d['funding_need'].update(amount='125000.001')))
    def tamper():
     for change in (lambda o:sc(o)['loan_projection'].update(total_interest='0.00'),lambda o:o['result'].update(selected_option='SBLOC'),lambda o:o.update(action_taken=True),lambda o:lo(o).update(opening_total_principal='125000.00')):
      o=copy.deepcopy(out);change(o);assert validate_output(o)
    check('tampered arithmetic selection and action rejected',tamper)
    report=dict(checks=checks,passed=sum(c['passed'] for c in checks),total=len(checks),independent_amortization=expected)
    print(json.dumps(report,indent=2))
    return int(report['passed'] != report['total'])


def main():
    """Run against this package without retaining its path or generic module names."""
    prior_path = list(sys.path)
    names = ('domain', 'wealth_contract', 'wealth_workflow')
    prior_modules = {name: sys.modules.pop(name) for name in names if name in sys.modules}
    try:
        return _run_checks()
    finally:
        sys.path[:] = prior_path
        for name in names:
            sys.modules.pop(name, None)
        sys.modules.update(prior_modules)


if __name__ == '__main__':
    raise SystemExit(main())
