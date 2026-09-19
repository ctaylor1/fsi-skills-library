"""Claimant-owned reason/evidence/request packet with source-bound chronology."""
from domain_support import Review, validate_shape

SKILL = 'claimant-dispute-packager'
METHOD = 'claimant-reason-evidence-request-matrix'


def validate(doc):
    return validate_shape(doc, arrays=('events', 'reasons', 'evidence', 'links', 'requests'), objects=('notice',),
                          dates=('date', 'received_date', 'response_due_date', 'effective_from', 'effective_to'),
                          lists=('source_refs', 'jurisdictions', 'lines_of_business', 'reason_ids', 'evidence_ids'),
                          booleans=('reasons_complete', 'chronology_complete'))


def evaluate(doc):
    d, r = doc['data'], Review(doc, METHOD)
    if doc['context']['capacity'] not in {'claimant', 'claimant-representative'} or d.get('claimant_id') != doc['context']['represented_party'] or d.get('claim_id') != doc['context']['object_id']:
        r.add('claimant-capacity', 'This is a claimant-owned packet; require matching claimant, claim and claimant/representative capacity.')
    if d.get('reasons_complete') is not True or d.get('chronology_complete') is not True:
        r.add('scope-completeness', 'Confirm supplied adverse reasons and material event chronology are complete within the stated dispute scope.')
    notice = d.get('notice', {})
    r.evidence(notice, 'Adverse notice, receipt and supplied appeal route')
    received = r.date(notice.get('received_date'), 'Notice received date', notice)
    due = r.date(notice.get('response_due_date'), 'Source-reviewed response due date', notice, future=True)
    if not notice.get('notice_id') or not notice.get('recipient') or not notice.get('route') or not notice.get('deadline_basis') or not notice.get('reviewed_by'):
        r.add('notice-route', 'Notice must carry ID, intended recipient, appeal route and source-bound deadline basis/reviewer; no default deadline is inferred.', notice)
    if received and due and due < received:
        r.add('deadline-order', 'Supplied response due date precedes receipt; a reviewer must resolve the governing basis.', notice)
    if due and due < r.date(doc['as_of'], 'As of'):
        r.add('past-supplied-deadline', 'Supplied response date has passed. Escalate promptly for options; the assistant does not determine that rights are lost.', notice, 'review')
    events, reasons, evidence, links, requests = (d.get(k, []) for k in ('events', 'reasons', 'evidence', 'links', 'requests'))
    for rows, key in ((events, 'event_id'), (reasons, 'reason_id'), (evidence, 'evidence_id'), (links, 'link_id'), (requests, 'request_id')):
        r.unique(rows, key)
    chronology = []
    for row in events:
        r.evidence(row, 'Dispute chronology event')
        day = r.date(row.get('date'), 'Event date', row)
        if not row.get('actor') or not row.get('description'):
            r.add('event-content', 'Events require actor and material factual description.', row)
        chronology.append(dict(row, chronological_date=day.isoformat() if day else None))
    chronology.sort(key=lambda x: (x['chronological_date'] or '', x.get('event_id') or ''))
    reason_map, evidence_map = {}, {}
    for row in reasons:
        r.evidence(row, 'Exact adverse reason and cited provision')
        if row.get('notice_id') != notice.get('notice_id') or not row.get('reason_text') or not row.get('provision'):
            r.add('reason-binding', 'Each adverse reason must bind this notice, retain exact reason text and identify the cited provision or explicit absent-in-notice marker.', row)
        reason_map[row.get('reason_id')] = row
    for row in evidence:
        r.evidence(row, 'Claimant packet evidence')
        r.date(row.get('date'), 'Evidence document date', row)
        if not row.get('description') or not row.get('locator'):
            r.add('evidence-locator', 'Evidence needs factual description and usable document/page locator.', row)
        evidence_map[row.get('evidence_id')] = row
    matrix = {rid: {'reason_id': rid, 'reason_text': row.get('reason_text'), 'provision': row.get('provision'),
                        'supporting': [], 'contrary': [], 'contextual': [], 'request_ids': []} for rid, row in reason_map.items()}
    seen_links = set()
    for row in links:
        r.evidence(row, 'Reason-to-evidence explanation')
        pair = (row.get('reason_id'), row.get('evidence_id'))
        if pair in seen_links or pair[0] not in matrix or pair[1] not in evidence_map or row.get('stance') not in {'supporting', 'contrary', 'contextual'} or not row.get('explanation'):
            r.add('evidence-link', 'Each unique reason/evidence link requires a valid stance and explanation; conflicting interpretations require one explicit contextual explanation.', row)
            continue
        seen_links.add(pair)
        matrix[pair[0]][row['stance']].append({'evidence_id': pair[1], 'explanation': row['explanation'], 'source_refs': row.get('source_refs', [])})
    request_report = []
    for row in requests:
        r.evidence(row, 'Claimant requested remedy or information')
        ids = row.get('reason_ids', [])
        if not ids or len(set(ids)) != len(ids) or any(x not in matrix for x in ids) or not row.get('request_text') or row.get('kind') not in {'reconsideration', 'information', 'correction'}:
            r.add('request-link', 'Each claimant request must identify unique adverse reasons and a concrete reconsideration, information or correction request.', row)
        else:
            for rid in ids:
                matrix[rid]['request_ids'].append(row.get('request_id'))
        request_report.append(dict(row, status='draft-unsubmitted'))
    if not events or not reasons or not requests:
        r.add('packet-inventory', 'A dispute packet requires material chronology, adverse reasons and claimant requests.')
    for rid, row in matrix.items():
        if not any(row[k] for k in ('supporting', 'contrary', 'contextual')):
            r.add('reason-evidence-gap', f'{rid}: no mapped evidence; preserve the gap and request relevant records.')
        if not row['request_ids']:
            r.add('unaddressed-reason', f'{rid}: no claimant request addresses this adverse reason.')
    return r.finish({'claim_id': d.get('claim_id'), 'claimant_id': d.get('claimant_id'), 'chronology': chronology,
                         'reason_evidence_matrix': list(matrix.values()), 'claimant_requests': request_report,
                         'recipient': notice.get('recipient'), 'route': notice.get('route'), 'supplied_response_due_date': notice.get('response_due_date'),
                         'merits_determined': False, 'submitted': False, 'carrier_response_drafted': False})
