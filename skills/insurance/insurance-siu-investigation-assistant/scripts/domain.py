"""Hypothesis/contradiction matrix, custody continuity and lawful draft tasks."""
import re

from domain_support import Review, validate_shape
from insurance_contract import timestamp

SKILL = 'insurance-siu-investigation-assistant'
METHOD = 'hypothesis-contradiction-custody-task-review'


def validate(doc):
    errors = validate_shape(doc, arrays=('hypotheses', 'evidence', 'links', 'custody', 'tasks'),
                            dates=('due_date', 'effective_from', 'effective_to'),
                            lists=('source_refs', 'jurisdictions', 'lines_of_business', 'evidence_ids'),
                            booleans=('lawful_collection_reviewed', 'authority_reviewed', 'privacy_reviewed', 'evidence_inventory_complete', 'tests_alternative'))
    for row in doc.get('data', {}).get('custody', []) if not errors else []:
        if row.get('at') is not None:
            try:
                timestamp(row['at'])
            except (TypeError, ValueError):
                errors.append('custody at requires an ISO timestamp with timezone')
    return errors


def evaluate(doc):
    d, r = doc['data'], Review(doc, METHOD)
    if d.get('claim_id') != doc['context']['object_id'] or doc['context']['capacity'] != 'insurer-siu-investigation':
        r.add('capacity', 'Require claim-bound insurer SIU capacity; claimant representation and claim adjudication are separate workflows.')
    if not d.get('investigation_owner') or not d.get('referral_question') or d.get('evidence_inventory_complete') is not True:
        r.add('scope', 'Specify investigation owner, bounded referral question and complete supplied evidence inventory.')
    hypotheses, evidence, links, custody, tasks = (d.get(k, []) for k in ('hypotheses', 'evidence', 'links', 'custody', 'tasks'))
    for rows, key in ((hypotheses, 'hypothesis_id'), (evidence, 'evidence_id'), (links, 'link_id'), (custody, 'transfer_id'), (tasks, 'task_id')):
        r.unique(rows, key)
    hypothesis_map, evidence_map, matrix = {}, {}, {}
    for row in hypotheses:
        r.evidence(row, 'Investigation hypothesis')
        if not row.get('question') or not row.get('innocent_alternative'):
            r.add('alternative', 'Each hypothesis needs a falsifiable question and explicit innocent alternative.', row)
        hypothesis_map[row.get('hypothesis_id')] = row
        matrix[row.get('hypothesis_id')] = {'hypothesis_id': row.get('hypothesis_id'), 'question': row.get('question'),
                                              'innocent_alternative': row.get('innocent_alternative'), 'supports': [], 'contradicts': [], 'neutral': []}
    for row in evidence:
        r.evidence(row, 'Evidence item and collection authority')
        if not row.get('description') or not row.get('initial_holder') or not row.get('locator') or not re.fullmatch(r'[0-9a-f]{64}', row.get('content_digest') or ''):
            r.add('evidence-identity', 'Evidence needs description, locator, initial holder and supplied SHA256 content digest.', row)
        if row.get('lawful_collection_reviewed') is not True or not row.get('collection_basis') or not row.get('reviewed_by'):
            r.add('collection-authority', 'Evidence collection basis requires a named human lawful-access reviewer.', row)
        evidence_map[row.get('evidence_id')] = row
    seen_links = set()
    for row in links:
        r.evidence(row, 'Hypothesis evidence relationship')
        pair = (row.get('hypothesis_id'), row.get('evidence_id'))
        if pair in seen_links or pair[0] not in matrix or pair[1] not in evidence_map or row.get('stance') not in {'supports', 'contradicts', 'neutral'} or not row.get('reasoning'):
            r.add('hypothesis-link', 'Each unique hypothesis/evidence relationship requires supported stance and reasoning.', row)
            continue
        seen_links.add(pair)
        matrix[pair[0]][row['stance']].append({'evidence_id': pair[1], 'reasoning': row['reasoning'], 'source_refs': row.get('source_refs', [])})
    custody_map = {eid: [] for eid in evidence_map}
    for row in custody:
        r.evidence(row, 'Custody transfer')
        eid = row.get('evidence_id')
        try:
            at = timestamp(row.get('at'))
            if at.date().isoformat() > doc['as_of']:
                raise ValueError('future')
        except (ValueError, TypeError):
            at = None
            r.add('custody-date', 'Custody timestamp must be known and no later than as_of.', row)
        if eid not in evidence_map:
            r.add('custody-item', 'Custody transfer refers to an unknown evidence item.', row)
        else:
            custody_map[eid].append((row, at))
    custody_report = []
    for eid, transfers in custody_map.items():
        evidence_row = evidence_map[eid]
        holder, seen_times, valid = evidence_row.get('initial_holder'), set(), True
        for row, at in sorted(transfers, key=lambda x: (x[1] is not None, x[1])):
            if at is None or at in seen_times or row.get('from_holder') != holder or not row.get('to_holder') or row.get('content_digest') != evidence_row.get('content_digest'):
                valid = False
                r.add('custody-break', 'Custody order, holder chain or digest does not match the retained original; resolve before reliance.', row)
            seen_times.add(at)
            holder = row.get('to_holder')
        if not transfers:
            valid = False
            r.add('custody-missing', f'{eid}: record receipt or custody attestation, even when no subsequent transfer occurred.', evidence_row)
        custody_report.append({'evidence_id': eid, 'current_holder': holder if valid else None, 'continuity': 'consistent-supplied-records' if valid else 'unresolved',
                                   'content_digest': evidence_row.get('content_digest'), 'authenticated': False})
    task_report = []
    for row in tasks:
        evidence_ids = row.get('evidence_ids', [])
        valid = r.evidence(row, 'Lawful investigation task plan')
        due = r.date(row.get('due_date'), 'Investigation task due date', row, future=True)
        if row.get('hypothesis_id') not in hypothesis_map or any(x not in evidence_map for x in evidence_ids) or len(set(evidence_ids)) != len(evidence_ids) or not row.get('owner') or not row.get('purpose'):
            valid = False
            r.add('task-binding', 'Task needs hypothesis, known unique evidence IDs, owner and bounded purpose.', row)
        if row.get('method') not in {'supplied-record-review', 'authorized-specialist-interview', 'authorized-record-request'} or row.get('authority_reviewed') is not True or row.get('privacy_reviewed') is not True or not row.get('authority_basis'):
            valid = False
            r.add('task-authority', 'Task needs a supported lawful method and source-bound authority/privacy review; no covert access or surveillance is enabled.', row)
        task_report.append(dict(row, draft_state='review-ready' if valid and due else 'needs-data', execution='not_performed'))
    if not hypotheses or not evidence or not tasks:
        r.add('investigation-inventory', 'Supply hypotheses, evidence, contradictory-evidence search and bounded tasks.')
    for hid, row in matrix.items():
        if not any(row[k] for k in ('supports', 'contradicts', 'neutral')):
            r.add('hypothesis-evidence-gap', f'{hid}: no evidence relationships have been supplied.')
        if not row['contradicts'] and not any(x.get('hypothesis_id') == hid and x.get('tests_alternative') is True for x in tasks):
            r.add('alternative-test', f'{hid}: missing contradictory evidence requires an explicit task testing the innocent alternative.')
    return r.finish({'hypothesis_matrix': list(matrix.values()), 'custody_register': custody_report, 'task_plan': task_report,
                         'investigation_owner': d.get('investigation_owner'), 'fraud_verdict': 'not-determined',
                         'referral_submitted': False, 'claim_decision': 'not-performed', 'evidence_authentication': 'not-performed'})
