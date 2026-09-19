from decimal import Decimal
from analytics_helpers import Review, rows, text, total, ratio, validate_with


def evaluate(doc):
    r = Review(doc)
    d, scope = r.data, r.data.get('scope', {})
    r.evidence(scope, 'market scope')
    keys = ('market_id', 'metric', 'currency', 'basis', 'period', 'product', 'geography')
    if not all(text(scope.get(k)) for k in keys):
        r.add('scope-gap', 'Market, product, geography, period, metric, currency and basis are required', scope)
    observations = rows(d.get('observations', []), 'entity_id')
    if not observations:
        r.add('market-gap', 'Comparable market observations are unavailable')
    shares, values = [], []
    denominator = d.get('market_total', {})
    total_ok = r.evidence(denominator, 'market denominator') and r.scope(denominator, scope, keys)
    market_total = r.num(denominator, 'value', positive=True)
    if not total_ok:
        market_total = None
    for row in observations:
        valid = r.evidence(row, row['entity_id']) and r.scope(row, scope, keys)
        value = r.num(row, 'value')
        if not valid:
            value = None
        values.append(value)
        shares.append({**row, 'comparable_value': value, 'market_share': ratio(value, market_total)})
    listed = total(values)
    remainder = market_total - listed if market_total is not None and listed is not None else None
    complete = d.get('inventory_complete') is True
    if not complete:
        r.add('market-incomplete', 'Listed competitors are a partial market; concentration is unavailable')
    if remainder is not None and (remainder < 0 or (complete and remainder != 0)):
        r.add('market-total-conflict', 'Listed entities do not reconcile to the supplied market total', denominator)
    hhi = sum((s['market_share'] ** 2 for s in shares), Decimal(0)) * 10000 if complete and remainder == 0 and all(s['market_share'] is not None for s in shares) else None
    claims = rows(d.get('claims', []), 'claim_id')
    ids = {x['entity_id'] for x in observations}
    if not claims:
        r.add('research-gap', 'A source-backed strategic claim and implication register is required')
    for claim in claims:
        r.evidence(claim, claim['claim_id'])
        if claim.get('kind') not in {'fact', 'inference', 'hypothesis'}:
            raise ValueError('claim.kind must be fact, inference or hypothesis')
        for field in ('statement', 'implication', 'falsification_or_next_evidence'):
            if not text(claim.get(field)):
                r.add('claim-gap', claim['claim_id'] + ': ' + field + ' is missing', claim)
        if not isinstance(claim.get('entity_ids'), list) or any(x not in ids for x in claim['entity_ids']):
            raise ValueError('claim.entity_ids must reference listed entities (empty allowed for market-wide claim)')
        if claim.get('contrary_evidence_reviewed') is not True:
            r.add('contrary-gap', claim['claim_id'] + ': contrary evidence review incomplete', claim)
        contrary = claim.get('contrary_source_refs')
        if not isinstance(contrary, list):
            r.add('contrary-gap', 'Explicit contrary_source_refs inventory required', claim)
        elif contrary:
            r.evidence({'source_refs': contrary}, 'contrary evidence')
            r.add('contested-claim', claim['claim_id'] + ': competing evidence retained', claim, 'review')
    return r.finish({'market_scope': scope, 'competitor_shares': shares, 'listed_value': listed,
                     'unlisted_value': remainder, 'market_hhi_10000': hhi, 'claims': claims,
                     'strategy_selected': False, 'inference_status': 'Claims are supplied research interpretations, not automatically proven facts'})


def validate(doc):
    return validate_with(evaluate, doc)
