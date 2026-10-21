#!/usr/bin/env python3
"""Source-bound, Decimal position/cash comparison. No side is presumed authoritative."""
from __future__ import annotations
import json, sys
from decimal import Context, Decimal, Inexact, InvalidOperation, Rounded, localcontext
from datetime import date
from pathlib import Path
from native_integrity import attach_source, canonical_hash

DEFAULT_CONFIG = {"quantity_tolerance": "0", "cash_tolerance": "0.01",
                  "quantity_materiality": "100", "cash_materiality_base": "1000",
                  "aggregation_mode": "one-to-one", "pending_settlement_days": 3, "fx_rates": {}}
BREAK_TYPES = ("quantity_break", "cash_break", "missing_internal", "missing_external",
               "pending_settlement", "duplicate", "not_comparable")
TRADE_ROUTE = "trade-break-resolver"
DISCLAIMER = ("Reconciliation and proposed reconciling items only; no record has been repaired or "
              "adjusted and no asset, position, or cash has been moved. Breaks and proposed items "
              "require human review and authorized action in the book of record.")


def number(value):
    if value is None or isinstance(value, bool): raise ValueError("known finite numeric amount required")
    literal = str(value).strip()
    if len(literal) > 256: raise ValueError('numeric literal exceeds 256 characters')
    try: n = Decimal(literal)
    except InvalidOperation as exc: raise ValueError("invalid numeric amount") from exc
    if not n.is_finite(): raise ValueError("finite numeric amount required")
    parts = n.as_tuple()
    if len(parts.digits) > 38 or not -38 <= parts.exponent <= 38 or (n and not -38 <= n.adjusted() <= 38):
        raise ValueError('numeric value exceeds supported precision/magnitude: 38 coefficient digits, exponent and adjusted exponent -38..38')
    return n


def text_number(value):
    return format(value, 'f') if value is not None else None


def _compute(doc):
    cfg = {**DEFAULT_CONFIG, **doc.get('config', {})}
    cutoff = date.fromisoformat(doc['as_of'][:10])
    if cfg['aggregation_mode'] not in {'one-to-one', 'sum'}: raise ValueError('unsupported aggregation_mode')
    grouped = {}
    for side in ('internal', 'external'):
        seen = set()
        for row in doc.get(side+'_records', []):
            if row['record_id'] in seen: raise ValueError('duplicate record_id on '+side)
            seen.add(row['record_id'])
            grouped.setdefault(str(row['match_key']), {'internal': [], 'external': []})[side].append(row)
    breaks, groups, matched = [], [], 0
    for key, sides in sorted(grouped.items()):
        ir, er = sides['internal'], sides['external']
        rows = ir + er
        sample = rows[0]
        rtype, unit = sample['record_type'], sample.get('quantity_unit') if sample['record_type']=='position' else sample.get('currency')
        reasons = []
        dimensions = []
        for row in rows:
            basis = row.get('position_basis') or doc.get('position_basis')
            row_unit = row.get('quantity_unit') if row['record_type']=='position' else row.get('currency')
            if not basis or not row_unit: reasons.append('explicit position/cash basis and unit required')
            dimensions.append((row.get('account'),row['record_type'],str(row.get('currency') or '').upper(),row_unit,basis,row.get('security_id')))
            try:
                if date.fromisoformat(str(row.get('date'))[:10]) > cutoff: reasons.append('record date is after cutoff')
            except (ValueError, TypeError): reasons.append('record date missing or invalid')
        if len(set(dimensions)) != 1: reasons.append('account/instrument/type/currency/unit/basis differs within supplied match_key')
        if (len(ir)>1 or len(er)>1) and cfg['aggregation_mode']!='sum': reasons.append('multiple rows require explicit sum aggregation at compatible grain')
        duplicate = any(row.get('duplicate_of') for row in rows)
        if duplicate: reasons.append('declared duplicate requires investigation; not silently summed or removed')
        lineage = [f"{side}:{r.get('source_ref')}@{r.get('date')}" for side in ('internal','external') for r in sides[side]]
        it = sum((number(r.get('quantity') if r['record_type']=='position' else r.get('amount')) for r in ir),Decimal(0))
        et = sum((number(r.get('quantity') if r['record_type']=='position' else r.get('amount')) for r in er),Decimal(0))
        diff = it-et if not reasons else None
        tol = number(cfg['quantity_tolerance'] if rtype=='position' else cfg['cash_tolerance'])
        if tol < 0: raise ValueError('tolerance cannot be negative')
        comparable = not reasons
        within = comparable and ir and er and abs(diff)<=tol
        b = None
        if within:
            matched += 1
        else:
            btype = 'duplicate' if duplicate else 'not_comparable' if reasons else 'missing_internal' if not ir else 'missing_external' if not er else 'quantity_break' if rtype=='position' else 'cash_break'
            # A date alone does not establish settlement causality.
            if comparable and all(r.get('settlement_evidence_ref') for r in rows):
                try:
                    if any(0 < (date.fromisoformat(r['settle_date'][:10])-cutoff).days <= int(cfg['pending_settlement_days']) for r in rows): btype='pending_settlement'
                except (KeyError, TypeError, ValueError): pass
            routed = any(r.get('route_hint')=='trade_discrepancy' for r in rows)
            base_impact = None
            if comparable and rtype=='cash':
                rate = '1' if str(unit).upper()==str(doc['base_currency']).upper() else cfg.get('fx_rates',{}).get(str(unit).upper())
                if rate is not None:
                    fx = number(rate)
                    if fx <= 0: raise ValueError('FX rate must be positive')
                    base_impact=diff*fx
            material = abs(diff)>=number(cfg['quantity_materiality']) if comparable and rtype=='position' else abs(base_impact)>=number(cfg['cash_materiality_base']) if base_impact is not None else None
            bid=f'BRK-{len(breaks)+1:04d}'
            proposal = None
            if comparable and not routed and btype!='pending_settlement':
                proposal={'proposed_item_id':f'PITM-{len(breaks)+1:04d}','break_id':bid,'status':'PROPOSED',
                          'adjustment_amount':None,'selected_alternative':None,
                          'alternatives':[{'condition':'internal record independently established wrong','side':'internal','possible_adjustment':text_number(-diff)},
                                          {'condition':'external record independently established wrong','side':'external','possible_adjustment':text_number(diff)},
                                          {'condition':'cause unresolved or timing supported','side':None,'possible_adjustment':None}],
                          'action':'Investigate both source records and obtain owner review before selecting a correction; no side is presumed authoritative.'}
            b={'break_id':bid,'type':btype,'match_key':key,'record_type':rtype,'account':sample.get('account'),
               'unit':unit,'currency':sample.get('currency'),'break_amount':text_number(diff),'base_impact':text_number(base_impact),
               'material':material,'materiality_status':'known' if material is not None else 'not_evaluable',
               'lineage':lineage,'requires_correction':False,'requires_investigation':True,'proposed_item':proposal,
               'routing':{'route_to':TRADE_ROUTE,'reason':'supplied trade-discrepancy classification'} if routed else None,
               'note':'; '.join(sorted(set(reasons))) or 'Difference remains unresolved; supporting evidence and professional review required.'}
            breaks.append(b)
        groups.append({'match_key':key,'record_type':rtype,'unit':unit,'account':sample.get('account'),
                       'internal_record_ids':[r['record_id'] for r in ir],'external_record_ids':[r['record_id'] for r in er],
                       'aggregation_mode':cfg['aggregation_mode'],'comparable':comparable,
                       'internal_total':text_number(it) if comparable else None,'external_total':text_number(et) if comparable else None,
                       'difference':text_number(diff),'breaks_total':text_number(diff if b and comparable else Decimal(0)) if comparable else None,
                       'within_tolerance_difference':text_number(diff if within else Decimal(0)) if comparable else None,
                       'residual':'0' if comparable else None,'ties_out':True if comparable else None})
    fp=canonical_hash(doc)
    proposed=[b['proposed_item'] for b in breaks if b['proposed_item']]
    out={'reconciliation_id':f"pcr-{doc['entity']}-{doc['as_of']}-{fp[:8]}",'entity':doc['entity'],'as_of':doc['as_of'],
         'base_currency':doc['base_currency'],'config_version':doc.get('config_version'),'input_fingerprint':fp,
         'effective_config':cfg,'tie_out':{'groups':groups,'all_ties_out':all(g['ties_out'] is True for g in groups),
                                          'status':'needs_data' if any(not g['comparable'] for g in groups) else 'reconciled_with_breaks' if breaks else 'clean_tie_out'},
         'matched_count':matched,'breaks':breaks,'proposed_items':proposed,'routed_breaks':[b['break_id'] for b in breaks if b['routing']],
         'summary':{'total_breaks':len(breaks),'by_type':{t:sum(b['type']==t for b in breaks) for t in BREAK_TYPES if any(b['type']==t for b in breaks)},
                    'material_breaks':sum(b['material'] is True for b in breaks),'unknown_materiality_breaks':sum(b['material'] is None for b in breaks),
                    'proposed_items':len(proposed),'documented_pending':sum(b['type']=='pending_settlement' for b in breaks)},
         'disclaimer':DISCLAIMER}
    return attach_source(out,doc)


def compute(doc):
    """Keep all arithmetic local and exact within the documented input bounds."""
    with localcontext(Context(prec=256)) as context:
        context.traps[Inexact] = True
        context.traps[Rounded] = True
        if sum(len(doc.get(side+'_records', [])) for side in ('internal', 'external')) > 100000:
            raise ValueError('at most 100000 total reconciliation records supported')
        cfg = {**DEFAULT_CONFIG, **doc.get('config', {})}
        for key in ('quantity_tolerance', 'cash_tolerance', 'quantity_materiality', 'cash_materiality_base'):
            number(cfg[key])
        for rate in cfg.get('fx_rates', {}).values():
            if number(rate) <= 0: raise ValueError('FX rate must be positive')
        return _compute(doc)


def main(argv):
    selftest='--selftest' in argv
    path=Path(__file__).resolve().parents[1]/'evals/files/reconciliation_example.json' if selftest else Path(argv[0]) if argv else None
    doc=json.loads(path.read_text() if path else sys.stdin.read());out=compute(doc)
    if selftest:
        from validate_output import validate
        errors=validate(out,original_input=doc)
        for e in errors: print('ERROR',e)
        print(f'reconciliation self-test: {len(errors)} error(s)');return bool(errors)
    print(json.dumps(out,indent=2));return 0

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
