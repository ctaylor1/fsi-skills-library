"""Question, evidence and dependency planning for a supplied research mandate."""
from analysis_contract import validate_base, number, require, rows, unique, references, finish

def validate_document(doc):
    validate_base(doc, subject_types=('issuer','security','universe','sector'))
    questions=rows(doc.get('questions'),'questions',nonempty=True); unique(questions,'question_id','questions')
    ids={q['question_id'] for q in questions}
    for q in questions:
        require(isinstance(q.get('question'),str) and bool(q['question'].strip()),'question text required')
        require(q.get('priority') in ('critical','important','optional'),'invalid question priority')
        require(q.get('decision') in ('initiate','update','monitor','defer'),'invalid decision context')
        deps=q.get('depends_on',[]); require(isinstance(deps,list) and len(deps)==len(set(deps)) and all(isinstance(x,str) and x in ids and x!=q['question_id'] for x in deps),'invalid dependency')
        require(q.get('answer_status') in ('unanswered','supplied','contradicted'),'invalid answer_status')
        if q['answer_status']=='supplied': require(isinstance(q.get('answer'),str) and bool(q['answer'].strip()),'supplied answer text required')
        references(doc,q.get('evidence_refs',[]),'question evidence')
        require(isinstance(q.get('required_evidence'),list) and all(isinstance(x,str) and x.strip() for x in q['required_evidence']),'required_evidence must be text list')
    pending={q['question_id']:set(q.get('depends_on',[])) for q in questions}; done=set()
    while pending:
        ready={k for k,v in pending.items() if v <= done}; require(bool(ready),'question dependency cycle')
        done |= ready; pending={k:v for k,v in pending.items() if k not in ready}

def compute(doc):
    validate_document(doc)
    questions={q['question_id']:q for q in doc['questions']}; pending=set(questions); ordered=[]; done=set()
    while pending:
        ready=sorted(k for k in pending if set(questions[k].get('depends_on',[])) <= done)
        ordered.extend(ready); done.update(ready); pending.difference_update(ready)
    answered={k for k,q in questions.items() if q['answer_status']=='supplied' and bool(q.get('evidence_refs'))}
    plan=[]; gaps=[]
    for key in ordered:
        q=questions[key]; blockers=[x for x in q.get('depends_on',[]) if x not in answered]
        state='contradicted' if q['answer_status']=='contradicted' else ('evidence-supplied' if key in answered else 'evidence-needed')
        if blockers: state='dependency-blocked'
        if state!='evidence-supplied': gaps.append(key+': '+state)
        plan.append({'question_id':key,'question':q['question'],'answer':q.get('answer') if key in answered else None,'priority':q['priority'],'decision':q['decision'],'state':state,'dependency_blockers':blockers,'required_evidence':q['required_evidence'],'evidence_refs':q.get('evidence_refs',[])})
    critical=[p['question_id'] for p in plan if p['priority']=='critical' and p['state']!='evidence-supplied']
    return finish(doc,'research-coverage-planner',{'execution_order':ordered,'question_plan':plan,'critical_gaps':critical,'supplied_answer_coverage':len(answered)/len(questions),'decision_readiness':'defer-for-evidence' if critical else 'analyst-review','scope':'Supplied mandate and dependency graph; evidence truth and complete coverage are not established'},issues=gaps,lineage=[{'formula':'answered questions / supplied questions','inputs':sorted(answered)}])
