"""Reconcile explicit insurance subledger/GL scope and balanced draft adjustments."""
from collections import defaultdict
from decimal import Decimal

from insurance_foundation import number
from local_review import Review, shape, text

SKILL = 'insurance-financial-close-reviewer'
METHOD = 'subledger-gl-proposed-adjustment-v1'


def validate(doc):
    errors = shape(doc, objects=('profile', 'period'), lists=('accounts', 'subledger_balances', 'gl_balances', 'proposed_journals'), numbers=('amount',))
    for journal in doc.get('data', {}).get('proposed_journals', []) if not errors else []:
        if 'lines' in journal and (not isinstance(journal['lines'], list) or any(not isinstance(x, dict) for x in journal['lines'])):
            errors.append('journal.lines must be a list of objects')
    return errors


def evaluate(doc):
    d, r = doc['data'], Review(doc)
    p = r.profile(METHOD)
    r.check(d.get('sign_convention') == 'debit-positive' and p.get('sign_convention') == 'debit-positive', 'sign-convention', 'All supplied balance and journal amounts must use the reviewed debit-positive convention.')
    start = r.date(d.get('period', {}).get('start'), 'period-start', latest=doc['as_of'])
    end = r.date(d.get('period', {}).get('end'), 'period-end', equal=d.get('valuation_date'), latest=doc['as_of'])
    r.check(start is not None and end is not None and start <= end, 'period-order', 'Period start must be no later than period end.')
    r.check(d.get('subledgers_complete') is True and d.get('gl_complete') is True and all(k in d for k in ('accounts', 'subledger_balances', 'gl_balances', 'proposed_journals')), 'close-completeness', 'Require complete selected account mapping, subledger balances, GL controls and explicit proposed-journal inventory.')
    accounts, components, gl, sub = {}, set(), {}, defaultdict(Decimal)
    for row in d.get('accounts', []):
        aid = row.get('account_id')
        r.evidence(row, 'account-map')
        r.check(text(aid) and aid not in accounts and row.get('normal_side') in {'debit', 'credit'} and text(row.get('reviewed_by')), 'account-map', 'Unique reviewed account mapping and normal balance side are required.', row)
        accounts[aid] = row
    r.check(bool(accounts), 'account-scope', 'Select at least one insurance close account.')
    for row in d.get('subledger_balances', []):
        r.bind(row, 'subledger')
        cid, aid, value = row.get('component_id'), row.get('account_id'), number(row.get('amount'))
        r.check(text(cid) and cid not in components and aid in accounts and value is not None, 'subledger-identity', 'Each subledger component must uniquely map to a selected control account with known signed balance.', row)
        components.add(cid)
        if aid in accounts and value is not None:
            sub[aid] += value
    for row in d.get('gl_balances', []):
        r.bind(row, 'gl')
        aid, value = row.get('account_id'), number(row.get('amount'))
        r.check(aid in accounts and aid not in gl and value is not None, 'gl-identity', 'Each selected GL account requires exactly one known control balance.', row)
        gl[aid] = value
    r.check(set(gl) == set(accounts) and set(sub) == set(accounts), 'account-coverage', 'Every selected account requires both a GL control and explicit subledger balance; omitted zero is unknown.')
    adjustments, journals, seen_journals = defaultdict(Decimal), [], set()
    for row in d.get('proposed_journals', []):
        r.bind(row, 'journal')
        jid = row.get('journal_id')
        r.check(text(jid) and jid not in seen_journals and text(row.get('reviewed_by')) and row.get('status') == 'proposed', 'journal-identity', 'Each balanced adjustment must be uniquely identified, reviewed and explicitly proposed, never silently treated as posted.', row)
        seen_journals.add(jid)
        date = r.date(row.get('date'), 'journal', latest=doc['as_of'], row=row)
        r.check(date is not None and start is not None and end is not None and start <= date <= end, 'journal-period', 'Proposed journal date must lie within the close period.', row)
        lines = row.get('lines', [])
        r.check(len(lines) >= 2, 'journal-lines', 'A proposed entry needs at least two lines and all offset accounts in scope.', row)
        total, ids, valid_lines = Decimal(0), set(), True
        for line in lines:
            lid, aid, value = line.get('line_id'), line.get('account_id'), number(line.get('amount'))
            valid_lines &= r.evidence(line, 'journal-line')
            valid_lines &= r.check(text(lid) and lid not in ids and aid in accounts and value is not None, 'journal-line-identity', 'Journal lines must uniquely identify mapped accounts and known debit-positive amounts.', line)
            ids.add(lid)
            if aid in accounts and value is not None:
                total += value
                adjustments[aid] += value
        r.check(valid_lines and total == 0, 'unbalanced-proposal', 'Proposed journal debit-positive amounts must sum exactly to zero; no balancing plug.', row)
        journals.append({'journal_id': jid, 'signed_sum': total if valid_lines else None, 'posted': False})
    reconciliations = None
    if not r.blocked:
        reconciliations = []
        for aid in sorted(accounts):
            before, after = sub[aid] - gl[aid], sub[aid] - (gl[aid] + adjustments[aid])
            reconciliations.append({'account_id': aid, 'subledger_balance': sub[aid], 'gl_balance': gl[aid], 'difference_before': before, 'proposed_gl_delta': adjustments[aid], 'pro_forma_gl_balance': gl[aid] + adjustments[aid], 'difference_after_proposal': after})
            if before or after:
                r.add('close-control-break', f'{aid}: current difference {before}; proposed pro forma difference {after}. Review the original break and any residual.', accounts[aid], block=False, severity='review')
    return r.result({'account_reconciliations': reconciliations, 'journal_checks': journals,
                     'basis': d.get('basis'), 'currency': d.get('currency'), 'period': d.get('period'),
                     'sign_convention': 'debit-positive', 'close_certified': False, 'journal_posting_authorized': False,
                     'measurement_and_recognition_decisions': 'outside-method; approved supplied basis required'})
