"""Bounded journey/control coverage and multi-rule retrospective portfolio replay."""
from collections import Counter
from datetime import date
from decimal import Decimal
from itertools import combinations
import operator
import re

from payment_foundation import dec, finding

SKILL = 'payment-fraud-control-evaluator'
OPS = {'>=': operator.ge, '>': operator.gt, '<=': operator.le, '<': operator.lt, '==': operator.eq}


def text(v):
    return isinstance(v, str) and bool(v.strip())


def num(v):
    n = dec(v)
    if n < 0:
        raise ValueError('amount/cost must be nonnegative')
    return n


def rate(n, d):
    return str(Decimal(n) / Decimal(d)) if d else None


def unique(rows, field, errors):
    if not isinstance(rows, list):
        errors.append(field + ' collection must be a list')
        return set()
    ids = [x.get(field) for x in rows]
    if any(not text(x) for x in ids) or len(set(ids)) != len(ids):
        errors.append('duplicate or missing ' + field)
    return set(ids)


def validate(d):
    e = []
    if d.get('mode') not in {'strategy', 'portfolio', 'strategy-and-portfolio'}:
        e.append('mode must be strategy, portfolio or strategy-and-portfolio')
    journeys = unique(d.get('journeys', []), 'journey_id', e)
    threats = unique(d.get('threats', []), 'threat_id', e)
    unique(d.get('controls', []), 'control_id', e)
    for j in d.get('journeys', []):
        if not text(j.get('description')) or not isinstance(j.get('stages'), list) or not j['stages'] or any(not text(x) for x in j['stages']):
            e.append('journey requires description and nonempty stages')
    stages = {j['journey_id']: set(j['stages']) for j in d.get('journeys', [])}
    for t in d.get('threats', []):
        if t.get('journey_id') not in journeys or t.get('stage') not in stages.get(t.get('journey_id'), set()) or not text(t.get('scenario')):
            e.append('threat must identify a known journey/stage and scenario')
    for c in d.get('controls', []):
        if c.get('kind') not in {'preventive', 'detective', 'responsive'} or not isinstance(c.get('threat_ids'), list) or not c['threat_ids'] or not set(c['threat_ids']) <= threats:
            e.append('control requires kind and known threat_ids')
        for field in ('owner', 'signal', 'response', 'failure_mode', 'evidence_metric'):
            if not text(c.get(field)):
                e.append('control requires ' + field)
    appetite = d.get('risk_appetite')
    if appetite is not None:
        for key in ('max_review_rate', 'max_legitimate_block_rate'):
            if appetite.get(key) is not None and not 0 <= num(appetite[key]) <= 1:
                e.append('appetite rates must be fractions in [0,1]')
    if d.get('mode') == 'strategy':
        if d.get('transactions') or d.get('rules') or d.get('portfolios'):
            e.append('strategy mode does not silently ignore portfolio data')
        return e
    rule_ids = unique(d.get('rules'), 'rule_id', e)
    for r in d.get('rules', []):
        if r.get('action') not in {'block', 'review'} or r.get('op') not in OPS or not text(r.get('field')) or not text(r.get('version')):
            e.append('rule requires supported action/op, field and version')
        dec(r['threshold'])
    portfolios = d.get('portfolios', {})
    if set(portfolios) != {'baseline', 'proposed'}:
        e.append('portfolios require baseline and proposed')
    else:
        for ids in portfolios.values():
            if not isinstance(ids, list) or len(ids) != len(set(ids)) or not set(ids) <= rule_ids:
                e.append('portfolio requires unique known rule IDs')
    tx = d.get('transactions')
    unique(tx, 'transaction_id', e)
    if not tx:
        e.append('portfolio replay requires transactions')
    for t in tx or []:
        if not re.fullmatch('[A-Z]{3}', t.get('currency', '')):
            e.append('transaction currency required')
        num(t['amount'])
        for field in ('occurred_on', 'label_observed_on', 'maturity_due', 'features_observed_on'):
            date.fromisoformat(t[field])
        if t['label_observed_on'] < t['occurred_on'] or t['maturity_due'] < t['occurred_on']:
            e.append('label or maturity precedes transaction')
        if t.get('label') not in {'fraud', 'legit', 'pending', 'unknown'}:
            e.append('unsupported label')
        if not isinstance(t.get('features'), dict):
            e.append('features must be an object')
        else:
            for value in t['features'].values():
                if value is not None:
                    dec(value)
        if t.get('observed_net_fraud_loss') is not None:
            num(t['observed_net_fraud_loss'])
            if t['label'] != 'fraud' and num(t['observed_net_fraud_loss']) != 0:
                e.append('nonzero observed fraud loss requires fraud label')
    costs = d.get('friction_costs', [])
    unique(costs, 'currency', e)
    for c in costs:
        if not re.fullmatch('[A-Z]{3}', c['currency']):
            e.append('cost currency invalid')
        for field in ('per_review', 'per_legitimate_block'):
            if c.get(field) is not None:
                num(c[field])
    return e


def analyze(req):
    d = req['data']
    findings = []
    mode = d['mode']
    coverage = []
    if mode != 'portfolio':
        if not d.get('journeys') or not d.get('threats') or not d.get('controls'):
            findings.append(finding('strategy-incomplete', 'Supply journey stages, threat scenarios and control ownership before treating strategy as covered.'))
        for threat in d.get('threats', []):
            controls = [c for c in d.get('controls', []) if threat['threat_id'] in c['threat_ids']]
            kinds = sorted({c['kind'] for c in controls})
            coverage.append({'threat_id': threat['threat_id'], 'journey_id': threat['journey_id'], 'stage': threat['stage'],
                             'control_ids': [c['control_id'] for c in controls], 'kinds': kinds,
                             'uncovered_kinds': sorted({'preventive', 'detective', 'responsive'} - set(kinds)),
                             'effectiveness_established': False})
            if set(kinds) != {'preventive', 'detective', 'responsive'}:
                findings.append(finding('threat-coverage-gap', 'Threat ' + threat['threat_id'] + ' lacks one or more preventive, detective or responsive options; document compensating controls or reviewed risk acceptance.'))
        for kind in ('journeys', 'threats', 'controls'):
            if any(not r.get('source_ids') for r in d.get(kind, [])):
                findings.append(finding('strategy-evidence-gap', kind + ' require their own source evidence.'))
    appetite = d.get('risk_appetite') or {}
    if not appetite.get('source_ids') or not text(appetite.get('owner')) or not text(appetite.get('rationale')):
        findings.append(finding('risk-appetite-gap', 'A named owner and sourced rationale must define review/friction tolerances; no universal thresholds are supplied.'))
    result = {'mode': mode, 'strategy_coverage': coverage, 'control_options': d.get('controls', []), 'portfolio_replay': [],
              'causal_avoided_loss': None, 'deployment_recommendation': 'Human control, legal, model-risk and change owners review; no deployment or live decision is authorized.'}
    if mode == 'strategy':
        return {'result': result, 'findings': findings, 'handoffs': handoffs()}
    rules = {r['rule_id']: r for r in d['rules']}
    tx = d['transactions']
    if any(t['occurred_on'] > req['as_of'] or t['label_observed_on'] > req['as_of'] or t['features_observed_on'] > req['as_of'] for t in tx):
        findings.append(finding('future-evidence', 'Transaction, features or labels extend beyond as_of; replay quarantined.'))
        result['replay_quarantined'] = True
        return {'result': result, 'findings': findings, 'handoffs': handoffs()}
    if any(t['features_observed_on'] > t['occurred_on'] for t in tx):
        findings.append(finding('feature-leakage', 'Some features were observed after the transaction decision date; replay quarantined to prevent hindsight leakage.'))
        result['replay_quarantined'] = True
        return {'result': result, 'findings': findings, 'handoffs': handoffs()}
    if not d.get('sample_source_ids') or not d.get('maturity_policy_source_ids'):
        findings.append(finding('sample-policy-gap', 'Sample inclusion/exclusion and cohort-specific label maturity policy need sources.'))
    if any(not r.get('source_ids') for r in d['rules']) or any(not t.get('source_ids') for t in tx):
        findings.append(finding('replay-evidence-gap', 'Each rule version and transaction needs source evidence.'))
    mature = {t['transaction_id'] for t in tx if t['label'] in {'fraud', 'legit'} and t['maturity_due'] <= req['as_of'] and (t['label'] == 'fraud' or t['label_observed_on'] >= t['maturity_due'])}
    if len(mature) < len(tx):
        findings.append(finding('immature-labels', 'Pending, unknown and not-yet-mature labels remain outside confusion/value metrics; no label is imputed.'))
    costs = {c['currency']: c for c in d.get('friction_costs', [])}
    selected_currencies = sorted({t['currency'] for t in tx})
    for cur in selected_currencies:
        if cur not in costs or any(costs[cur].get(k) is None for k in ('per_review', 'per_legitimate_block')) or not costs[cur].get('source_ids'):
            findings.append(finding('friction-assumptions-gap', cur + ' review and legitimate-block unit cost assumptions need values and sources.'))
    actions_by_portfolio = {}
    for pname, ids in d['portfolios'].items():
        rows = []
        triggers, exclusive, overlaps = Counter(), Counter(), Counter()
        for t in tx:
            hits, unavailable = [], []
            for rid in ids:
                rule = rules[rid]
                value = t['features'].get(rule['field'])
                if value is None:
                    unavailable.append(rid)
                elif OPS[rule['op']](dec(value), dec(rule['threshold'])):
                    hits.append(rid)
            triggers.update(hits)
            if len(hits) == 1:
                exclusive.update(hits)
            overlaps.update(combinations(sorted(hits), 2))
            # Missing features could change portfolio semantics; preserve unknown even if another rule fires.
            action = 'unknown' if unavailable else 'block' if any(rules[r]['action'] == 'block' for r in hits) else 'review' if hits else 'allow'
            rows.append({'transaction_id': t['transaction_id'], 'matched_rule_ids': hits, 'unavailable_rule_ids': unavailable,
                         'replayed_action': action, 'mature_label_eligible': t['transaction_id'] in mature})
        actions = {r['transaction_id']: r['replayed_action'] for r in rows}
        actions_by_portfolio[pname] = actions
        if any(r['unavailable_rule_ids'] for r in rows):
            findings.append(finding('missing-rule-feature', pname + ' has indeterminate replay rows; never default missing features to allow.'))
        currency_rows = []
        for cur in selected_currencies:
            sample = [t for t in tx if t['currency'] == cur]
            labeled = [t for t in sample if t['transaction_id'] in mature and actions[t['transaction_id']] != 'unknown']
            counts = {label: {act: 0 for act in ('block', 'review', 'allow')} for label in ('fraud', 'legit')}
            values = {act: Decimal(0) for act in ('block', 'review', 'allow')}
            losses = {act: Decimal(0) for act in ('block', 'review', 'allow')}
            loss_known = {act: True for act in ('block', 'review', 'allow')}
            for t in labeled:
                act = actions[t['transaction_id']]
                counts[t['label']][act] += 1
                if t['label'] == 'fraud':
                    values[act] += num(t['amount'])
                    if t.get('observed_net_fraud_loss') is None:
                        loss_known[act] = False
                    else:
                        losses[act] += num(t['observed_net_fraud_loss'])
            c = costs.get(cur, {})
            n_review = sum(actions[t['transaction_id']] == 'review' for t in sample)
            reviews_cost = Decimal(n_review) * num(c['per_review']) if c.get('per_review') is not None else None
            fp_cost = Decimal(counts['legit']['block']) * num(c['per_legitimate_block']) if c.get('per_legitimate_block') is not None else None
            review_rate = rate(n_review, len(sample))
            legit_n = sum(counts['legit'].values())
            false_positive_rate = rate(counts['legit']['block'], legit_n)
            guardrails = []
            for key, observed in (('max_review_rate', review_rate), ('max_legitimate_block_rate', false_positive_rate)):
                limit = appetite.get(key)
                state = 'unknown' if limit is None or observed is None else 'within-supplied-appetite' if Decimal(observed) <= num(limit) else 'outside-supplied-appetite'
                if key == 'max_review_rate' and state == 'within-supplied-appetite' and Decimal(rate(n_review + sum(actions[t['transaction_id']] == 'unknown' for t in sample), len(sample))) > num(limit):
                    state = 'unknown'
                if state != 'within-supplied-appetite':
                    findings.append(finding('appetite-review-required', pname + '/' + cur + '/' + key + ': ' + state))
                guardrails.append({'metric': key, 'supplied_limit': limit, 'observed': observed, 'state': state})
            currency_rows.append({'currency': cur, 'sample_size': len(sample), 'mature_evaluable_size': len(labeled),
                                  'excluded_immature_or_unknown_feature_size': len(sample) - len(labeled),
                                  'sample_face_value': str(sum((num(t['amount']) for t in sample), Decimal(0))),
                                  'excluded_immature_or_unknown_feature_face_value': str(sum((num(t['amount']) for t in sample if t not in labeled), Decimal(0))),
                                  'action_counts': dict(sorted(Counter(actions[t['transaction_id']] for t in sample).items())),
                                  'confusion_by_mature_label': counts, 'observed_mature_fraud_value_by_replayed_action': {k: str(v) for k, v in values.items()},
                                  'observed_net_fraud_loss_by_replayed_action': {k: str(v) if loss_known[k] else None for k, v in losses.items()},
                                  'review_rate_all_sample': review_rate, 'review_rate_upper_bound': rate(n_review + sum(actions[t['transaction_id']] == 'unknown' for t in sample), len(sample)), 'legitimate_block_rate_mature': false_positive_rate,
                                  'modeled_review_cost': str(reviews_cost) if reviews_cost is not None else None,
                                  'modeled_mature_legitimate_block_friction_cost': str(fp_cost) if fp_cost is not None else None,
                                  'guardrails': guardrails})
        result['portfolio_replay'].append({'portfolio': pname, 'rule_ids': ids, 'rows': rows, 'currency_metrics': currency_rows,
                                           'rule_trigger_counts': dict(sorted(triggers.items())), 'exclusive_trigger_counts': dict(sorted(exclusive.items())),
                                           'pairwise_overlaps': [{'rule_ids': list(k), 'transactions': v} for k, v in sorted(overlaps.items())]})
    result['action_transitions'] = [{'transaction_id': t['transaction_id'], 'baseline': actions_by_portfolio['baseline'][t['transaction_id']], 'proposed': actions_by_portfolio['proposed'][t['transaction_id']]} for t in tx]
    result['replay_quarantined'] = False
    return {'result': result, 'findings': findings, 'handoffs': handoffs(),
            'limitations': ['Retrospective labels and feature provenance are supplied, not authenticated. Blocks/reviews are simulated categories, not live decisions. Selection bias, suppressed outcomes, changing attack patterns, label error and nonrandom samples prevent causal avoided-loss claims. No statistical confidence interval or population extrapolation is supplied; mature counts and excluded counts bound interpretation. Fraud face value, observed net loss and modeled friction costs are distinct and must not be summed into net savings.']}


def handoffs():
    return [{'target_skill': 'payment-initiation-control-reviewer', 'reason': 'Check payee, intent, delegation and authorization controls for covered payment journeys.', 'required_inputs': ['threat and journey IDs', 'intent and delegation artifacts', 'control owners and unresolved issues']},
            {'target_skill': 'payment-acceptance-performance-analyzer', 'reason': 'Inspect observed acceptance and customer friction cohorts around proposed controls.', 'required_inputs': ['unique order and attempt population', 'control version dates', 'mature outcome and source evidence']}]
