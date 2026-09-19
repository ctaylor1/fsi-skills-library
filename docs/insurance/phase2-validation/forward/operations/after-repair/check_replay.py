import json,pathlib,hashlib
R=pathlib.Path('/tmp/insurance-p2-forward-operations');A=R/'after-repair';repo=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
# Replay the original 32 independent expectations without altering them or the saved script.
original=(R/'independent_checks.py').read_text().split("(R/'independent-checks.json')")[0]
original=original.replace("R/k/'native-output.json'","R/'after-repair'/k/'native-output.json'")
namespace={};exec(compile(original,str(R/'independent_checks.py'),'exec'),namespace)
checks=namespace['checks']; original_count=len(checks);check=namespace['check'];get=namespace['get']
p=get('policy')['results']['proposed_changes'][0]
check('policy','requested_before retains conflicting original','10 Main St',p['requested_before'])
check('policy','current before is known',True,p['before_known'])
check('policy','conflict explicitly remains false-match',False,p['before_matches_request'])
check('policy','current policy source attribution',['POL'],p['policy_source_refs'])
check('policy','request source attribution retained',['REQ'],p['source_refs'])
check('policy','case still requires review','needs-review',get('policy')['status'])
a=get('delegation');b=a['results']['bordereaux_checks'][0]
check('delegation','report uses own amount basis','written-premium',b['amount_basis'])
check('delegation','report retains USD','USD',b['currency'])
check('delegation','report retains period end','2026-08-31',b['period_end'])
check('delegation','known report exception rather than unknown','observed-exception',b['status'])
check('delegation','no fictitious data gaps remain','needs-review',a['status'])
check('delegation','authority still not granted',False,a['results']['authority_granted'])
check('delegation','aggregate overrun specifically reported',True,any(f['code']=='aggregate-limit' and 'exceeds' in f['message'] and '60000' in f['message'] for f in a['findings']))
for key in ['billing','producer','placement','life']:
 before=json.loads((R/key/'native-output.json').read_text())
 check(key,'native results unchanged from first review',before['results'],get(key)['results'])
# Check published topic interface against the vocabulary used to map the unchanged evidence.
life_schema=(repo/'skills/insurance/life-annuity-sales-reviewer/references/schema.md').read_text()
topics=['insurance-needs','financial-objectives','liquidity-needs','funding-source','financial-capacity','age','time-horizon','risk-tolerance','financial-experience','tax-status','charges','surrender-terms','guarantees','non-guaranteed-elements','restrictions','death-benefit','compensation-and-conflicts','disclosures-and-training','annuitization-options','riders','premium-obligations','coverage-duration','existing-values','existing-benefits','existing-charges','new-charges','lost-guarantees','new-surrender-period','replacement-rationale','retain-or-modify-alternative','replacement-disclosures']
check('documentation','all 31 life topic strings published',[],[x for x in topics if f'`{x}`' not in life_schema])
policy_schema=(repo/'skills/insurance/insurance-policy-transaction-packager/references/source-map.md').read_text()
check('documentation','policy line enum published',True,all(f'`{x}`' in policy_schema for x in ['pc','life','annuity']))
check('documentation','policy conflict fields explained',True,all(x in policy_schema for x in ['requested_before','before_matches_request','policy_source_refs','before_known']))
for key,path in [('life','life-annuity-sales-reviewer/references/schema.md'),('policy','insurance-policy-transaction-packager/references/source-map.md'),('delegation','insurance-delegated-authority-reviewer/references/schema.md')]:
 (A/key/'reviewed-schema.md').write_bytes((repo/'skills/insurance'/path).read_bytes())
(A/'independent-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
summary=dict(original_checks=original_count,original_checks_passed=sum(x['pass_'] for x in checks[:original_count]),repair_and_documentation_checks=len(checks)-original_count,all_checks=len(checks),all_checks_passed=sum(x['pass_'] for x in checks),failures=[x for x in checks if not x['pass_']])
(A/'check-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
# Update practitioner delivery separately, never edit the original memos.
for key in json.loads((R/'cases.json').read_text()):
 s=(R/key/'practitioner-response.md').read_text()
 if key=='policy':
  s=s.replace('Native-output defect: proposed_changes.before repeats 10 Main St, although the current policy remains 12 Main St and the discrepancy is flagged. A reviewer should use the current/source/request distinction above, not copy that native row as an authoritative before/after instruction.','The repaired native change table records current before=12 Main St from POL, separately retains requested_before=10 Main St from REQ, and flags before_matches_request=false. This correctly preserves the unresolved conflict in the draft; it does not adjudicate the requested change.')
 if key=='delegation':
  s=s.replace('Native result: needs-data; substantive authority result: aggregate exception.','Native result: needs-review; substantive authority result: aggregate exception.')
  s=s.replace('The native method flags lateness but suppresses this difference because the agreement authority basis is insured limit. That restriction conflates authority-limit units with report units; the above difference is independently calculated from comparable report amounts and must remain separate from insured-limit capacity.','The repaired native method reports that -249.50 difference on written-premium basis, retains the period and USD currency, and flags the late/out-of-balance report. This agrees with the independent calculation and remains separate from insured-limit authority capacity.')
  s=s.replace('Native aggregate wording also says a complete ledger is needed although one was supplied; the problem is insufficient capacity, not an absent ledger.','The repaired aggregate finding now states the 60000 overrun explicitly and does not misdescribe the complete ledger as missing.')
 (A/key/'practitioner-response.md').write_text(s+'\nAfter-repair replay uses the unchanged original native input; identity evidence is ../unchanged-input-evidence.json.\n')
