import json,pathlib,datetime
root=pathlib.Path('/tmp/insurance-p2-forward-operations')
cases={
'policy':('insurance-policy-transaction-packager','Please prepare a draft location-change endorsement for synthetic bakery Cedar Oven. The request email says the old address is 10 Main St. Check the current policy export and the queue before sending this to policy operations.',{
 'POL':'PAS snapshot 2026-09-18: policy P-CO-77, version 8, active, insured CO-1, US-TEST commercial-property, USD, term 2026-01-01 through 2027-01-01. values.location_address = 12 Main St.',
 'REQ':'Email E-24 from account manager AM-7 dated 2026-09-18: policy P-CO-77 expected version 8, endorsement effective 2026-09-25; change location_address from 10 Main St to 40 Mill Rd.',
 'RULE':'Synthetic reviewed operations profile OP-9 v2 (reviewer OPS-OWNER), effective 2026-01-01 through 2026-12-31, US-TEST commercial-property. Endorsement: active policies, location_address changes, required endorsement-form, no notice recipients, calendar-day notice minimum zero; backdating prohibited.',
 'AUTH':'AM-7 has documented P-CO-77 endorsement preparation authority 2026-01-01 through 2026-12-31.',
 'DOC':'Endorsement form END-24, version 1, P-CO-77, policy version 8, kind endorsement-form.',
 'PREM':'Underwriting premium worksheet PW-24: USD +125.50 written-premium-change for E-24.',
 'QUEUE':'Full queue snapshot 2026-09-18 includes another pending endorsement E-23 on P-CO-77. No sequence or effect has been reconciled.'}),
'billing':('insurance-premium-billing-reconciler','Reconcile the August gross premium receivable for synthetic account AC-72 and explain the control difference, aged invoices, and any unapplied cash. Do not propose postings.',{
 'CTL':'Account AC-72, policy P-72, USD gross-premium-receivable. Period 2026-08-01 to 2026-08-31. Prior close 2026-07-31: 1000.00; reported close 2026-08-31: 420.00. Complete period ledger and opening invoice inventory supplied.',
 'OPEN':'Opening invoice OLD-1, P-72, USD remaining 1000.00, due 2026-07-15.',
 'LEDGER':'2026-08-02 I-1 invoice NEW-1 USD 600.00 due 2026-08-20; 2026-08-05 R-1 receipt USD 700.00; 2026-08-06 C-1 credit-adjustment USD 100.00; 2026-08-10 R-2 receipt USD 200.00; 2026-08-11 V-2 reversal of R-2 USD 200.00; 2026-08-15 R-3 receipt USD 650.00. All account AC-72 policy P-72.',
 'ALLOC':'A-1 applies R-1 700.00 to OLD-1. A-2 applies C-1 100.00 to OLD-1. A-3 applies R-3 600.00 to NEW-1. The remaining 50.00 of R-3 is unapplied. No allocation of reversed receipt R-2.'}),
'producer':('insurance-producer-onboarding-reviewer','Review individual and agency evidence for synthetic Harbor Agency onboarding with carrier C-9 for the property line. The licensing feed appears to disagree with the later compliance extract. Explain what the licensing owner still needs.',{
 'SCOPE':'Individual IND-4: Mira Vale; business entity AGENCY-4: Harbor Agency LLC. Both require US-TEST property line license and C-9 appointment under synthetic profile PR-4 v3 reviewed by LC-OWNER, effective 2026-01-01 to 2026-12-31. Evidence max age 30 days.',
 'LICA':'Feed observed 2026-09-17: LIC-I-A, IND-4, Mira Vale, US-TEST property, active, effective 2026-01-01 expires 2027-01-01.',
 'LICB':'Compliance extract observed 2026-09-18: LIC-I-B, IND-4, Mira Vale, US-TEST property, suspended, effective 2026-09-16 expires 2027-01-01. No adjudication supplied.',
 'LICAG':'Feed observed 2026-09-17: LIC-A, AGENCY-4, Harbor Agency LLC, US-TEST property, active, effective 2026-01-01 expires 2027-01-01.',
 'APPT':'Carrier C-9 extract 2026-09-17: APP-I, IND-4 Mira Vale US-TEST property active, effective 2026-01-01 expires 2026-12-31. No agency appointment record supplied.'}),
'placement':('insurance-placement-packager','Package the two market responses for synthetic Cedar Oven. Preserve Market North version 1, use version 2 per the broker email, and explain which totals and terms can be compared. Do not select a market.',{
 'MANDATE':'Placement PL-77, insured CO-1. Broker represents CO-1; US-TEST commercial-property term 2026-10-01 through 2027-10-01. Requested USD occurrence primary layer, building coverage, flood excluded, limit 1000000, retention 5000.',
 'PROFILE':'Synthetic comparison profile MK-2 v1 reviewed by BROKER-OWNER effective 2026-01-01 through 2026-12-31, US-TEST commercial-property.',
 'N1':'Market North response N-1 v1 issued 2026-09-15 valid until 2026-09-25: requested terms, premium 12000, fees 250, taxes 600, no subjectivities.',
 'N2':'Market North response N-2 v2 issued 2026-09-18 valid until 2026-09-25: requested terms, premium 11800, fees 300, taxes pending confirmation. Subjectivity S-N: roof inspection, status satisfied according to broker; no supporting carrier or inspection evidence supplied.',
 'S1':'Market South response S-1 v1 issued 2026-09-17 valid until 2026-09-24: requested terms except retention 10000. Premium 10900, fees 200, taxes 545. Subjectivity S-S: signed application remains open.',
 'SELECT':'Broker instruction 2026-09-18: N-2 is North current response; N-1 superseded. S-1 is South current response.'}),
'delegation':('insurance-delegated-authority-reviewer','Prepare an oversight review of synthetic MGA Delta proposed risk T-88. Check per-risk and aggregate authority and the August bordereau; expose exceptions for the insurer owner without treating an email as an amendment.',{
 'PROFILE':'Synthetic oversight profile DA-P v1 reviewed by INS-OWNER, effective 2026-01-01 through 2026-12-31 for US-TEST commercial-property.',
 'AGR':'Executed agreement DA-12 v4, insurer INS-1, delegate MGA-2, effective 2026-01-01 through 2026-12-31. US-TEST commercial-property action bind. USD insured-limit basis, per-risk limit 250000, aggregate limit 2000000.',
 'REQUEST':'Transaction T-88, INS-1/MGA-2, US-TEST commercial-property, bind, 2026-09-18, USD 180000 insured-limit basis.',
 'LEDGER':'DA-12 v4 utilization ledger as of 2026-09-18: complete; used 1880000 USD insured-limit basis; T-88 is not included.',
 'REPORT':'August report B-8 period_end 2026-08-31 due 2026-09-10 received 2026-09-16 complete USD written-premium; expected 95000.00 reported 94750.50.',
 'EMAIL':'MGA email: please allow this one risk over aggregate. No insurer acceptance or executed amendment supplied.'}),
'life':('life-annuity-sales-reviewer','Prepare a fixed-annuity replacement supervisory memo for synthetic customer L-17. The application and recorded interview conflict about near-term liquidity. Preserve that conflict, show lost guarantees and missing evidence, and do not decide suitability.',{
 'PROFILE':'Synthetic fixed-annuity review profile LA-P v1 reviewed by SALES-OWNER, effective 2026-01-01 through 2026-12-31, US-TEST life-annuity, insurance-agent channel, max evidence age 30 days. Includes state-sales-standard and state-replacement as institution-policy review topics only, not legal determinations.',
 'APP':'Application observed 2026-09-17: age 66; goal stable retirement income; annual income 48000; liquid assets 160000; planned premium 100000 from existing annuity surrender; time horizon 7 years; conservative risk tolerance; prior fixed annuity experience; nonqualified tax status. States near-term liquidity need 10000.',
 'INTERVIEW':'Interview record verified 2026-09-18: customer expects 60000 for home repairs within 12 months. Existing annuity value 103000, surrender charge 3000; guaranteed rate 3.5% for remaining 2 years. Customer considering surrender to fund proposed annuity.',
 'PROD':'Proposed fixed annuity: premium 100000; 4.2% guaranteed rate for 3 years; 7-year surrender schedule 7/6/5/4/3/2/1%; 10% annual free withdrawal; no market value adjustment; death benefit account value; no income rider elected; annuitization options require brochure confirmation. Producer commission 5% of premium. Disclosure acknowledged 2026-09-17. Product training evidence absent.',
 'RATIONALE':'Agent memo 2026-09-18 proposes higher initial guaranteed rate. Alternatives recorded: retain existing contract to avoid surrender cost and preserve guarantee; defer transaction until home-repair liquidity resolved. No determination supplied on lost benefits beyond the existing 3.5% guarantee.',
 'RULE':'Reviewed institution-only applicability record 2026-09-18: state-sales-standard applies to fixed-annuity/insurance-agent for this synthetic checklist; state-replacement applies due to surrender funding. No assertion that this establishes enacted state requirements.'})
}
for key,(skill,request,raw) in cases.items():
 d=root/key;d.mkdir(exist_ok=True);(d/'request.txt').write_text(request+'\n');(d/'raw-source.json').write_text(json.dumps(raw,indent=2)+'\n');(d/'design.json').write_text(json.dumps({'skill':skill,'designed_before_native_code_read':True,'synthetic':True,'as_of':'2026-09-18'},indent=2)+'\n')
(root/'cases.json').write_text(json.dumps({k:v[0] for k,v in cases.items()},indent=2)+'\n')
