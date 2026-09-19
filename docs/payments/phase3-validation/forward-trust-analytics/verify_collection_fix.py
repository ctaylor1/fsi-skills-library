from pathlib import Path
import json,subprocess,hashlib,copy
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
D=Path('/tmp/payments-phase3-forward-trust-analytics')
T=D/'final-fix-verification';T.mkdir(exist_ok=True)
P=R/'skills/payments/bank-payment-workflow-designer'
py='/tmp/fsi-p0-venv/bin/python'
tracked=list((P/'scripts').glob('*.py'))+list((P/'references').glob('*'))+[P/'SKILL.md']
tracked=[p for p in tracked if p.is_file() and not p.name.startswith(('test','regression'))]
def hashes():return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
before=hashes();commands=[];assertions=[]
def check(label,cond):assertions.append({'assertion':label,'passed':bool(cond)});assert cond,label
cases={'unchanged-conflicting-response-id':D/'collection-conflicting-response-id.json','unchanged-valid-response':D/'collection-base.json'}
base=json.loads((D/'collection-base.json').read_text())
for name,value in [('malformed-response-list',[]),('malformed-response-string','bad'),('invalid-response-id-object',{'response_id':{'bad':'id'},'decision':'accept'}),('empty-response-id',{'response_id':'','decision':'accept'})]:
 doc=copy.deepcopy(base);doc['data']['requests'][0]['payer_response']=value
 path=T/(name+'.json');path.write_text(json.dumps(doc,indent=2)+'\n');cases[name]=path
for name,path in cases.items():
 valid=name=='unchanged-valid-response'
 for phase,script in [('input','validate_collection_input.py'),('calculate','review_collection.py')]:
  argv=[py,'-B',str(P/'scripts'/script),str(path)];proc=subprocess.run(argv,capture_output=True,text=True)
  stdout=T/(name+'-'+phase+'.stdout');stderr=T/(name+'-'+phase+'.stderr');stdout.write_text(proc.stdout);stderr.write_text(proc.stderr)
  commands.append({'case':name,'phase':phase,'argv':argv,'exit':proc.returncode,'stdout':str(stdout.relative_to(D)),'stderr':str(stderr.relative_to(D))})
  check(name+'/'+phase+' exit',proc.returncode==(0 if valid else 1));check(name+'/'+phase+' clean JSON',isinstance(json.loads(proc.stdout),dict));check(name+'/'+phase+' no traceback','Traceback' not in proc.stderr)
  if valid and phase=='calculate':
   op=T/(name+'-output.json');op.write_text(proc.stdout)
   argv=[py,'-B',str(P/'scripts/validate_collection_output.py'),str(op),'--input',str(path)];p2=subprocess.run(argv,capture_output=True,text=True)
   (T/(name+'-output-check.stdout')).write_text(p2.stdout);(T/(name+'-output-check.stderr')).write_text(p2.stderr);commands.append({'case':name,'phase':'output','argv':argv,'exit':p2.returncode});check('unchanged valid source binding',p2.returncode==0)
   tampered=json.loads(proc.stdout);tampered['result']['requests'][0]['payment_authorized']=True;tp=T/'tampered-authority-output.json';tp.write_text(json.dumps(tampered,indent=2)+'\n')
   argv=[py,'-B',str(P/'scripts/validate_collection_output.py'),str(tp),'--input',str(path)];p2=subprocess.run(argv,capture_output=True,text=True)
   (T/'tampered-authority-check.stdout').write_text(p2.stdout);(T/'tampered-authority-check.stderr').write_text(p2.stderr);commands.append({'case':'tampered-authority','phase':'output','argv':argv,'exit':p2.returncode});check('tampered authority rejected',p2.returncode==1)
after=hashes();check('source stable through verification',before==after)
for name,data in [('commands',commands),('assertions',assertions),('source-hashes-before',before),('source-hashes-after',after)]: (T/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'calls':len(commands),'assertions':len(assertions),'passed':sum(a['passed'] for a in assertions),'source_files':len(before)},indent=2))
