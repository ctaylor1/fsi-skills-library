"""Validate the explicitly supplied policy and bounded native input."""
from policy_contract import *
CONFIG_KEYS=('ubo_threshold_pct','ubo_coverage_target_pct','high_risk_countries','high_risk_industries','required_fields_individual','required_fields_entity','required_documents_individual','required_documents_entity','screening_max_age_days','edd_signals')

def validate(doc):
    errors=base_errors(doc,'config_version','as_of','config',CONFIG_KEYS)
    if not isinstance(doc,dict) or errors: return errors,[]
    cfg=doc.get('config') or {}
    for k in ('ubo_threshold_pct','ubo_coverage_target_pct'):
        if not number(cfg.get(k),0,100): errors.append('config.'+k+' must be within 0..100')
    if not number(cfg.get('screening_max_age_days'),0): errors.append('screening_max_age_days must be nonnegative')
    for k in CONFIG_KEYS:
        if k not in ('ubo_threshold_pct','ubo_coverage_target_pct','screening_max_age_days') and not strings(cfg.get(k)):
            errors.append('config.'+k+' must be a string list')
    c=doc.get('customer')
    if not isinstance(c,dict) or c.get('customer_type') not in ('individual','entity'):
        errors.append('customer with individual/entity type is required')
    if isinstance(c,dict):
        for key in ('country','industry'):
            if c.get(key) is not None and not isinstance(c[key],str): errors.append('customer.'+key+' must be a string')
    allowed_signals={'high_risk_jurisdiction','high_risk_industry','pep_flag','adverse_media_flag','ubo_below_coverage','ubo_unverified','missing_required_field','missing_required_document','expired_document','unverified_identity','identity_mismatch','ownership_over_100'}
    if strings(cfg.get('edd_signals')) and not set(cfg['edd_signals'])<=allowed_signals: errors.append('unknown edd_signals policy entry')
    if not text(doc.get('case_id')): errors.append('case_id is required')
    for key in ('documents','identity_checks','beneficial_owners'):
        value=doc.get(key,[])
        if not records(value): errors.append(key+' must be a list of objects'); continue
        for i,row in enumerate(value):
            if not text(row.get('source_ref')): errors.append(f'{key}[{i}] needs a supplied source_ref')
            if key=='documents':
                if not text(row.get('type')): errors.append('document type required')
                if 'verified' in row and not isinstance(row['verified'],bool): errors.append('document verified must be boolean')
                for k in ('issue_date','expiry_date'):
                    if row.get(k) is not None and not day(row[k]): errors.append('invalid document '+k)
            if key=='identity_checks' and not isinstance(row.get('match'),bool): errors.append('identity check match must be boolean')
            if key=='beneficial_owners':
                if row.get('country') is not None and not isinstance(row['country'],str): errors.append('owner country must be a string')
                if not number(row.get('ownership_pct'),0,100): errors.append('ownership_pct must be within 0..100')
                if 'verified' in row and not isinstance(row['verified'],bool): errors.append('owner verified must be boolean')
    hits=doc.get('screening_hits',{})
    if not isinstance(hits,dict): errors.append('screening_hits must be an object')
    else:
        for key,rows in hits.items():
            if key not in ('pep','sanctions','adverse_media') or not records(rows): errors.append('invalid screening hit list'); continue
            if any(not text(r.get('source_ref')) for r in rows): errors.append('screening hits require source_ref')
    coverage=doc.get('screening_coverage',{})
    if not isinstance(coverage,dict) or any(not isinstance(x,dict) for x in coverage.values()): errors.append('screening_coverage must contain objects')
    return errors,[]


def main(argv):
    import json, sys
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'evals/files/case_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
    try:
        doc=json.loads(p.read_text() if p else sys.stdin.read())
        errors,warnings=validate(doc)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        errors,warnings=[str(exc)],[]
    for message in errors: print('ERROR',message)
    for message in warnings: print('WARN',message)
    print(f'input validation: {len(errors)} error(s), {len(warnings)} warning(s)')
    return int(bool(errors))

if __name__=='__main__':
    import sys
    raise SystemExit(main(sys.argv[1:]))
