from pathlib import Path
import json,hashlib,subprocess
P=Path('/tmp/insurance-p2-forward-life');rows=[];native=0;numeric=0
for p in sorted(P.iterdir()):
 if not p.is_dir():continue
 s=json.loads((p/'status.json').read_text());design=json.loads((p/'design-status.json').read_text())
 assert hashlib.sha256((p/'raw-source.md').read_bytes()).hexdigest()==design['raw_source_sha256']
 for cf in ['commands.json','same-day-commands.json']:
  if not (p/cf).exists():continue
  c=json.loads((p/cf).read_text());assert all(x['returncode']==0 for x in c);native+=len(c)
 for mf in ['source-hashes.json']:
  for x in json.loads((p/mf).read_text()):assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
 numeric+=s['independent_numeric_checks'];rows.append({'package':p.name,**s})
cp=subprocess.run(['/tmp/fsi-p0-venv/bin/python',str(P/'check_arithmetic.py')],capture_output=True,text=True)
assert cp.returncode==0
(P/'independent-check-command.json').write_text(json.dumps(dict(command=['/tmp/fsi-p0-venv/bin/python',str(P/'check_arithmetic.py')],returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr),indent=2)+'\n')
summary={'packages':5,'fresh_original_cases':5,'separately_sourced_variants':1,'native_cli_checks':native,'native_cli_checks_passed':native,'independent_arithmetic_comparisons':numeric,'independent_arithmetic_passed':numeric,'package_test_or_eval_fixtures_read':False,'raw_source_hashes_unchanged_from_case_design':True,'source_and_artifact_hash_readback':'pass','findings':[{'package':'life-annuity-contract-service-reviewer','type':'documentation/usability','severity':'minor','summary':'Exact same-day account valuation requirement absent from source schema and domain method docs; generic failure does not identify date mismatch. Original scenario null; distinct same-day variant calculates correctly.'}],'cases':rows}
(P/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(P/'README.md').write_text('''# Independent fresh insurance forward evaluation

Five original synthetic practitioner requests were designed and raw evidence frozen before implementation logic was examined. No packaged eval/test/golden fixtures or prior audits were read. All repository interactions were read-only apart from ordinary interpreter caches; evidence was saved under this temporary directory.

## Results

- 18 of 18 native CLI checks passed across five original cases and one separately sourced same-day valuation variant.
- 26 of 26 independent arithmetic comparisons passed; those checks import no package logic.
- Four original cases delivered their requested bounded arithmetic with correct evidence/workflow states. The original annuity case returned a null value scenario because its account value preceded review by one day; the package requires exact same-day values. The documentation and generic gap finding do not explain that restriction. The original source was retained, and a distinct sourced variant verified the arithmetic.
- All cases retained human review and no-action boundaries. This is a bounded synthetic forward evaluation, not source authentication or professional acceptance.

Each package directory contains `request.md`, frozen `raw-source.md`, `input.json`, `actual-output.json`, native validation outputs, `commands.json`, `response.md`, `mapping-notes.json`, `independent-arithmetic.json`, `status.json`, and `source-hashes.json`. The service package also contains its original-date finding and separate same-day supplement/input/output/checks. `summary.json` records readback and counts. Source hashes verify content consistency only.

## Package-specific observations

| Package | Original output status | Observed result |
|---|---|---|
| life-underwriting-reviewer | needs-data | Pending income evidence retained; 20-times disclosed ratio and literal disclosure conflict referred. |
| life-annuity-contract-service-reviewer | needs-data | Consent gap retained; undocumented exact-date requirement suppressed original scenario; distinct same-day variant yielded $41,250 proceeds and $130,000 account value. |
| life-benefit-claim-reviewer | needs-data | Wrong-insured certificate rejected; disputed designation prevented allocation; before-entitlement bridge $739,895.50. |
| reinsurance-program-analyzer | ready-for-review | Four supplied program/scenario pairs reconciled; sequential inuring and aggregate exhaustion matched independent arithmetic. |
| reinsurance-contract-administration-reviewer | needs-review | Total roll-forward tied at $268,750 while +$5,000/-$5,000 claim breaks remained; collateral and notice exceptions retained. |

No production source, live customer case, execution flow, or external professional review was exercised.
''')
print(json.dumps({k:v for k,v in summary.items() if k!='cases'},indent=2))
