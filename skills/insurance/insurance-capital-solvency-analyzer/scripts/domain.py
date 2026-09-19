"""Approved additive capital/control ratio review; not an RBC or SCR engine."""
from decimal import Decimal

from insurance_foundation import number
from local_review import Review, shape, text

SKILL = 'insurance-capital-solvency-analyzer'
METHOD = 'approved-capital-control-ratio-v1'


def validate(doc):
    errors = shape(doc, objects=('profile', 'available_control', 'requirement'), lists=('components', 'stresses'), numbers=('amount', 'available_delta', 'requirement_delta', 'reported_available', 'reported_requirement'), nonnegative=('ratio_pct',))
    p = doc.get('data', {}).get('profile', {})
    if isinstance(p, dict) and 'thresholds' in p and (not isinstance(p['thresholds'], list) or any(not isinstance(x, dict) for x in p['thresholds'])):
        errors.append('profile.thresholds must be a list of objects')
    return errors


def evaluate(doc):
    d, r = doc['data'], Review(doc)
    p = r.profile(METHOD)
    r.check(p.get('aggregation_method') == 'approved-additive-components', 'capital-aggregation', 'Only a supplied approved additive numerator bridge is supported; covariance, diversification, eligibility caps and statutory charges must be calculated and approved upstream.', p)
    r.check(d.get('components_complete') is True and 'components' in d and 'stresses' in d, 'capital-inventory', 'Supply complete approved components and an explicit stress inventory.')
    expected = p.get('component_ids', [])
    r.check(bool(expected) and len(expected) == len(set(expected)), 'approved-component-set', 'Profile must enumerate unique approved signed numerator components.', p)
    seen, total, bridge = set(), Decimal(0), []
    for row in d.get('components', []):
        r.bind(row, 'component')
        cid, value = row.get('component_id'), number(row.get('amount'))
        r.check(text(cid) and cid not in seen and cid in expected and value is not None and text(row.get('reviewed_by')), 'component-identity', 'Each numerator component requires unique approved identity, signed amount, scope and reviewer.', row)
        seen.add(cid)
        if value is not None:
            total += value
        bridge.append({'component_id': cid, 'signed_amount': value, 'source_refs': row.get('source_refs', [])})
    r.check(seen == set(expected), 'component-coverage', 'Supplied component set must exactly equal the approved component scope; no missing deduction or duplicate eligibility credit.')
    control, requirement = d.get('available_control', {}), d.get('requirement', {})
    r.bind(control, 'available-control')
    r.bind(requirement, 'requirement')
    supplied, denominator = number(control.get('amount')), number(requirement.get('amount'))
    r.check(supplied is not None, 'capital-control-unknown', 'Supply the reported available-capital control.')
    r.check(denominator is not None and denominator > 0 and text(p.get('denominator_name')) and requirement.get('denominator_name') == p.get('denominator_name') and text(requirement.get('reviewed_by')), 'denominator-basis', 'A positive approved denominator with the exact profile label is required; do not substitute ACL RBC, CAL RBC, SCR or an economic measure.', requirement)
    thresholds, tids = [], set()
    for row in p.get('thresholds', []):
        tid, level = row.get('threshold_id'), number(row.get('ratio_pct'))
        r.evidence(row, 'threshold')
        r.check(text(tid) and tid not in tids and level is not None and text(row.get('purpose')), 'threshold-definition', 'Each threshold needs unique identity, percentage units, purpose and versioned evidence.', row)
        tids.add(tid)
        thresholds.append((tid, level))
    available = total if not r.blocked else None
    difference = total - supplied if available is not None else None
    if difference is not None and difference != 0:
        r.add('available-capital-control-break', 'Approved signed components do not tie to the supplied available-capital control; arithmetic remains visible but no capital conclusion is supported.', control, block=False, severity='review')
    ratio = available / denominator * 100 if available is not None else None
    def comparisons(value):
        return [{'threshold_id': tid, 'ratio_pct': level, 'comparison': 'below' if value < level else 'at-or-above'} for tid, level in thresholds] if value is not None else None
    stresses, stress_seen = [], set()
    base_blocked = r.blocked
    for row in d.get('stresses', []):
        prior_findings = len(r.findings)
        r.bind(row, 'stress')
        sid = row.get('scenario_id')
        da, dr = number(row.get('available_delta')), number(row.get('requirement_delta'))
        ra, rr = number(row.get('reported_available')), number(row.get('reported_requirement'))
        r.check(text(sid) and sid not in stress_seen and text(row.get('reviewed_by')) and text(row.get('horizon')) and all(v is not None for v in (da, dr, ra, rr)), 'stress-bridge', 'Stress requires a unique scenario, horizon, approved signed numerator/denominator changes and reported stressed controls.', row)
        stress_seen.add(sid)
        valid = not base_blocked and not any(f['severity'] == 'gap' for f in r.findings[prior_findings:])
        sa, sr = (available + da, denominator + dr) if valid else (None, None)
        if sr is not None and sr <= 0:
            r.add('stress-denominator', 'Stressed requirement is not positive; ratio is undefined.', row)
            valid = False
        sa_diff, sr_diff = (sa - ra, sr - rr) if valid else (None, None)
        if valid and (sa_diff or sr_diff):
            r.add('stress-control-break', 'Stress bridge differs from supplied stressed capital or requirement.', row, block=False, severity='review')
        sr_ratio = sa / sr * 100 if valid else None
        stresses.append({'scenario_id': sid, 'horizon': row.get('horizon'), 'available_capital': sa, 'required_capital': sr, 'available_control_difference': sa_diff, 'requirement_control_difference': sr_diff, 'ratio_pct': sr_ratio, 'threshold_comparisons': comparisons(sr_ratio)})
    return r.result({'component_bridge': bridge, 'available_capital': available, 'available_control_difference': difference,
                     'required_capital': denominator if not base_blocked else None, 'denominator_name': p.get('denominator_name'),
                     'ratio_pct': ratio, 'threshold_comparisons': comparisons(ratio), 'stress_bridges': stresses,
                     'basis': d.get('basis'), 'currency': d.get('currency'),
                     'regulatory_action_determined': False, 'solvency_certified': False,
                     'statutory_capital_engine': False})
