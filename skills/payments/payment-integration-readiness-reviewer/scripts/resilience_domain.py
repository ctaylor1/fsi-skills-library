"""Inspect supplied version-bound negative-path artifacts for a payment architecture."""
from collections import Counter
from datetime import date
from payment_contract import stable_hash
from payment_foundation import finding

SKILL = 'payment-integration-readiness-reviewer'
MODES = {'hub', 'orchestration', 'cloud-mainframe', 'ledger', 'active-active'}
# These are this package's baseline scenarios, not a scheme certification standard.
SCENARIOS = {
 'duplicate-event': {'financial_effect_count':1,'payload_conflict_rejected':True},
 'lost-event': {'missing_event_detected':True,'reconciliation_break_opened':True},
 'delayed-event': {'late_event_retained':True,'original_identity_preserved':True},
 'out-of-order': {'state_regression_blocked':True,'ledger_balance_preserved':True},
 'crash-after-commit': {'financial_effect_count':1,'durable_result_recovered':True},
 'network-partition': {'isolated_writer_fenced':True,'financial_effect_count':1},
 'uncertain-money': {'status_checked':True,'reconciliation_performed':True,'blind_resends':0,'unresolved_outcomes_retained':True},
 'cutover-inflight': {'exactly_one_financial_owner':True,'inflight_inventory_tied_out':True},
 'rollback': {'settled_entries_preserved':True,'new_intake_rerouted_only':True,'outstanding_ownership_preserved':True},
 'recovery-support': {'reconciliation_breaks_owned':True,'support_handoff_exercised':True,'monitoring_alert_observed':True},
}


def validate(data):
    errors=[]
    for k in ('design','controls','migration'):
        if k in data and not isinstance(data[k],dict): errors.append(k+' must be an object')
    for k in ('test_artifacts',):
        if not isinstance(data.get(k,[]),list) or any(not isinstance(r,dict) for r in data.get(k,[])): errors.append(k+' must be a list of objects')
    for row in data.get('test_artifacts',[]):
        for k in ('observations','inspection'):
            if k in row and not isinstance(row[k],dict): errors.append(k+' must be an object')
        if 'steps' in row and (not isinstance(row['steps'],list) or any(not isinstance(r,dict) for r in row['steps'])): errors.append('steps must be a list of objects')
    return errors


def artifact_scope(row):
    return {k:row.get(k) for k in ('artifact_id','release_version','mode','scenario','component_scope','steps','observations','source_ids')}


def analyze(request):
    data=request['data']; findings=[]
    def gap(code,msg,row=None): findings.append(finding(code,msg,(row or {}).get('source_ids',[])))
    design=data.get('design',{}); mode=design.get('mode'); controls=data.get('controls',{}); migration=data.get('migration',{})
    if mode not in MODES: gap('mode-unsupported','Supported modules: hub, orchestration, cloud-mainframe, ledger and active-active.',design)
    for field in ('release_version','component_scope','business_flow','owner','source_ids'):
        if not design.get(field): gap('design-scope-gap','Version-specific design '+field+' required.',design)
    for field in ('financial_owner','writer_fence','fence_authority','idempotency_scope','key_retention','atomic_commit_boundary','status_authority','reconciliation_owner','ledger_invariant','source_ids'):
        if not controls.get(field): gap('control-design-gap',field+' unresolved.',controls)
    if controls.get('payload_conflict_behavior') != 'reject-conflict': gap('payload-conflict-gap','A reused idempotency key with a changed payload must reject the conflict.',controls)
    if controls.get('uncertain_outcome_strategy') not in {'status-then-reconcile','manual-reconcile-no-retry'}: gap('uncertain-money-gap','Unknown outcomes require authoritative status and reconciliation; a new key is unsafe.',controls)
    if controls.get('fenced_financial_writes') is not True: gap('writer-ownership-gap','Financial writes require explicit ownership and fencing across failover.',controls)
    if controls.get('partition_policy') not in {'fence-isolated-writer','stop-financial-writes'}: gap('partition-policy-gap','Choose an explicit partition policy that cannot leave two financial writers.',controls)
    for field in ('inflight_inventory_ref','cutover_owner','entry_gate','exit_gate','rollback_boundary','reconciliation_scope','support_owner','source_ids'):
        if not migration.get(field): gap('migration-evidence-gap',field+' unresolved.',migration)
    if migration.get('rollback_mode') != 'reroute-new-intake-preserve-effects': gap('rollback-unsafe','Application rollback must preserve completed financial effects and ownership of pending instructions.',migration)
    rows=data.get('test_artifacts',[]); counts=Counter(r.get('artifact_id') for r in rows); scenarios=Counter(r.get('scenario') for r in rows)
    assessments=[]
    for row in rows:
        reasons=[]; scenario=row.get('scenario'); observations=row.get('observations',{}); inspection=row.get('inspection',{})
        if not row.get('artifact_id') or counts[row.get('artifact_id')]>1: reasons.append('artifact identity missing or repeated')
        if scenario not in SCENARIOS: reasons.append('unsupported negative-path scenario')
        if row.get('release_version')!=design.get('release_version') or row.get('mode')!=mode or row.get('component_scope')!=design.get('component_scope'): reasons.append('artifact release/mode/component scope differs from proposed design')
        if not row.get('source_ids'): reasons.append('artifact source evidence missing')
        steps=row.get('steps',[])
        if not steps or any(not all(step.get(k) for k in ('step_id','action','observed','evidence_ref')) for step in steps): reasons.append('actual supplied test steps and observed evidence required; a pointer or pass flag is insufficient')
        stepids=[s.get('step_id') for s in steps]
        if len(set(stepids))!=len(stepids): reasons.append('test step identities repeated')
        if inspection.get('status')!='inspected' or not all(inspection.get(k) for k in ('reviewer','reviewed_on','result_ref','scope_hash')): reasons.append('inspection declaration incomplete')
        try:
            reviewed=date.fromisoformat(inspection.get('reviewed_on',''))
            if reviewed > date.fromisoformat(request['as_of']): reasons.append('inspection occurs after as_of')
        except (ValueError,TypeError): reasons.append('inspection date missing or invalid')
        if inspection.get('scope_hash')!=stable_hash(artifact_scope(row)): reasons.append('inspection not bound to this exact artifact, observations and version')
        for field,expected in SCENARIOS.get(scenario,{}).items():
            observed=observations.get(field)
            if type(observed) is not type(expected) or observed!=expected: reasons.append(field+' invariant is missing or failed')
        if row.get('claimed_result')=='pass' and reasons: gap('unsupported-pass-claim','Artifact claims pass without sufficient scoped evidence: '+str(row.get('artifact_id')),row)
        assessments.append({'artifact_id':row.get('artifact_id'),'scenario':scenario,'scope_hash':stable_hash(artifact_scope(row)),'status':'gap-or-failed' if reasons else 'supplied-artifact-inspected','observations':observations,'issues':reasons,'live_test_executed':False})
        for reason in reasons: gap('test-evidence-gap',str(row.get('artifact_id'))+': '+reason,row)
    coverage=[]
    for scenario in SCENARIOS:
        matching=[a for a in assessments if a['scenario']==scenario]
        satisfied=bool(matching) and all(a['status']=='supplied-artifact-inspected' for a in matching)
        if not satisfied: gap('negative-path-unresolved','Negative path needs complete inspected evidence: '+scenario)
        coverage.append({'scenario':scenario,'artifact_count':scenarios[scenario],'evidence_satisfied':satisfied})
    return {'result':{'module':mode,'release_version':design.get('release_version'),'design':design,'control_assessment':controls,'migration_assessment':migration,'artifact_assessments':assessments,'negative_path_coverage':coverage,'evidence_basis':'inline records inspected against explicit invariants; source identity and test execution not authenticated','go_live_authorized':False,'resilience_certified':False,'deployment_executed':False},'findings':findings,'handoffs':[{'target_skill':'payment-service-incident-investigator','reason':'Investigate operational failures and uncertain payment outcomes before closing readiness gaps.','required_inputs':['version-bound test failures and incident timeline','unique payment outcome inventory','reconciliation evidence']}], 'limitations':['This is a scoped offline artifact review, not a chaos test runner, production certification or independent source authentication. Baseline scenarios are library review criteria and cannot establish scheme or regulatory compliance.']}
