"""Consent-aware wealth prospect/referral briefing and internal outreach drafts."""
from copy import deepcopy
from wealth_contract import make_output, iso_date, nonempty, source_errors
from wealth_workflow import (base_errors, rows, texts, enum, number, dec, cited, add,
                             base_findings, common_result, validate_result)

SKILL = 'wealth-prospect-referral-preparer'
CHANNELS = {'email', 'manual-phone'}
KINDS = {'firm-record', 'prospect-provided', 'referrer-provided', 'approved-public-record'}
FACT_TOPICS = {'service-interest', 'professional-context', 'engagement-preference', 'existing-relationship'}
REVIEW_TOPICS = {'privacy-data-use', 'marketing-content', 'channel-permission', 'referrer-authority', 'referral-compensation'}


def dates(row, errors, path, start='effective_date', end='valid_until'):
    for key in (start, end):
        if row.get(key) is not None and iso_date(row[key]) is None:
            errors.append(f'{path}.{key} must be ISO date or null')
    if iso_date(row.get(start)) and iso_date(row.get(end)) and row[end] < row[start]:
        errors.append(f'{path} validity ends before its effective date')


def text_fields(row, keys, errors, path):
    for key in keys:
        if not nonempty(row.get(key)):
            errors.append(f'{path}.{key} must be nonempty')


def validate(doc):
    errors = base_errors(doc)
    if errors:
        return errors
    prohibited_keys = {'protected_traits', 'race', 'ethnicity', 'religion', 'sexual_orientation', 'gender_identity', 'medical_diagnosis', 'genetic_information', 'political_affiliation'}
    def prohibited_fields(value):
        if isinstance(value, dict):
            return bool(set(value) & prohibited_keys) or any(prohibited_fields(v) for v in value.values())
        if isinstance(value, list):
            return any(prohibited_fields(v) for v in value)
        return False
    if prohibited_fields(doc):
        errors.append('protected-trait and sensitive-profile fields are not accepted for prospect targeting')
    p = doc['policy']
    if not texts(p.get('allowed_channels')) or any(c not in CHANNELS for c in p['allowed_channels']):
        errors.append('policy.allowed_channels must explicitly select supported channels')
    if not texts(p.get('permitted_source_kinds')) or any(k not in KINDS for k in p['permitted_source_kinds']):
        errors.append('policy.permitted_source_kinds must explicitly select supported sources')
    if type(p.get('max_fact_age_days')) is not int or not 1 <= p['max_fact_age_days'] <= 3660:
        errors.append('policy.max_fact_age_days must be an integer 1..3660')
    if p.get('contact_basis') != 'documented-affirmative-permission-only':
        errors.append('this bounded workflow requires documented-affirmative-permission-only under firm policy; no legal exception is inferred')
    if not enum(p.get('regulatory_profile'), {'SEC-registered-adviser', 'state-registered-adviser', 'FINRA-member', 'bank-trust', 'dual-registrant'}):
        errors.append('policy.regulatory_profile must explicitly identify the supplied firm profile')
    for key in ('prospect', 'firm', 'outreach_request'):
        if not isinstance(doc.get(key), dict):
            errors.append(f'{key} must be an object')
    if errors:
        return errors
    text_fields(doc['prospect'], ('prospect_id', 'display_name_masked'), errors, 'prospect')
    if not enum(doc['prospect'].get('identity_basis'), {'provisional-prospect-case', 'documented-existing-record'}):
        errors.append('prospect.identity_basis must explicitly describe provisional or documented record identity')
    text_fields(doc['firm'], ('firm_id', 'display_name', 'representative', 'postal_address', 'opt_out_instruction'), errors, 'firm')
    text_fields(doc['outreach_request'], ('purpose_id',), errors, 'outreach_request')
    if doc['outreach_request'].get('purpose_id') != 'introductory-service-discussion':
        errors.append('outreach purpose is limited to introductory-service-discussion')
    if not enum(doc['outreach_request'].get('channel'), CHANNELS) or not texts(doc['outreach_request'].get('service_ids')):
        errors.append('outreach_request requires a supported channel and nonempty unique service_ids')
    for s in rows(p, 'services', errors, 'service_id'):
        text_fields(s, ('name', 'scope', 'discussion_question'), errors, 'policy.services')
    for r in rows(doc, 'research_permissions', errors, 'record_source_id'):
        if not enum(r.get('kind'), KINDS) or not enum(r.get('status'), {'permitted', 'denied', 'unknown'}):
            errors.append('research permission requires supported kind and explicit status')
        text_fields(r, ('owner', 'permission_reference'), errors, 'research_permissions')
        if not texts(r.get('permitted_uses'), True) or any(u not in {'internal-research', 'outreach-drafting'} for u in r['permitted_uses']):
            errors.append('research permission uses must explicitly list internal-research and/or outreach-drafting')
        dates(r, errors, 'research_permissions')
    for f in rows(doc, 'facts', errors, 'fact_id'):
        text_fields(f, ('text', 'record_source_id'), errors, 'facts')
        if not enum(f.get('topic'), FACT_TOPICS) or not enum(f.get('evidence_state'), {'documented', 'reported'}):
            errors.append('facts require an allowed professional/service topic and documented/reported state; sensitive/protected-trait targeting is outside scope')
        if f.get('sensitivity') != 'ordinary-service-context':
            errors.append('protected traits and sensitive profiling records cannot enter this package')
        if f.get('observed_date') is not None and iso_date(f['observed_date']) is None:
            errors.append('fact observed_date must be ISO date or null')
    for c in rows(doc, 'service_candidates', errors, 'candidate_id'):
        text_fields(c, ('service_id',), errors, 'service_candidates')
        if not texts(c.get('supporting_fact_ids')):
            errors.append('service candidate needs explicit supporting_fact_ids')
    for r in rows(doc, 'channel_permissions', errors, 'permission_id'):
        text_fields(r, ('prospect_id', 'firm_id', 'purpose_id'), errors, 'channel_permissions')
        if not enum(r.get('channel'), CHANNELS) or not enum(r.get('status'), {'granted', 'denied', 'withdrawn', 'unknown'}):
            errors.append('channel permission needs a supported channel and explicit status')
        if not enum(r.get('basis'), {'prospect-direct', 'authorized-representative', 'public-record', 'referral-only', 'unknown'}):
            errors.append('channel permission basis is unsupported')
        if r.get('authority_reference') is not None and not nonempty(r['authority_reference']):
            errors.append('authority_reference must be a source locator or null')
        dates(r, errors, 'channel_permissions')
    for c in rows(doc, 'contact_controls', errors, 'channel'):
        if not enum(c.get('channel'), CHANNELS | {'all'}) or not enum(c.get('opt_out_status'), {'none-recorded', 'opted-out', 'unknown'}):
            errors.append('contact control requires supported channel and explicit opt-out state')
        if not enum(c.get('screening_status'), {'recorded-no-block', 'block-recorded', 'unknown'}):
            errors.append('contact control requires explicit supplied suppression/screening status')
        dates(c, errors, 'contact_controls', 'checked_at')
    for r in rows(doc, 'review_records', errors, 'review_id'):
        if not enum(r.get('topic'), REVIEW_TOPICS) or not enum(r.get('status'), {'recorded', 'pending', 'conflicting'}):
            errors.append('review record requires supported topic and explicit status')
        text_fields(r, ('owner', 'reference', 'rationale'), errors, 'review_records')
        if not enum(r.get('applicability'), {'applies', 'not-applicable', 'unresolved'}):
            errors.append('review record needs explicit attributed applicability and rationale')
        dates(r, errors, 'review_records', 'as_of')
    if 'referral' not in doc:
        errors.append('referral must be explicitly null for no referral or a supported object')
    referral = doc.get('referral')
    if referral is not None:
        if not isinstance(referral, dict):
            errors.append('referral must be object or null')
        else:
            if not enum(referral.get('referrer_relationship_to_firm'), {'client', 'nonclient', 'affiliate', 'unknown'}):
                errors.append('referrer relationship to firm must be explicitly recorded')
            text_fields(referral, ('referral_id', 'referrer_id', 'referrer_name_masked', 'relationship_description'), errors, 'referral')
            if referral.get('referral_date') is not None and iso_date(referral['referral_date']) is None:
                errors.append('referral_date must be ISO date or null')
            for key in ('sharing_authority', 'incentives', 'conflicts', 'disclosure'):
                if not isinstance(referral.get(key), dict):
                    errors.append(f'referral.{key} must be an object')
            if all(isinstance(referral.get(k), dict) for k in ('sharing_authority', 'incentives', 'conflicts', 'disclosure')):
                a, inc, conf = referral['sharing_authority'], referral['incentives'], referral['conflicts']
                if not enum(a.get('status'), {'documented', 'denied', 'unknown'}) or not texts(a.get('record_source_ids'), True):
                    errors.append('sharing_authority needs explicit status and unique record_source_ids')
                text_fields(a, ('prospect_id', 'firm_id', 'reference'), errors, 'sharing_authority')
                dates(a, errors, 'sharing_authority')
                if not enum(inc.get('status'), {'none', 'cash', 'noncash', 'mixed', 'unknown'}) or inc.get('currency') != 'USD':
                    errors.append('incentives must explicitly identify kind and USD currency')
                if inc.get('amount') is not None and not number(inc['amount']):
                    errors.append('incentive amount must be a finite nonnegative amount or null')
                text_fields(inc, ('description',), errors, 'incentives')
                if not enum(conf.get('status'), {'none-recorded', 'identified', 'unknown'}):
                    errors.append('referral conflicts status must be explicit')
                text_fields(conf, ('description',), errors, 'conflicts')
                text_fields(referral['disclosure'], ('version', 'text'), errors, 'disclosure')
    return errors


def current(row, doc, findings, path, start='effective_date'):
    first, last = iso_date(row.get(start)), iso_date(row.get('valid_until'))
    if first is None or last is None or not first <= iso_date(doc['as_of']) <= last:
        add(findings, 'current-evidence-gap', 'Dated evidence is missing, not effective or expired for this request', path)
        return False
    return True


def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError('; '.join(errors))
    findings = base_findings(doc)
    for key in ('prospect', 'firm', 'outreach_request'):
        cited(doc[key], doc, findings, key)
    prospect, firm, request = doc['prospect'], doc['firm'], doc['outreach_request']
    channel = request['channel']
    if channel not in doc['policy']['allowed_channels']:
        add(findings, 'channel-policy-gap', 'Requested channel is not enabled by the supplied policy', 'outreach_request')
    permissions = {}
    registry = {s['source_id'] for s in doc['sources']}
    for p in doc['research_permissions']:
        supported = cited(p, doc, findings, 'research_permissions.' + p['record_source_id'])
        supported = current(p, doc, findings, 'research_permissions.' + p['record_source_id']) and supported
        if p['record_source_id'] not in registry or p['kind'] not in doc['policy']['permitted_source_kinds']:
            add(findings, 'research-source-gap', 'Source identity or source kind is not permitted by the supplied register', p['record_source_id'])
            supported = False
        if p['status'] != 'permitted' or 'internal-research' not in p['permitted_uses']:
            add(findings, 'research-permission-gap', 'Internal research use is denied or not documented', p['record_source_id'])
            supported = False
        permissions[p['record_source_id']] = (p, supported)
    accepted, excluded, fact_ids, outreach_fact_ids = [], [], set(), set()
    for f in doc['facts']:
        path = 'facts.' + f['fact_id']
        supported = cited(f, doc, findings, path)
        permission, permitted = permissions.get(f['record_source_id'], (None, False))
        item_sources = f.get('source_ids') if isinstance(f.get('source_ids'), list) else []
        if not permitted or f['record_source_id'] not in item_sources:
            add(findings, 'fact-use-gap', 'Fact lacks an explicit permitted source and item-level link; not used for service inference', path)
            supported = False
        if permission and permission['kind'] == 'referrer-provided':
            referral = doc.get('referral')
            authority = referral['sharing_authority'] if referral else None
            authority_current = authority and iso_date(authority.get('effective_date')) and iso_date(authority.get('valid_until')) and authority['effective_date'] <= doc['as_of'] <= authority['valid_until']
            if not authority or authority['status'] != 'documented' or not authority_current or authority['prospect_id'] != prospect['prospect_id'] or authority['firm_id'] != firm['firm_id'] or f['record_source_id'] not in authority['record_source_ids'] or source_errors(authority.get('source_ids'), doc):
                add(findings, 'referrer-fact-use-gap', 'Referrer fact is not used without scoped current sharing-authority evidence', path)
                supported = False
        observed = iso_date(f.get('observed_date'))
        if observed is None or not 0 <= (iso_date(doc['as_of']) - observed).days <= doc['policy']['max_fact_age_days']:
            add(findings, 'fact-date-gap', 'Fact observation is missing, future or outside the supplied freshness window', path)
            supported = False
        if supported:
            accepted.append(deepcopy(f))
            fact_ids.add(f['fact_id'])
            if 'outreach-drafting' in permission['permitted_uses']:
                outreach_fact_ids.add(f['fact_id'])
        else:
            excluded.append({'fact_id': f['fact_id'], 'record_source_id': f['record_source_id'], 'state': 'not-used'})
    if not doc['facts']:
        add(findings, 'missing-prospect-context', 'No permitted professional or service context supplied', 'facts')
    services = {}
    for s in doc['policy']['services']:
        supported = cited(s, doc, findings, 'policy.services.' + s['service_id'])
        services[s['service_id']] = (s, supported)
    candidates = []
    candidate_services = set()
    for c in doc['service_candidates']:
        supported = cited(c, doc, findings, c['candidate_id'])
        service, service_supported = services.get(c['service_id'], (None, False))
        valid = supported and service_supported and set(c['supporting_fact_ids']).issubset(fact_ids)
        if not valid:
            add(findings, 'service-context-gap', 'Candidate service or supporting facts lack permitted current evidence', c['candidate_id'])
        outreach_permitted = valid and set(c['supporting_fact_ids']).issubset(outreach_fact_ids)
        if outreach_permitted:
            candidate_services.add(c['service_id'])
        candidates.append({'candidate_id': c['candidate_id'], 'service_id': c['service_id'],
                           'status': 'question-only-not-a-fit-conclusion' if valid else 'not-evaluable',
                           'outreach_use_permitted_under_supplied_records': outreach_permitted,
                           'supporting_fact_ids': deepcopy(c['supporting_fact_ids']),
                           'discussion_question': service['discussion_question'] if valid else None,
                           'service_scope': service['scope'] if valid else None, 'source_ids': deepcopy(c.get('source_ids'))})
    for sid in request['service_ids']:
        if sid not in candidate_services:
            add(findings, 'outreach-service-gap', 'Requested service lacks an evidenced service-discussion candidate', sid)
    selected_permissions = [p for p in doc['channel_permissions'] if p['channel'] == channel]
    for p in doc['channel_permissions']:
        cited(p, doc, findings, 'channel_permissions.' + p['permission_id'])
    if len(selected_permissions) != 1:
        add(findings, 'contact-permission-gap', 'One unambiguous selected-channel permission record is required; never choose between competing permissions', 'channel_permissions')
    for p in selected_permissions:
        current(p, doc, findings, 'channel_permissions.' + p['permission_id'])
        if (p['prospect_id'], p['firm_id'], p['purpose_id']) != (prospect['prospect_id'], firm['firm_id'], request['purpose_id']):
            add(findings, 'contact-scope-mismatch', 'Permission does not match this prospect, firm and purpose', p['permission_id'])
        if p['status'] != 'granted' or p['basis'] not in {'prospect-direct', 'authorized-representative'}:
            add(findings, 'contact-permission-gap', 'Referral, public data, unknown or withdrawn/denied permission does not support outreach drafting', p['permission_id'])
        if p['basis'] == 'authorized-representative' and not nonempty(p.get('authority_reference')):
            add(findings, 'representative-authority-gap', 'Representative permission needs a documented authority locator; role alone is insufficient', p['permission_id'])
    controls = {r['channel']: r for r in doc['contact_controls']}
    for c in doc['contact_controls']:
        cited(c, doc, findings, 'contact_controls.' + c['channel'])
        current(c, doc, findings, 'contact_controls.' + c['channel'], 'checked_at')
        if c['channel'] in {'all', channel} and (c['opt_out_status'] != 'none-recorded' or c['screening_status'] != 'recorded-no-block'):
            add(findings, 'contact-suppression', 'Opt-out, screening block or unknown suppression state withholds outreach; public/referral data cannot override it', 'contact_controls.' + c['channel'])
    for scope in ('all', channel):
        if scope not in controls:
            add(findings, 'suppression-inventory-gap', 'Explicit current global and channel suppression checks are required', 'contact_controls.' + scope)
    required = {'privacy-data-use', 'marketing-content', 'channel-permission'}
    referral = doc['referral']
    if referral is not None:
        required |= {'referrer-authority', 'referral-compensation'}
        for key, row in [('referral', referral)] + [('referral.' + k, referral[k]) for k in ('sharing_authority', 'incentives', 'conflicts', 'disclosure')]:
            cited(row, doc, findings, key)
        if referral['referrer_relationship_to_firm'] == 'unknown':
            add(findings, 'referrer-relationship-gap', 'Referrer relationship to firm is unknown; no testimonial/endorsement characterization is inferred', 'referral')
        if iso_date(referral.get('referral_date')) is None or referral['referral_date'] > doc['as_of']:
            add(findings, 'referral-date-gap', 'Referral date is unknown or future', 'referral')
        a, inc, conf = referral['sharing_authority'], referral['incentives'], referral['conflicts']
        current(a, doc, findings, 'referral.sharing_authority')
        if a['status'] != 'documented' or a['prospect_id'] != prospect['prospect_id'] or a['firm_id'] != firm['firm_id']:
            add(findings, 'referrer-authority-gap', 'Data-sharing authority is absent, denied or scoped to a different prospect/firm', 'referral.sharing_authority')
        for sid, (permission, _) in permissions.items():
            if permission['kind'] == 'referrer-provided' and sid not in a['record_source_ids']:
                add(findings, 'referral-sharing-scope-gap', 'Referrer authority does not cover this supplied record source', sid)
        if inc['status'] == 'unknown' or inc.get('amount') is None:
            add(findings, 'incentive-gap', 'Cash/noncash economics must be explicitly recorded; unknown compensation is never none', 'referral.incentives')
        elif (inc['status'] == 'none') != (dec(inc['amount']) == 0):
            add(findings, 'incentive-conflict', 'Incentive status and supplied amount disagree', 'referral.incentives')
        if conf['status'] == 'unknown':
            add(findings, 'conflict-context-gap', 'Referral conflicts have not been assessed in the supplied evidence', 'referral.conflicts')
    elif any(p['kind'] == 'referrer-provided' for p, _ in permissions.values()):
        add(findings, 'missing-referral-context', 'Referrer-provided records require referral and sharing-authority context', 'referral')
    for r in doc['review_records']:
        cited(r, doc, findings, 'review_records.' + r['review_id'])
        current(r, doc, findings, 'review_records.' + r['review_id'], 'as_of')
        if r['applicability'] == 'unresolved':
            add(findings, 'review-applicability-gap', 'The responsible reviewer has not resolved applicability for this prospect/referral scope', r['review_id'])
        if r['status'] == 'conflicting':
            add(findings, 'review-conflict', 'A supplied specialist review is conflicting and remains unresolved', r['review_id'])
    for topic in sorted(required):
        matching = [r for r in doc['review_records'] if r['topic'] == topic]
        if len(matching) != 1 or matching[0]['status'] != 'recorded':
            add(findings, 'review-evidence-gap', 'One recorded review under the firm applicability policy is required for ' + topic, 'review_records.' + topic)
    draft = None
    if not findings:
        selected = [services[s][0] for s in request['service_ids']]
        parts = [f"Hello {prospect['display_name_masked']},", f"I am {firm['representative']} from {firm['display_name']}. This is an introduction to our services."]
        for s in selected:
            parts.append(s['name'] + ': ' + s['scope'])
            parts.append(s['discussion_question'])
        if referral is not None:
            parts.append(referral['disclosure']['text'])
        parts.extend([firm['opt_out_instruction'], firm['display_name'] + ' | ' + firm['postal_address']])
        draft = {'channel': channel, 'subject': 'Introduction to ' + firm['display_name'] + ' services' if channel == 'email' else None,
                 'body': '\n\n'.join(parts), 'source_ids': sorted({sid for row in [prospect, firm] + selected + ([referral['disclosure']] if referral else []) for sid in row['source_ids']}),
                 'status': 'internal-draft-for-communications-review', 'send_authorization': False}
    result = common_result(doc)
    result.update(prospect=deepcopy(prospect), firm=deepcopy(firm), research_permission_register=deepcopy(doc['research_permissions']),
                  supported_facts=accepted, excluded_fact_register=excluded, service_discussion_candidates=candidates,
                  referral_context=deepcopy(referral), channel_permission_register=deepcopy(doc['channel_permissions']),
                  contact_control_register=deepcopy(doc['contact_controls']), specialist_review_register=deepcopy(doc['review_records']),
                  required_review_topics=sorted(required), outreach_draft=draft,
                  draft_status='withheld-pending-evidence-or-contact-controls' if draft is None else 'draft-for-human-review',
                  contact_permission_determination='not-made', prospect_qualification='not-decided',
                  next_questions=[{'path': f['path'], 'question': f['message']} for f in findings],
                  limitations=['Service candidates are questions, not inferred wealth, eligibility, protected-trait targeting, risk assessments or recommendations.',
                               'Public records, client/referrer assertions and named review owners do not authenticate permissions. No scraping, enrichment, contact, CRM write or final legal clearance occurs.',
                               'The draft requires a fresh applicable communications/privacy review and contact-control check before any human use.'])
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    return validate_result(out, SKILL, build)
