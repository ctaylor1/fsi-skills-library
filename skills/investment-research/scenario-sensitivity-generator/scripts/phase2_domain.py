from __future__ import annotations
import math, importlib.util
from pathlib import Path
from analysis_contract import validate_base, number, require, rows, unique, references, finish
from native_integrity import canonical_hash
SKILL='scenario-sensitivity-generator'
def local(filename):
    spec=importlib.util.spec_from_file_location('_phase2_'+SKILL.replace('-','_')+'_'+filename.replace('.','_'),Path(__file__).with_name(filename));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def context(doc):
    validate_base(doc)
    require(doc.get('schema_version')=='ir-phase2/1.0','Phase2 schema_version required')
    require(doc.get('issuer_type')=='nonfinancial-corporate','supported annual operating method requires nonfinancial-corporate; no bank/insurer/REIT fallback')
    for k in ('accounting_basis','consolidation_scope'):require(isinstance(doc.get(k),str) and doc[k].strip(),k+' required')

def native_valid(doc,key):
    errors,warnings=local('validate_input.py')._validate_phase1(doc.get(key))
    require(not errors,'; '.join(errors))

def validate_document(doc):
    validate_base(doc);require(doc.get('schema_version')=='ir-phase2/1.0','Phase2 schema required')
    require(doc.get('engine')=='dcf-forecast','only explicitly bundled DCF forecast rerunner supported')
    base=doc.get('base_input');require(isinstance(base,dict),'base_input required')
    for k in ('subject','as_of','use_on','knowledge_cutoff','purpose','audience','information_barrier','sources','evidence_refs','valuation_subject'):
        require(base.get(k)==doc.get(k),'base model context mismatch: '+k)
    model=local('model_dcf.py');model.validate_document(base)
    scenarios=rows(doc.get('scenarios'),'scenarios',nonempty=True);unique(scenarios,'scenario_id','scenarios')
    require(len(scenarios)<=250,'scenario count exceeds 250')
    allowed={'wacc','terminal_growth','bridge.total_debt','bridge.cash_and_equivalents','bridge.minority_interest','bridge.preferred_equity','bridge.investments_associates'}
    for scenario in scenarios:
        overrides=scenario.get('overrides');require(isinstance(overrides,dict) and bool(overrides) and set(overrides)<=allowed,'unsupported or empty model override')
        for key,value in overrides.items():number(value,key)
        references(doc,scenario.get('evidence_refs'),'scenario assumptions')
        model.validate_document(apply_overrides(base,overrides))
    return []

def apply_overrides(base,overrides):
    import copy
    target=copy.deepcopy(base)
    for key,value in overrides.items():
        if key.startswith('bridge.'):target['bridge'][key.split('.')[1]]=value
        else:target[key]=value
    return target

def compute(doc):
    validate_document(doc);model=local('model_dcf.py');base=model.compute(doc['base_input']);scenarios=[];issues=[]
    for sc in doc['scenarios']:
        source=apply_overrides(doc['base_input'],sc['overrides']);output=model.compute(source)
        # The model is rerun from retained assumptions; no formula-only proxy substitutes for a linked method.
        model_result=output['results'];scenarios.append({'scenario_id':sc['scenario_id'],'overrides':sc['overrides'],'model_input_hash':canonical_hash(source),'enterprise_value':None if model_result is None else model_result['enterprise_value'],'equity_value':None if model_result is None else model_result['equity_value'],'value_per_share':None if model_result is None else model_result['value_per_share'],'producer_result_hash':canonical_hash(output)})
        issues.extend(output['unresolved_issues'])
    return finish(doc,SKILL,{'engine':'dcf-forecast','base_result':base['results'],'scenarios':scenarios,'method_scope':'Actual bundled DCF forecast rerun for discount-rate, terminal-growth and EV/equity bridge overrides; no integrated operating-model rerun or arbitrary engine.'},issues=issues,lineage=[{'formula':'Rerun maintained DCF forecast method independently for each explicit validated override set','model_input_hash':canonical_hash(doc['base_input'])}])
