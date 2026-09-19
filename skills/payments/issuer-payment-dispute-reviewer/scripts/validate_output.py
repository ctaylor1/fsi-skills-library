#!/usr/bin/env python3
"""Check issuer-review ownership, legal-clock separation and non-execution."""
import json, sys, re
from pathlib import Path
from calculate_or_transform import ALLOWED_DISPOSITIONS, _clock_review
from datetime import date
from payment_contract import validate_rule_profile


def validate(doc):
    errors = []
    if not doc.get('cases'): return ['case-work output has no cases']
    for r in doc['cases']:
        cid = r.get('case_id')
        if r.get('disposition') not in ALLOWED_DISPOSITIONS: errors.append(f'{cid}: disallowed disposition')
        if r.get('role') in {'merchant', 'acquirer'}:
            if r.get('route_specialist') != 'merchant-chargeback-response-packager' or r.get('draft_response'):
                errors.append(f'{cid}: merchant/acquirer response must route out')
        elif r.get('role') != 'issuer': errors.append(f'{cid}: issuer role required')
        draft = r.get('draft_response')
        if draft:
            if draft.get('authorized_submission') is not False or draft.get('authorization_status') != 'pending-human-review': errors.append(f'{cid}: unauthorized action')
            if draft.get('evidence_status') != 'supplied': errors.append(f'{cid}: unsupported evidence promotion')
        if r.get('disposition') == 'draft-ready-for-review':
            stat = r.get('statutory_review') or {}
            if not draft or stat.get('status') != 'supplied-for-review' or not stat.get('clocks') or r.get('needs'):
                errors.append(f'{cid}: draft-ready requires resolved supplied statutory profile and review records')
            errors.extend(validate_rule_profile(stat.get('profile'), doc.get('processing_date'), participant='issuer', jurisdiction=r.get('jurisdiction')))
            for clock in stat.get('clocks', []):
                try:
                    errors.extend(_clock_review(clock, date.fromisoformat(doc.get('processing_date','')))['issues'])
                except (ValueError, TypeError): errors.append('invalid processing date')
                if clock.get('status') != 'review-open' or not clock.get('source_ref') or not clock.get('trigger_source_ref'):
                    errors.append(f'{cid}: clock unavailable, overdue or uncited')
        if r.get('recommended_action') in {'represent-defend', 'deny', 'accept', 'credit', 'close'}:
            errors.append(f'{cid}: unsupported issuer outcome/action')
    text = json.dumps(doc.get('cases', [])) + str(doc.get('narrative', ''))
    for pattern in (r"\bcase (?:is |was )?closed\b", r"\b(?:provisional|final) credit (?:was )?(?:issued|posted|granted)\b", r"\bliability (?:assigned|accepted)\b", r"\bchargeback (?:accepted|denied|reversed)\b", r"\bresponse (?:submitted|filed)\b", r"\bguaranteed (?:win|outcome)\b"):
        if re.search(pattern, text, re.I): errors.append('prohibited decision/closure/filing language')
    if 'draft decision-support only'  not in str(doc.get('standing_note','')).lower(): errors.append('missing standing note')
    return errors


def main(argv):
    p = Path(__file__).resolve().parents[1]/'evals/files/response_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
    errors = validate(json.loads(p.read_text() if p else sys.stdin.read()))
    for e in errors: print('ERROR', e)
    print(f'output validation: {len(errors)} error(s)')
    return int(bool(errors))
if __name__ == '__main__': raise SystemExit(main(sys.argv[1:]))
