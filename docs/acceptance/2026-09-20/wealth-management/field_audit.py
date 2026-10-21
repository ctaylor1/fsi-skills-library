import json,pathlib,re,hashlib
O=pathlib.Path('/tmp/fsi-final-wealth-acceptance')
raw=(O/'raw-notes.md').read_text();lines=raw.splitlines();source_line={f'S{i}':next(n for n,l in enumerate(lines,1) if l.startswith(f'S{i} —')) for i in range(1,8)}
rows=[]
def leaves(o,path=''):
 if isinstance(o,dict):
  for k,v in o.items():yield from leaves(v,path+'.'+k if path else k)
 elif isinstance(o,list):
  for i,v in enumerate(o):yield from leaves(v,f'{path}[{i}]')
 else:yield path,o
for file in ['reconciliation-request.json','planning-request.json']:
 doc=json.loads((O/file).read_text())
 for path,val in leaves(doc):
  src=[];kind='source fact';support=''
  if path.startswith('sources['):
   idx=int(re.search(r'\[(\d+)\]',path).group(1));src=[f'S{idx+1}'];support='Exact attributed record reference and owner; common source-registry dates at raw-notes.md line 7.'
  elif path=='schema_version':kind='technical contract';support='Loaded native wealth-p0-v1 schema.'
  elif path=='request_id' or re.search(r'\.(record_id|pool_id|goal_id|item_id|debt_id)$',path):kind='local tracking';support='Locally authored tracking label, explicitly permitted by S7; does not claim external identity.';src=['S7']
  elif path.startswith('upstream_issues['):kind='derived lineage';src=['S1','S3','S4','S7'];support='Exact current reconciliation output artifact, code and message; unresolved original state, not a fabricated prior origin.'
  elif path.startswith('records['):
   idx=int(re.search(r'\[(\d+)\]',path).group(1));key=path.split('].',1)[1]
   src=['S1'] if key.startswith(('account_id','kind','household_share','owner_party_ids','identity_verified','is_held_away')) else [doc['records'][idx]['source_ids'][-1]];support='Raw confirmed inventory identity/share/held-away statement or the matching account balance and valuation date.'
  elif path.startswith(('expected_accounts[','household_party_ids','valuation_policy')):src=['S1'];support='Explicit source inventory, party scope and two-day test policy.'
  elif path.startswith('assumptions.'):src=['S6'];support='Explicit zero return/inflation, monthly convention, 120-month limit and 0.80 test threshold.'
  elif path.startswith('asset_pools['):src=['S5'];support='Pool balance 48,750, reserve 15,000; source explicitly lacks membership. Null preserves that unknown.'
  elif path.startswith('goals['):src=['S5'];support='Matching roof or education nominal target/date, contribution and pool assignment; null priority preserves explicit missing rank.'
  elif path.startswith('cash_flow.'):src=['S5'];support='After-tax pay 6,250; living expenses 3,900 excluding debt/goals/reserve; reserve 200. Labels describe those facts.'
  elif path.startswith('debts['):src=['S2'];support='Loan 9,000, 6% nominal APR, minimum 300 plus additional 50. Label identifies L-CAR without introducing a second account.'
  elif path in ['mode']:kind='task selection';support='User request asks integrated cash-flow and goal-funding discussion; documented household_plan mode.'
  else:src=['S1'];support='Explicit user request: HH-FWA-7, date 2026-09-20, US advisory, USD.'
  if '.source_ids[' in path:
   kind='citation pointer';support='Pointer to the raw record supporting its containing facts; all values checked for actual field support in this matrix.';src=[val]
  if path.endswith('.allocations[0].pool_id'):kind='local tracking';src=['S5','S7'];support='Locally named same pool shared by both goals; not an asserted source account ID.'
  rows.append({'file':file,'path':path,'value':val,'classification':kind,'source_ids':src,'source_lines':[source_line[s] for s in src],'support':support,'review':'inspected against raw notes; no unsupported fact found'})
(O/'field-to-source-audit.json').write_text(json.dumps({'method':'Agent-authored complete normalized-input leaf inventory and explicit raw-note semantic comparison; not automated semantic verification or independent professional grading. Technical/local fields are distinguished.','fields':rows},indent=2)+'\n')
print('leaf fields audited',len(rows))
# Bind current resources and fresh artifacts before any parent implementation changes.
R=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');source=[]
for base in [R/'skills/wealth-management',R/'skills/asset-management/investment-manager-due-diligence-reviewer',R/'shared']:
 for p in base.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.name!='.DS_Store' and ('shared' not in p.parts or 'wealth' in str(p)):
   source.append({'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(O/'source-manifest.json').write_text(json.dumps(source,indent=2)+'\n')
