from pathlib import Path
from fractions import Fraction
import json
P=Path('/private/tmp/ir-reconciliation-forward-independent')
raw={
 'synthetic_only':True,
 'context':{'as_of':'2026-10-20','knowledge_cutoff':'2026-10-20T22:00:00Z','purpose':'internal-research','audience':'internal-review','information_barrier':'public-side','currency':'USD','unit':'USD_m','accounting_basis':'US-GAAP-supplied','consolidation_scope':'consolidated'},
 'current':{'period':{'start':'2026-01-01','end':'2026-09-30'},'ebitda':84,'gross_debt_carrying':438,'unrestricted_cash':38,'interest_expense':12,'operating_cash_flow':61,'capex':19,'funds_from_operations':42,'mandatory_capex':19,'available_committed_facilities':30,'near_term_maturities':90,'maturity_inventory_complete':True},
 'prior':{'period':{'start':'2025-01-01','end':'2025-09-30'},'ebitda':100,'gross_debt_carrying':420,'unrestricted_cash':50,'interest_expense':10,'mandatory_capex':15,'available_committed_facilities':20,'near_term_maturities':80,'maturity_inventory_complete':True},
 'debt_inventory':{'instrument_id':'ORION-USD-NOTE-2030','legal_issuer_id':'ORION-INDUSTRIAL-HOLDINGS','inventory_coverage':'complete-for-supplied-scope','contractual_principal':450,'carrying_value_bridge':-12,'bridge_instrument_ids':['ORION-USD-NOTE-2030'],'no_other_bridge_items':True},
 'adjustment_events':[{'economic_event':'R','components':[{'component':'R-WORKFORCE','amount':7},{'component':'R-FACILITY','amount':5}],'aggregation':'additive-components'},{'economic_event':'B','amount':-4,'aggregation':'event-total-only'}],
 'sources':{'financials':{'known_at':'2026-10-19T14:00:00Z','version':'supplied-2026-10-19-v1','locator':'synthetic:orion-2026-9m-filing/financial-table-and-note-7'},'prior_financials':{'known_at':'2026-10-19T14:00:00Z','version':'comparative-supplied-2026-10-19-v1','locator':'synthetic:orion-2026-9m-filing/comparative-2025-9m'},'adjustment_R':{'known_at':'2026-10-19T14:00:00Z','version':'supplied-2026-10-19-v1','locator':'synthetic:orion-2026-9m-filing/note-8-restructuring'},'adjustment_B':{'known_at':'2026-10-19T14:00:00Z','version':'supplied-2026-10-19-v1','locator':'synthetic:orion-2026-9m-filing/note-9-disposal-gain'},'mapping':{'known_at':'2026-10-19T14:00:00Z','version':'supplied-2026-10-19-v1','locator':'synthetic:orion-2026-9m-filing/note-7-note-identity'}},
 'spreads':{'prior':{'spread_bps':'125.25','observed_at':'2026-10-19T18:00:00Z','source_known_at':'2026-10-19T18:30:00Z','source_version':'snapshot-20261019-1830-v1','source_locator':'synthetic:desk-quotes/20261019-1800/orion-note'},'current':{'spread_bps':'167.75','observed_at':'2026-10-20T19:00:00Z','source_known_at':'2026-10-20T19:30:00Z','source_version':'snapshot-20261020-1930-v1','source_locator':'synthetic:desk-quotes/20261020-1900/orion-note'},'basis':'OAS-supplied','max_current_age_hours':8,'mapping_valid_from':'2019-01-01','mapping_valid_to':'2030-12-31'},
 'thresholds':{'leverage_increase_x':'0.25','coverage_decline_x':'0.25','spread_widening_bps':'40'}
}
def q(a,b=1):
 f=Fraction(a,b);return {'fraction':str(f),'decimal':float(f)}
expect={'method':'Independent rational arithmetic from raw facts; no native implementation or output fixture imported.','issuer':{'signed_adjustments':q(7+5-4),'reported_ebitda':q(84),'adjusted_ebitda':q(84+7+5-4),'included_principal':q(450),'carrying_value_bridge':q(-12),'reconstructed_gross_debt':q(450-12),'reported_gross_leverage':q(438,84),'reported_net_leverage':q(438-38,84),'reported_interest_coverage':q(84,12),'adjusted_gross_leverage':q(438,92),'adjusted_net_leverage':q(438-38,92),'adjusted_interest_coverage':q(92,12),'free_cash_flow':q(61-19),'ffo_to_debt':q(42,438)},'surveillance':{}}
s=expect['surveillance']
for label,values in [('prior',(100,420,50,10,15,20,80)),('current',(84,438,38,12,19,30,90))]:
 e,d,c,i,cap,fac,m=values
 s[label]={'gross_leverage':q(d,e),'net_leverage':q(d-c,e),'interest_coverage':q(e,i),'fixed_charge_proxy':q(e-cap,i),'liquidity_coverage':q(c+fac,m)}
for metric in s['current']:
 v=Fraction(s['current'][metric]['fraction'])-Fraction(s['prior'][metric]['fraction'])
 s[metric+'_change']={'fraction':str(v),'decimal':float(v)}
s['spread_change_bps']=q(Fraction('167.75')-Fraction('125.25'));s['current_spread_age_hours']=q(3)
s['expected_material_changes']=['gross leverage increase above 0.25x','net leverage increase above 0.25x','interest coverage decline above 0.25x','spread widening 42.5bps above 40bps']
cases=[
 ('I01','issuer','Same component counted twice under distinct adjustment IDs','Adjustment reconciliation unavailable; reported metrics can remain supported'),
 ('I02','issuer','Same economic event recited by a second source/version and renamed event','Adjustment reconciliation unavailable; distinct documents must not create additivity'),
 ('I03','issuer','Event total selected alongside its component rows','Adjustment reconciliation unavailable'),
 ('I04','issuer','Only one of two additive event components selected','Adjustment reconciliation unavailable; no silent partial event total'),
 ('I05','issuer','Ledger source version differs from registered source version','Adjustment reconciliation unavailable'),
 ('I06','issuer','Duplicate adjustment_id in native intake','Controlled input rejection'),
 ('I07','issuer','Carrying-value bridge sign reversed to +12','Debt reconciliation unavailable; debt-dependent ratios withheld'),
 ('I08','issuer','Debt inventory coverage explicitly partial','Debt reconciliation unavailable; debt-dependent ratios withheld'),
 ('I09','issuer','Identified instrument has no explicit inclusion treatment','Debt reconciliation unavailable; debt-dependent ratios withheld'),
 ('I10','issuer','Debt bridge event repeated under a distinct bridge row ID','Debt reconciliation unavailable; duplicate bridge cannot be added'),
 ('S01','surveillance','Current quote exactly 8 elapsed hours old','Reconciled spread 42.5bps; financial metrics remain supported'),
 ('S02','surveillance','Current quote 8 hours plus one second old','Spread comparison/alert withheld; financial metrics remain supported'),
 ('S03','surveillance','Current quote assertion disagrees with selected evidence value','Spread comparison/alert withheld; financial metrics remain supported'),
 ('S04','surveillance','Supplied mapping starts after prior observation','Spread comparison/alert withheld; financial metrics remain supported'),
 ('S05','surveillance','Prior quote source known one second before its observation','Spread comparison/alert withheld; financial metrics remain supported'),
 ('S06','surveillance','Current observed_at omits timezone','Controlled input rejection'),
 ('S07','surveillance','Two selected-instant records have different IDs but identical value','Spread comparison/alert withheld; financial metrics remain supported'),
 ('S08','surveillance','A used source is known one second after research cutoff','Whole analytical projection withheld under source gate'),
]
(P/'raw_facts.json').write_text(json.dumps(raw,indent=2)+'\n')
(P/'independent_expectations.json').write_text(json.dumps(expect,indent=2)+'\n')
(P/'case_design.json').write_text(json.dumps([dict(zip(('case_id','skill','change','expected_control'),c)) for c in cases],indent=2)+'\n')
(P/'design_status.md').write_text('# Independent forward reconciliation design\n\nRaw facts and rational expectations are derived before native execution. The native envelopes will be authored after the issuer 0.2.0 schema is published. No output/golden fixture was read. Eighteen adverse or boundary cases are specified. All sources are synthetic supplied evidence, with no authentication or entitlement claim.\n')
print('Wrote raw facts, independent expectations and 18 case designs under '+str(P))
