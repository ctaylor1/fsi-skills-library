"""Independent synthetic forward review. Writes only this evidence directory.

The original requests/results are historical and are never overwritten. Expectations
below were calculated independently of package functions. Native reconstruction is
an additional integrity check, not the numerical/semantic oracle.
"""
import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
NEW = {
    'asset-manager-economics-analyzer', 'investment-product-lifecycle-planner',
    'investment-distribution-planner', 'investment-client-service-preparer',
    'investment-investor-report-builder',
}
RUN = HERE / 'current-replay'
RUN.mkdir(exist_ok=True)
checks = []
commands = []


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def check(case, assertion, actual, expected, numeric=False, phase='current'):
    try:
        passed = D(str(actual)) == D(str(expected)) if numeric else actual == expected
    except Exception:
        passed = False
    checks.append(dict(case=case, phase=phase, assertion=assertion, actual=actual,
                       expected=expected, passed=passed))


def run(package, script, args, case):
    argv = [sys.executable, '-B', str(ROOT / 'skills/asset-management' / package / 'scripts' / script), *map(str, args)]
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=ROOT)
    commands.append(dict(case=case, command=argv, exit_code=proc.returncode,
                         stdout=proc.stdout, stderr=proc.stderr))
    return proc


def compute(case, package, doc):
    inp = RUN / (case + '-input.json')
    save(inp, doc)
    proc = run(package, 'calculate_or_transform.py', [inp], case)
    if proc.returncode:
        return None, inp, None
    output = json.loads(proc.stdout)
    out = RUN / (case + '-output.json')
    save(out, output)
    return output, inp, out


def expected(case, output, phase='current'):
    r = output['results']
    def eq(label, actual, value, num=False):
        check(case, label, actual, value, num, phase)
    eq('draft', output['draft'], True)
    eq('no action', output['action_taken'], False)
    eq('human review required', output['human_review_required'], True)
    eq('source truth unverified', output['source_truth'], 'unverified')
    eq('upstream issue preserved', 'UPSTREAM-REVIEW-OPEN' in output['unresolved_issues'], True)
    eq('no originals embedded', 'source_input' in output, False)
    if case == 'economics':
        eq('AUM bridge 200+30-20+10-5 + 100 =315m', r['totals']['closing_aum'], '315000000', True)
        eq('annual revenue 210m*40bps+10k+100m*20bps', r['totals']['annualized_revenue'], '1050000', True)
        eq('annual contribution 290k+100k', r['totals']['annualized_profit'], '390000', True)
        eq('scenario AUM 215m*.9*.95+10m', r['scenarios'][0]['scenario_aum'], '193825000', True)
        eq('scenario revenue 193.825m*35bps+10k', r['scenarios'][0]['annualized_revenue'], '688387.5', True)
        eq('scenario profit after10bps+370k costs', r['scenarios'][0]['annualized_profit'], '124562.5', True)
    elif case.startswith('lifecycle-'):
        e = r['economics']
        eq('annual contribution 150m*30bps-300k', e['annual_contribution'], '150000', True)
        eq('first-year contribution less200k launch cost', e['first_year_contribution'], '-50000', True)
        eq('break-even 300k/30bps', e['break_even_aum'], '100000000', True)
        eq('unknown gate blocks readiness', r['review_readiness'], 'blocked')
        eq('no lifecycle decision', r['decision'], 'not-made')
        if case.endswith('merge'):
            eq('retained AUM150m*.8', e['retained_aum'], '120000000', True)
            eq('simple payback200k/50k', e['payback_years'], '4', True)
        if case.endswith('close'):
            eq('residual2m-1.2m-.1m-.2m', e['modeled_residual'], '500000', True)
    elif case == 'distribution':
        eq('qualified annual net fee5m*30bps', r['opportunities'][0]['annual_net_fee'], '15000', True)
        eq('qualified supplied policy outcome', r['opportunities'][0]['eligibility'], 'meets-supplied-policy')
        eq('conflict/minimum failure blocks', r['opportunities'][1]['eligibility'], 'blocked')
        eq('minimum not met', r['opportunities'][1]['controls']['minimum_subscription'], False)
        eq('undisclosed conflict not met', r['opportunities'][1]['controls']['conflict_disclosure'], False)
        eq('no outreach', r['outreach_authorized'], False)
    elif case == 'service':
        eq('open high SLA due September13', r['action_plan'][0]['sla_due'], '2026-09-13')
        eq('open issue overdue', r['action_plan'][0]['overdue'], True)
        eq('unverified resolution remains unverified', r['action_plan'][1]['status'], 'resolution-unverified')
        eq('unverified resolution must not clear overdue', r['action_plan'][1]['overdue'], True)
        eq('unverified resolution must not clear SLA breach', r['action_plan'][1]['sla_breached'], True)
        eq('monthly next due August20+30days', r['reporting_calendar'][0]['next_due'], '2026-09-19')
        eq('monthly report overdue', r['reporting_calendar'][0]['overdue'], True)
        eq('no client contact', r['client_contacted'], False)
        for token in ['SECRET-CLIENT-MESSAGE', 'DO-NOT-DISCLOSE-CLIENT-TOKEN-9241', 'RESTRICTED-FORWARD-SOURCE']:
            eq('restricted token omitted:' + token, token in json.dumps(output), False)
    elif case == 'investor-report':
        eq('capital bridge independent sum', r['capital_bridge']['expected_closing'], '1085000', True)
        eq('bridge reconciles', r['capital_bridge']['reconciled'], True)
        eq('arithmetic excess4%-3%', r['performance']['arithmetic_excess'], '.01', True)
        eq('relative return1.04/1.03-1 rounded6', r['performance']['relative_return'], '.009709', True)
        eq('publication not authorized', r['publication_status'], 'not-authorized')
        for token in ['SECRET-NOTE', 'DO-NOT-DISCLOSE-REPORT-TOKEN-8372', 'RESTRICTED-FORWARD-SOURCE']:
            eq('restricted token omitted:' + token, token in json.dumps(output), False)
    elif case == 'rfp':
        eq('exact approved supplied answer', r['responses'][0]['text'], 'The supplied period net return was4%.')
        eq('commercial revenue40m*35bps', r['commercial_review']['annual_revenue'], '140000', True)
        eq('commercial contribution less60k', r['commercial_review']['annual_contribution'], '80000', True)
        eq('supplied eligibility met', r['eligibility'][0]['status'], 'met')
        eq('two supplied approval records', [a['status'] for a in r['approval_queue']], ['recorded-supplied'] * 2)
        eq('no submission', r['submission'], 'not-performed')
    elif case == 'institutional-dd':
        eq('capacity1bn-900m-150m', r['capacity']['post_commitment_headroom'], '-50000000', True)
        eq('annual fee150m*50bps', r['fees']['annual_flat_fee'], '750000', True)
        eq('arithmetic excess7%-6%', r['performance']['arithmetic_excess'], '.01', True)
        eq('capacity blocks despite all criteria met', r['eligibility'], 'unresolved')
        eq('no manager appointment', r['manager_appointment'], 'not-made')
    else:
        a = r['analysis']
        eq('committee decision pending', r['committee_decision'], 'pending')
        eq('hard limit blocks', r['review_readiness'], 'blocked')
        if case.endswith('public-security'):
            eq('weighted return .2*(-.225)+.5*.15+.3*.4', a['expected_total_return'], '.15', True)
            eq('sector after .20-.02+.06', a['sector_weight_after'], '.24', True)
            eq('downside total return(60+2-80)/80', a['scenarios'][0]['total_return'], '-.225', True)
        elif case.endswith('manager'):
            eq('manager allocation15m/100m', a['allocation_fraction'], '.15', True)
        else:
            eq('expected allocation return .5*.08+.3*.04+.2*.02', a['expected_return'], '.056', True)
            eq('half L1 turnover', a['one_way_turnover'], '.1', True)
            eq('cash only liquid allocation', a['liquid_weight'], '.2', True)


original = json.loads((HERE / 'requests.json').read_text())['cases']
for case in original:
    expected(case['case_id'], json.loads((HERE / (case['case_id'] + '-output.json')).read_text()), 'historical')

replays = []
for case in original:
    name, package = case['case_id'], case['package']
    doc = copy.deepcopy(case['input'])
    changes = []
    if package in NEW:
        changes.append('Removed mode=' + str(doc.pop('mode')) + '; single-method package now explicitly rejects mode. No economic/source values changed.')
    output, inp, out = compute(name, package, doc)
    check(name, 'current compute completes', output is not None, True)
    if output is None:
        continue
    expected(name, output)
    check(name, 'native input validator', run(package, 'validate_input.py', [inp], name).returncode, 0)
    check(name, 'detached output validator', run(package, 'validate_output.py', [out, '--input', inp], name).returncode, 0)
    altered = copy.deepcopy(output)
    altered['action_taken'] = True
    badpath = RUN / (name + '-authority-tamper.json')
    save(badpath, altered)
    check(name, 'authority tamper rejected', run(package, 'validate_output.py', [badpath, '--input', inp], name).returncode != 0, True)
    altered_input = copy.deepcopy(doc)
    altered_input['unresolved_issues'].append('ADDED-AFTER-OUTPUT')
    changedpath = RUN / (name + '-changed-original.json')
    save(changedpath, altered_input)
    check(name, 'changed detached original rejected', run(package, 'validate_output.py', [out, '--input', changedpath], name).returncode != 0, True)
    check(name, 'missing original rejected', run(package, 'validate_output.py', [out], name).returncode != 0, True)
    replays.append(dict(case=name, package=package, changes=changes, input=doc, output=output))

# One representative per package: dates, unknown method, audience and future knowledge.
seen = set()
for base in replays:
    package = base['package']
    if package in seen:
        continue
    seen.add(package)
    for mutation in ['malformed-date', 'unknown-mode', 'restricted-all', 'future-known-all']:
        name = base['case'] + '-' + mutation
        doc = copy.deepcopy(base['input'])
        if mutation == 'malformed-date':
            doc['as_of'] = '2026-02-30'
        elif mutation == 'unknown-mode':
            doc['mode'] = 'execute-and-send'
        else:
            for source in doc['sources']:
                if mutation == 'restricted-all':
                    source['permitted_audiences'] = ['private-author-only']
                else:
                    source['known_at'] = '2026-10-01'
        output, inp, out = compute(name, package, doc)
        if mutation in ['malformed-date', 'unknown-mode']:
            check(name, 'unsupported request rejected', output is None, True)
        elif output is None:
            check(name, 'unusable evidence rejected before output', True, True)
        else:
            check(name, 'unusable evidence produces needs-review', output['status'], 'needs-review')
            check(name, 'no unusable source identifiers emitted', any(s['source_ref'] in json.dumps(output) for s in doc['sources']), False)
            check(name, 'no source refs emitted', output['source_refs'], [])
            check(name, 'detached output validation for omission result', run(package, 'validate_output.py', [out, '--input', inp], name).returncode, 0)

base = next(r for r in replays if r['case'] == 'economics')
doc = copy.deepcopy(base['input'])
doc['products'][0]['data']['closing_aum'] = '216000000'  # source claim stays unchanged
output, inp, out = compute('economics-unbound-altered-claim', base['package'], doc)
check('economics-unbound-altered-claim', 'unsupported product omitted', [r['id'] for r in output['results']['products']], ['LIQUID'])
check('economics-unbound-altered-claim', 'aggregate unavailable for incomplete product book', output['results']['totals'], None)
check('economics-unbound-altered-claim', 'supported individual product100m retained', output['results']['products'][0]['expected_closing_aum'], '100000000', True)

# Explicit correction after schema discovery: supplied approval metadata for gate records.
base = next(r for r in replays if r['case'] == 'lifecycle-launch')
doc = copy.deepcopy(base['input'])
for gate in doc['gates']:
    source = next(s for s in doc['sources'] if s['source_ref'] == gate['source_ref'])
    source.update(approval_status='approved', effective_from='2026-01-01', expires='2026-12-31')
output, inp, out = compute('lifecycle-approved-gate-evidence', base['package'], doc)
check('lifecycle-approved-gate-evidence', 'approved LEGAL supplied pass retained', output['results']['gates'][0]['status'], 'passed')
check('lifecycle-approved-gate-evidence', 'explicit unknown OPERATIONS retained', output['results']['gates'][1]['status'], 'unknown')
check('lifecycle-approved-gate-evidence', 'unknown gate still blocks', output['results']['review_readiness'], 'blocked')
check('lifecycle-approved-gate-evidence', 'detached output validator', run(base['package'], 'validate_output.py', [out, '--input', inp], 'lifecycle-approved-gate-evidence').returncode, 0)

def sync_claim(doc, row):
    source = next(s for s in doc['sources'] if s['source_ref'] == row['source_ref'])
    source['claims'][row['claim_id']] = copy.deepcopy(row['data'])

# Separation of duties and actual-record chronology are semantic checks, not hash checks.
base = next(r for r in replays if r['case'] == 'rfp')
for variant in ['blank-actor', 'self-approval', 'approval-after-knowledge-cutoff']:
    name = 'rfp-' + variant
    doc = copy.deepcopy(base['input'])
    if variant == 'blank-actor':
        doc['approvals'][0]['data']['actor'] = ' '
    elif variant == 'self-approval':
        doc['approvals'][0]['data']['actor'] = doc['engagement']['data']['author']
    else:
        doc['knowledge_cutoff'] = '2026-09-15'
        for source in doc['sources']:
            source['as_of'] = source['known_at'] = '2026-09-15'
        # Supplied record says actual approval recorded September20. An earlier
        # knowledge cutoff cannot establish this actual completed approval.
    sync_claim(doc, doc['approvals'][0])
    output, inp, out = compute(name, base['package'], doc)
    if output is None:
        check(name, 'unsupported approval evidence rejected', True, True)
    else:
        check(name, 'approval remains outstanding', output['results']['approval_queue'][0]['status'], 'outstanding')
        check(name, 'no RFP submission', output['results']['submission'], 'not-performed')

base = next(r for r in replays if r['case'] == 'institutional-dd')
doc = copy.deepcopy(base['input'])
row = next(e for e in doc['evidence'] if e['data']['criterion_id'] == 'operations')
row['data']['origin'] = 'manager-reported'
sync_claim(doc, row)
output, inp, out = compute('diligence-independent-evidence-missing', base['package'], doc)
check('diligence-independent-evidence-missing', 'operations criterion remains unknown', next(r for r in output['results']['criteria'] if r['criterion_id']=='operations')['status'], 'unknown')
check('diligence-independent-evidence-missing', 'score withheld without independent evidence', output['results']['policy_score'], None)

for case in ['economics', 'service', 'investor-report', 'institutional-dd']:
    base = next(r for r in replays if r['case'] == case)
    doc = json.loads((HERE / 'additional-chronology' / (case + '-input.json')).read_text())
    name = case + '-actual-event-after-cutoff'
    output, inp, out = compute(name, base['package'], doc)
    if output is None:
        check(name, 'actual observations unavailable at cutoff rejected', True, True)
    else:
        field = {'economics':'totals', 'service':'reporting_calendar', 'investor-report':'performance', 'institutional-dd':'performance'}[case]
        check(name, 'actual observation unavailable at cutoff withheld', output['results'][field], [] if case == 'service' else None)
        if case == 'investor-report':
            check(name, 'capital bridge after cutoff also withheld', output['results']['capital_bridge'], None)
        check(name, 'unresolved chronology remains needs-review', output['status'], 'needs-review')
        check(name, 'detached omission-result validator', run(base['package'], 'validate_output.py', [out, '--input', inp], name).returncode, 0)

hashes = {}
for package in seen:
    for path in sorted((ROOT / 'skills/asset-management' / package).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
record = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), reviewer='am_investment',
    scope='Eight business packages; five new packages and three expanded methods. Synthetic internal-review cases only.',
    methodology='Original12 fresh requests and expected amounts authored before execution. Review uses independent arithmetic/semantic assertions plus native detached-input validation. Historical inputs/outputs remain untouched. Current replays remove the unsupported mode selector from five single-method packages following author clarification. Gate correction adds only explicit supplied source approval metadata. No author fixtures copied.',
    limitations=['This is bounded evaluation, not source-truth verification, authenticated approval, professional acceptance, production certification or exhaustive testing.', 'Current file hashes identify this run only; helper or package changes require replay.', 'Only new modes of expanded packages reviewed here; legacy modes are outside this forward review.'],
    reviewer_corrections=['Initial negative-case expectation assumed a100m partial aggregate after withholding one unsupported product. The documented method requires a complete reconciled book for aggregate totals; expectation corrected to null totals and retained100m individual product. Initial interrupted replay left its output intact and no completed review report. This was a reviewer error, not a package defect.'],
    historical_failures=[c for c in checks if c['phase']=='historical' and not c['passed']],
    current_failures=[c for c in checks if c['phase']=='current' and not c['passed']],
    counts=dict(historical_checks=sum(c['phase']=='historical' for c in checks), current_checks=sum(c['phase']=='current' for c in checks), native_commands=len(commands), compute_cases=sum('calculate_or_transform.py' in c['command'][2] for c in commands), package_count=len(seen)),
    checks=checks, commands=commands, current_replays=replays, package_file_sha256=hashes)
save(RUN / 'review.json', record)
print(json.dumps({k:record[k] for k in ['counts','historical_failures','current_failures']}, indent=2))
