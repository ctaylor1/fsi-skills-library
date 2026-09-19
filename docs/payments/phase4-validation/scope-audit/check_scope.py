from pathlib import Path
import json,hashlib,re
from urllib.parse import unquote
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');O=Path('/tmp/payments-phase4-scope-audit')
names=['cross-border-payment-designer','wallet-and-mobile-money-program-designer','stablecoin-settlement-assessor','payment-business-model-analyzer','bank-payment-workflow-designer','payment-liquidity-and-funding-analyzer','platform-payment-flow-designer','commercial-payment-workflow-designer','payment-initiation-control-reviewer','payment-credential-authentication-reviewer','stablecoin-payment-controls-reviewer','payments-router']
files=[R/'docs/payments/ROADMAP.md',R/'docs/payments/PHASE4-IMPLEMENTATION.md',R/'shared/payments/payment_foundation.py',R/'shared/payments/agent_commerce.py']
for name in names:
 files.extend(p for p in (R/'skills/payments'/name).rglob('*') if p.is_file() and 'evals' not in p.parts and not p.name.startswith(('test','regression')) and p.suffix in {'.md','.py','.json'})
hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}
(O/'source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
links=[]
for path in files:
 if path.suffix!='.md' or not path.exists():continue
 text=path.read_text()
 for m in re.finditer(r'\[[^\]]*\]\(([^\)]+)\)',text):
  href=m.group(1).strip().strip('<>')
  if href.startswith(('https:','http:','mailto:','#')):continue
  target=unquote(href.split('#',1)[0])
  if target.startswith('/Users/'):
   resolved=Path(target)
  else:resolved=path.parent/target
  links.append({'source':str(path.relative_to(R)),'line':text.count('\n',0,m.start())+1,'href':href,'exists':resolved.exists()})
(O/'local-link-check.json').write_text(json.dumps(links,indent=2)+'\n')
summary={'packages':len(names),'hashed_files':len(hashes),'markdown_links':len(links),'broken_links':[x for x in links if not x['exists']],'payments_package_count':sum(1 for p in (R/'skills/payments').iterdir() if (p/'SKILL.md').exists())}
(O/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
