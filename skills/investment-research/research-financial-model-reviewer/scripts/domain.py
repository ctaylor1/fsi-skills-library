from __future__ import annotations
import ast, math, operator, importlib.util
from pathlib import Path
from analysis_contract import validate_base, number, require, rows, unique, references, finish
from native_integrity import attach_source
SKILL = 'research-financial-model-reviewer'
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}

def local(name):
    spec=importlib.util.spec_from_file_location('_reviewer_'+name,Path(__file__).with_name(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def parse(expression):
    require(isinstance(expression,str) and 0<len(expression)<=1024,'formula must be a bounded arithmetic expression')
    try: tree=ast.parse(expression,mode='eval')
    except SyntaxError as exc: raise ValueError('invalid arithmetic expression') from exc
    require(len(list(ast.walk(tree)))<=128,'formula exceeds node limit')
    for n in ast.walk(tree):
        require(isinstance(n,(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Constant,ast.Name,ast.Load,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.USub,ast.UAdd)),'only names, numeric constants and + - * / arithmetic supported')
        if isinstance(n,ast.Constant):number(n.value,'formula constant')
    return tree.body

def names(tree):return {n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}

def evaluate(node,resolve):
    if isinstance(node,ast.Constant):v=number(node.value,'constant')
    elif isinstance(node,ast.Name):v=resolve(node.id)
    elif isinstance(node,ast.UnaryOp):v=(-1 if isinstance(node.op,ast.USub) else 1)*evaluate(node.operand,resolve)
    elif isinstance(node,ast.BinOp):v=OPS[type(node.op)](evaluate(node.left,resolve),evaluate(node.right,resolve))
    else:raise ValueError('unsupported arithmetic node')
    require(math.isfinite(v),'nonfinite formula result');return v

def validate_document(doc):
    require(isinstance(doc,dict),'input must be an object')
    if doc.get('mode')=='legacy-roll-forward':
        require(set(doc)=={'mode','input'},'legacy mode accepts only mode and original input')
        errors,warnings=local('legacy_validate_input').validate(doc.get('input'))
        require(not errors,'; '.join(errors));return []
    validate_base(doc,subject_types=('issuer','security','model'))
    require(doc.get('mode')=='independent-review','explicit independent-review or legacy-roll-forward mode required')
    require(isinstance(doc.get('model_id'),str) and doc['model_id'].strip(),'model_id required')
    for k in ('currency','units','accounting_basis','consolidation_scope'):require(isinstance(doc.get(k),str) and doc[k].strip() and doc[k].lower() not in ('unknown','not-provided','unavailable'),k+' requires known supplied context')
    cells=rows(doc.get('cells'),'cells',nonempty=True);unique(cells,'cell_id','cells');ids={x['cell_id'] for x in cells}
    require(len(cells)<=5000,'cell inventory exceeds bounded scope')
    for c in cells:
        require(c['cell_id'].isidentifier(),'cell_id must be an arithmetic identifier')
        number(c.get('value'),'cell value');number(c.get('tolerance'),'cell tolerance',minimum=0)
        require(c.get('kind') in ('input','formula'),'cell kind must be input or formula')
        if c['kind']=='formula':
            require(names(parse(c.get('formula')))<=ids,'formula references unknown cell')
        else:
            require(bool(c.get('evidence_refs')),'input cell evidence required')
            references(doc,c.get('evidence_refs'),'input cell evidence')
    checks=rows(doc.get('reconciliations'),'reconciliations',nonempty=True);unique(checks,'check_id','reconciliations')
    for check in checks:
        for k in ('left','right'):require(names(parse(check.get(k)))<=ids,'reconciliation references unknown cell')
        number(check.get('tolerance'),'reconciliation tolerance',minimum=0)
    assumptions=rows(doc.get('assumptions'),'assumptions',nonempty=True);unique(assumptions,'assumption_id','assumptions')
    for a in assumptions:
        for k in ('value','lower','upper'):number(a.get(k),'assumption '+k)
        require(a['lower']<=a['upper'],'assumption lower exceeds upper')
        references(doc,a.get('evidence_refs'),'assumption evidence')
    economics=rows(doc.get('economic_checks'),'economic_checks',nonempty=True);unique(economics,'check_id','economic_checks')
    for e in economics:
        require(e.get('cell_id') in ids,'economic check references unknown cell')
        require(e.get('meaning') in ('cash-funding','debt-nonnegative','margin-range','custom-supplied-bound'),'explicit economic check meaning required')
        number(e.get('lower'),'economic lower');number(e.get('upper'),'economic upper');require(e['lower']<=e['upper'],'economic bound order invalid')
        references(doc,e.get('evidence_refs'),'economic bounds evidence')
    # Cycle detection and recomputation are part of input validity, before any verdict.
    calculate_cells(cells)
    return []

def calculate_cells(cells):
    records={r['cell_id']:r for r in cells};cache={};active=set()
    def resolve(key):
        if key in cache:return cache[key]
        require(key not in active,'circular formula dependency: '+key)
        require(len(active)<128,'formula graph dependency depth exceeds 128')
        active.add(key);c=records[key]
        v=c['value'] if c['kind']=='input' else evaluate(parse(c['formula']),resolve)
        active.remove(key);cache[key]=v;return v
    for key in records:resolve(key)
    return cache

def compute(doc):
    validate_document(doc)
    if doc.get('mode')=='legacy-roll-forward':
        old=local('legacy_calculate').compute(doc['input'])
        errors=local('legacy_validate_output').validate(old,doc['input'])
        require(not errors,'legacy parity validation failed: '+'; '.join(errors))
        return attach_source({'method_id':SKILL,'method_version':'0.1.0','mode':'legacy-roll-forward','legacy_result':old,'parity_scope':'Exact original supplied-balance continuity behavior, rounding, tolerances and fields.','authority_granted':False,'review_status':'not-requested','execution_status':'not-performed','professional_acceptance':'not-established'},doc)
    values=calculate_cells(doc['cells']);issues=[];formula_results=[]
    for c in doc['cells']:
        if c['kind']=='formula':
            residual=c['value']-values[c['cell_id']];ok=abs(residual)<=c['tolerance']
            formula_results.append({'cell_id':c['cell_id'],'formula':c['formula'],'supplied_value':c['value'],'recomputed_value':values[c['cell_id']],'residual':residual,'within_tolerance':ok})
            if not ok:issues.append('Formula residual outside tolerance: '+c['cell_id'])
    reconciliations=[]
    for c in doc['reconciliations']:
        left=evaluate(parse(c['left']),lambda n:values[n]);right=evaluate(parse(c['right']),lambda n:values[n]);residual=left-right;ok=abs(residual)<=c['tolerance']
        reconciliations.append({'check_id':c['check_id'],'left_value':left,'right_value':right,'residual':residual,'within_tolerance':ok})
        if not ok:issues.append('Reconciliation failed: '+c['check_id'])
    assumptions=[]
    for a in doc['assumptions']:
        ok=a['lower']<=a['value']<=a['upper'];assumptions.append({'assumption_id':a['assumption_id'],'within_supplied_bounds':ok,'evidence_refs':a['evidence_refs']})
        if not ok:issues.append('Assumption outside supplied bounds: '+a['assumption_id'])
    economics=[]
    for e in doc['economic_checks']:
        v=values[e['cell_id']];ok=e['lower']<=v<=e['upper'];economics.append({'check_id':e['check_id'],'meaning':e['meaning'],'recomputed_value':v,'within_supplied_bounds':ok})
        if not ok:issues.append('Economic plausibility/funding check failed: '+e['check_id'])
    return finish(doc,SKILL,{'model_id':doc['model_id'],'mode':'independent-review','formula_results':formula_results,'reconciliations':reconciliations,'assumption_results':assumptions,'economic_results':economics,'findings_count':len(issues),'model_approved':False,'scope':'Supplied arithmetic formula graph, reconciliations, evidence metadata and configured economic bounds; no workbook ingestion, source authentication or institutional sign-off.'},issues=issues,lineage=[{'formula':'Recompute formula graph independently; compare supplied cell values and configured reconciliation/economic limits.'}])
