import pathlib,zipfile,json,hashlib,collections
R=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');O=pathlib.Path('/tmp/fsi-final-wealth-acceptance');D=R/'docs/wealth-management/p4/results';idx=json.loads((D/'artifact-index.json').read_text());rows=[];failures=[];all_review_rows=[]
for e in idx['experiments']:
 p=D/e['file'];row={'file':e['file'],'archive_sha256_matches':hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'],'archive_bytes_matches':p.stat().st_size==e['bytes'],'snapshots_compared':0,'current_file_differences':[],'model_identity_counts':{},'scores':{}}
 with zipfile.ZipFile(p) as z:
  m=json.loads(z.read('manifest.json'));row['manifest_hash_matches_index']=m['manifest_sha256']==e['manifest_sha256'];row['snapshot_hash_matches_index']=m['snapshot_sha256']==e['snapshot_sha256']
  for name in z.namelist():
   if name.startswith('frozen_snapshot/packages/') and not name.endswith('/'):
    rel=name.removeprefix('frozen_snapshot/packages/');slug,tail=rel.split('/',1);candidate=list((R/'skills').glob('*/'+slug+'/'+tail));row['snapshots_compared']+=1
    if len(candidate)!=1 or candidate[0].read_bytes()!=z.read(name):row['current_file_differences'].append({'archive_path':name,'current_paths':[str(x.relative_to(R)) for x in candidate]})
  for n in z.namelist():
   if n.startswith('runs/') and n.endswith('.json'):
    run=json.loads(z.read(n));av=run['generator']['model']['availability'];row['model_identity_counts'][av]=row['model_identity_counts'].get(av,0)+1
   if n.startswith('reviews/') and n.endswith('.json'):
    rev=json.loads(z.read(n));condition='without-skill' if '--without-skill--' in n else 'with-skill';scores=row['scores'].setdefault(condition,collections.Counter());scores['runs']+=1;scores['all_pass_runs']+=all(x['verdict']=='pass' for x in rev['items'])
    for item in rev['items']:
     scores[item['verdict']]+=1;all_review_rows.append({'archive':p.name,'run_id':rev['run_id'],'item':item['item_id'],'verdict':item['verdict'],'rationale':item['rationale']})
     if item['verdict']!='pass': failures.append({'archive':p.name,'review':n,**item})
 rows.append(row)
(O/'archive-audit.json').write_text(json.dumps(rows,indent=2)+'\n');(O/'all-item-review-index.json').write_text(json.dumps(all_review_rows,indent=2)+'\n');(O/'historical-failed-items.json').write_text(json.dumps(failures,indent=2)+'\n')
for row in rows:print(json.dumps(row,indent=2))
print('total decisions',len(all_review_rows),'failed',len(failures))
