from pathlib import Path
import hashlib,json,datetime
root=Path.cwd(); out=Path('/tmp/fsi-final-existing-acceptance'); results=[]
paths=[('docs/payments/validation/source-manifest.json','source'),('docs/payments/phase2-validation/source-manifest.json','source'),('docs/payments/phase2-validation/artifact-manifest.json','artifact'),('docs/payments/phase3-validation/source-manifest.json','source'),('docs/payments/phase3-validation/artifact-manifest.json','artifact'),('docs/payments/phase4-validation/source-manifest.json','source'),('docs/payments/phase4-validation/artifact-manifest.json','artifact'),('docs/insurance/validation/source-manifest.json','source'),('docs/insurance/phase2-validation/source-hashes.json','source'),('docs/insurance/phase2-validation/artifact-hashes.json','artifact'),('docs/insurance/phase3-validation/source-hashes.json','source'),('docs/insurance/phase3-validation/artifact-hashes.json','artifact')]
for rel,kind in paths:
 p=root/rel; d=json.loads(p.read_text()); d=d.get('files',d); base=root if kind=='source' else p.parent
 assert all(isinstance(v,str) and len(v)==64 for v in d.values()),p
 diff=[];matches=0
 for target,want in d.items():
  f=base/target; got=hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else None
  if got!=want: diff.append({'path':target,'expected':want,'actual':got})
  else:matches+=1
 results.append({'manifest':rel,'kind':kind,'entries':len(d),'matches':matches,'differences':diff})
 print(rel,len(d),'matches',matches,'diffs',len(diff))
 if kind=='artifact' or ('phase4' in rel) or ('insurance/phase3' in rel):print([e['path'] for e in diff])
(out/'historical-manifest-audit.json').write_text(json.dumps({'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifests':results},indent=2)+'\n')
