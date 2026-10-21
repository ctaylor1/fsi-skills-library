from pathlib import Path
from decimal import Decimal
import json,subprocess,sys
root=Path('/tmp/insurance-p5-forward/pricing-network')
repo=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance')
for case in ('pricing-normal','pricing-adverse','network-normal','network-adverse'):
 p=root/case; pricing=case.startswith('pricing'); name='health-plan-pricing-reviewer' if pricing else 'health-provider-network-reviewer'
 doc=json.loads((p/'native-input.json').read_text()); old=doc['context']['capacity']; new='health-pricing-review' if pricing else 'health-network-review'
 (p/'capacity-normalization.json').write_text(json.dumps({'source_role_preserved':'Fictional sponsor actuarial pricing review' if pricing else 'Fictional sponsor network operations review','previous_native_label':old,'current_schema_label':new,'basis':'The current documented native capacity enum was clarified after initial authoring. Same represented party, object and raw role; no source fact or professional authority changed.'},indent=2)+'\n')
 doc['context']['capacity']=new
 (p/'native-input.json').write_text(json.dumps(doc,indent=2)+'\n')
 out=subprocess.run([sys.executable,str(repo/name/'scripts/calculate_or_transform.py'),str(p/'native-input.json')],text=True,capture_output=True,check=True)
 (p/'native-output.json').write_text(out.stdout)
 checked=subprocess.run([sys.executable,str(repo/name/'scripts/validate_output.py'),str(p/'native-output.json')],text=True,capture_output=True,check=True)
 (p/'validation.json').write_text(checked.stdout)
 with (p/'mapping.md').open('a') as f:f.write('\nFinal replay normalizes capacity to the current schema label; capacity-normalization.json preserves the prior spelling and unchanged underlying source role.\n')
outs={case:json.loads((root/case/'native-output.json').read_text()) for case in ('pricing-normal','pricing-adverse','network-normal','network-adverse')}
a=outs['pricing-normal'];assert a['status']=='ready-for-review',(a['status'],a['findings']);assert Decimal(a['results']['metrics']['conditional_premium_pmpm'])==340;assert Decimal(a['results']['metrics']['renewal_change_fraction'])==Decimal('0.0625')
a=outs['pricing-adverse'];assert a['status']=='needs-data';assert all(v is None for v in a['results']['metrics'].values())
a=outs['network-normal'];assert a['status']=='needs-review',(a['status'],a['findings']);c=a['results']['access_comparisons'][0];assert Decimal(c['member_fraction'])==Decimal('0.5');assert c['meets_supplied_threshold'] is False;assert [m['distinct_qualifying_providers'] for m in c['member_results']]==[2,1]
a=outs['network-adverse'];assert a['status']=='needs-data';assert a['results']['access_comparisons'][0]['member_fraction'] is None
for case,out in outs.items():
 doc=json.loads((root/case/'native-input.json').read_text());assert out['source_document']==doc
 assert out['action_taken'] is False and out['human_review_required'] is True and out['approval']=='not_requested' and out['execution']=='not_performed'
 assert json.loads((root/case/'validation.json').read_text())=={'errors':[],'valid':True}
(root/'review.md').write_text('''# Independent forward-test review — 2026-10-04

Scope: fresh synthetic source-mapping cases for health-plan-pricing-reviewer and health-provider-network-reviewer. Read only package SKILL.md and schema before drafting cases; no author input fixtures, tests or domain implementation were read. Each folder contains the raw source, request, native mapping, retained-output artifact and native output validation. No package edits were made by the forward tester.

## Findings

No implementation defect was observed in these four bounded cases. They exercise source mapping and the native evaluator through the documented interface. This is an independent agent forward test, not a blind human trial, real institution acceptance, evidence authentication, licensing review or statistical quality benchmark.

- Pricing normal: 125000 paid + 10000 unpaid case + 20000 IBNR minus 5000 recoveries = 150000 incurred; /600 member months = 250 base PMPM; cumulative cost factor 1.08 and utilization factor 1 give 270 projected claims PMPM. Fixed 7200/720 plus 26 PMPM yields 36 nonpremium expense. (270+36)/(1-0.08-0.02) = 340 conditional premium PMPM; compared with 320 supplied comparable current premium gives 0.0625 renewal change. Output matched every value, remained draft and did not call the descriptive ratio statutory MLR.
- Pricing adverse: raw source explicitly withholds IBNR and does not assert zero. Native null mapped directly. Result needs-data, all derived metrics and category measures null; original facts retained.
- Network normal: three provider-site records represent two distinct clinicians. For the first member both clinicians are within 10 driving miles; for the second, only clinician A qualifies despite two qualifying sites. Output counts 2 and 1, respectively: 1 of 2 members meets the supplied two-provider threshold, fraction 0.5 below the supplied 0.75 benchmark. Result needs-review; no regulatory inadequacy or licensure conclusion was asserted.
- Network adverse: source expressly supplies only five of six required measurements and flags the missing second-member/B-CENTRAL distance. No distance or nearest-provider inference was inserted. Native result needs-data and withholds derived counts/fractions/eligibility/comparison.

All four final outputs retained source_document exactly and passed native output recomputation. Action remained false; human review remained required; approval not requested and execution not performed.

## Source clarification and current-schema replay

The initial network source narrative described per-site contract and credential evidence without spelling its exact record IDs. A distinct fictional source-author clarification supplies those exact IDs. Initial inputs/outputs remain saved; final mappings explicitly cite the supplement. This is documented source clarification and a rerun, not an unchanged-input repair or inferred professional review. It changes no statuses, dates, measurements, population, completeness facts or expected results.

After package schema tightened the accepted capacity enums, the final mappings use health-pricing-review and health-network-review. Per-case capacity-normalization.json preserves the previous native spelling and actual source review role. Raw represented party, object and professional boundaries are unchanged. All final cases were replayed against the revised runtime; current output validation passed.

## Remaining acceptance limits

No real clinical/actuarial/network specialist evaluated these outputs. Real-source authenticity, private-source access, legal/program applicability, privacy/accessibility, real-model benchmark variance and production operation remain unverified. Further tests are warranted only for new changes or new failure evidence.
''')
print('Four independent final native outputs and review verified; source clarification separately preserved.')
