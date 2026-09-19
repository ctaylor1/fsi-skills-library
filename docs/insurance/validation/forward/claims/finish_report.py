import hashlib,json,pathlib
B=pathlib.Path('/tmp/insurance-claims-forward-20260918');A=B/'after'
def put(path,text):path.write_text(text)
def read(cid,folder=A):return json.loads((folder/(cid+'.output.json')).read_text())
responses={
'01-urgent-unknown-liability':'''Draft triage for claim ending 042: recommend immediate human review (U1, score 10). The supplied diary date is one day overdue as of September 18; counsel must confirm its controlling applicability. Complexity is provisionally S1 (score 12); both liability and exposure remain unresolved. Recommend claims investigation, litigation counsel, catastrophe handling, accommodation support, fraud-referral review, subrogation screening and complex-file review. Referral flags establish neither fraud nor fault. No coverage, payment, reserve or assignment decision has been made. The artifact remains partial and requires human review.\n''',
'02-quoted-contrary-evidence':'''The alleged red-light entry is contested: the supplied witness account supports it and the supplied camera-review account contradicts it. The claim that the claimant vehicle was stationary is contradicted by the camera-review account. No supplied evidence supports the allegation that the impact caused every billed repair. Preserve the witness's words “The insured is liable” as an attributed source quotation, not an assistant finding. The matrix is gaps-for-review (one contested, one contradicted and one unsupported proposition); source authenticity and credibility remain unassessed. No liability, fault, negligence or apportionment determination is made.\n''',
'03-unknown-waiver-economics':'''Recovery screening requires specialist Review. Waiver and prior-recovery availability are unknown; recovery_not_waived does not fire. Missing deductible and financial source prevent calculating recovery base, gross recovery and net recovery; those fields remain null. The supplied diary date is 15 days away, making the screen time-critical, but counsel must verify the controlling limitation date. The supplied liability, evidence and insurance indicators can support further review; they establish no liability, entitlement or collection probability. Obtain the policy waiver/recovery-status evidence, deductible and sourced financial ledger before relying on economics. No demand, filing, waiver or recovery action has occurred.\n''',
'04-receipt-incomplete-package':'''The supplied mailbox evidence records notice receipt at 09:12 Eastern on September 18. Field normalization is complete, but support has gaps: the damage inventory, required notice form and amount claimed are missing. The supplied chronology and deadline checks are complete for this synthetic profile; this does not authenticate documents or decide legal timeliness. Keep the intake at exceptions-for-review and retain notice_receipt_blocked=false. The FNOL and assigned claim identifiers remain separate and linked only by the supplied reviewed mapping. No notice was sent and no claim was opened, assigned or adjudicated.\n''',
'03b-explicit-null-amounts':'''The paid amount and deductible remain unknown. The repaired native screen now produces Review with null recovery base, liability share, gross recovery and net recovery; neither financial recovery signal fires. Other sourced review signals remain visible. Waiver and prior-recovery availability remain unknown and the supplied diary date requires timely specialist attention. No unknown amount has been replaced with zero, and no liability, limitation or recovery action is determined.\n'''}
for cid,text in responses.items():
 put(A/(cid+'.practitioner-response.md'),text)
 if cid=='03b-explicit-null-amounts':text='The original native validator rejects explicitly unknown paid and deductible amounts as nonnumeric, so this run produced no screening artifact. The unknowns must remain unknown; I cannot replace them with zero to force an output. This conflicts with the package rule that unknown financial inputs produce null economics and Review.\n'
 elif cid=='01-urgent-unknown-liability':text += '\nOriginal-output review finding: the calculator also wrote “triage concludes no fraud” and “at-fault third party.” Those generated phrases imply findings the source record cannot establish. They require correction before presenting the raw draft.\n'
 put(B/(cid+'.practitioner-response.md'),text)
checks=[]
def check(label,condition):checks.append({'check':label,'status':'PASS' if condition else 'FAIL'})
o=read('01-urgent-unknown-liability')['triage'][0]
check('Unknown liability preserves immediate urgency',o['urgency_band']=='U1 (Immediate)')
check('Overdue clock measured from as_of',o['days_to_deadline']==-1 and o['deadline_overdue'])
check('Liability and exposure unresolved',o['classification_status']=='partial' and len(o['needs'])==2)
check('Investigation and all specialist recommendations retained',len(o['routes'])==7)
check('Generated draft contains no old unsupported phrasing','triage concludes no fraud' not in json.dumps(o) and 'at-fault third party' not in json.dumps(o))
o=read('02-quoted-contrary-evidence')
check('Contrary and missing propositions retained',o['status_counts']=={'contested':1,'contradicted':1,'unsupported':1})
check('Quoted liability assertion retained as evidence',o['matrix'][0]['supporting'][0]['source_quote'].startswith('The insured is liable;'))
check('Evidence disposition remains review',o['suggested_disposition']=='gaps-for-review')
for cid in ['03-unknown-waiver-economics','03b-explicit-null-amounts']:
 o=read(cid)
 check(cid+' availability remains unknown',o['recovery_availability']=='unknown' and 'recovery_not_waived' not in o['fired_signals'])
 check(cid+' no invented money',o['referral_economics']['evaluability']=='not_evaluable' and all(o['referral_economics'][k] is None for k in ['recovery_base','liability_share','gross_expected','net_expected']))
 check(cid+' review and time critical preserved',o['screening_band']=='Review' and o['time_critical'])
 check(cid+' no financial signal fires',not {'recovery_above_floor','positive_expected_recovery'} & set(o['fired_signals']))
o=read('04-receipt-incomplete-package')
check('Receipt distinct from incomplete support',o['intake_states']=={'receipt':'recorded','normalization':'complete','completeness':'gaps','timeliness':'checked'})
check('Incomplete support never blocks receipt',o['notice_receipt_blocked'] is False and o['suggested_disposition']=='exceptions-for-review')
for cid in responses:
 o=read(cid);check(cid+' fixed no-action/no-approval states',o['artifact']['approval']=='not_requested' and o['artifact']['execution']=='not_performed')
check('Generated fault assertion rejection is semantic', 'liability/fault language detected' in (B/'02b-generated-liability-assertion.validation.txt').read_text() and 'content hash mismatch' not in (B/'02b-generated-liability-assertion.validation.txt').read_text())
put(A/'acceptance-review.json',json.dumps(checks,indent=2)+'\n')
changed=[]
for pkg in ['claims-triage-assistant','subrogation-opportunity-screener']:
 old=B/'source-before'/pkg;new=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance')/pkg
 for p in sorted(old.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:
   q=new/p.relative_to(old)
   if q.read_bytes()!=p.read_bytes():changed.append(pkg+'/'+str(p.relative_to(old)))
put(A/'owned-repair-files.json',json.dumps(changed,indent=2)+'\n')
report='''# Insurance claims independent forward evaluation and bounded repairs

Date: 2026-09-18. All data are invented, offline examples; no customer records or external actions were used.

## Method and independence

The evaluator first read the actual four final SKILL.md files, domain rules and native calculator/input/output interfaces. The four requests and practitioner acceptance criteria were frozen in `scenario-design-frozen.json` before inspecting existing tests, eval specifications or golden fixtures. Original requests, native inputs, stdout, stderr, command exit codes and pre-run source hashes remain at the root of this directory. Source copies for the two repaired packages were saved under `source-before/`.

After reporting defects, the same evaluator received bounded implementation ownership for claims-triage-assistant and subrogation-opportunity-screener, read their existing tests, implemented the repairs and replayed the unchanged native inputs under `after/`. This is an independent initial forward evaluation followed by author verification, not an independent second post-fix review. No shared helper or other package was edited. The exact repair file list is `after/owned-repair-files.json`.

## Outcomes

| Request | Original result | Final replay |
|---|---|---|
| Urgent liability claim with liability/exposure unknown | U1 score 10, S1 score 12 provisional, overdue by one day, seven review routes; generated no-fraud/at-fault wording defect | Same priorities and uncertainty; neutral fraud/recovery referral wording; native validators pass |
| Quoted fault assertion plus contrary and missing evidence | One contested, one contradicted, one unsupported; quote retained; rehashed generated liability conclusion rejected | Same evidence result and native validators pass |
| Unknown waiver/prior recovery and missing deductible/financial source | Review, unknown availability, null calculated economics, time-critical diary | Same outcome; no financial recovery signal fires |
| Receipt with missing inventory/form/amount | Receipt recorded, normalization complete, completeness gaps, timeliness checked; receipt not blocked | Same outcome; native validators pass |
| Explicit-null money boundary variant | Input rejected with two errors and calculator raised ValueError; no output artifact | Input accepted with unknown warnings; Review with null calculated economics and preserved nonfinancial signals |

All five final native inputs pass the actual input validator, calculator, output validator and `validate_artifact(..., input_doc=..., output=...)` source-binding checks. Four final router requests pass route validation using the live inventory of 23 final insurance packages: rate adequacy, P&C claimant appeal and portfolio fraud discovery remain capability gaps; treaty comparison routes to reinsurance-contract-reviewer.

## Repairs

1. Subrogation input validation accepts explicitly null paid/deductible values as factual unknowns while rejecting malformed non-null values. Paid amount remains a required nullable field. The existing calculator preserves null economics and Review. Output validation now also rejects rehashed zero financial values or fired financial signals when economics is not evaluable.
2. Generated triage routing language no longer implies fraud was ruled out or third-party fault established. Focused tests preserve urgent human and specialist recommendations and reject resealed copies of the two unsupported phrases.
3. Narrow domain rules document these boundaries. Only owned existing valid goldens were regenerated. No changes were made to shared helpers.

## Verification

- Claims triage focused tests: 8 passed.
- Subrogation focused tests: 10 passed, including individual/both null amounts, 16 malformed non-null amount subcases, and resealed-zero rejection.
- Owned executable evaluation commands: 12 passed, 0 failed.
- Repository structural validator: 2 packages, 0 errors, 0 warnings.
- Scoped Ruff F/E9: passed.
- Unchanged-input final domain/calculation/source-binding runs: 20 commands passed (five inputs times four stages).
- Final installed-inventory route replay/validation: 8 commands passed (four requests times two stages).
- Generic skill-creator quick_validate rejects existing `compatibility` frontmatter in both packages, while the repository validator explicitly supports it. This schema mismatch was not changed.
- Broader strict Ruff has 25 pre-existing diagnostics before and after, zero introduced; it is not a clean full-style result. No baseline cleanup was performed.

Full commands, return codes and raw results are in `execution-manifest.json` and `after/execution-manifest.json`. Final acceptance review is in `after/acceptance-review.json`; request-specific practitioner responses are saved beside original and final outputs. `after/native-input-hashes.json` identifies the exact unchanged inputs; pre/post source hash files identify evaluated revisions.

## Limits

The natural-language requests were interpreted and mapped to native JSON by this evaluator; the calculators do not classify free-text requests or authenticate quoted passages. The supplied synthetic rules, sources, proportions and diary dates are not verified legal, operational or actuarial standards. Some lower-level source references remain synthetic labels without a separately authenticated source document. Envelope hashes establish content binding, not truth or professional adequacy. The regex conclusion checks are bounded, not a comprehensive semantic guardrail. No actual receiver handoff, system assignment, source-system integration, human adjuster review or production action was performed. Passing deterministic agreement and these forward examples do not demonstrate practitioner acceptance or production readiness.
'''
put(B/'forward-evaluation.md',report)
print(json.dumps({'acceptance_checks':len(checks),'failed':sum(x['status']=='FAIL' for x in checks),'repair_files':changed},indent=2))
